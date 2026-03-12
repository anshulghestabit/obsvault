FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY prediction_logs.csv ./prediction_logs.csv

EXPOSE 8000

CMD ["uvicorn", "src.deployment.api:app", "--host", "0.0.0.0", "--port", "8000"]