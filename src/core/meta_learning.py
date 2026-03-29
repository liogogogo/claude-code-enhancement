"""
元学习模块 - 核心模块
实现 MAML (Model-Agnostic Meta-Learning) 算法
快速适应新任务
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class Task:
    """任务定义"""
    task_id: str
    train_data: Any  # 训练数据
    test_data: Any   # 测试数据
    metadata: Dict[str, Any]


@dataclass
class MetaLearningConfig:
    """元学习配置"""
    inner_lr: float = 0.01  # 内循环学习率
    outer_lr: float = 0.001  # 外循环学习率
    inner_steps: int = 5  # 内循环步数
    meta_batch_size: int = 32  # 元批次大小
    num_iterations: int = 1000  # 元迭代次数


class MAML:
    """
    Model-Agnostic Meta-Learning (MAML)

    实现元学习算法，使模型能够快速适应新任务

    算法流程:
    1. 采样一批任务
    2. 对每个任务:
       a. 在支持集上计算梯度
       b. 更新参数（内循环）
       c. 在查询集上计算损失（外循环）
    3. 在元批次上平均梯度
    4. 更新初始参数（外循环）
    """

    def __init__(
        self,
        model: nn.Module,
        config: MetaLearningConfig,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        初始化 MAML

        Args:
            model: 基础模型
            config: 元学习配置
            device: 设备
        """
        self.model = model.to(device)
        self.config = config
        self.device = device

        # 元优化器
        self.meta_optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=config.outer_lr,
        )

        # 训练历史
        self.training_history: List[Dict[str, float]] = []

    def meta_train(
        self,
        task_sampler: Callable[[], List[Task]],
        num_iterations: Optional[int] = None,
    ) -> Dict[str, List[float]]:
        """
        元训练

        Args:
            task_sampler: 任务采样函数
            num_iterations: 迭代次数（使用配置值如果为 None）

        Returns:
            训练历史 {"meta_loss": [...], "train_accuracy": [...], "val_accuracy": [...]}
        """
        num_iterations = num_iterations or self.config.num_iterations

        meta_losses = []
        train_accuracies = []
        val_accuracies = []

        for iteration in range(num_iterations):
            # 1. 采样一批任务
            tasks = task_sampler()
            tasks = tasks[:self.config.meta_batch_size]

            # 2. 元更新
            meta_loss, train_acc, val_acc = self._meta_update(tasks)

            # 3. 记录历史
            meta_losses.append(meta_loss)
            train_accuracies.append(train_acc)
            val_accuracies.append(val_acc)

            # 4. 日志
            if iteration % 100 == 0:
                print(f"Iteration {iteration}: "
                      f"Meta Loss = {meta_loss:.4f}, "
                      f"Train Acc = {train_acc:.4f}, "
                      f"Val Acc = {val_acc:.4f}")

        return {
            "meta_loss": meta_losses,
            "train_accuracy": train_accuracies,
            "val_accuracy": val_accuracies,
        }

    def adapt(
        self,
        task: Task,
        num_steps: Optional[int] = None,
    ) -> nn.Module:
        """
        适应新任务

        Args:
            task: 目标任务
            num_steps: 适应步数（使用配置值如果为 None）

        Returns:
            适应后的模型
        """
        num_steps = num_steps or self.config.inner_steps

        # 复制模型
        adapted_model = deepcopy(self.model)

        # 内循环优化器
        inner_optimizer = torch.optim.SGD(
            adapted_model.parameters(),
            lr=self.config.inner_lr,
        )

        # 在任务支持集上训练
        for step in range(num_steps):
            # 前向传播
            loss, accuracy = self._task_forward(adapted_model, task.train_data)

            # 反向传播
            inner_optimizer.zero_grad()
            loss.backward()
            inner_optimizer.step()

        return adapted_model

    def evaluate(
        self,
        tasks: List[Task],
        num_adaptation_steps: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        评估元学习性能

        Args:
            tasks: 测试任务列表
            num_adaptation_steps: 适应步数

        Returns:
            评估指标
        """
        num_steps = num_adaptation_steps or self.config.inner_steps

        total_accuracy = 0.0
        total_loss = 0.0

        for task in tasks:
            # 适应任务
            adapted_model = self.adapt(task, num_steps)

            # 在查询集上评估
            loss, accuracy = self._task_forward(adapted_model, task.test_data)

            total_accuracy += accuracy
            total_loss += loss.item()

        avg_accuracy = total_accuracy / len(tasks)
        avg_loss = total_loss / len(tasks)

        return {
            "accuracy": avg_accuracy,
            "loss": avg_loss,
        }

    def _meta_update(self, tasks: List[Task]) -> Tuple[float, float, float]:
        """
        元更新（一次迭代）

        Returns:
            (元损失, 训练准确率, 验证准确率)
        """
        meta_loss = 0.0
        train_accuracy = 0.0
        val_accuracy = 0.0

        # 计算每个任务的梯度和损失
        for task in tasks:
            # 1. 内循环: 在支持集上更新
            adapted_model = self._inner_loop(task)

            # 2. 外循环: 在查询集上计算损失
            loss, accuracy = self._task_forward(adapted_model, task.test_data)

            meta_loss += loss
            val_accuracy += accuracy

            # 3. 训练准确率（支持集）
            _, train_acc = self._task_forward(self.model, task.train_data)
            train_accuracy += train_acc

        # 平均
        meta_loss /= len(tasks)
        train_accuracy /= len(tasks)
        val_accuracy /= len(tasks)

        # 元更新
        self.meta_optimizer.zero_grad()
        meta_loss.backward()
        self.meta_optimizer.step()

        return meta_loss.item(), train_accuracy, val_accuracy

    def _inner_loop(self, task: Task) -> nn.Module:
        """
        内循环: 快速适应

        Returns:
            适应后的模型
        """
        # 创建临时模型
        temp_model = deepcopy(self.model)

        # 内循环优化器
        inner_optimizer = torch.optim.SGD(
            temp_model.parameters(),
            lr=self.config.inner_lr,
        )

        # 在支持集上训练
        for _ in range(self.config.inner_steps):
            loss, _ = self._task_forward(temp_model, task.train_data)

            inner_optimizer.zero_grad()
            loss.backward()
            inner_optimizer.step()

        return temp_model

    def _task_forward(
        self,
        model: nn.Module,
        data: Any,
    ) -> Tuple[torch.Tensor, float]:
        """
        任务前向传播

        Args:
            model: 模型
            data: 数据

        Returns:
            (损失, 准确率)
        """
        # TODO: 实现具体的前向传播逻辑
        # 这里需要根据具体任务类型实现

        # Placeholder
        loss = torch.tensor(0.0, requires_grad=True).to(self.device)
        accuracy = 0.0

        return loss, accuracy

    def save_checkpoint(self, path: str) -> None:
        """
        保存检查点

        Args:
            path: 保存路径
        """
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "meta_optimizer_state_dict": self.meta_optimizer.state_dict(),
            "config": self.config,
            "training_history": self.training_history,
        }

        torch.save(checkpoint, path)

    def load_checkpoint(self, path: str) -> None:
        """
        加载检查点

        Args:
            path: 加载路径
        """
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.meta_optimizer.load_state_dict(checkpoint["meta_optimizer_state_dict"])
        self.config = checkpoint["config"]
        self.training_history = checkpoint["training_history"]


class MetaLearningOptimizer:
    """
    元学习优化器

    封装 MAML，提供高层接口
    """

    def __init__(
        self,
        model: nn.Module,
        config: Optional[MetaLearningConfig] = None,
    ):
        """
        初始化元学习优化器

        Args:
            model: 基础模型
            config: 元学习配置
        """
        self.config = config or MetaLearningConfig()
        self.maml = MAML(model, self.config)

    def meta_train(
        self,
        support_tasks: List[Task],
        validation_tasks: Optional[List[Task]] = None,
    ) -> Dict[str, List[float]]:
        """
        元训练

        Args:
            support_tasks: 支持任务列表
            validation_tasks: 验证任务列表（可选）

        Returns:
            训练历史
        """
        # 定义任务采样器
        def task_sampler() -> List[Task]:
            import random
            return random.sample(support_tasks, k=self.config.meta_batch_size)

        # 元训练
        history = self.maml.meta_train(task_sampler)

        # 验证
        if validation_tasks:
            val_metrics = self.maml.evaluate(validation_tasks)
            print(f"Validation Metrics: {val_metrics}")

        return history

    def adapt_to_task(self, task: Task, steps: Optional[int] = None) -> nn.Module:
        """
        适应到新任务

        Args:
            task: 目标任务
            steps: 适应步数

        Returns:
            适应后的模型
        """
        return self.maml.adapt(task, steps)

    def get_model(self) -> nn.Module:
        """
        获取当前模型

        Returns:
            模型
        """
        return self.maml.model
