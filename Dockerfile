FROM python:3.9-alpine
WORKDIR /fastapi_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt