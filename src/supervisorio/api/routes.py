import time
from supervisorio.core.monitor import monitor
from fastapi import APIRouter
from fastapi import APIRouter, Query
from datetime import date
from supervisorio.infrastructure.database.repositories import PesagemRepository, EventRepository
from supervisorio.utils.date import range_date
from datetime import datetime
from supervisorio.core.config import settings


router = APIRouter()


@router.get("/pesagens")
async def listar_pesagens(
    maquina_id: str = Query(None, description="ID da máquina"),
    data: date = Query(None, description="Data da pesagem (YYYY-MM-DD)"),
    classificacao: int = Query(None, description="Código da classificação"),
    limit: int = Query(20, description='Total de pesagens buscadas'),
    period: date = Query(
        None, description="Define o dia central de um período de busca"),
    periodOffset: int = Query(
        15, description="Define o offset do período de busca")
):
    """Busca pesagens com filtros opcionais"""

    _period: None | tuple[date, date] = None
    if period:
        _period = range_date(period, periodOffset)

    return await PesagemRepository.find(
        maquina_id=maquina_id,
        timestamp=data,
        classificacao=classificacao,
        limit=limit,
        periodo=_period
    )


@router.get('/eventos')
async def listar_eventos(
    maquina_id: str = Query(None, description="ID da máquina"),
    reason: int = Query(None, description="Código da classificação"),
    limit: int = Query(20, description='Total de pesagens buscadas'),
    period: date = Query(
        None, description="Define o dia central de um período de busca"),
    periodOffset: int = Query(
        15, description="Define o offset do período de busca")
):
    _period: None | tuple[date, date] = None
    if period:
        _period = range_date(period, periodOffset)

    return await EventRepository.find(
        maquina_id=maquina_id,
        reason=reason,
        periodo=_period,
        limit=limit,
    )


@router.get("/health")
async def health_check():
    return {"status": "online", "message": "Coletor e API operando"}


@router.get('/realtime/{cw_name}')
async def realtime(cw_name: str):
    target = settings.get_cw_by_name(cw_name)
    return target.payload if target is not None else None


@router.get("/hhh")
async def get_system_health():
    health_report = {}
    current_time = time.time()

    for name, info in monitor.components.items():  # type: ignore
        # Se não houver sinal de vida por mais de 30 segundos, marca como instável
        is_stale = (current_time - info.last_heartbeat) > 30

        health_report[name] = {
            "status": "warning" if is_stale and info.status == "online" else info.status,
            "buffer_usage": info.buffer_usage,
            "total_processed": info.total_processed,
            "errors": info.error_count,
            "uptime_relativo": f"{int(current_time - info.last_heartbeat)}s atrás"
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "services": health_report,
        "overall_status": "ok" if all(s["status"] == "online" for s in health_report.values()) else "critical"
    }
