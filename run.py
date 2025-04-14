#!/usr/bin/env python3
import os
import sys
import dotenv
import pymysql
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement avant d'importer les autres modules
dotenv.load_dotenv()

# Importer et exécuter les configurations depuis settings.py si disponible
logger.info("Chargement des configurations...")
try:
    from config import settings
    logger.info("Configurations chargées avec succès")
except ImportError:
    logger.warning("Module config.settings non trouvé, utilisation des variables d'environnement par défaut")
except Exception as e:
    logger.error(f"Erreur lors du chargement des configurations: {e}")

# Fonction pour initialiser la base de données
def init_database():
    try:
        logger.info("Initialisation de la base de données...")
        # Récupérer les informations de connexion depuis les variables d'environnement
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_port = int(os.getenv('MYSQL_PORT'))
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD')
        mysql_db = os.getenv('MYSQL_DB')
        
        logger.info(f"Connexion à MySQL: {mysql_host}:{mysql_port} avec l'utilisateur {mysql_user}")
        
        # Créer la base de données si elle n'existe pas
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password
        )
        
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_db}")
        conn.commit()
        
        logger.info(f"Base de données '{mysql_db}' créée ou déjà existante.")
        
        cursor.close()
        conn.close()
        
        # Maintenant importer l'application pour créer les tables
        from app import create_tables
        
        # Utiliser la fonction create_tables définie dans app.py
        create_tables()
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

# Fonction pour ajouter des données de test
def seed_database():
    try:
        logger.info("Ajout des données de test...")
        from app import SessionLocal, VMOffer
        from sqlalchemy.orm import Session
        from decimal import Decimal
        
        # Données de test
        test_offers = [
            {
                'name': 'Basic',
                'description': 'Parfait pour les petits projets et le développement',
                'cpu_count': 1,
                'memory_size_mib': 1024,
                'disk_size_gb': 10,
                'price_per_hour': Decimal('0.50'),
                'is_active': True
            },
            {
                'name': 'Standard',
                'description': 'Idéal pour les applications web et les bases de données moyennes',
                'cpu_count': 2,
                'memory_size_mib': 2048,
                'disk_size_gb': 20,
                'price_per_hour': Decimal('1.00'),
                'is_active': True
            },
            {
                'name': 'Premium',
                'description': 'Pour les applications exigeantes et les charges de travail intensives',
                'cpu_count': 4,
                'memory_size_mib': 4096,
                'disk_size_gb': 40,
                'price_per_hour': Decimal('2.00'),
                'is_active': True
            },
            {
                'name': 'Enterprise',
                'description': 'Solutions haute performance pour les entreprises',
                'cpu_count': 8,
                'memory_size_mib': 8192,
                'disk_size_gb': 80,
                'price_per_hour': Decimal('4.00'),
                'is_active': True
            }
        ]
        
        # Créer une session de base de données
        db = SessionLocal()
        try:
            # Vérifier si des données existent déjà
            existing_count = db.query(VMOffer).count()
            if existing_count > 0:
                logger.info(f"{existing_count} offres de VM existent déjà dans la base de données.")
                return True
            
            # Ajouter les offres de VM de test
            for offer_data in test_offers:
                offer = VMOffer(**offer_data)
                db.add(offer)
            
            # Sauvegarder les changements
            db.commit()
            logger.info(f"{len(test_offers)} offres de VM ajoutées avec succès.")
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout des données de test: {e}")
        return False

# Point d'entrée principal
if __name__ == '__main__':
    # Récupérer le port de l'application depuis les variables d'environnement
    app_port = int(os.getenv('APP_PORT', 5002))
    logger.info(f"Port de l'application configuré: {app_port}")
    
    # Initialiser la base de données
    if init_database():
        # Ajouter des données de test
        seed_database()
        
        # Démarrer l'application FastAPI avec uvicorn
        import uvicorn
        logger.info(f"Démarrage de l'application FastAPI sur le port {app_port}...")
        uvicorn.run("app:app", host="0.0.0.0", port=app_port, reload=True)
    else:
        logger.error("Impossible de démarrer l'application en raison d'erreurs d'initialisation.")
        sys.exit(1)
