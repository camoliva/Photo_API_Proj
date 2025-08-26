# app/routers/shoots.py 
"""
Shoots API endpoints.

This router manages photo shoots for clients:
- Create a shoot for a client
- List shoots with pagination
- Get one shoot
- Update selected fields
- Delete a shoot

Notes:
- We check the client exists when creating a shoot.
- Location is optional to keep it flexible for early bookings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter()


def _get_shoot_or_404(db: Session, shoot_id: int) -> models.Shoot:
    """Small helper to fetch a shoot or raise a 404."""
    obj = db.query(models.Shoot).filter(models.Shoot.shoot_id == shoot_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")
    return obj


@router.post("", response_model=schemas.ShootOut, status_code=status.HTTP_201_CREATED, summary="Create a shoot")
def create_shoot(payload: schemas.ShootCreate, db: Session = Depends(get_db)):
    """
    Create a shoot for a client.

    We make sure the client id is valid before inserting.
    """
    client = db.query(models.Client).filter(models.Client.client_id == payload.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client does not exist"
        )

    shoot = models.Shoot(**payload.model_dump())
    db.add(shoot)
    db.commit()
    db.refresh(shoot)
    return shoot


@router.get("", response_model=list[schemas.ShootOut], summary="List shoots")
def list_shoots(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    Return a simple list of shoots.
    """
    return (
        db.query(models.Shoot)
        .order_by(models.Shoot.shoot_date.desc(), models.Shoot.shoot_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{shoot_id}", response_model=schemas.ShootOut, summary="Get a shoot by id")
def get_shoot(shoot_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Fetch one shoot. Returns 404 if not found."""
    return _get_shoot_or_404(db, shoot_id)


@router.put("/{shoot_id}", response_model=schemas.ShootOut, summary="Update a shoot")
def update_shoot(
    shoot_id: int = Path(..., ge=1),
    payload: schemas.ShootUpdate = ...,
    db: Session = Depends(get_db),
):
    """
    Patch style update for a shoot.
    Only provided fields are changed.
    """
    shoot = _get_shoot_or_404(db, shoot_id)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(shoot, field, value)

    db.commit()
    db.refresh(shoot)
    return shoot


@router.delete("/{shoot_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a shoot")
def delete_shoot(shoot_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Delete a shoot.
    """
    shoot = _get_shoot_or_404(db, shoot_id)
    db.delete(shoot)
    db.commit()
    return None
