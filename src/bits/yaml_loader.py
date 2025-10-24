import re
from pathlib import Path

import yaml

from .config import config

var_pattern = re.compile(r"\$\{([^}]+)\}")

yaml.add_implicit_resolver("!var", var_pattern)


def interpolated_var_constructor(loader, node):
    value = loader.construct_scalar(node)

    def replace_var(match):
        variable_name = match.group(1)
        if config.has_option("variables", variable_name):
            val = config.get("variables", variable_name)
            # Treat [variables] entries as paths by default; resolve relative to CWD
            try:
                p = Path(val)
                if not p.is_absolute():
                    return str((Path.cwd() / p).resolve())
                return str(p)
            except Exception:
                return val
        return match.group(0)

    return var_pattern.sub(replace_var, value)


yaml.add_constructor("!var", interpolated_var_constructor)


def load_yaml(src: str) -> dict:
    return yaml.load(src, Loader=yaml.FullLoader)
