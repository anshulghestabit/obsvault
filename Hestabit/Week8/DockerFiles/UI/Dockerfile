FROM python:3.10-slim

WORKDIR /app

COPY DockerFiles/UI/requirements.txt .

RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copy ONLY deploy folder
COPY deploy ./deploy

EXPOSE 8501

CMD ["streamlit", "run", "deploy/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]