FROM python:3.9-slim

WORKDIR /app

COPY serverless_runtime.py /app/serverless_runtime.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/app/serverless_runtime.py"]
