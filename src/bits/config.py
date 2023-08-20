import configparser
import shutil
from pathlib import Path

BITS_CONFIG_DIR = Path("~/.bits").expanduser()
BITS_CONFIG_FILE = BITS_CONFIG_DIR / "config.ini"
BITS_TEMPLATES_DIR = BITS_CONFIG_DIR / "templates"

BITS_CONFIG_DIR_SRC = Path(__file__).parent / "config"

if not BITS_CONFIG_DIR.exists():
    Path.mkdir(BITS_CONFIG_DIR, parents=True)

shutil.copytree(BITS_CONFIG_DIR_SRC, BITS_CONFIG_DIR, dirs_exist_ok=True)

config = configparser.ConfigParser()

config.read(BITS_CONFIG_FILE)
