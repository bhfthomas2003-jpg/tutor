FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ARG WITH_MANIM=0
RUN if [ "$WITH_MANIM" = "1" ]; then apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config libcairo2-dev libpango1.0-dev && pip install --no-cache-dir manim && rm -rf /var/lib/apt/lists/*; fi
COPY app app
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
