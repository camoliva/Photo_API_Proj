# app/routers/clients.py
"""
Clients API endpoints!!!

This router handles CRUD for clients:
- Create a client with unique email
- List clients with pagination
- Get a single client by id
- Update selected fields
- Delete a client

Notes:
- Duplicate email checks keep the data clean.
- Response models use Pydantic schemas so Swagger reads nicely.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter()


def _get_client_or_404(db: Session, client_id: int) -> models.Client:
    """Small helper to fetch a client or raise a 404."""
    obj = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return obj


@router.post("", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED, summary="Create a client")
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    """
    Create a new client.

    We block duplicate emails so contacts stay unique.
    """
    existing = db.query(models.Client).filter(models.Client.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this email already exists"
        )
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[schemas.ClientOut], summary="List clients")
def list_clients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    Return a simple paginated list of clients.

    """
    return (
        db.query(models.Client)
        .order_by(models.Client.client_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{client_id}", response_model=schemas.ClientOut, summary="Get a client by id")
def get_client(client_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Fetch one client. Returns 404 if it does not exist."""
    return _get_client_or_404(db, client_id)


@router.put("/{client_id}", response_model=schemas.ClientOut, summary="Update a client")
def update_client(
    client_id: int = Path(..., ge=1),
    payload: schemas.ClientUpdate = ...,
    db: Session = Depends(get_db),
):
    """
    Patch style update.

    Only fields provided in the payload are changed. If email is being
    updated, we re-check duplicate emails to protect uniquenesss.
    """
    client = _get_client_or_404(db, client_id)

    data = payload.model_dump(exclude_unset=True)
    if "email" in data:
        clash = (
            db.query(models.Client)
            .filter(models.Client.email == data["email"], models.Client.client_id != client_id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Oops another client already uses this email"
            )

    for field, value in data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a client")
def delete_client(client_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Delete a client.

    Cascades will remove child rows according to the model config.
    """
    client = _get_client_or_404(db, client_id)
    db.delete(client)
    db.commit()
    return None
