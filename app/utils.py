import uuid
from datetime import datetime
from app.models import OverToleranceLevel


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


def determine_over_tolerance_level(error: float, tolerance: float) -> OverToleranceLevel:
    if tolerance == 0:
        return OverToleranceLevel.SEVERE
    ratio = abs(error) / tolerance
    if ratio <= 1.0:
        return OverToleranceLevel.NONE
    elif ratio <= 1.5:
        return OverToleranceLevel.SLIGHT
    elif ratio <= 2.0:
        return OverToleranceLevel.MODERATE
    else:
        return OverToleranceLevel.SEVERE


def calculate_over_tolerance_ratio(error: float, tolerance: float) -> float:
    if tolerance == 0:
        return 999.0
    return abs(error) / tolerance


def is_adjustment_allowed(worst_level: OverToleranceLevel, failed_count: int, total_count: int) -> bool:
    if worst_level == OverToleranceLevel.SEVERE:
        return False
    if total_count == 0:
        return False
    fail_ratio = failed_count / total_count
    if worst_level == OverToleranceLevel.MODERATE and fail_ratio > 0.5:
        return False
    return True


def get_adjustment_deadline_days(worst_level: OverToleranceLevel) -> int:
    if worst_level == OverToleranceLevel.SLIGHT:
        return 15
    elif worst_level == OverToleranceLevel.MODERATE:
        return 7
    elif worst_level == OverToleranceLevel.SEVERE:
        return 3
    return 30


def get_reinspection_deadline_days(accuracy_class: str, worst_level: OverToleranceLevel) -> int:
    base_map = {
        "I": 180,
        "II": 90,
        "III": 30,
        "IIII": 15,
    }
    base = base_map.get(accuracy_class, 30)
    if worst_level == OverToleranceLevel.SLIGHT:
        return base
    elif worst_level == OverToleranceLevel.MODERATE:
        return max(base // 2, 7)
    elif worst_level == OverToleranceLevel.SEVERE:
        return max(base // 4, 3)
    return base


def generate_rectification_suggestions(
    worst_level: OverToleranceLevel,
    failed_details: list,
    seal_intact: bool,
    accuracy_class: str
) -> list:
    suggestions = []

    if not seal_intact and seal_intact is not None:
        suggestions.append("检定封印已破损，需检查是否存在人为篡改，必要时报请监管部门介入调查")

    if worst_level == OverToleranceLevel.SLIGHT:
        suggestions.append("超差属于轻微范围，建议进行零点校准和线性调整")
        suggestions.append("检查秤体放置是否平稳，避免地面倾斜或震动干扰")
    elif worst_level == OverToleranceLevel.MODERATE:
        suggestions.append("超差较为明显，需要由专业维修人员进行全面调校")
        suggestions.append("检查称重传感器是否老化或损坏，必要时更换")
        suggestions.append("调校完成后需在相同载荷点进行复测确认")
    elif worst_level == OverToleranceLevel.SEVERE:
        suggestions.append("严重超差，该衡器禁止继续使用，需立即停止营业使用")
        suggestions.append("建议联系生产厂家或具备资质的维修机构进行全面检修")
        suggestions.append("检修后必须经过重新检定合格方可投入使用")
        suggestions.append("需将严重超差情况通报市场监管部门备案")

    has_positive = any(d["error"] > 0 for d in failed_details)
    has_negative = any(d["error"] < 0 for d in failed_details)
    if has_positive and has_negative:
        suggestions.append("误差方向不一致（既有正差也有负差），提示传感器线性度异常，建议重点检查")
    elif has_positive:
        suggestions.append("误差均为正方向（示值偏重），建议检查传感器受力是否偏心")
    elif has_negative:
        suggestions.append("误差均为负方向（示值偏轻），建议检查是否存在零点漂移")

    high_value_failures = [d for d in failed_details if d.get("nominal_weight", 0) > 0]
    if high_value_failures:
        max_nominal = max(d["nominal_weight"] for d in high_value_failures)
        half_capacity = [d for d in failed_details if d["nominal_weight"] <= max_nominal * 0.5]
        full_capacity = [d for d in failed_details if d["nominal_weight"] > max_nominal * 0.5]
        if full_capacity and not half_capacity:
            suggestions.append("仅在大载荷区间超差，可能是传感器过载保护或弹性体疲劳")
        elif half_capacity and not full_capacity:
            suggestions.append("仅在中小载荷区间超差，重点检查零点附近传感器特性")

    if accuracy_class in ["I", "II"]:
        suggestions.append("高精度等级衡器，调校需在恒温恒湿环境下由专业人员操作")

    return suggestions


def determine_reinspection_load_points(failed_details: list) -> list:
    load_points = set()
    for d in failed_details:
        if d.get("load_point"):
            load_points.add(d["load_point"])
        else:
            load_points.add(f"{d['nominal_weight']}")
    nominal_weights = sorted(set(d["nominal_weight"] for d in failed_details))
    for w in nominal_weights:
        adjacent = w * 0.5
        if adjacent > 0:
            load_points.add(f"约{adjacent}（邻近超差点）")
    return sorted(load_points)
