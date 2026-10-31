import csv
import re
import os
import ssl
import time
import paho.mqtt.client as mqtt

PORT = int(os.getenv("BROKER_PORT", "8887"))
BROKERS = {
    "public": os.getenv("BROKER_PUBLIC_HOST", "broker-public"),
    "prive": os.getenv("BROKER_PRIVE_HOST", "broker-prive"),
}
TOPIC = "city/sensor/+"

# Seuils par type : à aligner avec les valeurs simulées par les capteurs
SEUILS = {"temperature": 30.0, "humidity": 90.0, "wind": 80.0, "speed": 50.0}



def log(message):
    print(message, flush=True)


def charger_inventaire(chemin):
    inventaire = {}
    with open(chemin, newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            inventaire[ligne["id"]] = {"type": ligne["type"], "zone": ligne["zone"]}
    return inventaire


INVENTAIRE = charger_inventaire("inventaire.csv")
ALLOWLIST = set(INVENTAIRE)      # les identités autorisées : tout le reste est un intrus

HISTORIQUE = {}
BLACKLIST = []
ALREADY_REPORT = set()

def appliquer_regle(type_objet, id_objet, valeur):
    if type_objet in SEUILS:
        if valeur > SEUILS[type_objet]:
            log(f"[ALERTE SEUIL] {id_objet} ({type_objet}) : {valeur} (seuil {SEUILS[type_objet]})")
        else:
            log(f"[MESURE NORMALE] {id_objet} : {valeur}")
    elif type_objet == "smoke":
        log(f"[ALERTE FUMEE] {id_objet} : {valeur}")
    else:                         # presence, traffic : pas de seuil, on journalise l'événement
        log(f"[EVENEMENT] {id_objet} ({type_objet}) : {valeur}")


def on_connect(client, zone, flags, reason_code, properties):
    if reason_code.is_failure:
        log(f"[{zone}] connexion refusée : {reason_code}")
    else:
        log(f"[{zone}] connecté en mTLS, abonnement à {TOPIC}")
        client.subscribe(TOPIC)

def extraire_valeur(type_objet, texte):
    if type_objet in ("presence", "traffic","smoke"):
        return texte                              # message texte, pas de nombre
    m = re.search(r"-?\d+(?:\.\d+)?", texte)      # ignore les unités : °C, %, km/h
    return float(m.group()) if m else None


def on_message(client, zone, msg):
    id_objet = msg.topic.split("/")[-1]
    texte = msg.payload.decode(errors="replace")

    result=ddos(id_objet,HISTORIQUE,BLACKLIST)
    if result == "ALREADY IN BLACKLIST":
        if id_objet not in ALREADY_REPORT:
            log(f"[ALERTE DEBIT] {id_objet} : ALREADY BLACKLIST")
            ALREADY_REPORT.add(id_objet)
        return
    if result == "ADD TO BLACKLIST":
       log(f"[ALERTE DEBIT] {id_objet},{result}")
       return

    if id_objet not in ALLOWLIST:                 # 1. l'identité d'abord
        log(f"[ALERTE INTRUSION] objet inconnu '{id_objet}' via broker {zone} | {msg.topic} | {texte}")
        return

    objet = INVENTAIRE[id_objet]
    if objet["zone"] != zone:                     # 2. la zone
        log(f"[ALERTE ZONE] '{id_objet}' devrait être en zone {objet['zone']}, vu via {zone}")
        return

    valeur = extraire_valeur(objet["type"], texte)  # 3. le contenu seulement ensuite
    if valeur is None:
        log(f"[PAYLOAD INVALIDE] {msg.topic} : {texte!r}")
        return
    appliquer_regle(objet["type"], id_objet, valeur)

def creer_client(zone):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"supervisor-{zone}")
    client.tls_set(ca_certs="certs/ca.crt",
                   certfile="certs/supervisor.crt",
                   keyfile="certs/supervisor.key",
                   cert_reqs=ssl.CERT_REQUIRED)  # on valide le certificat du broker, jamais tls_insecure
    client.user_data_set(zone)                   # chaque client sait de quel broker il écoute
    client.on_connect = on_connect
    client.on_message = on_message
    return client


def connecter(client, hote):
    while True:                                  # le broker peut démarrer après le superviseur
        try:
            client.connect(hote, PORT, 60)
            return
        except OSError as e:
            log(f"broker {hote} pas prêt ({e}), nouvel essai dans 3 s")
            time.sleep(3)

def ddos(id_objet,HISTORIQUE,BLACKLIST):
    now = time.time()
    HISTORIQUE.setdefault(id_objet, [])
    HISTORIQUE[id_objet].append(now)
    HISTORIQUE[id_objet] = [t for t in HISTORIQUE[id_objet] if t > now - 10]
    if id_objet in BLACKLIST:
        return "ALREADY IN BLACKLIST"
    if len(HISTORIQUE[id_objet]) > 5:
        BLACKLIST.append(id_objet)
        return "ADD TO BLACKLIST"
    return False
    


log("Démarrage du superviseur...")
for zone, hote in BROKERS.items():
    client = creer_client(zone)
    connecter(client, hote)
    client.loop_start()                          # une boucle réseau par broker

while True:
    time.sleep(1)