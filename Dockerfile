FROM python:3.13.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY supportops_platform ./supportops_platform
RUN pip install --no-cache-dir uv==0.12.7 && uv sync --locked --no-dev
ENV LLM_MODE=fake
EXPOSE 8080
CMD ["uv", "run", "--locked", "--no-dev", "python", "-m", "supportops_platform"]
