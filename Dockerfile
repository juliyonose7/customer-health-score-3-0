FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-docker.txt /app/requirements-docker.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements-docker.txt

# Optional full NLP dependencies for Hugging Face stage.
ARG INSTALL_FULL_NLP=0
RUN if [ "$INSTALL_FULL_NLP" = "1" ]; then \
      pip install --no-cache-dir transformers torch; \
    fi

COPY . /app

CMD ["python", "-m", "src.run_pipeline"]
