"""Qdrant vector store adapter."""

from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.ai.vectorstore.base import VectorStore
from app.core.config import settings
from app.core.errors import AppError


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self.url = (url or settings.QDRANT_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.QDRANT_API_KEY or None
        self.collection = collection or settings.QDRANT_COLLECTION
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client: AsyncQdrantClient | None = None
        self._ensured = False

    def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(
                url=self.url,
                api_key=self.api_key,
                prefer_grpc=False,
                check_compatibility=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._ensured = False

    async def ensure_collection(self) -> None:
        if self._ensured:
            return
        client = self._get_client()
        try:
            exists = await client.collection_exists(self.collection)
            if not exists:
                await client.create_collection(
                    collection_name=self.collection,
                    vectors_config=qm.VectorParams(
                        size=self.dimension,
                        distance=qm.Distance.COSINE,
                    ),
                )
            # Payload indexes for filter performance
            for field in ("org_id", "kb_id", "document_id", "chunk_id"):
                try:
                    await client.create_payload_index(
                        collection_name=self.collection,
                        field_name=field,
                        field_schema=qm.PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    # index may already exist
                    pass
            self._ensured = True
        except Exception as exc:
            raise AppError(
                "VECTOR_STORE_UNAVAILABLE",
                "向量库不可用",
                http_status=503,
                details=str(exc),
            ) from exc

    async def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return
        await self.ensure_collection()
        client = self._get_client()
        points: list[qm.PointStruct] = []
        for item in chunks:
            vector = item["vector"]
            if len(vector) != self.dimension:
                raise AppError(
                    "INTERNAL_ERROR",
                    f"向量维度不匹配: got {len(vector)}, expect {self.dimension}",
                    http_status=500,
                )
            payload = {
                "org_id": item["org_id"],
                "kb_id": item["kb_id"],
                "document_id": item["document_id"],
                "chunk_id": item["chunk_id"],
                "page": item.get("page"),
                "section": item.get("section"),
            }
            points.append(
                qm.PointStruct(
                    id=item["chunk_id"],
                    vector=vector,
                    payload=payload,
                )
            )
        try:
            # upsert in batches
            batch_size = 64
            for i in range(0, len(points), batch_size):
                await client.upsert(
                    collection_name=self.collection,
                    points=points[i : i + batch_size],
                    wait=True,
                )
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                "VECTOR_STORE_UNAVAILABLE",
                "写入向量索引失败",
                http_status=503,
                details=str(exc),
            ) from exc

    async def delete_by_document(self, document_id: str) -> None:
        await self.ensure_collection()
        client = self._get_client()
        try:
            await client.delete(
                collection_name=self.collection,
                points_selector=qm.FilterSelector(
                    filter=qm.Filter(
                        must=[
                            qm.FieldCondition(
                                key="document_id",
                                match=qm.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )
        except Exception as exc:
            raise AppError(
                "VECTOR_STORE_UNAVAILABLE",
                "删除向量索引失败",
                http_status=503,
                details=str(exc),
            ) from exc

    async def search(
        self,
        query_vector: list[float],
        filters: dict[str, Any],
        top_k: int,
    ) -> list[dict[str, Any]]:
        await self.ensure_collection()
        client = self._get_client()
        must: list[qm.Condition] = []
        if org_id := filters.get("org_id"):
            must.append(
                qm.FieldCondition(key="org_id", match=qm.MatchValue(value=org_id))
            )
        kb_ids = filters.get("kb_ids") or []
        if kb_ids:
            must.append(
                qm.FieldCondition(key="kb_id", match=qm.MatchAny(any=list(kb_ids)))
            )
        try:
            response = await client.query_points(
                collection_name=self.collection,
                query=query_vector,
                query_filter=qm.Filter(must=must) if must else None,
                limit=top_k,
                with_payload=True,
            )
            hits = response.points
        except Exception as exc:
            raise AppError(
                "VECTOR_STORE_UNAVAILABLE",
                "向量检索失败",
                http_status=503,
                details=str(exc),
            ) from exc

        results: list[dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "chunk_id": payload.get("chunk_id") or str(hit.id),
                    "score": hit.score,
                    "org_id": payload.get("org_id"),
                    "kb_id": payload.get("kb_id"),
                    "document_id": payload.get("document_id"),
                    "page": payload.get("page"),
                    "section": payload.get("section"),
                }
            )
        return results

    async def count_by_document(self, document_id: str) -> int:
        await self.ensure_collection()
        client = self._get_client()
        result = await client.count(
            collection_name=self.collection,
            count_filter=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="document_id",
                        match=qm.MatchValue(value=document_id),
                    )
                ]
            ),
            exact=True,
        )
        return int(result.count)
