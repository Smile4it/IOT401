# IOT401 — Chaîne de supervision IoT sécurisée (Ville / Parking)

Projet d'examen du module IOT401 (École 2600) : concevoir une solution IoT, prototyper son cœur sécurisé dès la construction, puis auditer sa propre infrastructure et justifier sa conformité.

## Équipe et répartition du travail

| Membre | Compte GitHub | Parties réalisées |
|---|---|---|
| Clovis Le Floc'h | Smile4it | Arborescence du dépôt, README, `certs/gen-certs.sh` (PKI) et fichiers `.ext`, `inventaire.csv`, `supervisor/supervisor.py`, `broker-public/` et `broker-prive/` (`mosquitto.conf` et `acl`) |
| Axel Pineau | bigcataxel | Tous les `Dockerfile`, tous les scripts des capteurs (`sensors/`), mise en place du rate limiting (détection de débit du superviseur) |

Le dossier complet (CDC, architecture, sécurité implémentée, rapport d'audit, rapport de conformité, limites, contributions signées) est dans `dossier/dossier-iot401.pdf`.

## Cas d'usage

- **Contexte** : une ville avec deux parkings fermés (2 × 40 places), des capteurs de fumée, trois stations météo (température, humidité, vent), trois radars de vitesse et trois radars de feu. Les données de présence et de météo sont publiques (tableau de bord citoyen) ; les radars et la fumée sont restreints (usage gouvernemental).
- **Priorités de sécurité** : *intégrité et détection d'anomalie* pour les radars et la fumée ; *résilience* pour la présence et la météo.
- **Échelle visée** : 105 objets (80 présence, 8 fumée, 9 météo, 3 radars de vitesse, 3 radars de feu, 2 intrus). Le prototype en simule un échantillon représentatif : 2 capteurs de présence, 1 capteur de fumée, 1 station météo, 1 radar de vitesse, 1 radar de feu, 2 intrus.

## Architecture

```
 reseau-public                                      reseau-prive (internal: true)
┌─────────────────────────┐                        ┌──────────────────────────┐
│ presence_1, presence_2  │                        │ SMOKE, SPEED,            │
│ TEMPERATURE, HUMIDITY,  │                        │ TRAFFIC_LIGHT,           │
│ WIND, INTRUS_1          │                        │ INTRUS_2                 │
└───────────┬─────────────┘                        └────────────┬─────────────┘
            │ MQTT / mTLS :8887                                 │ MQTT / mTLS :8887
     ┌──────▼───────┐                                    ┌──────▼───────┐
     │broker-public │ (seul port publié sur l'hôte)      │ broker-prive │ (aucun port publié)
     └──────┬───────┘                                    └──────┬───────┘
            └───────────────────►  supervisor  ◄────────────────┘
                              allowlist · seuils · débit · alertes
```

- Topics : `city/sensor/<ID>`, où `<ID>` est le CN du certificat de l'objet.
- **Identité par objet** : un certificat client par objet, vérifié par le broker (mTLS).
- **ACL par topic** : un objet ne publie que sur `city/sensor/<son identité>` ; seul le superviseur lit `city/#`.
- **Segmentation réseau** : `broker-prive` n'a aucun port publié et son réseau est `internal`. Le superviseur est le seul service présent sur les deux réseaux.
- **Détection** : règle de seuil, objet inconnu (hors allowlist), objet dans la mauvaise zone, détection de débit (plus de 5 messages en 10 s : identité mise en blacklist).

## Structure du dépôt

```
.
├── docker-compose.yml        # brokers, capteurs, superviseur, réseaux
├── inventaire.csv            # allowlist : id;type;zone
├── certs/
│   ├── gen-certs.sh          # génère l'AC, les certificats et les clés
│   ├── broker-public.ext     # extensions X.509 du broker public
│   ├── broker-prive.ext      # extensions X.509 du broker privé
│   └── client.ext            # extensions X.509 des clients (clientAuth)
├── broker-public/            # mosquitto.conf + acl
├── broker-prive/             # mosquitto.conf + acl
├── supervisor/               # supervisor.py + Dockerfile
├── sensors/                  # un dossier par type de capteur (script + Dockerfile)
│   ├── presence/  smoke/  intrus/
│   ├── weather/{temperature,humidity,wind}/
│   └── radars/{speed,traffic-light}/
└── dossier/                  # dossier-iot401.pdf (dossier complet) et CDC source
    └── preuves/              # captures : preuve-mtls, preuve-acl-rc135, preuve-intrusion, preuve-segmentation
```

## Lancer le projet (à suivre dans l'ordre)

**Prérequis** : Docker, Docker Compose v2, `openssl`, `bash`. Le port **8887** doit être libre sur la machine. Les certificats et clés ne sont pas dans l'archive : ils sont générés sur la machine qui lance le projet.

### 1. Générer la PKI

Depuis la racine du projet, **sans `sudo`** :

```bash
bash certs/gen-certs.sh
```

Le script génère l'AC, les certificats des brokers, du superviseur et de chaque objet (14 certificats attendus pour l'échantillon du prototype), puis demande le mot de passe `sudo` **pour une seule commande** : donner la propriété des clés des brokers à l'UID 1883 (utilisateur `mosquitto` de l'image), afin que les brokers n'aient pas à tourner en root. Si `sudo` est indisponible, le script affiche la commande à copier :

```bash
sudo chown 1883:1883 certs/broker-public.key certs/broker-prive.key
```

Sans cette étape, les brokers s'arrêtent avec `Permission denied` sur leur clé.

### 2. Démarrer l'infrastructure

```bash
docker compose up -d --build
```

Ajouter `sudo` devant si l'utilisateur n'a pas accès à Docker. Le premier démarrage construit les images ; compter une à deux minutes, puis quelques secondes avant que les mesures arrivent.

### 3. Observer le superviseur

```bash
docker compose logs -f supervisor
```

On voit :
- `connecté en mTLS` pour chacun des deux brokers ;
- `[MESURE NORMALE]` et `[EVENEMENT]` pour les objets normaux ;
- `[ALERTE SEUIL]` quand une valeur dépasse son seuil (température > 30, humidité > 90, vent > 80, vitesse > 50) ;
- `[ALERTE FUMEE]` pour le capteur de fumée ;
- `[ALERTE INTRUSION]` puis `[ALERTE DEBIT]` pour `INTRUS_1` et `INTRUS_2`, qui ont un certificat valide mais ne figurent pas dans `inventaire.csv`.

`Ctrl+C` quitte l'affichage sans arrêter les conteneurs.

### 4. Arrêter

```bash
docker compose down
```

### Relancer après un changement

- Code modifié (capteurs, superviseur) : `docker compose up -d --build`.
- Certificats régénérés : `bash certs/gen-certs.sh`, puis `docker compose up -d --build --force-recreate`.
- Repartir de zéro : `docker compose down`, supprimer `certs/*.key certs/*.crt certs/*.srl`, puis reprendre l'étape 1.

## Rejouer les preuves de sécurité

À lancer **depuis la racine du projet, une fois l'infrastructure démarrée**. On repère d'abord le réseau Docker créé par Compose :

```bash
RESEAU=$(docker network ls --format '{{.Name}}' | grep reseau-public)
echo "$RESEAU"
```

### Preuve 1 — mTLS : un client sans certificat est rejeté

```bash
docker run --rm --network "$RESEAU" -v "$PWD/certs/ca.crt:/ca.crt:ro" \
  eclipse-mosquitto:2.0.18 \
  mosquitto_pub -d -h broker-public -p 8887 --cafile /ca.crt -t city/sensor/TEST -m 1
```

Résultat attendu : le client fait confiance au broker (il a la CA) mais n'a pas de certificat client ; la connexion est refusée (`Error: Protocol error`, `reason(1116)`).

### Preuve 2 — ACL : refus `RC:135` sur le topic d'un autre objet

`TEMPERATURE` (certificat valide) tente de publier sur le topic de `HUMIDITY` :

```bash
docker run --rm --network "$RESEAU" \
  -v "$PWD/certs/ca.crt:/c/ca.crt:ro" \
  -v "$PWD/certs/TEMPERATURE.crt:/c/c.crt:ro" \
  -v "$PWD/certs/TEMPERATURE.key:/c/c.key:ro" \
  eclipse-mosquitto:2.0.18 \
  mosquitto_pub -V mqttv5 -d -q 1 -h broker-public -p 8887 \
  --cafile /c/ca.crt --cert /c/c.crt --key /c/c.key \
  -t city/sensor/HUMIDITY -m 99
```

Résultat attendu : `Warning: Publish 1 failed: Not authorized.` et `PUBACK (Mid: 1, RC:135)`. La valeur `99` n'apparaît pas dans le superviseur.

> Le flag `-V mqttv5` est indispensable : en MQTT 3.1.1 (défaut de `mosquitto_pub`), le broker acquitte la publication refusée sans code d'erreur (`RC:0`) puis l'ignore. Le code `RC:135` n'existe qu'en MQTT 5.

### Preuve 3 — Alerte d'intrusion : objet inconnu

```bash
docker compose logs supervisor | grep -E "INTRUSION|DEBIT"
```

Résultat attendu : `[ALERTE INTRUSION] objet inconnu 'INTRUS_1' ...` (et `INTRUS_2` côté privé), puis `[ALERTE DEBIT] ... ADD TO BLACKLIST`.

### Preuve 4 (complément) — Segmentation réseau

```bash
docker run --rm --network "$RESEAU" eclipse-mosquitto:2.0.18 ping -c1 -W2 broker-prive
```

Résultat attendu : `bad address 'broker-prive'`. Le broker privé n'existe pas sur le réseau public et n'a aucun port publié.

Les captures correspondantes sont dans `dossier/preuves/` (`preuve-mtls`, `preuve-acl-rc135`, `preuve-intrusion`, `preuve-segmentation`).

## Remarques

- Le port **8887** du broker public est publié sur la machine ; le broker privé n'est joignable que depuis le réseau Docker `reseau-prive`.
- **Aucun secret n'est versionné** : les fichiers `.key`, `.crt`, `.srl` sont dans `.gitignore`. Chaque objet a sa propre clé ; aucune clé n'est partagée par la flotte.
- Certificats feuilles valables 90 jours, AC valable 1095 jours ; stratégie de rotation et de révocation décrite dans le dossier.
- Limites connues (détaillées dans l'audit) : pas de limite de débit native dans Mosquitto 2.0.18 (la détection de débit est faite par le superviseur), pas de révocation CRL/OCSP, pas de protection contre le rejeu applicatif, le superviseur relie les deux zones, secure boot et OTA décrits mais non implémentés.

## Livrables

- [x] Cahier des charges (CDC) — `dossier/dossier-iot401.pdf`
- [x] Infrastructure qui tourne (`docker compose`)
- [x] Sécurité implémentée (mTLS, ACL, segmentation, détection)
- [x] Rapport d'audit (STRIDE, arbre d'attaque, preuves) — `dossier/dossier-iot401.pdf`
- [x] Rapport de conformité (ETSI EN 303 645, OWASP IoT Top 10, CRA, RGPD) — `dossier/dossier-iot401.pdf`
