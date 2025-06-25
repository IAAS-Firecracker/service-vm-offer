# Service VM Offer API

Une API Flask pour gérer les offres de machines virtuelles dans le cadre du projet Tsore-Iaas-Firecracker.

## Fonctionnalités

- API RESTful complète pour gérer les offres de machines virtuelles
- Documentation Swagger intégrée
- Connexion à une base de données MySQL
- Intégration avec RabbitMQ pour la messagerie asynchrone
- Communication avec les autres services via Eureka

## Structure de la base de données

Table `vm_offer` avec les champs suivants :
- `id` : Identifiant unique
- `nom` : Nom de l'offre
- `description` : Description de l'offre
- `prix` : Prix de l'offre
- `ram` : Quantité de RAM (en GB)
- `rom` : Quantité de ROM (en GB)
- `processeur` : Type de processeur
- `nombre_coeurs` : Nombre de cœurs CPU
- `date_creation` : Date de création de l'offre
- `statut` : Statut de l'offre (active, inactive)

## Installation

1. Cloner le dépôt :
```
git clone <repository-url>
cd Tsore-Iaas-Firecracker/service-vm-offer
```

2. Créer un environnement virtuel et l'activer :
```
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installer les dépendances :
```
pip install -r requirements.txt
```

4. Configurer la base de données :
   - Créer une base de données MySQL nommée `service_vm_offer_db`
   - Modifier le fichier `.env` avec vos informations de connexion

5. Initialiser la base de données :
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Utilisation

1. Démarrer le serveur :
```
python3 app.py
```

2. Accéder à l'API :
   - API : http://localhost:5002/api/vm-offers
   - Documentation Swagger : http://localhost:5002/swagger

## Endpoints API

- `GET /api/vm-offers` : Liste toutes les offres de machines virtuelles
- `POST /api/vm-offers` : Crée une nouvelle offre de machine virtuelle
- `GET /api/vm-offers/<id>` : Obtient une offre de machine virtuelle par son ID
- `PUT /api/vm-offers/<id>` : Met à jour une offre de machine virtuelle
- `DELETE /api/vm-offers/<id>` : Supprime une offre de machine virtuelle
- `GET /api/vm-offers/search/<nom>` : Recherche des offres de machines virtuelles par nom
- `GET /api/vm-offers/active` : Obtient les offres de machines virtuelles actives

## Configuration .env docker

```
SECRET_KEY=your_secret_key_here
MYSQL_HOST=mysql_db_service_vm_offer
MYSQL_PORT=3306
MYSQL_USER=firecracker
MYSQL_PASSWORD=firecracker
MYSQL_DB=service_vm_offer_db
APP_PORT=5002
SERVICE_CONFIG_URI=http://service-config:8080
APP_NAME=service-vm-offer
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
EUREKA_SERVER=http://service-registry:8761/eureka/
SERVICE_VM_OFFER_EXCHANGE=vm-offer-exchange
```

## Configuration .env local

```
#Service VM Offer
SECRET_KEY=4b4017b60ba6766fa68ac34cda732625aceb1248483b363507c62a76aeb0fb3d5df4fbec77ebb94c409294ff1597ac093cee490e1e842674ab3c989a2162b1104214f0c802fe1d3ca8cbc823b162fc6fd986c53147a0a5b23467238feb9ff9c0f92135dbee5710550466a1013b20abd96496f61c1b44d74e9b3438c8fefa89cd

MYSQL_HOST=localhost
MYSQL_PORT=13319
MYSQL_USER=firecracker
MYSQL_PASSWORD=firecracker
MYSQL_DB=service_vm_offer_db
APP_PORT=5002
SERVICE_CONFIG_URI=http://localhost:8080
APP_NAME=service-vm-offer
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
EUREKA_SERVER=http://localhost:8761/eureka/
SERVICE_VM_OFFER_EXCHANGE=vm-offer-exchange

### Service VM Offer ###
```
