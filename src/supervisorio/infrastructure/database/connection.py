from supervisorio.core.logger import get_logger
import asyncpg
from supervisorio.core.config import settings


logger = get_logger(__name__)
DATABASE_URL = settings['global']['DATABASE_URL']

if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL deve ser definida.")


# Variável global para armazenar o pool (Singleton)
_pool = None


async def get_pool():
    """
    Cria ou retorna um pool de conexões existente.
    """
    global _pool

    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                # Configurações de performance:
                min_size=5,       # Mantém 5 conexões sempre prontas
                max_size=20,      # Expande até 20 sob carga alta
                # Reinicia a conexão após 1000 usos (evita leak de memória)
                max_queries=1000,
                timeout=30.0,     # Timeout para aquisição de conexão
                command_timeout=60.0
            )
            logger.info("Pool de conexões PostgreSQL estabelecido.")
        except Exception as e:
            logger.error(f"Falha ao criar o pool de conexões: {e}")
            raise

    return _pool


async def close_pool():
    """Fecha o pool corretamente ao encerrar a aplicação."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Pool de conexões PostgreSQL encerrado.")
