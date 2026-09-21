from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.models.user import User
from app.schemas.service import (
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
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
    db: Session = Depends(get_db)
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


from app.services.notification_service import create_system_notification


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db)
):
    new_service = Service(
        name=service_data.name,
        category=service_data.category,
        description=service_data.description,
        price=service_data.price,
        staff_required=service_data.staff_required,
        available_staff=service_data.available_staff,
        bookings=service_data.bookings,
        rating=service_data.rating,
        duration=service_data.duration,
        is_active=service_data.is_active
    )

    db.add(new_service)

    # Automated Notification Trigger
    create_system_notification(
        db=db,
        title=f"New Service Added: {new_service.name}",
        message=f"A new medical service '{new_service.name}' ({new_service.category}) was added with fee ₹{new_service.price}.",
        notif_type="Services",
        priority="Normal",
        department=new_service.category or "Administration",
        recipient="All Hospital Staff",
    )

    db.commit()
    db.refresh(new_service)

    return new_service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse
)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db)
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

    if service_data.name is not None:
        service.name = service_data.name
    if service_data.category is not None:
        service.category = service_data.category
    if service_data.description is not None:
        service.description = service_data.description
    if service_data.price is not None:
        service.price = service_data.price
    if service_data.staff_required is not None:
        service.staff_required = service_data.staff_required
    if service_data.available_staff is not None:
        service.available_staff = service_data.available_staff
    if service_data.bookings is not None:
        service.bookings = service_data.bookings
    if service_data.rating is not None:
        service.rating = service_data.rating
    if service_data.duration is not None:
        service.duration = service_data.duration
    if service_data.is_active is not None:
        service.is_active = service_data.is_active

    db.commit()
    db.refresh(service)

    return service


@router.delete(
    "/{service_id}"
)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db)
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