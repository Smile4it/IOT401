import ssl
import paho.mqtt.client as mqtt
import time, random, os

SENSOR_ID = os.environ["TRAFFIC_LIGHT_ID"]

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=SENSOR_ID)

c.tls_set(ca_certs="certs/ca.crt",
certfile=f"certs/{SENSOR_ID}.crt",
keyfile=f"certs/{SENSOR_ID}.key",
cert_reqs=ssl.CERT_REQUIRED)

# JAMAIS ceci : chiffré mais non validé = interceptable
#c.tls_insecure_set(True) # <-- interdit

c.connect("broker-prive",8887)
c.loop_start()

redlight = False

while True:
    redlight = not redlight
    if redlight:
        if random.random() < 1/30:
            c.publish(f"city/sensor/{SENSOR_ID}","POLICE ALERTE: A CAR SKIPPED A RED LIGHT",qos=1)
    time.sleep(15)