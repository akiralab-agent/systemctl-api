from fastapi import Depends, FastAPI

from app.auth import verify_authorization
from app.schemas import (
    ServiceCommandRequest,
    ServiceCommandResponse,
    ServiceListResponse,
)
from app.systemctl import list_services, run_service_action


app = FastAPI(
    title="Systemctl API",
    description="API para listar e gerenciar services do systemd via systemctl.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/services",
    response_model=ServiceListResponse,
    dependencies=[Depends(verify_authorization)],
)
def get_services() -> ServiceListResponse:
    return ServiceListResponse(services=list_services())


@app.post(
    "/services/command",
    response_model=ServiceCommandResponse,
    dependencies=[Depends(verify_authorization)],
)
def execute_service_command(
    payload: ServiceCommandRequest,
) -> ServiceCommandResponse:
    result = run_service_action(payload.action, payload.service)
    service = payload.service.strip()
    if not service.endswith(".service"):
        service = f"{service}.service"

    return ServiceCommandResponse(
        action=payload.action.lower().strip(),
        service=service,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
