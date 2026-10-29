import ssl
import paho.mqtt.client as mqtt
import time, random, os

SENSOR_ID = os.environ["SPEED_ID"]

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=SENSOR_ID)

c.tls_set(ca_certs="certs/ca.crt",
certfile=f"certs/{SENSOR_ID}.crt",
keyfile=f"certs/{SENSOR_ID}.key",
cert_reqs=ssl.CERT_REQUIRED)

# JAMAIS ceci : chiffré mais non validé = interceptable
#c.tls_insecure_set(True) # <-- interdit

c.connect("broker-prive")
c.loop_start()

while True:
    limite=55
    car = 48 + random.randint(-5,7)
    if random.random() < 1/20:
        car=55+ random.randint(2,30)
    if car > limite:
        c.publish(f"city/sensor/{SENSOR_ID}", "POLICE ALERTE: A CAR WAS SPEEDING AT "+str(car)+"km/h",qos=1)
    time.sleep(10)
