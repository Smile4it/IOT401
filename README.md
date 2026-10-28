# IOT401

Projet du module IOT401 (École 2600) : concevoir une solution IoT, prototyper son cœur sécurisé dès la construction, puis auditer sa propre infrastructure et justifier sa conformité.

## Equipe

- <Smile4it> : <parties>
- <bigcataxel> : <parties>

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
