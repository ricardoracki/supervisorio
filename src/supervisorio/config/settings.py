import sys
import pathlib

# Detecta se o código está rodando dentro de um executável (.exe)
if getattr(sys, 'frozen', False):
    ROOT_PATH = pathlib.Path(sys.executable).parent
else:
    ROOT_PATH = pathlib.Path(__file__).parent.parent.parent.parent

CONFIG_PATH = ROOT_PATH / "config"
DATA_PATH = ROOT_PATH / "data"
LOG_PATH = DATA_PATH / "logs"

# Garante que as pastas de dados e logs existam
LOG_PATH.mkdir(parents=True, exist_ok=True)
