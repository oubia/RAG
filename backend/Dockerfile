ARG BUILD_IMAGE=python
ARG BUILD_IMAGE_TAG=3.12-slim
FROM ${BUILD_IMAGE}:${BUILD_IMAGE_TAG}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
      curl \
      wget \
      unzip \
      ffmpeg \
      && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
