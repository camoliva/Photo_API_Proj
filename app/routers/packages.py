# app/routers/packages.py 
"""
Packages API endpoints.

This router manages the packages that can be referenced by invoices:
- Create a package
- List packages with pagination
- Get one package
- Update selected fields
- Delete a package

Notes:
- Using Decimal for price in schemas avoids float rounding surprises.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter()


def _get_package_or_404(db: Session, package_id: int) -> models.Package:
    """Fetch a package or return 404 if it does not exist."""
    obj = db.query(models.Package).filter(models.Package.package_id == package_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return obj


@router.post("", response_model=schemas.PackageOut, status_code=status.HTTP_201_CREATED, summary="Create a package")
def create_package(payload: schemas.PackageCreate, db: Session = Depends(get_db)):
    """
    Create a package.

    Name does not need to be unique globally, but keep it sensible.
    """
    package = models.Package(**payload.model_dump())
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


@router.get("", response_model=list[schemas.PackageOut], summary="List packages")
def list_packages(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """Paginated list of packages, newest first."""
    return (
        db.query(models.Package)
        .order_by(models.Package.package_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{package_id}", response_model=schemas.PackageOut, summary="Get a package by id")
def get_package(package_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Return one package by id."""
    return _get_package_or_404(db, package_id)


@router.put("/{package_id}", response_model=schemas.PackageOut, summary="Update a package")
def update_package(
    package_id: int = Path(..., ge=1),
    payload: schemas.PackageUpdate = ...,
    db: Session = Depends(get_db),
):
    """
    Patch style update for a package.
    Only provided fields are changed.
    """
    package = _get_package_or_404(db, package_id)
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(package, field, value)

    db.commit()
    db.refresh(package)
    return package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a package")
def delete_package(package_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """
    Delete a package.

    If invoices reference this package, the delete may fail depending on
    your foreign key constraints. In that case, make the package inactive.
    """
    package = _get_package_or_404(db, package_id)
    db.delete(package)
    db.commit()
    return None
