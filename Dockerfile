FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8000 8001 8501

CMD ["sh", "-c", "streamlit run app.py & uvicorn utils.chat_api:app --host 0.0.0.0 --port 8000 & uvicorn utils.import_data:app --host 0.0.0.0 --port 8001"]
