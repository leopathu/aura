from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Report, User
from app.schemas.domain import ReportResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission

router = APIRouter(prefix="/reports", tags=["Reports & Artifacts"])

@router.get("", response_model=List[ReportResponse])
async def list_reports(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Report).where(Report.organization_id == org_id).order_by(Report.created_at.desc())
    )
    reports = res.scalars().all()
    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            summary=r.summary,
            content_markdown=r.content_markdown,
            data_sources=r.data_sources_json or [],
            created_at=r.created_at
        )
        for r in reports
    ]

@router.get("/{id}")
async def get_report(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Report).where(Report.id == id, Report.organization_id == org_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report.id,
        "title": report.title,
        "summary": report.summary,
        "content_markdown": report.content_markdown,
        "data_sources": report.data_sources_json or [],
        "query_references": report.query_references_json or [],
        "chart_configs": report.chart_configs_json or [],
        "created_at": report.created_at.isoformat()
    }

@router.get("/{id}/export")
async def export_report(
    id: str,
    format: str = "md",
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Report).where(Report.id == id, Report.organization_id == org_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format.lower() == "json":
        import json
        data = {
            "title": report.title,
            "summary": report.summary,
            "content": report.content_markdown,
            "data_sources": report.data_sources_json,
            "created_at": report.created_at.isoformat()
        }
        return Response(content=json.dumps(data, indent=2), media_type="application/json")
    else:
        # Default Markdown
        content = f"# {report.title}\n\n"
        if report.summary:
            content += f"> {report.summary}\n\n"
        content += report.content_markdown
        return Response(content=content, media_type="text/markdown")
