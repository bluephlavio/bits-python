import configparser
import os
import shutil
from configparser import ExtendedInterpolation
from pathlib import Path
from typing import Any, Dict

try:  # Python 3.11+
    import tomllib as _toml_impl  # type: ignore
except Exception:  # pragma: no cover - fallback to tomli if present
    try:
        import tomli as _toml_impl  # type: ignore
    except Exception:  # pragma: no cover - optional
        _toml_impl = None

GLOBAL_BITS_CONFIG_DIR = Path("~/.bits").expanduser()
GLOBAL_BITS_CONFIG_FILE = GLOBAL_BITS_CONFIG_DIR / "config.ini"
GLOBAL_BITS_CONFIG_TOML_FILE = GLOBAL_BITS_CONFIG_DIR / "config.toml"
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

def _to_string(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        # Represent arrays as newline-separated values so downstream splitters work
        return "\n".join(_to_string(v) for v in val)
    return str(val)


def _flatten_sections(data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    def visit(obj: Dict[str, Any], prefix: str) -> None:
        scalars: Dict[str, str] = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                visit(v, f"{prefix}.{k}" if prefix else k)
            else:
                scalars[k] = _to_string(v)
        if scalars:
            sect = prefix or "DEFAULT"
            if sect not in result:
                result[sect] = {}
            result[sect].update(scalars)

    for k, v in data.items():
        if isinstance(v, dict):
            visit(v, k)
        else:
            result.setdefault("DEFAULT", {})[k] = _to_string(v)
    return result


def _merge_sections_into_config(sections: Dict[str, Dict[str, str]]) -> None:
    for section, values in sections.items():
        if section != "DEFAULT" and not config.has_section(section):
            config.add_section(section)
        for key, value in values.items():
            config.set(section, key, value)


def _load_toml_file(path: Path) -> None:
    try:
        src = path.read_bytes()
        data: Dict[str, Any]
        if _toml_impl is not None:
            # tomllib/tomli returns a nested dict structure
            data = _toml_impl.loads(src.decode("utf-8"))
        else:  # pragma: no cover - minimal fallback parser for simple cases
            data = _minimal_toml_parse(src.decode("utf-8"))
        sections = _flatten_sections(data)
        _merge_sections_into_config(sections)
    except Exception:  # pragma: no cover - be forgiving in environments
        pass


def _minimal_toml_parse(text: str) -> Dict[str, Any]:  # pragma: no cover
    """Very small TOML subset parser.

    Supports:
    - [section] and dotted [a.b] sections
    - key = "string" | true/false | ["a", "b"] | numbers
    - # comments
    This is used only when tomllib/tomli is unavailable.
    """
    import re

    def strip_comment(s: str) -> str:
        out = []
        in_str = False
        quote = ""
        i = 0
        while i < len(s):
            ch = s[i]
            if ch in ('"', "'"):
                if not in_str:
                    in_str = True
                    quote = ch
                elif quote == ch:
                    in_str = False
            if ch == "#" and not in_str:
                break
            out.append(ch)
            i += 1
        return "".join(out).rstrip()

    def parse_value(v: str):
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            items = []
            cur = []
            in_str = False
            quote = ""
            for ch in inner:
                if ch in ('"', "'"):
                    if not in_str:
                        in_str = True
                        quote = ch
                    elif quote == ch:
                        in_str = False
                if ch == "," and not in_str:
                    item = "".join(cur).strip()
                    if item:
                        items.append(parse_value(item))
                    cur = []
                else:
                    cur.append(ch)
            last = "".join(cur).strip()
            if last:
                items.append(parse_value(last))
            return items
        if v.lower() in ("true", "false"):
            return v.lower() == "true"
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        # number fallback or bare string
        try:
            if "." in v:
                return float(v)
            return int(v)
        except Exception:
            return v

    data: Dict[str, Any] = {}
    cur: Dict[str, Any] = data
    cur_path = []
    for raw in text.splitlines():
        line = strip_comment(raw).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            sect = line[1:-1].strip()
            parts = sect.split(".") if sect else []
            node = data
            for p in parts:
                node = node.setdefault(p, {})
            cur = node
            cur_path = parts
            continue
        m = re.match(r"([A-Za-z0-9_.\-]+)\s*=\s*(.+)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        cur[key] = parse_value(val)
    return data


def load_config_file(path: Path) -> None:
    """Merge a config file (INI or TOML) into the global config object."""
    try:
        suffix = path.suffix.lower()
        if suffix in (".toml", ".tml"):
            _load_toml_file(path)
        else:
            parser = configparser.ConfigParser(interpolation=ExtendedInterpolation())
            parser.read(path)
            for section in parser.sections():
                if not config.has_section(section):
                    config.add_section(section)
                for key, value in parser.items(section):
                    config.set(section, key, value)
    except Exception:  # pragma: no cover
        pass


# Load global config if present (INI then TOML, TOML wins)
try:
    if GLOBAL_BITS_CONFIG_FILE.exists():
        load_config_file(GLOBAL_BITS_CONFIG_FILE)
    if GLOBAL_BITS_CONFIG_TOML_FILE.exists():
        load_config_file(GLOBAL_BITS_CONFIG_TOML_FILE)
except Exception:  # pragma: no cover
    pass

# Load config from env override (highest precedence)
ENV_CONFIG_FILE = os.environ.get("BITS_CONFIG")
if ENV_CONFIG_FILE:
    try:
        load_config_file(Path(ENV_CONFIG_FILE))
    except Exception:  # pragma: no cover
        pass

# Merge local project config (.bitsrc) if present
LOCAL_BITS_CONFIG_TOML = Path(".bits.toml")
LOCAL_BITS_CONFIG_FILE = Path(".bitsrc")
try:
    if LOCAL_BITS_CONFIG_TOML.exists():
        load_config_file(LOCAL_BITS_CONFIG_TOML)
    if LOCAL_BITS_CONFIG_FILE.exists():
        load_config_file(LOCAL_BITS_CONFIG_FILE)
except Exception:  # pragma: no cover
    pass
