import sys
import toml
from supervisorio.core.logger import get_logger
from supervisorio.config.settings import CONFIG_PATH
from supervisorio.infrastructure.CW import CheckWeigher

logger = get_logger(__name__)


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}  # type: ignore

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Settings(metaclass=SingletonMeta):
    def __init__(self):
        config_path = CONFIG_PATH / "settings.toml"

        if not config_path.exists():
            logger.error(
                f"ERRO: Arquivo de configuração não encontrado em: {config_path}")
            sys.exit(1)

        self._data = toml.load(config_path)
        self.cws = []

        self.__install_checkeweighers()

    def get_cw_by_name(self, cw_name):
        target = None
        for cw in self.cws:
            if cw.name == cw_name:
                target = cw
                break

        return target

    def __install_checkeweighers(self):
        cws_config = self._data["observer"]["checkweighers"]
        self.cws = [CheckWeigher(cw_id=args['cw_id'],
                                 name=args['name'],
                                 ip_address=args['ip_address'],
                                 port=args['port'],
                                 enabled=args['enabled'],
                                 pool_interval=args.get('pool_interval', None),
                                 timeout=args.get('timeout', None)
                                 )
                    for args in cws_config]

        logger.info(f'Instalado {len(self.cws)} CheckWeighers')

    def __getitem__(self, name: str):
        return self._data[name]


settings = Settings()
