import math

from fastapi import HTTPException

from app.core.config import Settings

EARTH_RADIUS_METERS = 6_371_008.8


def distance_meters(
    latitude: float,
    longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    """Return the great-circle distance between two WGS-84 coordinates."""

    lat1, lat2 = math.radians(latitude), math.radians(target_latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(target_longitude - longitude)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return EARTH_RADIUS_METERS * 2 * math.atan2(
        math.sqrt(haversine), math.sqrt(max(0.0, 1 - haversine))
    )


def validate_attendance_location(
    settings: Settings,
    latitude: float | None,
    longitude: float | None,
    accuracy_meters: float | None,
) -> float | None:
    """Validate an attendance coordinate and return its distance from the office."""

    if latitude is None or longitude is None or not settings.geofencing_enabled:
        return None
    if accuracy_meters is not None and accuracy_meters > settings.geofence_max_accuracy_meters:
        raise HTTPException(
            422,
            "Tín hiệu GPS chưa đủ chính xác để chấm công "
            f"(sai số {accuracy_meters:.0f} m, tối đa {settings.geofence_max_accuracy_meters:.0f} m)",
        )
    distance = distance_meters(
        latitude,
        longitude,
        settings.company_latitude,
        settings.company_longitude,
    )
    if distance > settings.geofence_radius_meters:
        raise HTTPException(
            403,
            "Bạn đang ở ngoài khu vực chấm công "
            f"({distance:.0f} m từ công ty, bán kính cho phép {settings.geofence_radius_meters:.0f} m)",
        )
    return round(distance, 1)
