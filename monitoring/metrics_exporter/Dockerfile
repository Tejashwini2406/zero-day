FROM python:3.11-slim
WORKDIR /app
COPY metrics_exporter.py /app/metrics_exporter.py
RUN pip install prometheus_client
EXPOSE 8000
CMD ["python", "metrics_exporter.py"]
