# IOT401

Projet du module IOT401 (École 2600) : concevoir une solution IoT, prototyper son cœur sécurisé dès la construction, puis auditer sa propre infrastructure et justifier sa conformité.

## Equipe

- Smile4it : <parties>
- bigcataxel : <parties>

## Cas d'usage

- **Contexte** : capteurs urbains dispersés (qualité de l'air, stationnement, etc.)
- **Priorité sécurité** : résilience, <à compléter>
- **Contrainte** : des milliers d'objets, données parfois publiques

## Architecture

```
capteur (simulé) ──► MQTT sur mTLS ──► broker ──► superviseur (seuil + alerte)
```

- **Identité par objet** : un certificat client par capteur, vérifié par le broker (mTLS)
- **ACL par topic** : un capteur ne publie que sous son propre identifiant, le superviseur lit tout
- **Segmentation réseau** : broker joignable uniquement par les services autorisés (réseau Docker interne)
- **Détection** : règle de seuil et détection d'un objet inconnu (hors allowlist)

## Lancer le projet

Prérequis : Docker, Docker Compose, openssl.

```bash
cd certs && ./gen-certs.sh && cd ..   # génère l'AC et les certificats
docker compose up -d --build
docker logs -f superviseur
```

## Structure du dépôt








## Livrables

- [ ] Cahier des charges (CDC)
- [ ] Infrastructure qui tourne (docker compose)
- [ ] Sécurité implémentée (mTLS, ACL, segmentation, détection)
- [ ] Rapport d'audit (STRIDE, arbre d'attaque, preuves)
- [ ] Rapport de conformité (ETSI EN 303 645, OWASP IoT Top 10, CRA, RGPD)


## Lancer le projet

### Prérequis

Docker, Docker Compose (v2), openssl et bash. Les certificats ne sont pas dans l'archive : ils sont générés sur la machine qui lance le projet.

### 1. Générer la PKI (autorité, certificats et clés)

```bash
bash certs/gen-certs.sh
```

À lancer **sans `sudo`**, depuis la racine du projet. Le script demande le mot de passe `sudo` pour une seule commande : donner les clés des brokers à l'utilisateur `mosquitto` (UID 1883, droits 600), afin que les brokers ne tournent pas en root. S'il échoue, il affiche la commande à copier.

### 2. Démarrer l'infrastructure

```bash
docker compose up -d --build
```

Ajouter `sudo` devant si l'utilisateur n'a pas accès à Docker.

### 3. Observer le superviseur

```bash
docker compose logs -f supervisor
```

On y voit les connexions mTLS aux deux brokers, les mesures, les alertes de seuil (`[ALERTE SEUIL]`) et les alertes d'intrusion (`[ALERTE INTRUSION]`). `Ctrl+C` quitte l'affichage sans arrêter les conteneurs.

### 4. Arrêter

```bash
docker compose down
```

### Relancer après un changement

- Code (capteurs, superviseur) : `docker compose up -d --build`.
- Certificats régénérés : relancer `bash certs/gen-certs.sh`, puis `docker compose up -d --build --force-recreate`.

### Remarques

- Le port 8887 du broker public est publié sur la machine (il doit être libre). Le broker privé n'est joignable que depuis le réseau Docker `reseau-prive`.
- Aucun secret n'est versionné : les fichiers `.key`, `.crt`, `.srl` sont dans le `.gitignore`.