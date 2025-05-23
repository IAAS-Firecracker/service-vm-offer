import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from RabbitMQ.publisher.vm_offer_publisher import vm_offer_publisher
from config.eureka_client import register_with_eureka, shutdown_eureka
import logging
from routes.vm_offers_route import router as vm_offer_router
from database import create_tables, init_database,seed_test_data

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



# Importer et exécuter les configurations depuis settings.py si disponible
logger.info("Chargement des configurations...")
try:
    from config.settings import load_config
    load_config()
    logger.info("Configurations chargées avec succès")
except ImportError:
    logger.warning("Module config.settings non trouvé, utilisation des variables d'environnement par défaut")
except Exception as e:
    logger.error(f"Erreur lors du chargement des configurations: {e}")


# Initialiser l'application FastAPI
app = FastAPI(
    title="VM Offer API",
    description="API pour gérer les offres de machines virtuelles",
    version="1.0.0",
    docs_url="/swagger"
)

# Ajouter le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to RabbitMQ on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize database
        logger.info("Initializing database...")
        if init_database():
            create_tables()
            seed_test_data()
            logger.info("Database initialized successfully")
        
        # Register with Eureka
        await register_with_eureka()
        
        # Connect to RabbitMQ and set up the exchange
        vm_offer_publisher.connect()
        print(f"Connected to RabbitMQ exchange: {vm_offer_publisher.exchange_name}")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

# Close RabbitMQ connection on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    #deregister eureka
    await shutdown_eureka()
    vm_offer_publisher.close()
    print("Closed RabbitMQ connection")


@app.get("/api/service-vm-offer/health", tags=["health"])
async def health_check():
    """Vérifie la santé de l'application"""
    return {"status": "UP", "service": "SERVICE-VM-OFFER"}

#Include routes
app.include_router(vm_offer_router)

if __name__ == '__main__':
    # Récupérer le port de l'application depuis les variables d'environnement
    app_port = int(os.getenv('APP_PORT', 5002))
    logger.info(f"Port de l'application configuré: {app_port}")
    
    # Initialiser la base de données
    if init_database():
        
        create_tables()
        # Ajouter des données de test
        seed_test_data()
        
        # Démarrer l'application FastAPI avec uvicorn
        import uvicorn
        logger.info(f"Démarrage de l'application FastAPI sur le port {app_port}...")
        uvicorn.run("app:app", host="0.0.0.0", port=app_port, reload=True)
    else:
        logger.error("Impossible de démarrer l'application en raison d'erreurs d'initialisation.")
        sys.exit(1)