FROM python:3.12-slim
WORKDIR /app
RUN pip install paho-mqtt==2.1.0
COPY capteurs.py .
CMD ["python", "-u", "capteurs.py"]
