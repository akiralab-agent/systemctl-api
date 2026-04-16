from pydantic import BaseModel, Field


class ServiceUnit(BaseModel):
    unit: str
    load: str
    active: str
    sub: str
    description: str


class ServiceListResponse(BaseModel):
    services: list[ServiceUnit]


class ServiceCommandRequest(BaseModel):
    action: str = Field(
        examples=["restart"],
        description="Systemctl action to run.",
    )
    service: str = Field(
        examples=["django"],
        description="Service name. The .service suffix is optional.",
    )


class ServiceCommandResponse(BaseModel):
    action: str
    service: str
    returncode: int
    stdout: str
    stderr: str
