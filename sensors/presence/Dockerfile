FROM python:3.12-slim
RUN pip install paho-mqtt==2.1.0
WORKDIR /app
COPY . /app
CMD ["python", "presence.py"]