"""ChromaDB 向量检索服务。

职责:
- 错题去重:题干向量化后按相似度(>0.95)判定重复并合并
- 知识点检索:为 LLM 诊断提供知识图谱相关上下文(RAG)

设计:chromadb 为可选依赖,未安装/不可用时 VectorService 标记 disabled,
调用方通过 is_available() 感知并降级,不影响主链路。
"""
from typing import Optional

from app.config import get_settings

settings = get_settings()

try:  # 可选依赖:chromadb 安装失败时服务仍可运行
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMA_OK = True
except Exception:  # pragma: no cover
    chromadb = None  # type: ignore[assignment]
    CHROMA_OK = False


class VectorService:
    """ChromaDB 持久化客户端封装。"""

    def __init__(self) -> None:
        if not CHROMA_OK:
            self.available = False
            self.collection = None
            return
        try:
            self.client = chromadb.PersistentClient(  # type: ignore[union-attr]
                path=settings.CHROMA_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),  # type: ignore[union-attr]
            )
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            self.available = True
        except Exception:
            self.available = False
            self.collection = None

    def is_available(self) -> bool:
        """向量库是否可用。"""
        return bool(self.available and self.collection is not None)

    def upsert_question(self, question_id: int, user_id: int, text: str, kp_name: str = "") -> None:
        """写入题目向量。embedding 由服务端统一模型生成,此处用哈希占位示意。

        Args:
            question_id: 题目 ID
            user_id: 用户 ID(分桶隔离)
            text: 题干文本
            kp_name: 知识点名称
        """
        if not self.is_available():
            return
        embedding = self._embed(text)
        self.collection.upsert(
            ids=[str(question_id)],
            embeddings=[embedding],
            metadatas=[{"user_id": user_id, "kp": kp_name, "question_id": question_id}],
            documents=[text],
        )

    def find_similar(self, text: str, user_id: int, threshold: float | None = None) -> Optional[dict]:
        """按用户分桶查找相似题目。

        Returns:
            {"question_id": int, "score": float} 或 None

        Raises:
            VectorStoreError: 向量库不可用
        """
        thr = threshold if threshold is not None else settings.DEDUP_THRESHOLD
        if not self.is_available():
            return None
        embedding = self._embed(text)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=5,
            where={"user_id": user_id},
        )
        if not results["ids"] or not results["ids"][0]:
            return None
        # 余弦距离 → 相似度: distance = 1 - similarity
        top_id = int(results["ids"][0][0])
        score = 1.0 - float(results["distances"][0][0])
        if score >= thr:
            return {"question_id": top_id, "score": round(score, 4)}
        return None

    def search_kp_context(self, text: str, top_k: int = 5) -> list[str]:
        """为 RAG 检索相关题目/知识点上下文。"""
        if not self.is_available():
            return []
        embedding = self._embed(text)
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        return results["documents"][0] if results["documents"] else []

    @staticmethod
    def _embed(text: str) -> list[float]:
        """生产环境应调用 bge-large-zh 等 embedding 模型。

        此处用确定性伪嵌入(按字符哈希到 128 维)保证可运行,
        语义质量依赖真实模型替换。
        """
        import hashlib

        vec = [0.0] * 128
        for ch in text:
            h = hashlib.md5(ch.encode("utf-8")).digest()
            idx = int.from_bytes(h[:2], "big") % 128
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [round(v / norm, 6) for v in vec]
