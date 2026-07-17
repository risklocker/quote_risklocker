"""Application API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, Response as FastAPIResponse, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import AuthContext, current_auth, current_user, ensure_trusted_origin, settings_dep
from app.api.schemas import LoginCodeRequest, LoginCodeVerify, UserCreateRequest, UserUpdateRequest
from app.auth.rbac import can_view_owner_record, require_role
from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.enums import Role, StorageStatus
from app.models.tables import (
    BenefitOption,
    FieldAlias,
    GeneratedPdfVersion,
    InsuranceCompany,
    OutputTemplateConfig,
    QuotationDraft,
    StorageConnection,
    UploadedFile,
    User,
    VehicleBrand,
    VehicleModel,
)
from app.services.admin_service import (
    copy_template,
    save_strategy_settings,
    serialize_template,
    update_template,
    upsert_benefit,
    upsert_company,
    upsert_field_alias,
    upsert_template,
    upsert_vehicle_brand,
    upsert_vehicle_model,
)
from app.services.auth_service import (
    LOGIN_REQUEST_MESSAGE,
    invite_user,
    notify_role_change,
    notify_status_change,
    request_login_code,
    revoke_session,
    revoke_user_sessions,
    serialize_user,
    update_user,
    verify_code_and_create_session,
)
from app.services.email_service import send_test_email, validate_smtp_connection
from app.services.notification_service import (
    get_notifications,
    get_unread_count,
    mark_all_read,
    mark_read,
    serialize_notification,
)
from app.services.pdf_service import generate_pdf
from app.services.pdf_content import load_pdf_bytes, parse_byte_range
from app.services.review_service import (
    get_accessible_draft,
    list_history,
    list_trash,
    move_to_trash,
    purge_expired_trash,
    restore_from_trash,
    serialize_draft,
    update_draft_fields,
)
from app.services.system_checks import get_system_checks
from app.services.storage_retention import purge_expired_pdfs
from app.services.template_assets import list_template_assets, resolve_template_asset
from app.services.upload_service import create_batch_from_uploads, serialize_batch, serialize_file
from app.storage.supabase import SupabaseStorage


router = APIRouter()


def _set_session_cookie(response: FastAPIResponse, settings: Settings, token: str, max_age: int) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _pdf_response(data: bytes, filename: str, range_header: str | None, download: bool) -> Response:
    selected_range = parse_byte_range(range_header, len(data))
    disposition = "attachment" if download else "inline"
    safe_filename = filename.replace('"', "_").replace("\r", "_").replace("\n", "_")
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'{disposition}; filename="{safe_filename}"',
        "Cache-Control": "private, no-store",
    }
    if selected_range:
        start, end = selected_range
        headers["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
        return Response(data[start : end + 1], status_code=206, media_type="application/pdf", headers=headers)
    return Response(data, media_type="application/pdf", headers=headers)


@router.get("/health")
def health(settings: Settings = Depends(settings_dep)) -> dict:
    return {"status": "Ready", "app": settings.app_name}


@router.post("/auth/request-code", status_code=202)
def auth_request_code(
    payload: LoginCodeRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    ensure_trusted_origin(request, settings)
    request_login_code(db, settings, payload.email)
    return {"message": LOGIN_REQUEST_MESSAGE}


@router.post("/auth/verify-code")
def auth_verify_code(
    payload: LoginCodeVerify,
    request: Request,
    response: FastAPIResponse,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    ensure_trusted_origin(request, settings)
    user, session, raw_token = verify_code_and_create_session(
        db,
        settings,
        payload.email,
        payload.code,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    max_age = int((session.absolute_expires_at - session.last_activity_at).total_seconds())
    _set_session_cookie(response, settings, raw_token, max_age)
    return {"user": serialize_user(user)}


@router.post("/auth/logout")
def auth_logout(
    response: FastAPIResponse,
    auth: AuthContext = Depends(current_auth),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> dict:
    revoke_session(db, auth.session, auth.user.id)
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return {"signed_out": True}


@router.get("/auth/me")
def me(user: User = Depends(current_user)) -> dict:
    return serialize_user(user)


@router.get("/system/checks")
def system_checks(db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN)
    return {"checks": get_system_checks(settings, db)}


@router.post("/users")
def user_create(payload: UserCreateRequest, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    created = invite_user(db, settings, user, payload.email, payload.role)
    return serialize_user(created)


@router.get("/users")
def users_list(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    query = select(User).order_by(User.created_at.desc())
    if user.role == Role.MANAGER.value:
        query = query.where(User.role == Role.STAFF.value)
    return {"users": [serialize_user(item) for item in db.scalars(query).all()]}


@router.patch("/users/{user_id}")
def users_update(user_id: str, payload: UserUpdateRequest, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    target = db.get(User, user_id)
    if not target:
        raise AppError("User not found.", 404)
    require_role(user, Role.ADMIN, Role.MANAGER)
    previous_role = target.role
    previous_status = target.status
    updated = update_user(db, user, target, email=payload.email, role=payload.role, status=payload.status)
    if payload.role is not None and payload.role != previous_role:
        notify_role_change(db, settings, user, updated, payload.role)
    if payload.status is not None and payload.status != previous_status:
        notify_status_change(db, settings, user, updated, payload.status)
    return serialize_user(updated)


@router.post("/users/{user_id}/sessions/revoke")
def user_sessions_revoke(user_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN)
    target = db.get(User, user_id)
    if not target:
        raise AppError("User not found.", 404)
    return {"revoked_sessions": revoke_user_sessions(db, target.id, user.id)}


@router.get("/notifications")
def notifications_list(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"notifications": [serialize_notification(n) for n in get_notifications(db, user.id)]}


@router.get("/notifications/unread-count")
def notifications_unread_count(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"unread_count": get_unread_count(db, user.id)}


@router.patch("/notifications/{notification_id}/read")
def notification_mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    notification = mark_read(db, notification_id, user.id)
    return {"notification": serialize_notification(notification)}


@router.patch("/notifications/read")
def notification_mark_all_read(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"updated": mark_all_read(db, user.id)}


@router.post("/admin/mail/test")
def admin_mail_test(db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN)
    valid, message = validate_smtp_connection(settings)
    if not valid:
        return {"ok": False, "message": message}
    try:
        send_test_email(settings, user.email)
    except Exception as exc:
        return {"ok": False, "message": f"SMTP connected but test delivery failed: {exc}."}
    return {"ok": True, "message": f"Test email sent to {user.email}. Check your inbox."}


@router.post("/batches/upload")
async def upload_batch(
    files: list[UploadFile] = File(...),
    enhanced_reading: bool = Form(False),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    user: User = Depends(current_user),
) -> dict:
    batch = await create_batch_from_uploads(db, settings, user.id, files, enhanced_reading)
    return {"batch": serialize_batch(batch)}


@router.get("/batches/{batch_id}")
def batch_detail(batch_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    from app.models.tables import Batch

    batch = db.scalar(select(Batch).where(Batch.id == batch_id).options(selectinload(Batch.files).selectinload(UploadedFile.draft)))
    if not batch or batch.deleted_at:
        raise AppError("Batch not found.", 404)
    if not can_view_owner_record(db, user, batch.owner_id):
        raise AppError("You do not have permission to view this batch.", 403)
    return {"batch": serialize_batch(batch)}


@router.get("/drafts/{draft_id}")
def draft_detail(draft_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    draft = get_accessible_draft(db, user, draft_id)
    return {"draft": serialize_draft(draft, db)}


@router.patch("/drafts/{draft_id}")
def draft_update(draft_id: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    draft = update_draft_fields(
        db,
        user,
        draft_id,
        payload.get("fields", {}),
        template_id=payload.get("template_id"),
        selected_package=payload.get("selected_package"),
        benefits_selected=payload.get("benefits_selected"),
        add_ons_selected=payload.get("add_ons_selected"),
    )
    return {"draft": serialize_draft(draft, db)}


@router.post("/drafts/{draft_id}/generate")
def draft_generate(draft_id: str, payload: dict | None = None, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    draft = get_accessible_draft(db, user, draft_id)
    version = generate_pdf(db, settings, user, draft, acknowledge_check_needed=bool((payload or {}).get("acknowledge_check_needed")))
    return {
        "version": {
            "id": version.id,
            "filename": version.filename,
            "version_number": version.version_number,
            "download_url": f"/generated-versions/{version.id}/content?download=true",
        }
    }


@router.post("/drafts/generate-selected")
def generate_selected(payload: dict, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    versions = []
    for draft_id in payload.get("draft_ids", []):
        draft = get_accessible_draft(db, user, draft_id)
        version = generate_pdf(db, settings, user, draft, acknowledge_check_needed=bool(payload.get("acknowledge_check_needed")))
        versions.append({"id": version.id, "filename": version.filename, "download_url": f"/generated-versions/{version.id}/content?download=true"})
    return {"versions": versions}


@router.get("/history")
def history(status: str | None = None, search: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"records": [serialize_file(file) for file in list_history(db, user, status, search)]}


@router.delete("/records/{uploaded_file_id}")
def delete_record(uploaded_file_id: str, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep), user: User = Depends(current_user)) -> dict:
    move_to_trash(db, settings, user, uploaded_file_id)
    return {"status": "Deleted"}


@router.get("/trash")
def trash(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"records": [serialize_file(file) for file in list_trash(db, user)]}


@router.post("/trash/{uploaded_file_id}/restore")
def trash_restore(uploaded_file_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    restore_from_trash(db, user, uploaded_file_id)
    return {"status": "Ready"}


@router.post("/trash/purge-expired")
def trash_purge(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return {"purged": purge_expired_trash(db, user)}


@router.get("/extractions/{uploaded_file_id}")
def extraction_detail(uploaded_file_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    uploaded = db.scalar(select(UploadedFile).where(UploadedFile.id == uploaded_file_id).options(selectinload(UploadedFile.extraction_record)))
    if not uploaded or not uploaded.extraction_record:
        raise AppError("Extraction details not found.", 404)
    record = uploaded.extraction_record
    return {
        "extraction": {
            "uploaded_file_id": uploaded.id,
            "method_summary": record.method_summary,
            "page_text": record.page_text,
            "words": record.words,
            "blocks": record.blocks,
            "tables": record.tables,
            "images": record.images,
            "regions": record.regions,
            "candidates": record.candidates,
            "warnings": record.warnings,
            "reading_quality": record.reading_quality,
        }
    }


@router.get("/admin/companies")
def admin_companies(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    return {
        "companies": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "source_template_category": item.source_template_category,
                "detection_phrases": item.detection_phrases,
                "status": item.status,
            }
            for item in db.scalars(select(InsuranceCompany)).all()
        ]
    }


@router.post("/admin/companies")
def admin_company_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    company = upsert_company(db, user, payload)
    return {"company": {"id": company.id, "name": company.name, "category": company.category, "status": company.status, "detection_phrases": company.detection_phrases}}


@router.get("/admin/templates")
def admin_templates(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    return {"templates": [serialize_template(item) for item in db.scalars(select(OutputTemplateConfig).order_by(OutputTemplateConfig.name)).all()]}


@router.get("/admin/template-assets")
def admin_template_assets(user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    return {"assets": list_template_assets()}


@router.get("/admin/templates/{template_id}")
def admin_template_detail(template_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    template = db.get(OutputTemplateConfig, template_id)
    if not template:
        raise AppError("Template not found.", 404)
    return {"template": serialize_template(template)}


@router.post("/admin/templates/{template_id}/copy")
def admin_template_copy(template_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    template = copy_template(db, user, template_id)
    return {"template": serialize_template(template)}


@router.patch("/admin/templates/{template_id}")
def admin_template_update(template_id: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    template = update_template(db, user, template_id, payload)
    return {"template": serialize_template(template)}


@router.post("/admin/templates")
def admin_template_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    template = upsert_template(db, user, payload)
    return {"template": serialize_template(template)}


@router.get("/template-assets/{asset_id}")
def template_asset_file(
    asset_id: str,
    user: User = Depends(current_user),
) -> FileResponse:
    if not user or user.role not in {Role.ADMIN.value, Role.MANAGER.value}:
        raise AppError("File not found.", 404)
    try:
        path = resolve_template_asset(asset_id)
    except FileNotFoundError:
        raise AppError("File not found.", 404) from None
    return FileResponse(path)


@router.get("/admin/benefits")
def admin_benefits(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    return {"benefits": [{"id": item.id, "label": item.label, "section": item.section, "default_selected": item.default_selected, "status": item.status} for item in db.scalars(select(BenefitOption)).all()]}


@router.post("/admin/benefits")
def admin_benefit_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    benefit = upsert_benefit(db, user, payload)
    return {"benefit": {"id": benefit.id, "label": benefit.label, "section": benefit.section, "status": benefit.status}}


@router.get("/admin/dictionaries")
def admin_dictionaries(db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN, Role.MANAGER)
    return {
        "field_aliases": [{"id": item.id, "field_name": item.field_name, "aliases": item.aliases} for item in db.scalars(select(FieldAlias)).all()],
        "vehicle_brands": [{"id": item.id, "name": item.name, "aliases": item.aliases} for item in db.scalars(select(VehicleBrand)).all()],
        "vehicle_models": [{"id": item.id, "brand_id": item.brand_id, "name": item.name, "aliases": item.aliases} for item in db.scalars(select(VehicleModel)).all()],
    }


@router.post("/admin/dictionaries/field-aliases")
def admin_field_alias_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    item = upsert_field_alias(db, user, payload)
    return {"field_alias": {"id": item.id, "field_name": item.field_name, "aliases": item.aliases}}


@router.post("/admin/dictionaries/vehicle-brands")
def admin_vehicle_brand_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    item = upsert_vehicle_brand(db, user, payload)
    return {"vehicle_brand": {"id": item.id, "name": item.name, "aliases": item.aliases}}


@router.post("/admin/dictionaries/vehicle-models")
def admin_vehicle_model_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    item = upsert_vehicle_model(db, user, payload)
    return {"vehicle_model": {"id": item.id, "name": item.name, "aliases": item.aliases}}


@router.post("/admin/extraction-settings")
def admin_extraction_settings_save(payload: dict, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    setting = save_strategy_settings(db, user, payload)
    return {"setting": {"key": setting.key, "value": setting.value}}


@router.get("/admin/storage")
def admin_storage_status(
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    user: User = Depends(current_user),
) -> dict:
    require_role(user, Role.ADMIN)
    storage_ready, storage_message = SupabaseStorage(settings).check()
    source_bytes = db.scalar(
        select(func.coalesce(func.sum(UploadedFile.size_bytes), 0)).where(
            UploadedFile.storage_provider == "supabase",
            UploadedFile.storage_status.in_([StorageStatus.AVAILABLE.value, StorageStatus.ARCHIVE_PENDING.value, StorageStatus.ARCHIVE_FAILED.value]),
        )
    )
    connections = list(db.scalars(select(StorageConnection).order_by(StorageConnection.created_at.desc())).all())
    return {
        "supabase": {
            "status": "Ready" if storage_ready else "Needs Setup",
            "message": storage_message,
            "bucket": settings.supabase_storage_bucket,
            "retention_days": settings.pdf_retention_days,
            "tracked_source_bytes": int(source_bytes or 0),
        },
        "microsoft": {
            "status": "Not Connected",
            "message": "SharePoint/OneDrive permanent archive is optional and can be connected later.",
            "connections": [
                {
                    "id": item.id,
                    "name": item.display_name,
                    "status": item.status,
                    "site_id": item.site_id,
                    "drive_id": item.drive_id,
                    "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else None,
                }
                for item in connections
            ],
        },
    }


@router.post("/admin/storage/purge-expired")
def admin_storage_purge(
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    user: User = Depends(current_user),
) -> dict:
    require_role(user, Role.ADMIN)
    return purge_expired_pdfs(db, SupabaseStorage(settings))


@router.post("/admin/storage/microsoft/connect")
def admin_storage_microsoft_connect(user: User = Depends(current_user)) -> dict:
    require_role(user, Role.ADMIN)
    raise AppError("Microsoft 365 archive requires Entra application credentials before it can be connected.", 503)


@router.get("/uploaded-files/{uploaded_file_id}/content")
def uploaded_file_content(
    uploaded_file_id: str,
    download: bool = Query(default=False),
    range_header: str | None = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    user: User = Depends(current_user),
) -> Response:
    uploaded = db.get(UploadedFile, uploaded_file_id)
    if not uploaded or not can_view_owner_record(db, user, uploaded.owner_id):
        raise AppError("File not found.", 404)
    return _pdf_response(load_pdf_bytes(uploaded, settings), uploaded.original_filename, range_header, download)


@router.get("/generated-versions/{version_id}/content")
def generated_version_content(
    version_id: str,
    download: bool = Query(default=False),
    range_header: str | None = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    user: User = Depends(current_user),
) -> Response:
    version = db.scalar(select(GeneratedPdfVersion).where(GeneratedPdfVersion.id == version_id).options(selectinload(GeneratedPdfVersion.draft)))
    if not version or not version.draft or not can_view_owner_record(db, user, version.draft.owner_id):
        raise AppError("File not found.", 404)
    return _pdf_response(load_pdf_bytes(version, settings), version.filename, range_header, download)
