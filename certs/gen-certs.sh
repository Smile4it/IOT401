#!/bin/bash


set -e #set -e permet au script de ce lancer et de s'arréter à la moindre erreur
cd "$(dirname "$0")" # permet de faire en sorte que la sortie du script aille automatiquement dans certs/ et non dans le dossier depuis lequel je lance gen-certs.sh
umask 077 # quand un fichier est crée il part des droits 666 (tout le monde lit et écrit). umask retire les droits en fonction du numero donner.

INVENTAIRE="${1:-../inventaire.csv}"

echo "=== 1. Génération du certificat auto-signé (CA) ==="
#on indique à openssl de nous générer un certificat auto-signé (-x509) car la CA est la source de confiance.
#-new combinée avec -newkey rsa:2048 indique à OpenSSL de nous générer une nouvelle paire de clés et prépare une demande de certificat avec les infos d'identité en utilisant cette nouvelles clé
#-keyout ca.key écrit la clé privée du CA dans un fichier ca.key et -out ca.crt enregistre le certificat public (qui contient la clé publique et les informations d'identité) qui sera partager avec le broker et les capteurs pour qu'ils reconaissent et valident le CA
#-days 1095 indique le nombre de jours de validité du certificat
#-subj "CN=AC-IoT" CN signifie Common Name et -subj donne une carte d'identité claire au CA en tant que CN=AC-IoT.
#-addext "basicConstraints=critical,CA:TRUE" CA:TRUE indique que ce certificat est une Autorité de Certification (il a le droit de signer d'autres certificats). basicConstraints=critical pousse le client à verifier que ce certificat à le droit d'être une Autorité de Certification (CA:TRUE)
openssl req -x509 -new -nodes -newkey rsa:2048 \
 -keyout ca.key -out ca.crt \
 -days 1095 -subj "/CN=AC-IoT" \
 -addext "basicConstraints=critical,CA:TRUE"


echo "=== 2a. Génération du certificat SERVEUR (broker-public) ==="
openssl req -new -nodes -newkey rsa:2048 \
 -keyout broker-public.key -out broker-public.csr \
 -subj "/CN=broker-public"

# demande au CA de valider le certificat server.csr grace à ca.key.
# CAcreateserial donne un numéro de série au certificat server.crt
openssl x509 -req -in broker-public.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
 -out broker-public.crt -days 90 -extfile broker-public.ext
rm broker-public.csr
 
echo "=== 2b. Génération du certificat SERVEUR (broker-prive) ==="
openssl req -new -nodes -newkey rsa:2048 \
 -keyout broker-prive.key -out broker-prive.csr \
 -subj "/CN=broker-prive"

openssl x509 -req -in broker-prive.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
 -out broker-prive.crt -days 90 -extfile broker-prive.ext
rm broker-prive.csr

echo "=== 3. Génération du certificat SUPERVISOR ==="
openssl req -new -nodes -newkey rsa:2048 \
 -keyout supervisor.key -out supervisor.csr \
 -subj "/CN=supervisor"

openssl x509 -req -in supervisor.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
 -out supervisor.crt -days 90 -extfile client.ext
rm supervisor.csr

echo "=== 4. Génération du certificat CLIENT (sensors) ==="

emettre_client() {
  openssl req -new -nodes -newkey rsa:2048 \
   -keyout "$1.key" -out "$1.csr" -subj "/CN=$1" </dev/null
  openssl x509 -req -in "$1.csr" -CA ca.crt -CAkey ca.key -CAcreateserial \
   -out "$1.crt" -days 90 -extfile client.ext
  rm "$1.csr"
}

tail -n +2 "$INVENTAIRE" | while IFS=';' read -r id type zone; do
  if [ -n "$id" ]; then
    emettre_client "$id"
  fi
done

echo "=== 5a. INTRUS_1 (certificat valide, absent de l'inventaire) ==="
openssl req -new -nodes -newkey rsa:2048 \
 -keyout INTRUS_1.key -out INTRUS_1.csr \
 -subj "/CN=INTRUS_1"

openssl x509 -req -in INTRUS_1.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
 -out INTRUS_1.crt -days 90 -extfile client.ext
rm INTRUS_1.csr

echo "=== 5b. INTRUS_2 (certificat valide, absent de l'inventaire) ==="
openssl req -new -nodes -newkey rsa:2048 \
 -keyout INTRUS_2.key -out INTRUS_2.csr \
 -subj "/CN=INTRUS_2"

openssl x509 -req -in INTRUS_2.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
 -out INTRUS_2.crt -days 90 -extfile client.ext
rm INTRUS_2.csr

chmod 644 *.crt # les certificats sont publics : le broker doit pouvoir les lire
echo "=== Terminé : $(ls *.crt | wc -l) certificats ==="