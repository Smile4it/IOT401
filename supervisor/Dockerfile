FROM python:3.12-slim
WORKDIR /app
RUN pip install paho-mqtt==2.1.0
COPY superviseur.py .
CMD ["python", "-u", "superviseur.py"]
