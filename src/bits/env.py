# pylint: disable=too-few-public-methods
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader

from .filters import *  # pylint: disable=wildcard-import


class EnvironmentFactory:
    _env_cache: Dict[str, Environment] = {}

    @classmethod
    def get(cls, templates_folder: Path | None = None) -> Environment:
        if templates_folder is None:
            env_key = "string"
        else:
            env_key = str(templates_folder)

        if env_key in cls._env_cache:
            return cls._env_cache[env_key]

        if templates_folder is None:
            loader = None
        else:
            loader = FileSystemLoader(str(templates_folder))

        env = Environment(
            loader=loader,
            block_start_string=r"\BLOCK{",
            block_end_string=r"}",
            variable_start_string=r"\VAR{",
            variable_end_string=r"}",
            comment_start_string=r"\#{",
            comment_end_string=r"}",
            line_statement_prefix=r"%%",
            line_comment_prefix=r"%#",
            trim_blocks=True,
            autoescape=False,
        )

        env.filters["floor"] = floor_filter
        env.filters["ceil"] = ceil_filter
        env.filters["getitem"] = getitem_filter
        env.filters["pick"] = pick_filter
        env.filters["render"] = render_filter
        env.filters["enumerate"] = enumerate_filter
        env.filters["show"] = show_filter

        cls._env_cache[env_key] = env
        return env
