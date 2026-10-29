import ssl
import paho.mqtt.client as mqtt
import time, random, os

SENSOR_ID = os.environ["PRESENCE_ID"]

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=SENSOR_ID)

c.tls_set(ca_certs="certs/ca.crt",
certfile=f"certs/{SENSOR_ID}.crt",
keyfile=f"certs/{SENSOR_ID}.key",
cert_reqs=ssl.CERT_REQUIRED)

# JAMAIS ceci : chiffré mais non validé = interceptable
#c.tls_insecure_set(True) # <-- interdit

c.connect("broker-public", 8887)
c.loop_start()

while True:
    place = False
    message="THE PARKING PLACE IS FREE"
    if random.random() < 1/6:
        place = True
        message="THE PARKING PLACE IS OCCUPED"
    
    c.publish(f"city/sensor/{SENSOR_ID}",message,qos=1)
    time.sleep(10)