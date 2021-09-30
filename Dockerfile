FROM python:3.9-slim
WORKDIR /fastapi_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt