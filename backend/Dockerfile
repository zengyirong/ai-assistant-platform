FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV TZ=Asia/Shanghai

WORKDIR /app

# 离线依赖：由本机 scripts/build-prod-images.ps1 预先 pip download 到 wheels/
COPY wheels /wheels
COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install --no-index --find-links=/wheels -e . \
    && rm -rf /wheels

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
