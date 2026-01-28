FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Instalar deps Python (editable)
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY app /app/app

RUN pip install --no-cache-dir -e .

# Puerto Railway / uvicorn
ENV PORT=8000

CMD ["bash", "-lc", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

