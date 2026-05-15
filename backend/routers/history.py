"""History & search router — query persons, vehicles, alerts with advanced filters."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc, text, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers.auth import get_current_user
from models.user import User
from models.person import Person
from models.vehicle import Vehicle
from models.alert import Alert

router = APIRouter(prefix="/api", tags=["History & Search"])


def _apply_color_filter(query, count_q, column, color_name: str):
    """Apply JSON color filter using PostgreSQL @> operator."""
    json_pattern = f'[{{"name": "{color_name}"}}]'
    condition = column.cast(String).op("@>")(json_pattern)
    return query.where(condition), count_q.where(condition)


@router.get("/persons")
async def list_persons(
    camera_id: str | None = None,
    shirt_color: str | None = None,
    pants_color: str | None = None,
    min_confidence: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Person)
    count_q = select(func.count(Person.id))

    if camera_id:
        query = query.where(Person.camera_id == camera_id)
        count_q = count_q.where(Person.camera_id == camera_id)
    if date_from:
        query = query.where(Person.timestamp >= date_from)
        count_q = count_q.where(Person.timestamp >= date_from)
    if date_to:
        query = query.where(Person.timestamp <= date_to)
        count_q = count_q.where(Person.timestamp <= date_to)
    if min_confidence:
        query = query.where(Person.confidence >= min_confidence)
        count_q = count_q.where(Person.confidence >= min_confidence)

    # Color filters using PostgreSQL JSON containment
    if shirt_color:
        json_pattern = f'[{{"name": "{shirt_color}"}}]'
        condition = text(f"shirt_colors::text @> :pattern").bindparams(pattern=json_pattern)
        query = query.where(condition)
        count_q = count_q.where(condition)
    if pants_color:
        json_pattern = f'[{{"name": "{pants_color}"}}]'
        condition = text(f"pants_colors::text @> :pattern").bindparams(pattern=json_pattern)
        query = query.where(condition)
        count_q = count_q.where(condition)

    total = (await db.execute(count_q)).scalar() or 0

    # Sorting
    sort_col = Person.confidence if sort_by == "confidence" else Person.timestamp
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(sort_col)).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    persons = [p.to_dict() for p in result.scalars().all()]

    return {"persons": persons, "total": total, "page": page, "per_page": per_page}


@router.get("/vehicles")
async def list_vehicles(
    camera_id: str | None = None,
    vehicle_type: str | None = None,
    vehicle_color: str | None = None,
    license_plate: str | None = None,
    has_plate: bool | None = None,
    min_confidence: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Vehicle)
    count_q = select(func.count(Vehicle.id))

    if camera_id:
        query = query.where(Vehicle.camera_id == camera_id)
        count_q = count_q.where(Vehicle.camera_id == camera_id)
    if vehicle_type:
        query = query.where(Vehicle.vehicle_type == vehicle_type)
        count_q = count_q.where(Vehicle.vehicle_type == vehicle_type)
    if license_plate:
        query = query.where(Vehicle.license_plate.ilike(f"%{license_plate}%"))
        count_q = count_q.where(Vehicle.license_plate.ilike(f"%{license_plate}%"))
    if has_plate is True:
        query = query.where(Vehicle.license_plate.isnot(None), Vehicle.license_plate != "")
        count_q = count_q.where(Vehicle.license_plate.isnot(None), Vehicle.license_plate != "")
    if min_confidence:
        query = query.where(Vehicle.confidence >= min_confidence)
        count_q = count_q.where(Vehicle.confidence >= min_confidence)
    if date_from:
        query = query.where(Vehicle.timestamp >= date_from)
        count_q = count_q.where(Vehicle.timestamp >= date_from)
    if date_to:
        query = query.where(Vehicle.timestamp <= date_to)
        count_q = count_q.where(Vehicle.timestamp <= date_to)

    # Vehicle color filter
    if vehicle_color:
        json_pattern = f'[{{"name": "{vehicle_color}"}}]'
        condition = text(f"vehicle_colors::text @> :pattern").bindparams(pattern=json_pattern)
        query = query.where(condition)
        count_q = count_q.where(condition)

    total = (await db.execute(count_q)).scalar() or 0

    sort_col = Vehicle.confidence if sort_by == "confidence" else Vehicle.timestamp
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(sort_col)).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    vehicles = [v.to_dict() for v in result.scalars().all()]

    return {"vehicles": vehicles, "total": total, "page": page, "per_page": per_page}


@router.get("/alerts")
async def list_alerts(
    camera_id: str | None = None,
    alert_type: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Alert)
    count_q = select(func.count(Alert.id))

    if camera_id:
        query = query.where(Alert.camera_id == camera_id)
        count_q = count_q.where(Alert.camera_id == camera_id)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
        count_q = count_q.where(Alert.alert_type == alert_type)
    if status:
        query = query.where(Alert.status == status)
        count_q = count_q.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
        count_q = count_q.where(Alert.severity == severity)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(desc(Alert.timestamp)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    alerts = [a.to_dict() for a in result.scalars().all()]

    return {"alerts": alerts, "total": total, "page": page, "per_page": per_page}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = user.username
    await db.commit()
    return alert.to_dict()


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dashboard overview statistics."""
    from models.camera import Camera

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    persons_today = (await db.execute(
        select(func.count(Person.id)).where(Person.timestamp >= today_start)
    )).scalar() or 0

    vehicles_today = (await db.execute(
        select(func.count(Vehicle.id)).where(Vehicle.timestamp >= today_start)
    )).scalar() or 0

    active_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.status == "active")
    )).scalar() or 0

    cameras_online = (await db.execute(
        select(func.count(Camera.id)).where(Camera.connection_status == "connected")
    )).scalar() or 0

    cameras_total = (await db.execute(select(func.count(Camera.id)))).scalar() or 0

    return {
        "persons_today": persons_today,
        "vehicles_today": vehicles_today,
        "active_alerts": active_alerts,
        "cameras_online": cameras_online,
        "cameras_total": cameras_total,
    }
