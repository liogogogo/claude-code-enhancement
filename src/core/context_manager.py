"""
上下文管理器 - 智能管理 Claude Code 的上下文窗口

功能:
- 向量数据库存储代码嵌入
- 智能检索 (RAG)
- 分层摘要 (文件级、模块级、项目级)
- 长对话维护

依赖:
- chromadb: 向量数据库
- sentence-transformers: 嵌入模型
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union, List, Dict, Tuple, Set

# 尝试导入可选依赖
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class ContextLevel(Enum):
    """上下文层级"""

    FILE = "file"  # 文件级
    MODULE = "module"  # 模块级
    PROJECT = "project"  # 项目级


class SummaryType(Enum):
    """摘要类型"""

    STRUCTURAL = "structural"  # 结构摘要
    SEMANTIC = "semantic"  # 语义摘要
    TEMPORAL = "temporal"  # 时间摘要


@dataclass
class CodeChunk:
    """代码块"""

    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodeChunk":
        return cls(
            id=data["id"],
            content=data["content"],
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            language=data["language"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class ContextSummary:
    """上下文摘要"""

    level: ContextLevel
    content: str
    tokens: int
    created_at: datetime
    source_files: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "content": self.content,
            "tokens": self.tokens,
            "created_at": self.created_at.isoformat(),
            "source_files": self.source_files,
            "metadata": self.metadata,
        }


@dataclass
class ConversationTurn:
    """对话轮次"""

    id: str
    role: str  # user, assistant, system
    content: str
    tokens: int
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "tokens": self.tokens,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class EmbeddingEngine:
    """嵌入引擎"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化嵌入引擎

        Args:
            model_name: sentence-transformers 模型名称
        """
        self.model_name = model_name
        self.model = None

        if HAS_SENTENCE_TRANSFORMERS:
            self.model = SentenceTransformer(model_name)
        else:
            print(
                "Warning: sentence-transformers not installed. Using simple hashing for embeddings."
            )

    def encode(self, text: str) -> List[float]:
        """
        生成文本嵌入

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        if self.model:
            return self.model.encode(text).tolist()
        else:
            # 简单哈希作为后备方案
            hash_obj = hashlib.sha256(text.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            return [float(hash_int % 1000) / 1000] * 384

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入"""
        if self.model:
            return self.model.encode(texts).tolist()
        else:
            return [self.encode(text) for text in texts]


class VectorStore:
    """向量存储"""

    def __init__(self, persist_directory: Optional[Path] = None):
        """
        初始化向量存储

        Args:
            persist_directory: 持久化目录
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._in_memory_store: Dict[str, dict] = {}  # 后备存储
        self._store_file = None  # 内存存储文件路径

        if HAS_CHROMA and persist_directory:
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name="code_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        elif persist_directory:
            # 使用文件存储作为降级方案
            self._store_file = persist_directory / "memory_store.json"

    def add(self, chunks: List[CodeChunk], embeddings: List[List[float]]):
        """
        添加代码块

        Args:
            chunks: 代码块列表
            embeddings: 嵌入向量列表
        """
        if self.collection:
            self.collection.add(
                ids=[c.id for c in chunks],
                embeddings=embeddings,
                documents=[c.content for c in chunks],
                metadatas=[c.to_dict() for c in chunks],
            )
        else:
            for chunk, embedding in zip(chunks, embeddings):
                self._in_memory_store[chunk.id] = {
                    "chunk": chunk.to_dict(),
                    "embedding": embedding,
                }
            # 保存到文件
            self._save_memory_store()

    def _save_memory_store(self):
        """保存内存存储到文件"""
        if self._store_file:
            self._store_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                chunk_id: {
                    "chunk": data["chunk"],
                    "embedding": data["embedding"],
                }
                for chunk_id, data in self._in_memory_store.items()
            }
            self._store_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def load_memory_store(self):
        """从文件加载内存存储"""
        if self._store_file and self._store_file.exists():
            try:
                data = json.loads(self._store_file.read_text())
                self._in_memory_store = {}
                for chunk_id, item in data.items():
                    self._in_memory_store[chunk_id] = {
                        "chunk": item["chunk"],
                        "embedding": item["embedding"],
                    }
            except Exception as e:
                print(f"Warning: Failed to load memory store: {e}")

    def search(
        self, query_embedding: List[float], n_results: int = 10
    ) -> List[Tuple[CodeChunk, float]]:
        """
        搜索相似代码块

        Args:
            query_embedding: 查询嵌入
            n_results: 返回数量

        Returns:
            (代码块, 相似度) 列表
        """
        if self.collection:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )

            chunks = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                chunk = CodeChunk.from_dict(metadata)
                chunks.append((chunk, 1 - distance))  # 转换为相似度
            return chunks
        else:
            # 简单余弦相似度计算
            results = []
            for chunk_id, data in self._in_memory_store.items():
                chunk = CodeChunk.from_dict(data["chunk"])
                embedding = data["embedding"]
                similarity = self._cosine_similarity(query_embedding, embedding)
                results.append((chunk, similarity))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:n_results]

    def delete(self, chunk_ids: List[str]):
        """删除代码块"""
        if self.collection:
            self.collection.delete(ids=chunk_ids)
        else:
            for cid in chunk_ids:
                self._in_memory_store.pop(cid, None)

    def clear(self):
        """清空存储"""
        if self.collection:
            self.client.delete_collection("code_chunks")
            self.collection = self.client.create_collection(
                name="code_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self._in_memory_store.clear()

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x**2 for x in a) ** 0.5
        norm_b = sum(x**2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot_product / (norm_a * norm_b)


class ContextManager:
    """
    上下文管理器

    功能:
    - 管理代码库的向量索引
    - 智能检索相关代码
    - 生成分层摘要
    - 管理对话历史
    """

    def __init__(
        self,
        project_path: Path,
        persist_directory: Optional[Path] = None,
        max_context_tokens: int = 1_000_000,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        初始化上下文管理器

        Args:
            project_path: 项目路径
            persist_directory: 持久化目录
            max_context_tokens: 最大上下文 token 数
            embedding_model: 嵌入模型名称
        """
        self.project_path = Path(project_path)
        self.persist_directory = persist_directory or (
            self.project_path / ".claude" / "context"
        )
        self.max_context_tokens = max_context_tokens

        # 初始化组件
        self.embedding_engine = EmbeddingEngine(embedding_model)
        self.vector_store = VectorStore(self.persist_directory)

        # 摘要存储
        self.summaries: Dict[ContextLevel, ContextSummary] = {}
        self.conversation_history: List[ConversationTurn] = []

        # 索引状态
        self._indexed_files: Set[str] = set()
        self._index_metadata: dict = {}

        # 加载持久化数据
        self._load_state()

    def index_codebase(
        self,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> dict:
        """
        索引代码库

        Args:
            file_patterns: 文件模式 (如 ["**/*.py", "**/*.ts"])
            exclude_patterns: 排除模式
            chunk_size: 块大小 (行数)
            chunk_overlap: 块重叠 (行数)

        Returns:
            索引统计
        """
        if file_patterns is None:
            file_patterns = ["**/*.py", "**/*.ts", "**/*.js", "**/*.go", "**/*.rs"]

        if exclude_patterns is None:
            exclude_patterns = [
                "**/node_modules/**",
                "**/.git/**",
                "**/__pycache__/**",
                "**/venv/**",
                "**/dist/**",
                "**/build/**",
            ]

        chunks = []
        files_processed = 0

        for pattern in file_patterns:
            for file_path in self.project_path.glob(pattern):
                # 检查排除模式
                if any(
                    file_path.match(excl) for excl in exclude_patterns
                ):
                    continue

                # 跳过已索引的文件 (除非修改)
                file_str = str(file_path)
                if file_str in self._indexed_files:
                    mtime = file_path.stat().st_mtime
                    if (
                        self._index_metadata.get(file_str, {}).get("mtime", 0)
                        >= mtime
                    ):
                        continue

                # 读取并分块
                try:
                    content = file_path.read_text(encoding="utf-8")
                    file_chunks = self._chunk_file(
                        file_path, content, chunk_size, chunk_overlap
                    )
                    chunks.extend(file_chunks)
                    files_processed += 1

                    # 更新元数据
                    self._index_metadata[file_str] = {
                        "mtime": file_path.stat().st_mtime,
                        "chunks": len(file_chunks),
                    }
                    self._indexed_files.add(file_str)
                except Exception as e:
                    print(f"Warning: Failed to index {file_path}: {e}")

        # 生成嵌入并存储
        if chunks:
            embeddings = self.embedding_engine.encode_batch(
                [c.content for c in chunks]
            )
            self.vector_store.add(chunks, embeddings)

        # 生成摘要
        self._generate_summaries()

        # 保存状态
        self._save_state()

        return {
            "files_processed": files_processed,
            "total_chunks": len(chunks),
            "indexed_files": len(self._indexed_files),
        }

    def _chunk_file(
        self,
        file_path: Path,
        content: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[CodeChunk]:
        """将文件分割成块"""
        lines = content.split("\n")
        chunks = []
        language = file_path.suffix.lstrip(".")

        for i in range(0, len(lines), chunk_size - chunk_overlap):
            chunk_lines = lines[i : i + chunk_size]
            chunk_content = "\n".join(chunk_lines)

            chunk_id = f"{file_path}:{i}:{i + len(chunk_lines)}"

            chunk = CodeChunk(
                id=chunk_id,
                content=chunk_content,
                file_path=str(file_path.relative_to(self.project_path)),
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                language=language,
                metadata={
                    "file_size": len(content),
                    "chunk_index": len(chunks),
                },
            )
            chunks.append(chunk)

        return chunks

    def search(
        self,
        query: str,
        n_results: int = 10,
        file_filter: Optional[List[str]] = None,
    ) -> List[Tuple[CodeChunk, float]]:
        """
        搜索相关代码

        Args:
            query: 查询文本
            n_results: 返回数量
            file_filter: 文件过滤 (只返回这些文件的块)

        Returns:
            (代码块, 相似度) 列表
        """
        # 如果没有向量存储或没有数据，使用关键词搜索
        if not self.vector_store.collection and not self.vector_store._in_memory_store:
            return []

        # 检查是否使用简单哈希（无 sentence-transformers）
        if self.embedding_engine.model is None:
            # 使用关键词搜索作为更好的降级方案
            results = self._keyword_search(query, n_results * 2)
        else:
            # 使用向量搜索
            query_embedding = self.embedding_engine.encode(query)
            results = self.vector_store.search(query_embedding, n_results * 2)

        # 应用文件过滤
        if file_filter:
            results = [
                (chunk, score)
                for chunk, score in results
                if chunk.file_path in file_filter
            ]

        return results[:n_results]

    def _keyword_search(self, query: str, n_results: int) -> List[Tuple[CodeChunk, float]]:
        """
        关键词搜索（无向量依赖时的降级方案）

        Args:
            query: 查询文本
            n_results: 返回数量

        Returns:
            (代码块, 相似度) 列表
        """
        query_terms = set(query.lower().split())
        results = []

        for chunk_id, data in self.vector_store._in_memory_store.items():
            chunk = CodeChunk.from_dict(data["chunk"])
            content_lower = chunk.content.lower()

            # 计算关键词匹配分数
            matched_terms = sum(1 for term in query_terms if term in content_lower)
            if matched_terms > 0:
                # 计算相似度：匹配词数 / 查询词数
                score = matched_terms / len(query_terms)
                # 加权：内容中出现的总次数
                term_freq = sum(content_lower.count(term) for term in query_terms)
                score = min(1.0, score + term_freq * 0.01)
                results.append((chunk, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n_results]

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 100_000,
        include_summaries: bool = True,
    ) -> str:
        """
        获取查询相关的上下文

        Args:
            query: 查询文本
            max_tokens: 最大 token 数
            include_summaries: 是否包含摘要

        Returns:
            上下文字符串
        """
        context_parts = []
        current_tokens = 0

        # 添加项目级摘要
        if include_summaries and ContextLevel.PROJECT in self.summaries:
            summary = self.summaries[ContextLevel.PROJECT]
            context_parts.append(f"# Project Overview\n\n{summary.content}\n")
            current_tokens += summary.tokens

        # 搜索相关代码
        results = self.search(query, n_results=20)

        for chunk, score in results:
            if current_tokens >= max_tokens:
                break

            # 估算 token 数 (约 4 字符 = 1 token)
            chunk_tokens = len(chunk.content) // 4

            if current_tokens + chunk_tokens <= max_tokens:
                context_parts.append(
                    f"\n## {chunk.file_path} (L{chunk.start_line}-L{chunk.end_line})\n"
                    f"Relevance: {score:.2%}\n\n"
                    f"```\n{chunk.content}\n```\n"
                )
                current_tokens += chunk_tokens

        return "\n".join(context_parts)

    def _generate_summaries(self):
        """生成各级摘要"""
        # 这里应该调用 LLM 生成摘要
        # 简化实现：使用文件列表作为项目级摘要

        files_by_ext: Dict[str, List[str]] = {}
        for file_str in self._indexed_files:
            ext = Path(file_str).suffix
            if ext not in files_by_ext:
                files_by_ext[ext] = []
            files_by_ext[ext].append(file_str)

        summary_content = "# Project Structure\n\n"
        for ext, files in sorted(files_by_ext.items()):
            summary_content += f"## {ext or 'no extension'} ({len(files)} files)\n"
            for f in files[:10]:  # 最多显示 10 个
                summary_content += f"- {f}\n"
            if len(files) > 10:
                summary_content += f"- ... and {len(files) - 10} more\n"
            summary_content += "\n"

        self.summaries[ContextLevel.PROJECT] = ContextSummary(
            level=ContextLevel.PROJECT,
            content=summary_content,
            tokens=len(summary_content) // 4,
            created_at=datetime.now(),
            source_files=list(self._indexed_files),
        )

    def add_conversation_turn(
        self,
        role: str,
        content: str,
        metadata: dict = None,
    ):
        """
        添加对话轮次

        Args:
            role: 角色 (user/assistant/system)
            content: 内容
            metadata: 元数据
        """
        turn = ConversationTurn(
            id=f"turn_{len(self.conversation_history)}_{datetime.now().timestamp()}",
            role=role,
            content=content,
            tokens=len(content) // 4,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.conversation_history.append(turn)
        self._save_state()

    def get_recent_conversation(self, max_tokens: int = 50_000) -> str:
        """
        获取最近的对话历史

        Args:
            max_tokens: 最大 token 数

        Returns:
            对话历史字符串
        """
        turns = []
        current_tokens = 0

        # 从后往前添加
        for turn in reversed(self.conversation_history):
            if current_tokens + turn.tokens > max_tokens:
                break
            turns.append(f"[{turn.role}]: {turn.content}")
            current_tokens += turn.tokens

        return "\n\n".join(reversed(turns))

    def compact_conversation(self, keep_last_n: int = 10) -> str:
        """
        压缩对话历史

        Args:
            keep_last_n: 保留最后 N 轮

        Returns:
            压缩后的摘要
        """
        if len(self.conversation_history) <= keep_last_n:
            return ""

        # 保留最后 N 轮
        to_compact = self.conversation_history[:-keep_last_n]
        self.conversation_history = self.conversation_history[-keep_last_n:]

        # 生成压缩摘要 (这里应该调用 LLM)
        summary = f"[Compacted {len(to_compact)} turns]\n"
        summary += f"Topics discussed: {self._extract_topics(to_compact)}"

        self._save_state()
        return summary

    def _extract_topics(self, turns: List[ConversationTurn]) -> str:
        """提取话题 (简化实现)"""
        # 这里应该使用 NLP 或 LLM 提取关键话题
        user_turns = [t.content[:50] for t in turns if t.role == "user"]
        return "; ".join(user_turns[:3]) + ("..." if len(user_turns) > 3 else "")

    def _save_state(self):
        """保存状态"""
        state_file = self.persist_directory / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "indexed_files": list(self._indexed_files),
            "index_metadata": self._index_metadata,
            "summaries": {
                level.value: summary.to_dict()
                for level, summary in self.summaries.items()
            },
            "conversation_history": [
                turn.to_dict() for turn in self.conversation_history[-100:]
            ],  # 只保留最近 100 轮
        }

        state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    def _load_state(self):
        """加载状态"""
        state_file = self.persist_directory / "state.json"

        # 加载向量存储的内存数据
        self.vector_store.load_memory_store()

        if not state_file.exists():
            return

        try:
            state = json.loads(state_file.read_text())
            self._indexed_files = set(state.get("indexed_files", []))
            self._index_metadata = state.get("index_metadata", {})

            for level_str, summary_data in state.get("summaries", {}).items():
                level = ContextLevel(level_str)
                self.summaries[level] = ContextSummary(
                    level=level,
                    content=summary_data["content"],
                    tokens=summary_data["tokens"],
                    created_at=datetime.fromisoformat(summary_data["created_at"]),
                    source_files=summary_data.get("source_files", []),
                    metadata=summary_data.get("metadata", {}),
                )

            for turn_data in state.get("conversation_history", []):
                self.conversation_history.append(
                    ConversationTurn(
                        id=turn_data["id"],
                        role=turn_data["role"],
                        content=turn_data["content"],
                        tokens=turn_data["tokens"],
                        timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                        metadata=turn_data.get("metadata", {}),
                    )
                )
        except Exception as e:
            print(f"Warning: Failed to load state: {e}")

    def clear_all(self):
        """清空所有数据"""
        self.vector_store.clear()
        self.summaries.clear()
        self.conversation_history.clear()
        self._indexed_files.clear()
        self._index_metadata.clear()
        self._save_state()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "indexed_files": len(self._indexed_files),
            "total_chunks": len(self._indexed_files) * 5,  # 估算
            "conversation_turns": len(self.conversation_history),
            "summaries": list(self.summaries.keys()),
            "has_vector_store": self.vector_store.collection is not None,
        }


# 便捷函数
def create_context_manager(
    project_path: Union[str, Path],
    **kwargs,
) -> ContextManager:
    """创建上下文管理器"""
    return ContextManager(Path(project_path), **kwargs)
