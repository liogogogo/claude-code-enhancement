"""
策略优化器 - 核心模块
基于 PPO (Proximal Policy Optimization) 的强化学习优化
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class PPOConfig:
    """PPO 配置"""
    learning_rate: float = 3e-4
    gamma: float = 0.99  # 折扣因子
    eps_clip: float = 0.2  # PPO 裁剪参数
    k_epochs: int = 4  # 每次更新训练的轮数
    entropy_coef: float = 0.01  # 熵系数（鼓励探索）
    value_coef: float = 0.5  # 价值损失系数


class PolicyNetwork(nn.Module):
    """
    策略网络
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
    ):
        super().__init__()

        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1),
        )

        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向传播

        Args:
            state: 状态 [batch_size, state_dim]

        Returns:
            (动作概率分布, 状态价值)
        """
        action_probs = self.actor(state)
        state_value = self.critic(state)

        return action_probs, state_value

    def act(self, state: torch.Tensor) -> int:
        """
        采样动作

        Args:
            state: 状态 [state_dim]

        Returns:
            动作
        """
        action_probs, _ = self.forward(state)

        # 从分布中采样
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()

        return action.item()


class PPO:
    """
    Proximal Policy Optimization (PPO)

    强化学习算法，用于优化决策策略
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        config: PPOConfig,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        初始化 PPO

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            config: PPO 配置
            device: 设备
        """
        self.config = config
        self.device = device

        # 策略网络
        self.policy = PolicyNetwork(state_dim, action_dim).to(device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=config.learning_rate)

        # 旧策略（用于计算比率）
        self.policy_old = PolicyNetwork(state_dim, action_dim).to(device)
        self.policy_old.load_state_dict(self.policy.state_dict())

        # 经验缓冲区
        self.buffer: List[Dict[str, Any]] = []

        # 训练历史
        self.training_history: List[Dict[str, float]] = []

    def select_action(self, state: np.ndarray) -> int:
        """
        选择动作

        Args:
            state: 状态 [state_dim]

        Returns:
            动作
        """
        state_tensor = torch.FloatTensor(state).to(self.device)
        action = self.policy_old.act(state_tensor)

        return action

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        done: bool,
    ) -> None:
        """
        存储转移

        Args:
            state: 状态
            action: 动作
            reward: 奖励
            done: 是否结束
        """
        self.buffer.append({
            "state": state,
            "action": action,
            "reward": reward,
            "done": done,
        })

    def update(self) -> Dict[str, float]:
        """
        更新策略

        Returns:
            训练指标
        """
        # 计算折扣奖励
        rewards = []
        discounted_reward = 0

        for transition in reversed(self.buffer):
            if transition["done"]:
                discounted_reward = 0
            discounted_reward = transition["reward"] + self.config.gamma * discounted_reward
            rewards.insert(0, discounted_reward)

        # 归一化奖励
        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-7)

        # 转换为张量
        states = torch.FloatTensor([t["state"] for t in self.buffer]).to(self.device)
        actions = torch.LongTensor([t["action"] for t in self.buffer]).to(self.device)

        # 旧策略的动作概率
        with torch.no_grad():
            old_probs, _ = self.policy_old(states)
            old_probs = old_probs.gather(1, actions.unsqueeze(1)).squeeze(1)

        # K 次更新
        total_loss = 0.0
        total_policy_loss = 0.0
        total_value_loss = 0.0

        for _ in range(self.config.k_epochs):
            # 当前策略的动作概率和状态价值
            probs, values = self.policy(states)
            probs = probs.gather(1, actions.unsqueeze(1)).squeeze(1)
            values = values.squeeze(1)

            # 计算比率
            ratio = torch.exp(torch.log(probs + 1e-8) - torch.log(old_probs + 1e-8))

            # 优势函数
            advantages = rewards - values.detach()

            # PPO 裁剪目标
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.config.eps_clip, 1 + self.config.eps_clip) * advantages

            # 策略损失
            policy_loss = -torch.min(surr1, surr2).mean()

            # 价值损失
            value_loss = F.mse_loss(values, rewards)

            # 熵损失（鼓励探索）
            entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=-1).mean()

            # 总损失
            loss = policy_loss + self.config.value_coef * value_loss - self.config.entropy_coef * entropy

            # 优化
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()

        # 更新旧策略
        self.policy_old.load_state_dict(self.policy.state_dict())

        # 清空缓冲区
        self.buffer.clear()

        # 返回训练指标
        metrics = {
            "loss": total_loss / self.config.k_epochs,
            "policy_loss": total_policy_loss / self.config.k_epochs,
            "value_loss": total_value_loss / self.config.k_epochs,
        }

        self.training_history.append(metrics)

        return metrics

    def save_model(self, path: str) -> None:
        """
        保存模型

        Args:
            path: 保存路径
        """
        torch.save({
            "policy_state_dict": self.policy.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.config,
            "training_history": self.training_history,
        }, path)

    def load_model(self, path: str) -> None:
        """
        加载模型

        Args:
            path: 加载路径
        """
        checkpoint = torch.load(path)

        self.policy.load_state_dict(checkpoint["policy_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.config = checkpoint["config"]
        self.training_history = checkpoint["training_history"]

        self.policy_old.load_state_dict(self.policy.state_dict())


class StrategyOptimizer:
    """
    策略优化器

    封装 PPO，提供高层接口
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        config: Optional[PPOConfig] = None,
    ):
        """
        初始化策略优化器

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            config: PPO 配置
        """
        self.config = config or PPOConfig()
        self.ppo = PPO(state_dim, action_dim, self.config)

    def train(
        self,
        env: Any,  # 环境
        num_episodes: int = 1000,
        max_steps_per_episode: int = 1000,
        update_frequency: int = 2000,
    ) -> List[Dict[str, float]]:
        """
        训练策略

        Args:
            env: 环境
            num_episodes: 训练回合数
            max_steps_per_episode: 每回合最大步数
            update_frequency: 更新频率（步数）

        Returns:
            训练历史
        """
        all_rewards = []
        all_metrics = []

        for episode in range(num_episodes):
            state, _ = env.reset()
            episode_reward = 0

            for step in range(max_steps_per_episode):
                # 选择动作
                action = self.ppo.select_action(state)

                # 执行动作
                next_state, reward, done, truncated, info = env.step(action)
                episode_reward += reward

                # 存储转移
                self.ppo.store_transition(state, action, reward, done or truncated)

                # 更新策略
                if len(self.ppo.buffer) >= update_frequency:
                    metrics = self.ppo.update()
                    all_metrics.append(metrics)

                state = next_state

                if done or truncated:
                    break

            all_rewards.append(episode_reward)

            # 日志
            if episode % 100 == 0:
                avg_reward = np.mean(all_rewards[-100:])
                print(f"Episode {episode}, Avg Reward: {avg_reward:.2f}")

        return all_metrics

    def evaluate(self, env: Any, num_episodes: int = 10) -> Dict[str, float]:
        """
        评估策略

        Args:
            env: 环境
            num_episodes: 评估回合数

        Returns:
            评估指标
        """
        total_rewards = []

        for _ in range(num_episodes):
            state, _ = env.reset()
            episode_reward = 0
            done = False

            while not done:
                action = self.ppo.select_action(state)
                next_state, reward, done, truncated, info = env.step(action)
                episode_reward += reward
                state = next_state

                if truncated:
                    break

            total_rewards.append(episode_reward)

        return {
            "mean_reward": np.mean(total_rewards),
            "std_reward": np.std(total_rewards),
        }
