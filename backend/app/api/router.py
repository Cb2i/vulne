from fastapi import APIRouter

from app.api.routes import (
    assets,
    auth,
    decommission,
    exceptions,
    exports,
    findings,
    kpi,
    remediation,
    rules,
    scans,
    teams,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(teams.router)
api_router.include_router(scans.router)
api_router.include_router(findings.router)
api_router.include_router(assets.router)
api_router.include_router(rules.router)
api_router.include_router(exceptions.router)
api_router.include_router(decommission.router)
api_router.include_router(remediation.router)
api_router.include_router(kpi.router)
api_router.include_router(exports.router)
