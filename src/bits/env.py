# pylint: disable=too-few-public-methods
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import importlib.util
import warnings

from jinja2 import Environment, FileSystemLoader
from .config import config


class EnvironmentFactory:
    _env_cache: Dict[str, Environment] = {}
    _plugins_enabled: bool = True

    @classmethod
    def enable_plugins(cls, enabled: bool) -> None:
        cls._plugins_enabled = enabled

    @classmethod
    def _get_path_list(cls, option: str) -> List[Path]:
        paths: List[Path] = []
        if not config.has_section("jinja"):
            return paths
        try:
            raw = config.get("jinja", option, fallback=None)
        except Exception:
            raw = None
        if not raw:
            return paths

        # Accept simple comma or newline separated list, or a Python/TOML-like array
        candidates: List[str] = []
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            # Try to parse simple list literal
            try:
                import ast

                val = ast.literal_eval(s)
                if isinstance(val, list):
                    candidates = [str(x) for x in val]
            except Exception:
                # Fallback to splitting by comma
                candidates = [x.strip() for x in s[1:-1].split(",") if x.strip()]
        else:
            # Split by newlines and commas
            parts: List[str] = []
            for line in s.splitlines():
                parts.extend([p.strip() for p in line.split(",")])
            candidates = [p for p in parts if p]

        for c in candidates:
            try:
                p = Path(c).expanduser()
                paths.append(p)
            except Exception:
                continue
        return paths

    @classmethod
    def _get_plugins_list(cls) -> List[Path]:
        return cls._get_path_list("plugins")

    @classmethod
    def _get_filter_files_list(cls) -> List[Path]:
        return cls._get_path_list("filter_files")

    @classmethod
    def _get_macro_files_list(cls) -> List[Path]:
        return cls._get_path_list("macro_files")

    @classmethod
    def _load_plugins(cls, env: Environment) -> None:
        if not cls._plugins_enabled:
            return
        plugins = cls._get_plugins_list()
        for path in plugins:
            try:
                if not path.exists():
                    warnings.warn(f"Jinja plugin not found: {path}")
                    continue
                spec = importlib.util.spec_from_file_location(path.stem, path)
                if spec is None or spec.loader is None:
                    warnings.warn(f"Unable to import plugin: {path}")
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[attr-defined]
                if hasattr(module, "register"):
                    try:
                        module.register(env)
                    except Exception as err:  # pragma: no cover - plugin code
                        warnings.warn(f"Error in plugin register(): {path}: {err}")
                else:
                    warnings.warn(f"Plugin missing register(env): {path}")
            except Exception as err:  # pragma: no cover
                warnings.warn(f"Failed to load plugin {path}: {err}")

    @classmethod
    def _load_auto_filters(cls, env: Environment) -> None:
        """Auto-register filters from simple Python modules declared via
        [jinja] filter_files in config.

        All top-level callables in each module are registered as filters,
        excluding private names (starting with '_') and a function named
        'register'.
        """
        if not cls._plugins_enabled:
            return
        files = cls._get_filter_files_list()
        for path in files:
            try:
                if not path.exists():
                    warnings.warn(f"Jinja filter file not found: {path}")
                    continue
                spec = importlib.util.spec_from_file_location(path.stem, path)
                if spec is None or spec.loader is None:
                    warnings.warn(f"Unable to import filter file: {path}")
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[attr-defined]
                for name in dir(module):
                    if name.startswith("_") or name == "register":
                        continue
                    func = getattr(module, name)
                    if callable(func) and getattr(func, "__module__", None) == module.__name__:
                        # Heuristic: treat functions ending in "_filter" as
                        # providing the implementation for a shorter filter
                        # name without the suffix (e.g. "floor_filter" ->
                        # "floor"), matching common patterns in existing
                        # plugins.
                        if name.endswith("_filter"):
                            filter_name = name[: -len("_filter")]
                        else:
                            filter_name = name
                        env.filters[filter_name] = func
            except Exception as err:  # pragma: no cover
                warnings.warn(f"Failed to load filters from {path}: {err}")

    @classmethod
    def _load_auto_macros(cls, env: Environment) -> None:
        """Auto-register Jinja macros from templates declared via
        [jinja] macro_files in config.

        Each macro file is compiled in this environment and all exported
        callables are registered as globals.
        """
        if not cls._plugins_enabled:
            return
        files = cls._get_macro_files_list()
        for path in files:
            try:
                if not path.exists():
                    warnings.warn(f"Jinja macro file not found: {path}")
                    continue
                text = path.read_text(encoding="utf-8")
                tpl = env.from_string(text)
                module = tpl.module
                for name in dir(module):
                    if name.startswith("_"):
                        continue
                    obj = getattr(module, name)
                    if callable(obj):
                        env.globals[name] = obj
            except Exception as err:  # pragma: no cover
                warnings.warn(f"Failed to load macros from {path}: {err}")

    @classmethod
    def get(cls, templates_folder: Path | None = None) -> Environment:
        # Build a cache key that incorporates templates folder and plugin settings
        if templates_folder is None:
            base_key = "string"
        else:
            base_key = str(templates_folder)

        # Hash plugin/macro/filter list for cache segregation
        try:
            plugin_list = (
                [str(p) for p in cls._get_plugins_list()]
                if cls._plugins_enabled
                else []
            )
            filter_list = (
                [str(p) for p in cls._get_filter_files_list()]
                if cls._plugins_enabled
                else []
            )
            macro_list = (
                [str(p) for p in cls._get_macro_files_list()]
                if cls._plugins_enabled
                else []
            )
            plugin_key = f"plugins:{int(cls._plugins_enabled)}|{','.join(plugin_list)}"
            extras_key = f"filters:{','.join(filter_list)}|macros:{','.join(macro_list)}"
        except Exception:
            plugin_key = f"plugins:{int(cls._plugins_enabled)}"
            extras_key = ""

        env_key = base_key + "|" + plugin_key + "|" + extras_key

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

        # Load user plugins last; allow overrides with warning emitted by plugin if desired
        cls._load_plugins(env)
        cls._load_auto_filters(env)
        cls._load_auto_macros(env)

        cls._env_cache[env_key] = env
        return env
