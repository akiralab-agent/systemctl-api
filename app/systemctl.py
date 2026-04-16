import re
import subprocess

from fastapi import HTTPException, status

from app.schemas import ServiceUnit


ALLOWED_ACTIONS = {
    "start",
    "stop",
    "restart",
    "reload",
    "enable",
    "disable",
    "status",
}

SERVICE_NAME_RE = re.compile(r"^[A-Za-z0-9_.@:-]+(?:\.service)?$")


def list_running_services() -> list[ServiceUnit]:
    result = _run_systemctl(
        [
            "list-units",
            "--type=service",
            "--state=running",
            "--no-pager",
            "--plain",
            "--all",
        ]
    )

    services: list[ServiceUnit] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("UNIT ") or line.startswith("LOAD "):
            continue
        if line.startswith("0 loaded units listed"):
            continue

        parts = line.split(None, 4)
        if len(parts) < 5:
            continue

        services.append(
            ServiceUnit(
                unit=parts[0],
                load=parts[1],
                active=parts[2],
                sub=parts[3],
                description=parts[4],
            )
        )

    return services


def run_service_action(action: str, service: str) -> subprocess.CompletedProcess[str]:
    normalized_action = action.lower().strip()
    normalized_service = service.strip()

    if normalized_action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Allowed actions: {', '.join(sorted(ALLOWED_ACTIONS))}",
        )

    if not SERVICE_NAME_RE.fullmatch(normalized_service):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service name",
        )

    if not normalized_service.endswith(".service"):
        normalized_service = f"{normalized_service}.service"

    result = _run_systemctl([normalized_action, normalized_service], check=False)
    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "systemctl command failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

    return result


def _run_systemctl(
    args: list[str],
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["systemctl", *args],
            capture_output=True,
            check=check,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="systemctl is not available on this server",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "systemctl command failed",
                "returncode": exc.returncode,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="systemctl command timed out",
        ) from exc

    return result
