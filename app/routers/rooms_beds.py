from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.room_bed import Bed, Room
from app.schemas.room_bed import (
    BedCreate,
    BedResponse,
    BedUpdate,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)

router = APIRouter(
    prefix="/api/rooms-beds",
    tags=["Rooms & Beds"]
)


def _format_flat_bed(bed: Bed) -> dict:
    return {
        "id": bed.id,
        "room_id": bed.room_id,
        "bed_number": bed.bed_number,
        "status": bed.status,
        "patient_id": bed.patient_id,
        "patient_name": bed.patient_name,
        "patient_code": bed.patient_code,
        "admission_date": bed.admission_date,
        "daily_charge": float(bed.daily_charge),
        "room_number": bed.room.room_number if bed.room else None,
        "room_type": bed.room.room_type if bed.room else None,
        "floor": bed.room.floor if bed.room else None,
        "ward": bed.room.ward if bed.room else None,
        "department": bed.room.department if bed.room else None,
    }


@router.get("")
def get_rooms_and_beds(db: Session = Depends(get_db)):
    rooms = db.query(Room).options(joinedload(Room.beds)).order_by(Room.id).all()
    beds = db.query(Bed).options(joinedload(Bed.room)).order_by(Bed.id).all()

    formatted_rooms = []
    for r in rooms:
        formatted_rooms.append({
            "id": r.id,
            "room_number": r.room_number,
            "ward": r.ward,
            "room_type": r.room_type,
            "floor": r.floor,
            "department": r.department,
            "daily_charge": float(r.daily_charge),
            "status": r.status,
            "beds": [
                {
                    "id": b.id,
                    "room_id": b.room_id,
                    "bed_number": b.bed_number,
                    "status": b.status,
                    "patient_id": b.patient_id,
                    "patient_name": b.patient_name,
                    "patient_code": b.patient_code,
                    "admission_date": b.admission_date,
                    "daily_charge": float(b.daily_charge),
                }
                for b in r.beds
            ]
        })

    formatted_beds = [_format_flat_bed(b) for b in beds]

    return {
        "rooms": formatted_rooms,
        "beds": formatted_beds,
        "items": formatted_beds
    }


@router.get("/beds", response_model=list[BedResponse])
def get_beds(db: Session = Depends(get_db)):
    beds = db.query(Bed).options(joinedload(Bed.room)).order_by(Bed.id).all()
    return [_format_flat_bed(b) for b in beds]


@router.post("/rooms", status_code=status.HTTP_201_CREATED)
def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter(Room.room_number == data.room_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room number already exists"
        )

    room = Room(
        room_number=data.room_number,
        ward=data.ward,
        room_type=data.room_type,
        floor=data.floor,
        department=data.department,
        daily_charge=data.daily_charge,
        status=data.status,
    )
    db.add(room)
    db.flush()

    for bed_data in data.beds:
        bed = Bed(
            room_id=room.id,
            bed_number=bed_data.bed_number,
            status=bed_data.status,
            patient_id=bed_data.patient_id,
            patient_name=bed_data.patient_name,
            patient_code=bed_data.patient_code,
            admission_date=bed_data.admission_date,
            daily_charge=bed_data.daily_charge or data.daily_charge,
        )
        db.add(bed)

    db.commit()
    db.refresh(room)
    return {"message": "Room created successfully", "room_id": room.id}


@router.put("/rooms/{room_id}")
def update_room(room_id: int, data: RoomUpdate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)

    db.commit()
    db.refresh(room)
    return {"message": "Room updated successfully"}


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    db.delete(room)
    db.commit()
    return {"message": "Room deleted successfully"}


@router.post("/beds", status_code=status.HTTP_201_CREATED)
def create_bed(data: BedCreate, room_id: int | None = None, db: Session = Depends(get_db)):
    target_room_id = room_id or data.room_id
    if not target_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="room_id is required"
        )
    room = db.query(Room).filter(Room.id == target_room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    bed = Bed(
        room_id=room.id,
        bed_number=data.bed_number,
        status=data.status,
        patient_id=data.patient_id,
        patient_name=data.patient_name,
        patient_code=data.patient_code,
        admission_date=data.admission_date,
        daily_charge=data.daily_charge,
    )
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return _format_flat_bed(bed)


@router.put("/beds/{bed_id}")
def update_bed(bed_id: int, data: BedUpdate, db: Session = Depends(get_db)):
    bed = db.query(Bed).options(joinedload(Bed.room)).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bed not found"
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bed, field, value)

    db.commit()
    db.refresh(bed)
    return _format_flat_bed(bed)


@router.delete("/beds/{bed_id}")
def delete_bed(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bed not found"
        )

    db.delete(bed)
    db.commit()
    return {"message": "Bed deleted successfully"}
