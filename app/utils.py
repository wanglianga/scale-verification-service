import uuid
from datetime import datetime


def generate_no(prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{timestamp}{short_uuid}"


def calculate_error(nominal: float, indication: float) -> float:
    return indication - nominal


def calculate_error_percentage(nominal: float, error: float) -> float:
    if nominal == 0:
        return 0.0
    return (error / nominal) * 100


def calculate_tolerance(nominal: float, accuracy_class: str = "III") -> float:
    tolerance_map = {
        "I": nominal * 0.0001,
        "II": nominal * 0.0005,
        "III": nominal * 0.001,
        "IIII": nominal * 0.005,
    }
    return tolerance_map.get(accuracy_class, nominal * 0.001)


def is_within_tolerance(error: float, tolerance: float) -> bool:
    return abs(error) <= tolerance
