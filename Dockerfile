FROM python:3.13.12-slim AS build
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.7
COPY pyproject.toml uv.lock ./
COPY artifacts/packages ./artifacts/packages
COPY migrations ./migrations
COPY scripts ./scripts
COPY supportops_platform ./supportops_platform
COPY agent/prompts ./agent/prompts
COPY infra/logging ./logcfg
ARG INSTALL_LIVE=false
RUN if [ "$INSTALL_LIVE" = "true" ]; then uv sync --locked --no-dev --extra live; else uv sync --locked --no-dev; fi

FROM python:3.13.12-slim
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --home /app app
COPY --from=build --chown=app:app /app /app
RUN mkdir -p /app/artifacts && chown app:app /app/artifacts
USER 10001:10001
ENV LLM_MODE=fake
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python","-m","uvicorn","supportops_platform.api.app:app","--host","0.0.0.0","--port","8000"]
