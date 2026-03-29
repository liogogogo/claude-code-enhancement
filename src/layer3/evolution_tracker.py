"""
进化追踪器 - Layer 3 核心模块
追踪自我进化和性能变化
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path
from datetime import datetime
import numpy as np


class EvolutionMetric(Enum):
    """进化指标"""
    TASK_SUCCESS_RATE = "task_success_rate"
    CODE_QUALITY_SCORE = "code_quality_score"
    FIX_SUCCESS_RATE = "fix_success_rate"
    AVG_FIX_TIME = "avg_fix_time"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"


@dataclass
class EvolutionCheckpoint:
    """进化检查点"""
    timestamp: str
    generation: int  # 代数
    metrics: Dict[str, float]
    changes: List[str]  # 自上次检查点的变更
    performance_delta: Dict[str, float]  # 相对于上次检查点的变化


@dataclass
class EvolutionReport:
    """进化报告"""
    start_time: str
    end_time: str
    total_generations: int
    initial_metrics: Dict[str, float]
    final_metrics: Dict[str, float]
    total_improvement: Dict[str, float]
    checkpoints: List[EvolutionCheckpoint]
    summary: str


class EvolutionTracker:
    """
    进化追踪器

    功能:
    - 记录每一代的性能
    - 计算进化趋势
    - 生成进化报告
    - 可视化进化过程
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        metrics_to_track: Optional[List[EvolutionMetric]] = None,
    ):
        """
        初始化进化追踪器

        Args:
            checkpoint_path: 检查点保存路径
            metrics_to_track: 要追踪的指标列表
        """
        self.checkpoint_path = checkpoint_path
        self.metrics_to_track = metrics_to_track or [
            EvolutionMetric.TASK_SUCCESS_RATE,
            EvolutionMetric.CODE_QUALITY_SCORE,
            EvolutionMetric.FIX_SUCCESS_RATE,
            EvolutionMetric.AVG_FIX_TIME,
        ]

        self.checkpoints: List[EvolutionCheckpoint] = []
        self.generation = 0
        self.start_time = datetime.now()

        # 加载历史检查点
        if checkpoint_path:
            self._load_checkpoints()

    def record_generation(
        self,
        metrics: Dict[str, float],
        changes: List[str],
    ) -> EvolutionCheckpoint:
        """
        记录新一代

        Args:
            metrics: 性能指标
            changes: 变更列表

        Returns:
            EvolutionCheckpoint: 创建的检查点
        """
        # 计算相对于上次检查点的变化
        performance_delta = {}

        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]

            for key, value in metrics.items():
                if key in last_checkpoint.metrics:
                    last_value = last_checkpoint.metrics[key]
                    performance_delta[key] = value - last_value
                else:
                    performance_delta[key] = 0.0

        # 创建检查点
        checkpoint = EvolutionCheckpoint(
            timestamp=datetime.now().isoformat(),
            generation=self.generation,
            metrics=metrics,
            changes=changes,
            performance_delta=performance_delta,
        )

        self.checkpoints.append(checkpoint)
        self.generation += 1

        # 保存检查点
        if self.checkpoint_path:
            self._save_checkpoints()

        return checkpoint

    def get_evolution_trend(self, metric: EvolutionMetric) -> Dict[str, Any]:
        """
        获取指标进化趋势

        Args:
            metric: 要分析的指标

        Returns:
            趋势信息 {"direction": "up/down/stable", "rate": ..., "confidence": ...}
        """
        if not self.checkpoints:
            return {
                "direction": "unknown",
                "rate": 0.0,
                "confidence": 0.0,
            }

        # 提取指标历史
        values = []
        for checkpoint in self.checkpoints:
            if metric.value in checkpoint.metrics:
                values.append(checkpoint.metrics[metric.value])

        if len(values) < 3:
            return {
                "direction": "insufficient_data",
                "rate": 0.0,
                "confidence": 0.0,
            }

        # 计算趋势（线性回归）
        x = np.arange(len(values))
        y = np.array(values)

        # 线性拟合
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # 计算R²（拟合优度）
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # 判断趋势方向
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "up"
        else:
            direction = "down"

        return {
            "direction": direction,
            "rate": float(slope),
            "confidence": float(r_squared),
            "initial_value": float(values[0]),
            "final_value": float(values[-1]),
            "total_change": float(values[-1] - values[0]),
        }

    def get_best_generation(self, metric: EvolutionMetric) -> Optional[EvolutionCheckpoint]:
        """
        获取最佳代

        Args:
            metric: 评估指标

        Returns:
            最佳检查点
        """
        best_checkpoint = None
        best_value = None

        for checkpoint in self.checkpoints:
            if metric.value in checkpoint.metrics:
                value = checkpoint.metrics[metric.value]

                if best_value is None or value > best_value:
                    best_value = value
                    best_checkpoint = checkpoint

        return best_checkpoint

    def generate_report(self) -> EvolutionReport:
        """
        生成进化报告

        Returns:
            EvolutionReport: 完整的进化报告
        """
        if not self.checkpoints:
            return EvolutionReport(
                start_time=self.start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                total_generations=0,
                initial_metrics={},
                final_metrics={},
                total_improvement={},
                checkpoints=[],
                summary="无进化数据",
            )

        # 初始和最终指标
        initial_metrics = self.checkpoints[0].metrics
        final_metrics = self.checkpoints[-1].metrics

        # 总体改进
        total_improvement = {}
        for key in final_metrics:
            if key in initial_metrics:
                total_improvement[key] = final_metrics[key] - initial_metrics[key]

        # 生成摘要
        summary = self._generate_summary(initial_metrics, final_metrics, total_improvement)

        return EvolutionReport(
            start_time=self.checkpoints[0].timestamp,
            end_time=self.checkpoints[-1].timestamp,
            total_generations=len(self.checkpoints),
            initial_metrics=initial_metrics,
            final_metrics=final_metrics,
            total_improvement=total_improvement,
            checkpoints=self.checkpoints,
            summary=summary,
        )

    def visualize_evolution(self, metrics: Optional[List[EvolutionMetric]] = None) -> str:
        """
        可视化进化过程

        Args:
            metrics: 要可视化的指标（全部如果为 None）

        Returns:
            ASCII 图表
        """
        if not self.checkpoints:
            return "无进化数据"

        metrics_to_plot = metrics or self.metrics_to_track

        lines = []
        lines.append("=" * 80)
        lines.append("进化趋势图")
        lines.append("=" * 80)

        for metric in metrics_to_plot:
            trend = self.get_evolution_trend(metric)

            lines.append(f"\n{metric.value}:")
            lines.append(f"  趋势: {trend['direction'].upper()}")
            lines.append(f"  变化率: {trend['rate']:.4f}/代")
            lines.append(f"  置信度: {trend['confidence']:.2f}")

            if 'initial_value' in trend:
                lines.append(f"  初始值: {trend['initial_value']:.2f}")
                lines.append(f"  当前值: {trend['final_value']:.2f}")
                lines.append(f"  总变化: {trend['total_change']:+.2f}")

            # ASCII 折线图
            chart = self._generate_ascii_chart(metric, width=60, height=10)
            lines.append(f"\n{chart}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def compare_generations(
        self,
        gen1: int,
        gen2: int,
    ) -> Dict[str, Any]:
        """
        比较两代

        Args:
            gen1: 代数1
            gen2: 代数2

        Returns:
            比较结果
        """
        if gen1 >= len(self.checkpoints) or gen2 >= len(self.checkpoints):
            return {"error": "无效的代数"}

        checkpoint1 = self.checkpoints[gen1]
        checkpoint2 = self.checkpoints[gen2]

        comparison = {
            "generation1": gen1,
            "generation2": gen2,
            "timestamp1": checkpoint1.timestamp,
            "timestamp2": checkpoint2.timestamp,
            "metric_deltas": {},
            "changes_between": [],
        }

        # 比较指标
        for key in checkpoint2.metrics:
            if key in checkpoint1.metrics:
                delta = checkpoint2.metrics[key] - checkpoint1.metrics[key]
                comparison["metric_deltas"][key] = delta

        # 变更列表
        comparison["changes_between"] = checkpoint2.changes

        return comparison

    def _generate_summary(
        self,
        initial: Dict[str, float],
        final: Dict[str, float],
        improvement: Dict[str, float],
    ) -> str:
        """生成摘要"""
        lines = []
        lines.append("进化摘要:")

        for key, delta in improvement.items():
            if delta > 0:
                lines.append(f"  ✓ {key}: +{delta:.2%}")
            elif delta < 0:
                lines.append(f"  ✗ {key}: {delta:.2%}")
            else:
                lines.append(f"  - {key}: 无变化")

        return "\n".join(lines)

    def _generate_ascii_chart(
        self,
        metric: EvolutionMetric,
        width: int = 60,
        height: int = 10,
    ) -> str:
        """
        生成 ASCII 折线图
        """
        # 提取数据
        values = []
        for checkpoint in self.checkpoints:
            if metric.value in checkpoint.metrics:
                values.append(checkpoint.metrics[metric.value])

        if len(values) < 2:
            return "  数据不足"

        # 归一化到 [0, height-1]
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val > min_val else 1.0

        normalized = [
            int((v - min_val) / val_range * (height - 1))
            for v in values
        ]

        # 构建图表
        chart = []
        for y in range(height - 1, -1, -1):
            line = "  "

            for x in range(len(normalized)):
                if normalized[x] == y:
                    if x == 0:
                        line += "●"
                    elif x == len(normalized) - 1:
                        line += "■"
                    else:
                        line += "·"
                else:
                    line += " "

            # 添加Y轴标签
            if y == height - 1:
                label = f"{max_val:.2f}"
            elif y == 0:
                label = f"{min_val:.2f}"
            else:
                label = ""

            line += f" | {label}"
            chart.append(line)

        # 添加X轴
        chart.append("  " + "─" * len(normalized))
        chart.append(f"  代数: 0 → {len(normalized) - 1}")

        return "\n".join(chart)

    def _load_checkpoints(self) -> None:
        """加载检查点"""
        if not self.checkpoint_path:
            return

        path = Path(self.checkpoint_path)
        if not path.exists():
            return

        with open(path, "r") as f:
            data = json.load(f)

        # TODO: 反序列化检查点
        # self.checkpoints = [EvolutionCheckpoint(**item) for item in data.get("checkpoints", [])]

    def _save_checkpoints(self) -> None:
        """保存检查点"""
        if not self.checkpoint_path:
            return

        path = Path(self.checkpoint_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "checkpoints": [asdict(c) for c in self.checkpoints],
            "generation": self.generation,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
