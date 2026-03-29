"""
对比学习模块 - Layer 2 核心模块
通过对比正负样本学习代码质量
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class CodePair:
    """代码对（用于对比学习）"""
    anchor: str  # 原始代码
    positive: str  # 改进后的代码（正确）
    negative: str  # 退化后的代码（错误）
    label: float  # 相似度标签 [0, 1]


@dataclass
class ContrastiveConfig:
    """对比学习配置"""
    embedding_dim: int = 768
    hidden_dim: int = 256
    temperature: float = 0.07
    learning_rate: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 10


class CodeEncoder(nn.Module):
    """
    代码编码器

    将代码片段编码为固定维度的向量表示
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 768,
        hidden_dim: int = 256,
        num_layers: int = 2,
    ):
        super().__init__()

        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=8,
            dim_feedforward=hidden_dim,
            num_layers=num_layers,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 池化层
        self.pooling = nn.AdaptiveAvgPool1d(1)

        # 投影层（用于对比学习）
        self.projection = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        """
        前向传播

        Args:
            input_ids: 输入 token IDs [batch_size, seq_len]
            attention_mask: 注意力掩码 [batch_size, seq_len]

        Returns:
            编码向量 [batch_size, hidden_dim]
        """
        # 词嵌入
        embeddings = self.embedding(input_ids)  # [batch_size, seq_len, embedding_dim]

        # Transformer 编码
        embeddings = embeddings.transpose(0, 1)  # [seq_len, batch_size, embedding_dim]
        encoded = self.transformer(embeddings)  # [seq_len, batch_size, embedding_dim]
        encoded = encoded.transpose(0, 1)  # [batch_size, seq_len, embedding_dim]

        # 注意力掩码
        if attention_mask is not None:
            mask = attention_mask.unsqueeze(-1).expand(encoded.size()).float()
            encoded = encoded * mask

        # 平均池化
        pooled = encoded.mean(dim=1)  # [batch_size, embedding_dim]

        # 投影
        projected = self.projection(pooled)  # [batch_size, hidden_dim]

        # L2 归一化
        projected = F.normalize(projected, p=2, dim=1)

        return projected


class ContrastiveLoss(nn.Module):
    """
    对比损失函数

    基于 InfoNCE 损失
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        """
        计算对比损失

        Args:
            anchor: 锚点向量 [batch_size, hidden_dim]
            positive: 正样本向量 [batch_size, hidden_dim]
            negative: 负样本向量 [batch_size, hidden_dim]

        Returns:
            损失值
        """
        # 计算相似度
        pos_sim = torch.sum(anchor * positive, dim=1) / self.temperature
        neg_sim = torch.sum(anchor * negative, dim=1) / self.temperature

        # InfoNCE 损失
        loss = -torch.mean(torch.log(torch.exp(pos_sim) / (
            torch.exp(pos_sim) + torch.exp(neg_sim)
        )))

        return loss


class CodeDataset(Dataset):
    """
    代码数据集
    """

    def __init__(self, code_pairs: List[CodePair], tokenizer: Any):
        """
        初始化数据集

        Args:
            code_pairs: 代码对列表
            tokenizer: 分词器
        """
        self.code_pairs = code_pairs
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.code_pairs)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        获取样本

        Returns:
            {
                "anchor_ids": ...,
                "positive_ids": ...,
                "negative_ids": ...,
                "attention_mask": ...,
            }
        """
        pair = self.code_pairs[idx]

        # 分词
        anchor_tokens = self.tokenizer.encode(pair.anchor)
        positive_tokens = self.tokenizer.encode(pair.positive)
        negative_tokens = self.tokenizer.encode(pair.negative)

        # Padding
        max_len = max(len(anchor_tokens), len(positive_tokens), len(negative_tokens))

        anchor_ids = torch.tensor(self._pad_tokens(anchor_tokens, max_len))
        positive_ids = torch.tensor(self._pad_tokens(positive_tokens, max_len))
        negative_ids = torch.tensor(self._pad_tokens(negative_tokens, max_len))

        # 注意力掩码
        attention_mask = torch.tensor([
            [1] * len(anchor_tokens) + [0] * (max_len - len(anchor_tokens)),
            [1] * len(positive_tokens) + [0] * (max_len - len(positive_tokens)),
            [1] * len(negative_tokens) + [0] * (max_len - len(negative_tokens)),
        ])

        return {
            "anchor_ids": anchor_ids,
            "positive_ids": positive_ids,
            "negative_ids": negative_ids,
            "attention_mask": attention_mask,
        }

    def _pad_tokens(self, tokens: List[int], max_len: int) -> List[int]:
        """Padding tokens"""
        if len(tokens) >= max_len:
            return tokens[:max_len]
        return tokens + [0] * (max_len - len(tokens))


class ContrastiveLearningModule:
    """
    对比学习模块

    功能:
    - 训练代码表示模型
    - 学习代码质量判别
    - 生成代码嵌入向量
    """

    def __init__(
        self,
        config: ContrastiveConfig,
        vocab_size: int = 50000,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        初始化对比学习模块

        Args:
            config: 对比学习配置
            vocab_size: 词汇表大小
            device: 设备
        """
        self.config = config
        self.device = device

        # 初始化模型
        self.encoder = CodeEncoder(
            vocab_size=vocab_size,
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim,
        ).to(device)

        # 初始化损失函数
        self.criterion = ContrastiveLoss(temperature=config.temperature)

        # 初始化优化器
        self.optimizer = torch.optim.Adam(
            self.encoder.parameters(),
            lr=config.learning_rate,
        )

    def train(
        self,
        train_pairs: List[CodePair],
        val_pairs: Optional[List[CodePair]] = None,
    ) -> Dict[str, List[float]]:
        """
        训练模型

        Args:
            train_pairs: 训练数据
            val_pairs: 验证数据（可选）

        Returns:
            训练历史 {"train_loss": [...], "val_loss": [...]}
        """
        # TODO: 实现 tokenizer
        # tokenizer = SimpleTokenizer()

        # 创建数据集和数据加载器
        # train_dataset = CodeDataset(train_pairs, tokenizer)
        # train_loader = DataLoader(
        #     train_dataset,
        #     batch_size=self.config.batch_size,
        #     shuffle=True,
        # )

        train_losses = []
        val_losses = []

        # 训练循环
        self.encoder.train()

        # for epoch in range(self.config.num_epochs):
        #     epoch_loss = 0.0
        #
        #     for batch in train_loader:
        #         # 移动到设备
        #         anchor_ids = batch["anchor_ids"].to(self.device)
        #         positive_ids = batch["positive_ids"].to(self.device)
        #         negative_ids = batch["negative_ids"].to(self.device)
        #         attention_mask = batch["attention_mask"].to(self.device)
        #
        #         # 前向传播
        #         anchor_emb = self.encoder(anchor_ids, attention_mask[:, 0, :])
        #         positive_emb = self.encoder(positive_ids, attention_mask[:, 1, :])
        #         negative_emb = self.encoder(negative_ids, attention_mask[:, 2, :])
        #
        #         # 计算损失
        #         loss = self.criterion(anchor_emb, positive_emb, negative_emb)
        #
        #         # 反向传播
        #         self.optimizer.zero_grad()
        #         loss.backward()
        #         self.optimizer.step()
        #
        #         epoch_loss += loss.item()
        #
        #     avg_loss = epoch_loss / len(train_loader)
        #     train_losses.append(avg_loss)
        #
        #     # 验证
        #     if val_pairs:
        #         val_loss = self.evaluate(val_pairs)
        #         val_losses.append(val_loss)
        #
        #     print(f"Epoch {epoch+1}/{self.config.num_epochs}, Loss: {avg_loss:.4f}")

        return {
            "train_loss": train_losses,
            "val_loss": val_losses,
        }

    def evaluate(self, val_pairs: List[CodePair]) -> float:
        """
        评估模型

        Args:
            val_pairs: 验证数据

        Returns:
            平均损失
        """
        self.encoder.eval()

        total_loss = 0.0
        # count = 0

        # with torch.no_grad():
        #     for pair in val_pairs:
        #         # 编码
        #         anchor_emb = self.encode(pair.anchor)
        #         positive_emb = self.encode(pair.positive)
        #         negative_emb = self.encode(pair.negative)
        #
        #         # 计算损失
        #         loss = self.criterion(anchor_emb, positive_emb, negative_emb)
        #         total_loss += loss.item()
        #         count += 1

        # avg_loss = total_loss / count if count > 0 else 0.0
        # return avg_loss

        return 0.0  # Placeholder

    def encode(self, code: str) -> torch.Tensor:
        """
        编码代码

        Args:
            code: 代码字符串

        Returns:
            编码向量 [hidden_dim]
        """
        self.encoder.eval()

        with torch.no_grad():
            # TODO: 实现分词
            # tokens = self.tokenizer.encode(code)
            # input_ids = torch.tensor([tokens]).to(self.device)

            # 前向传播
            # embedding = self.encoder(input_ids)
            # return embedding.cpu().squeeze(0)

            # Placeholder
            return torch.zeros(self.config.hidden_dim)

    def compute_similarity(self, code1: str, code2: str) -> float:
        """
        计算两个代码片段的相似度

        Args:
            code1: 代码1
            code2: 代码2

        Returns:
            相似度 [0, 1]
        """
        emb1 = self.encode(code1)
        emb2 = self.encode(code2)

        # 余弦相似度
        similarity = torch.sum(emb1 * emb2).item()

        return similarity

    def save_model(self, save_path: str) -> None:
        """
        保存模型

        Args:
            save_path: 保存路径
        """
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        torch.save({
            "encoder_state_dict": self.encoder.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.config,
        }, save_path)

    def load_model(self, load_path: str) -> None:
        """
        加载模型

        Args:
            load_path: 加载路径
        """
        checkpoint = torch.load(load_path, map_location=self.device)

        self.encoder.load_state_dict(checkpoint["encoder_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.config = checkpoint["config"]
