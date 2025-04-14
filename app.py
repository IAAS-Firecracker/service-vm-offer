import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Numeric, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import pymysql
import os
from typing import List, Optional
from fastapi import status, HTTPException, Depends
from RabbitMQ.publisher.vm_offer_publisher import vm_offer_publisher

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données
DATABASE_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"

# Créer le moteur SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    # Connect to RabbitMQ and set up the exchange
    vm_offer_publisher.connect()
    print(f"Connected to RabbitMQ exchange: {vm_offer_publisher.exchange_name}")

# Close RabbitMQ connection on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    vm_offer_publisher.close()
    print("Closed RabbitMQ connection")

# Définir le modèle de données SQLAlchemy
class VMOffer(Base):
    __tablename__ = 'vm_offers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    cpu_count = Column(Integer, nullable=False)
    memory_size_mib = Column(Integer, nullable=False)
    disk_size_gb = Column(Integer, nullable=False)
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Dépendance pour obtenir la session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modèles Pydantic pour la validation des données
class VMOfferBase(BaseModel):
    name: str
    description: str
    cpu_count: int
    memory_size_mib: int
    disk_size_gb: int
    price_per_hour: float
    is_active: Optional[bool] = True

class VMOfferCreate(VMOfferBase):
    pass

class VMOfferUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cpu_count: Optional[int] = None
    memory_size_mib: Optional[int] = None
    disk_size_gb: Optional[int] = None
    price_per_hour: Optional[float] = None
    is_active: Optional[bool] = None

class VMOfferResponse(VMOfferBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True

# Définir les routes API
@app.get("/vm-offers/", response_model=List[VMOfferResponse], tags=["vm-offers"])
async def list_vm_offers(db: Session = Depends(get_db)):
    """Liste toutes les offres de VM"""
    vm_offers = db.query(VMOffer).all()
    return vm_offers

@app.post("/vm-offers/", response_model=VMOfferResponse, status_code=status.HTTP_201_CREATED, tags=["vm-offers"])
async def create_vm_offer(vm_offer: VMOfferCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle offre de VM"""
    new_vm_offer = VMOffer(
        name=vm_offer.name,
        description=vm_offer.description,
        cpu_count=vm_offer.cpu_count,
        memory_size_mib=vm_offer.memory_size_mib,
        disk_size_gb=vm_offer.disk_size_gb,
        price_per_hour=vm_offer.price_per_hour,
        is_active=vm_offer.is_active
    )
    
    try:
        db.add(new_vm_offer)
        db.commit()
        db.refresh(new_vm_offer)
        
        # Publish creation event to RabbitMQ
        vm_offer_dict = {
            'id': new_vm_offer.id,
            'name': new_vm_offer.name,
            'description': new_vm_offer.description,
            'cpu_count': new_vm_offer.cpu_count,
            'memory_size_mib': new_vm_offer.memory_size_mib,
            'disk_size_gb': new_vm_offer.disk_size_gb,
            'price_per_hour': float(new_vm_offer.price_per_hour),
            'is_active': new_vm_offer.is_active
        }
        vm_offer_publisher.publish_vm_offer_event('create', vm_offer_dict)
        
        return new_vm_offer
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vm-offers/{id}", response_model=VMOfferResponse, tags=["vm-offers"])
async def get_vm_offer(id: int, db: Session = Depends(get_db)):
    """Obtient une offre de VM par son ID"""
    vm_offer = db.query(VMOffer).filter(VMOffer.id == id).first()
    if vm_offer is None:
        raise HTTPException(status_code=404, detail="Offre de VM non trouvée")
    return vm_offer

@app.put("/vm-offers/{id}", response_model=VMOfferResponse, tags=["vm-offers"])
async def update_vm_offer(id: int, vm_offer: VMOfferUpdate, db: Session = Depends(get_db)):
    """Met à jour une offre de VM"""
    db_vm_offer = db.query(VMOffer).filter(VMOffer.id == id).first()
    if db_vm_offer is None:
        raise HTTPException(status_code=404, detail="Offre de VM non trouvée")
    
    # Mettre à jour les attributs
    update_data = vm_offer.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vm_offer, key, value)
    
    db_vm_offer.updated_at = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_vm_offer)
        
        # Publish update event to RabbitMQ
        vm_offer_dict = {
            'id': db_vm_offer.id,
            'name': db_vm_offer.name,
            'description': db_vm_offer.description,
            'cpu_count': db_vm_offer.cpu_count,
            'memory_size_mib': db_vm_offer.memory_size_mib,
            'disk_size_gb': db_vm_offer.disk_size_gb,
            'price_per_hour': float(db_vm_offer.price_per_hour),
            'is_active': db_vm_offer.is_active
        }
        vm_offer_publisher.publish_vm_offer_event('update', vm_offer_dict)
        
        return db_vm_offer
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/vm-offers/{id}", status_code=status.HTTP_200_OK, tags=["vm-offers"])
async def delete_vm_offer(id: int, db: Session = Depends(get_db)):
    """Supprime une offre de VM"""
    vm_offer = db.query(VMOffer).filter(VMOffer.id == id).first()
    if vm_offer is None:
        raise HTTPException(status_code=404, detail="Offre de VM non trouvée")
    
    try:
        # Capture VM offer data before deletion for the event
        vm_offer_dict = {
            'id': vm_offer.id,
            'name': vm_offer.name,
            'description': vm_offer.description,
            'cpu_count': vm_offer.cpu_count,
            'memory_size_mib': vm_offer.memory_size_mib,
            'disk_size_gb': vm_offer.disk_size_gb,
            'price_per_hour': float(vm_offer.price_per_hour),
            'is_active': vm_offer.is_active
        }
        
        # Delete from database
        db.delete(vm_offer)
        db.commit()
        
        # Publish deletion event to RabbitMQ
        vm_offer_publisher.publish_vm_offer_event('delete', vm_offer_dict)
        
        return {"message": "Offre de VM supprimée avec succès"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vm-offers/search/{name}", response_model=List[VMOfferResponse], tags=["vm-offers"])
async def search_vm_offers(name: str, db: Session = Depends(get_db)):
    """Recherche des offres de VM par nom"""
    vm_offers = db.query(VMOffer).filter(VMOffer.name.like(f"%{name}%")).all()
    return vm_offers

@app.get("/vm-offers/active/", response_model=List[VMOfferResponse], tags=["vm-offers"])
async def get_active_vm_offers(db: Session = Depends(get_db)):
    """Obtient les offres de VM actives"""
    vm_offers = db.query(VMOffer).filter(VMOffer.is_active == True).all()
    return vm_offers

@app.get("/health", tags=["health"])
async def health_check():
    """Vérifie la santé de l'application"""
    return {"status": "UP", "service": "SERVICE-VM-OFFER"}

# Fonction pour créer les tables dans la base de données
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès.")

if __name__ == "__main__":
    import uvicorn
    # Créer les tables au démarrage
    create_tables()
    # Démarrer le serveur
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv('APP_PORT', 5002)), reload=True)
