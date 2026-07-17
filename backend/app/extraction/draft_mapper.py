"""Map extraction candidates into simple editable Risklocker draft fields."""

from __future__ import annotations

from app.extraction.candidate_finder import DRAFT_FIELDS, MONEY_FIELDS
from app.extraction.conflict_detector import select_all
from app.extraction.types import CandidateValue
from app.extraction.validators import validate_date_range, validate_engine_cc, validate_money, validate_ncd, validate_vehicle_number
from app.models.enums import RecordStatus


def build_draft(candidates: dict[str, list[CandidateValue]]) -> tuple[dict, list[str], str]:
    selections = select_all(candidates, DRAFT_FIELDS)
    fields = {field: selection.to_draft_field() for field, selection in selections.items()}
    fields["insurance_type"]["value"] = fields["insurance_type"]["value"] or "Motor"
    fields["insurance_type"]["status"] = "ready"

    warnings: list[str] = []
    required_money_fields = {"coverage_amount", "premium", "total_amount"}
    validators = {
        "vehicle_no": validate_vehicle_number,
        "ncd_percent": validate_ncd,
        "engine_cc": validate_engine_cc,
    }
    validators.update({field_name: validate_money for field_name in MONEY_FIELDS})
    for field_name, validator in validators.items():
        if field_name not in fields:
            continue
        if field_name in MONEY_FIELDS and field_name not in required_money_fields and not fields[field_name].get("value"):
            continue
        ok, message = validator(fields[field_name].get("value"))
        if not ok:
            fields[field_name]["status"] = "check_needed"
            fields[field_name]["message"] = "Please check this value."
            if message:
                fields[field_name].setdefault("warnings", []).append(message)

    date_ok, date_message = validate_date_range(fields.get("cover_start_date", {}).get("value"), fields.get("cover_end_date", {}).get("value"))
    if not date_ok:
        for name in ("cover_start_date", "cover_end_date"):
            fields[name]["status"] = "check_needed"
            fields[name]["message"] = "Please check this value."
            fields[name].setdefault("warnings", []).append(date_message or "Please check this value.")

    start = fields.get("cover_start_date", {}).get("value") or ""
    end = fields.get("cover_end_date", {}).get("value") or ""
    fields["cover_period"]["value"] = f"{start} to {end}".strip(" to")
    fields["cover_period"]["status"] = "check_needed" if not date_ok else "ready"

    check_count = sum(1 for field in fields.values() if field.get("status") == "check_needed")
    if check_count:
        warnings.append("Please check highlighted values before generating.")
        status = RecordStatus.CHECK_NEEDED.value
    else:
        status = RecordStatus.READY.value

    has_any_required = any(fields[name].get("value") for name in ("customer_name", "vehicle_no", "insurance_company"))
    if not has_any_required:
        status = RecordStatus.CANNOT_READ.value
        warnings.append("Cannot Read")

    return fields, warnings, status
