import configparser
import os
import shutil
from configparser import ExtendedInterpolation
from pathlib import Path

GLOBAL_BITS_CONFIG_DIR = Path("~/.bits").expanduser()
GLOBAL_BITS_CONFIG_FILE = GLOBAL_BITS_CONFIG_DIR / "config.ini"
GLOBAL_BITS_TEMPLATES_DIR = GLOBAL_BITS_CONFIG_DIR / "templates"

GLOBAL_BITS_CONFIG_DIR_SRC = Path(__file__).parent / "config"

# Best-effort: avoid crashing if home directory is not writable (e.g., in CI)
try:
    if not GLOBAL_BITS_CONFIG_DIR.exists():
        Path.mkdir(GLOBAL_BITS_CONFIG_DIR, parents=True, exist_ok=True)
    shutil.copytree(
        GLOBAL_BITS_CONFIG_DIR_SRC, GLOBAL_BITS_CONFIG_DIR, dirs_exist_ok=True
    )
except Exception:  # pragma: no cover - environment dependent
    # Fallback: continue without global defaults; local .bitsrc may provide paths
    pass

config = configparser.ConfigParser(interpolation=ExtendedInterpolation())

# Load global config if present
try:
    if GLOBAL_BITS_CONFIG_FILE.exists():
        config.read(GLOBAL_BITS_CONFIG_FILE)
except Exception:  # pragma: no cover
    pass

# Load config from env override (highest precedence)
ENV_CONFIG_FILE = os.environ.get("BITS_CONFIG")
if ENV_CONFIG_FILE:
    try:
        env_config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
        env_config.read(ENV_CONFIG_FILE)
        for section in env_config.sections():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in env_config.items(section):
                config.set(section, key, value)
    except Exception:  # pragma: no cover
        pass

# Merge local project config (.bitsrc) if present
LOCAL_BITS_CONFIG_FILE = Path(".bitsrc")
if LOCAL_BITS_CONFIG_FILE.exists():
    try:
        local_config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
        local_config.read(LOCAL_BITS_CONFIG_FILE)

        for section in local_config.sections():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in local_config.items(section):
                config.set(section, key, value)
    except Exception:  # pragma: no cover
        pass
