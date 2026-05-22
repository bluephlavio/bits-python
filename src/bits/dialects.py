from __future__ import annotations

import hashlib
import importlib.util
import inspect
import re
from pathlib import Path
from typing import Callable, Dict, Tuple

from .config import config
from .exceptions import DialectError

Transform = Callable[..., str]


class DialectRegistry:
    _cache: Dict[Tuple[str, str, str, int | None], Transform] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    @classmethod
    def resolve(cls, name: str) -> Transform:
        if not config.has_section("dialects") or not config.has_option(
            "dialects", name
        ):
            raise DialectError(
                f"Unknown dialect '{name}'. Configure it under [dialects] "
                "in .bitsrc/.bits.toml.",
                dialect=name,
            )

        target = config.get("dialects", name)
        module_path, function_name = cls._parse_target(name, target)
        mtime_ns = cls._module_mtime(module_path, name)
        cache_key = (name, module_path.as_posix(), function_name, mtime_ns)

        if cache_key in cls._cache:
            return cls._cache[cache_key]

        module = cls._load_module(name, module_path)
        try:
            transform = getattr(module, function_name)
        except AttributeError as err:
            raise DialectError(
                f"Dialect callable '{function_name}' was not found in {module_path}.",
                dialect=name,
                source_path=module_path.as_posix(),
                cause=err,
            ) from err

        if not callable(transform):
            raise DialectError(
                f"Dialect target '{function_name}' in {module_path} is not callable.",
                dialect=name,
                source_path=module_path.as_posix(),
            )

        cls._cache[cache_key] = transform
        return transform

    @classmethod
    def transform(
        cls,
        name: str,
        source: str,
        *,
        context: dict | None = None,
        path: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        transform = cls.resolve(name)
        try:
            result = cls._call_transform(
                transform,
                source,
                context=context,
                path=path,
                metadata=metadata,
            )
        except DialectError:
            raise
        except Exception as err:
            raise DialectError(
                f"Dialect transform failed: {err}",
                dialect=name,
                source_path=path,
                cause=err,
            ) from err

        if not isinstance(result, str):
            raise DialectError(
                "Dialect transform must return a string.",
                dialect=name,
                source_path=path,
            )
        return result

    @staticmethod
    def _parse_target(name: str, target: str) -> tuple[Path, str]:
        target = target.strip()
        if len(target) >= 2 and target[0] == target[-1] and target[0] in ("'", '"'):
            target = target[1:-1]

        if ":" not in target:
            raise DialectError(
                "Dialect config value must use '/path/to/module.py:function'.",
                dialect=name,
            )
        module_path_raw, function_name = target.rsplit(":", 1)
        module_path = Path(module_path_raw).expanduser()
        function_name = function_name.strip()

        if not module_path_raw.strip() or not function_name:
            raise DialectError(
                "Dialect config value must use '/path/to/module.py:function'.",
                dialect=name,
            )
        return module_path, function_name

    @staticmethod
    def _module_mtime(module_path: Path, name: str) -> int | None:
        try:
            return module_path.stat().st_mtime_ns
        except FileNotFoundError as err:
            raise DialectError(
                f"Dialect module not found: {module_path}",
                dialect=name,
                source_path=module_path.as_posix(),
                cause=err,
            ) from err
        except OSError:
            return None

    @staticmethod
    def _load_module(name: str, module_path: Path):
        module_id = hashlib.sha1(module_path.as_posix().encode("utf-8")).hexdigest()
        safe_name = re.sub(r"[^0-9A-Za-z_]", "_", name)
        module_name = f"bits_dialect_{safe_name}_{module_id}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise DialectError(
                f"Unable to import dialect module: {module_path}",
                dialect=name,
                source_path=module_path.as_posix(),
            )

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
        except DialectError:
            raise
        except Exception as err:
            raise DialectError(
                f"Unable to import dialect module: {err}",
                dialect=name,
                source_path=module_path.as_posix(),
                cause=err,
            ) from err
        return module

    @staticmethod
    def _call_transform(
        transform: Transform,
        source: str,
        *,
        context: dict | None,
        path: str | None,
        metadata: dict | None,
    ) -> str:
        kwargs = {
            "context": context,
            "path": path,
            "metadata": metadata,
        }

        try:
            signature = inspect.signature(transform)
        except (TypeError, ValueError):
            return transform(source, **kwargs)

        params = signature.parameters.values()
        if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params):
            return transform(source, **kwargs)

        accepted_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in signature.parameters
            and signature.parameters[key].kind
            in (
                inspect.Parameter.KEYWORD_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        }
        return transform(source, **accepted_kwargs)
