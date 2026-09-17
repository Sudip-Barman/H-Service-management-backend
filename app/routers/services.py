from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.models.user import User
from app.schemas.service import (
    ServiceCreate,
    ServiceResponse
)
from app.core.dependencies import require_role, require_admin


router = APIRouter(
    prefix="/api/services",
    tags=["Services"]
)


@router.get(
    "",
    response_model=list[ServiceResponse]
)
def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "admin",
            "receptionist",
            "doctor",
            "nurse"
        )
    )
):
    services = (
        db.query(Service)
        .order_by(Service.id.desc())
        .all()
    )

    return services


@router.get(
    "/{service_id}",
    response_model=ServiceResponse
)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "admin",
            "receptionist",
            "doctor",
            "nurse"
        )
    )
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    return service


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "admin",
            "receptionist"
        )
    )
):
    new_service = Service(
        name=service_data.name,
        category=service_data.category,
        description=service_data.description,
        price=service_data.price,
        duration=service_data.duration,
        is_active=service_data.is_active
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return new_service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse
)
def update_service(
    service_id: int,
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            "admin",
            "receptionist"
        )
    )
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    service.name = service_data.name
    service.category = service_data.category
    service.description = service_data.description
    service.price = service_data.price
    service.duration = service_data.duration
    service.is_active = service_data.is_active

    db.commit()
    db.refresh(service)

    return service


@router.delete(
    "/{service_id}"
)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    db.delete(service)
    db.commit()

    return {
        "message": "Service deleted successfully"
    }