import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
import pymysql
from models import *
from sqlalchemy.ext.declarative import declarative_base


# Charger les variables d'environnement
load_dotenv()

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de la base de données
DATABASE_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB', 'service_vm_offer_db')}"

# Créer le moteur SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_tables():
    """Crée les tables dans la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {str(e)}")
        raise


def init_database():
    """Initialise la base de données en créant la base et les tables"""
    try:
        logger.info("Initialisation de la base de données...")
        # Récupérer les informations de connexion depuis les variables d'environnement
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_port = int(os.getenv('MYSQL_PORT'))
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD')
        mysql_database = os.getenv('MYSQL_DB', 'service_vm_offer_db')
        
        logger.info(f"Connexion à MySQL: {mysql_host}:{mysql_port} avec l'utilisateur {mysql_user}")
        
        # Créer la base de données si elle n'existe pas
        conn = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password
        )
        
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {mysql_database}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database}")
        conn.commit()
        
        logger.info(f"Base de données '{mysql_database}' créée ou déjà existante.")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise


# Fonction pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fonction pour ajouter des données de test
def seed_test_data():
    """Ajoute des données de test dans la base de données"""
    # Import ici pour éviter les importations circulaires
    from models.model_vm_offer import VMOfferEntity
    
    try:
        db = SessionLocal()
        try:
            # 1. Création des profils documentaires
            vm_offers = [
                {"name": "Basic", "description": "Parfait pour les petits projets et le développement", "cpu_count": 1, "memory_size_mib": 1024, "disk_size_gb": 10, "price_per_hour": 0.50, "is_active": True, "created_at": "2024-12-26 11:12:52", "updated_at": "2024-12-26 11:12:52"},
                {"name": "Standard", "description": "Idéal pour les applications web et les bases de données moyennes", "cpu_count": 2, "memory_size_mib": 2048, "disk_size_gb": 20, "price_per_hour": 1.00, "is_active": True, "created_at": "2024-12-26 11:12:52", "updated_at": "2024-12-26 11:12:52"},
                {"name": "Premium", "description": "Pour les applications exigeantes et les charges de travail intensives", "cpu_count": 4, "memory_size_mib": 4096, "disk_size_gb": 40, "price_per_hour": 2.00, "is_active": True, "created_at": "2024-12-26 11:12:52", "updated_at": "2024-12-26 11:12:52"},
                {"name": "Enterprise", "description": "Solutions haute performance pour les entreprises", "cpu_count": 8, "memory_size_mib": 8192, "disk_size_gb": 80, "price_per_hour": 4.00, "is_active": True, "created_at": "2024-12-26 11:12:52", "updated_at": "2024-12-26 11:12:52"}
            ]
            for data in vm_offers:
                vm_offer = VMOfferEntity(**data)
                db.add(vm_offer)
            db.commit()

            logger.info("Données de test ajoutées avec succès")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de l'ajout des données de test: {e}")
            return False
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Erreur lors de la connexion à la base de données: {e}")
        return False