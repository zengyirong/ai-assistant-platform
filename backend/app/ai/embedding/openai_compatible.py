"""OpenAI-compatible Embedding HTTP client."""

from __future__ import annotations

import httpx

from app.ai.embedding.base import EmbeddingClient
from app.core.config import settings
from app.core.errors import AppError


class OpenAICompatibleEmbeddingClient(EmbeddingClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (base_url or settings.EMBEDDING_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.EMBEDDING_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.timeout = timeout
        # Aliyun text-embedding-v3/v4 allow at most 10 inputs per request.
        self.batch_size = max(1, int(getattr(settings, "EMBEDDING_BATCH_SIZE", 10) or 10))
        self.dimensions = int(settings.EMBEDDING_DIMENSION)
        if not self.api_key:
            raise AppError(
                "INTERNAL_ERROR",
                "EMBEDDING_API_KEY 未配置",
                http_status=500,
            )

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                vectors.extend(await self._embed_batch(client, batch))
        return vectors

    async def embed_query(self, query: str) -> list[float]:
        vectors = await self.embed_documents([query])
        return vectors[0]

    async def _embed_batch(
        self,
        client: httpx.AsyncClient,
        texts: list[str],
    ) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }
        # OpenAI optional; required/useful for DashScope v3/v4 dimension control.
        if self.dimensions > 0:
            body["dimensions"] = self.dimensions

        resp = await client.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json=body,
        )
        if resp.status_code >= 400:
            detail = (resp.text or "")[:500]
            raise AppError(
                "INTERNAL_ERROR",
                f"Embedding API 失败: HTTP {resp.status_code}",
                http_status=502,
                details=detail,
            )
        payload = resp.json()
        data = payload.get("data") or []
        # API may return out-of-order; sort by index
        data = sorted(data, key=lambda item: item.get("index", 0))
        if len(data) != len(texts):
            raise AppError(
                "INTERNAL_ERROR",
                "Embedding API 返回数量与输入不一致",
                http_status=502,
            )
        vectors = [item["embedding"] for item in data]
        if vectors and len(vectors[0]) != self.dimensions:
            raise AppError(
                "INTERNAL_ERROR",
                (
                    f"Embedding 维度不匹配: got {len(vectors[0])}, "
                    f"expect {self.dimensions}"
                ),
                http_status=502,
            )
        return vectors
