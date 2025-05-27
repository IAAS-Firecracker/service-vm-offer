#!/usr/bin/env python3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.model_vm_offer import VMOfferEntity, VMOfferCreate, VMOfferUpdate
from RabbitMQ.publisher.vm_offer_publisher import vm_offer_publisher
# Importer les dépendances depuis le fichier dependencies.py
from dependencies import get_db, StandardResponse
from datetime import datetime

router = APIRouter(
    prefix="/api/vm-offers",
    tags=["vm-offers"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=StandardResponse,
             summary="Liste toutes les offres de VM ou recherche par nom",
             description="Paramètres de requête: \n- nom (optionnel): Permet de filtrer les offres de VM par nom (recherche partielle)")
def get_all_vm_offers(nom: Optional[str] = None, db: Session = Depends(get_db)):
    """Liste toutes les offres de VM ou recherche par nom"""
    try:
        query = db.query(VMOfferEntity)
    
        # Si un nom est fourni, filtrer les résultats
        if nom:
            query = query.filter(VMOfferEntity.name.like(f'%{nom}%'))
        
        vm_offers = query.all()
        vm_offer_list = [vm_offer.to_dict() for vm_offer in vm_offers]
        
        # Message personnalisé en fonction du type de recherche
        if nom:
            message = f"Offres de VM correspondant à '{nom}' récupérées avec succès"
        else:
            message = "Liste des offres de VM récupérée avec succès"
        
        return StandardResponse(
            statusCode=200,
            message=message,
            data={"vm_offers": vm_offer_list}
        )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

@router.post("/", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_vm_offer(vm_offer: VMOfferCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle offre de VM"""
    new_vm_offer = VMOfferEntity(
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
        
        return StandardResponse(
            statusCode=201,
            message="Offre de VM créée avec succès",
            data={"vm_offer": new_vm_offer.to_dict()}
        )
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

@router.get("/active", response_model=StandardResponse)
async def get_active_vm_offers(db: Session = Depends(get_db)):
    """Obtient toutes les offres de VM actives"""
    try:
        vm_offers = db.query(VMOfferEntity).filter(VMOfferEntity.is_active == True).all()
        if not vm_offers:
            return StandardResponse(
                statusCode=404,
                message="Aucune offre de VM active trouvée",
                data=[]
            )
        # Convertir chaque VMOfferEntity en dictionnaire
        vm_offers_list = [offer.to_dict() for offer in vm_offers]
        return StandardResponse(
            statusCode=200,
            message="Liste des offres de VM actives récupérée avec succès",
            data={"offers": vm_offers_list}
        )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=f"Erreur lors de la récupération des offres actives: {str(e)}",
            data={}
        )

@router.get("/{id}", response_model=StandardResponse)
async def get_vm_offer(id: int, db: Session = Depends(get_db)):
    """Obtient une offre de VM par son ID"""
    try:
        vm_offer = db.query(VMOfferEntity).filter(VMOfferEntity.id == id).first()
        if vm_offer is None:
            return StandardResponse(
                statusCode=404,
                message=f"Offre de VM avec l'ID {id} non trouvée",
                data={}
            )
        return StandardResponse(
            statusCode=200,
            message=f"Offre de VM {id} récupérée avec succès",
            data=vm_offer.to_dict()
        )
    except Exception as e:
        return StandardResponse(
            statusCode=500,
            message=f"Erreur lors de la récupération de l'offre {id}: {str(e)}",
            data={}
        )

@router.put("/{id}", response_model=StandardResponse)
async def update_vm_offer(id: int, vm_offer: VMOfferUpdate, db: Session = Depends(get_db)):
    """Met à jour une offre de VM"""
    db_vm_offer = db.query(VMOfferEntity).filter(VMOfferEntity.id == id).first()
    if db_vm_offer is None:
        return StandardResponse(
            statusCode=404,
            message="Offre de VM non trouvée",
            data={}
        )
    
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
        
        return StandardResponse(
            statusCode=200,
            message="Offre de VM mise à jour avec succès",
            data=db_vm_offer.to_dict()
        )
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )

@router.delete("/{id}", response_model=StandardResponse)
async def delete_vm_offer(id: int, db: Session = Depends(get_db)):
    """Supprime une offre de VM"""
    vm_offer = db.query(VMOfferEntity).filter(VMOfferEntity.id == id).first()
    if vm_offer is None:
        return StandardResponse(
            statusCode=404,
            message="Offre de VM non trouvée",
            data={}
        )
    
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
        
        return StandardResponse(
            statusCode=200,
            message="Offre de VM supprimée avec succès",
            data={}
        )
    except Exception as e:
        db.rollback()
        return StandardResponse(
            statusCode=500,
            message=str(e),
            data={}
        )


# Route pour obtenir toutes les offres actives

    
