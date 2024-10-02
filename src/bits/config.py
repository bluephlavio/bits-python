import configparser
from configparser import ExtendedInterpolation
import shutil
from pathlib import Path

GLOBAL_BITS_CONFIG_DIR = Path("~/.bits").expanduser()
GLOBAL_BITS_CONFIG_FILE = GLOBAL_BITS_CONFIG_DIR / "config.ini"
GLOBAL_BITS_TEMPLATES_DIR = GLOBAL_BITS_CONFIG_DIR / "templates"

GLOBAL_BITS_CONFIG_DIR_SRC = Path(__file__).parent / "config"

if not GLOBAL_BITS_CONFIG_DIR.exists():
    Path.mkdir(GLOBAL_BITS_CONFIG_DIR, parents=True)

shutil.copytree(GLOBAL_BITS_CONFIG_DIR_SRC, GLOBAL_BITS_CONFIG_DIR, dirs_exist_ok=True)

config = configparser.ConfigParser(interpolation=ExtendedInterpolation())

config.read(GLOBAL_BITS_CONFIG_FILE)

print('config', config)

LOCAL_BITS_CONFIG_FILE = Path(".bitsrc")

print('local_config_file', LOCAL_BITS_CONFIG_FILE)

if LOCAL_BITS_CONFIG_FILE.exists():
    local_config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
    local_config.read(LOCAL_BITS_CONFIG_FILE)

    print('local_config', local_config)

    for section in local_config.sections():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in local_config.items(section):
            config.set(section, key, value)

    print('config', config)
