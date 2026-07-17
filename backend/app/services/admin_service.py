"""Admin CRUD helpers for system configuration."""

from __future__ import annotations

from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import AccountStatus, Role
from app.models.tables import AppSetting, BenefitOption, FieldAlias, InsuranceCompany, OutputTemplateConfig, VehicleBrand, VehicleModel
from app.services.template_config import normalize_template_config, review_schema_for


def require_admin(user) -> None:
    if user.role != Role.ADMIN.value:
        raise AppError("Only Admin can change this setting.", 403)


def upsert_company(db: Session, user, payload: dict) -> InsuranceCompany:
    require_admin(user)
    company = db.get(InsuranceCompany, payload.get("id")) if payload.get("id") else None
    if not company:
        company = InsuranceCompany(name=payload["name"], category=payload.get("category", "Motor"))
        db.add(company)
    company.name = payload.get("name", company.name)
    company.category = payload.get("category", company.category)
    company.source_template_category = payload.get("source_template_category", company.source_template_category)
    company.detection_phrases = payload.get("detection_phrases", company.detection_phrases)
    company.logo_path = payload.get("logo_path", company.logo_path)
    company.status = payload.get("status", company.status)
    db.commit()
    db.refresh(company)
    return company


def upsert_template(db: Session, user, payload: dict) -> OutputTemplateConfig:
    require_admin(user)
    template = db.get(OutputTemplateConfig, payload.get("id")) if payload.get("id") else None
    if template and normalize_template_config(template.fixed_fields, template.name).get("locked"):
        raise AppError("Copy this default template before editing.")
    if not template:
        template = OutputTemplateConfig(name=payload["name"], insurance_type=payload.get("insurance_type", "Motor"))
        db.add(template)
    for key in ["name", "insurance_type", "insurance_company_id", "html_template", "css_template", "static_notes", "editable_fields", "fixed_fields", "status"]:
        if key in payload:
            setattr(template, key, payload[key])
    db.commit()
    db.refresh(template)
    return template


def serialize_template(template: OutputTemplateConfig) -> dict:
    config = normalize_template_config(template.fixed_fields, template.name)
    return {
        "id": template.id,
        "name": template.name,
        "insurance_type": template.insurance_type,
        "insurance_company_id": template.insurance_company_id,
        "status": template.status,
        "static_notes": template.static_notes,
        "editable_fields": template.editable_fields,
        "fixed_fields": config,
        "locked": bool(config.get("locked")),
        "is_default": bool(config.get("is_default")),
        "packages": config.get("packages", []),
        "review_schema": review_schema_for(config, None),
    }


def copy_template(db: Session, user, template_id: str) -> OutputTemplateConfig:
    require_admin(user)
    source = db.get(OutputTemplateConfig, template_id)
    if not source:
        raise AppError("Template not found.", 404)
    config = normalize_template_config(source.fixed_fields, source.name)
    config["is_default"] = False
    config["locked"] = False
    copy = OutputTemplateConfig(
        name=f"Copy of {source.name}",
        insurance_type=source.insurance_type,
        insurance_company_id=source.insurance_company_id,
        html_template=source.html_template,
        css_template=source.css_template,
        static_notes=source.static_notes,
        editable_fields=list(source.editable_fields or []),
        fixed_fields=deepcopy(config),
        status=AccountStatus.ACTIVE.value,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


def update_template(db: Session, user, template_id: str, payload: dict) -> OutputTemplateConfig:
    require_admin(user)
    template = db.get(OutputTemplateConfig, template_id)
    if not template:
        raise AppError("Template not found.", 404)
    current_config = normalize_template_config(template.fixed_fields, template.name)
    if current_config.get("locked"):
        raise AppError("Copy this default template before editing.")
    for key in ["name", "insurance_type", "insurance_company_id", "static_notes", "editable_fields", "status"]:
        if key in payload:
            setattr(template, key, payload[key])
    if "fixed_fields" in payload:
        config = normalize_template_config(payload["fixed_fields"], template.name)
        config["is_default"] = False
        config["locked"] = False
        template.fixed_fields = config
    db.commit()
    db.refresh(template)
    return template


def upsert_benefit(db: Session, user, payload: dict) -> BenefitOption:
    require_admin(user)
    benefit = db.get(BenefitOption, payload.get("id")) if payload.get("id") else None
    if not benefit:
        benefit = BenefitOption(label=payload["label"])
        db.add(benefit)
    for key in ["insurance_company_id", "template_id", "label", "section", "default_selected", "status"]:
        if key in payload:
            setattr(benefit, key, payload[key])
    db.commit()
    db.refresh(benefit)
    return benefit


def upsert_field_alias(db: Session, user, payload: dict) -> FieldAlias:
    require_admin(user)
    alias = db.scalar(select(FieldAlias).where(FieldAlias.field_name == payload["field_name"]))
    if not alias:
        alias = FieldAlias(field_name=payload["field_name"])
        db.add(alias)
    alias.aliases = payload.get("aliases", alias.aliases)
    alias.status = payload.get("status", alias.status)
    db.commit()
    db.refresh(alias)
    return alias


def upsert_vehicle_brand(db: Session, user, payload: dict) -> VehicleBrand:
    require_admin(user)
    brand = db.get(VehicleBrand, payload.get("id")) if payload.get("id") else None
    if not brand:
        brand = VehicleBrand(name=payload["name"])
        db.add(brand)
    brand.name = payload.get("name", brand.name)
    brand.aliases = payload.get("aliases", brand.aliases)
    brand.status = payload.get("status", brand.status)
    db.commit()
    db.refresh(brand)
    return brand


def upsert_vehicle_model(db: Session, user, payload: dict) -> VehicleModel:
    require_admin(user)
    model = db.get(VehicleModel, payload.get("id")) if payload.get("id") else None
    if not model:
        model = VehicleModel(name=payload["name"])
        db.add(model)
    for key in ["brand_id", "name", "aliases", "status"]:
        if key in payload:
            setattr(model, key, payload[key])
    db.commit()
    db.refresh(model)
    return model


def save_strategy_settings(db: Session, user, payload: dict) -> AppSetting:
    require_admin(user)
    if not any(payload.values()):
        raise AppError("At least one reading method must stay enabled.")
    setting = db.get(AppSetting, "extraction_strategies")
    if not setting:
        setting = AppSetting(key="extraction_strategies", value=payload)
        db.add(setting)
    else:
        setting.value = payload
    db.commit()
    db.refresh(setting)
    return setting
