from __future__ import annotations

from pathlib import Path
import copy
from typing import Callable, List

import jinja2

from ..bit import Bit
from ..block import Block
from ..collections import Collection
from ..config import config
from ..constant import Constant
from ..env import EnvironmentFactory
from ..exceptions import RegistryLoadError, TemplateContextError, TemplateLoadError
from ..helpers import normalize_path
import warnings
from ..models import (
    BitModel,
    BlocksModel,
    ConstantModel,
    ConstantsModel,
    RegistryDataModel,
    TargetModel,
    WhereBitsModel,
    WhereConstantsModel,
    SelectModel,
)
from ..target import Target
from ..watcher import Watcher
from .registry import Registry
from .registry_factory import RegistryFactory
from .registryfile_dumpers import RegistryFileDumperFactory
from .registryfile_parsers import RegistryFileParserFactory


class RegistryFile(Registry):
    # pylint: disable=unused-argument
    def __init__(self, path: Path, as_dep: bool = False):
        super().__init__(path)
        if not self._path.is_file():
            raise IsADirectoryError
        self._watcher: Watcher = Watcher(self._path)
        self._parser = RegistryFileParserFactory.get(self._path)
        self.load(as_dep=as_dep)

    def load(self, as_dep: bool = False):
        try:
            with self._load_lock:
                self.clear_registry()

                self.registryfile_model: RegistryDataModel = self._parser.parse(
                    self._path
                )

                common_tags: List[str] = self.registryfile_model.tags or []

                (
                    imported_bits,
                    imported_constants,
                    imported_targets,
                ) = self._import_registry_data(self.registryfile_model.imports)

                self._load_bits(self.registryfile_model.bits, common_tags)
                self._bits.extend(imported_bits)

                self._load_constants(self.registryfile_model.constants, common_tags)
                self._constants.extend(imported_constants)

                if not as_dep:
                    self._load_targets(self.registryfile_model.targets, common_tags)
                    self._targets.extend(imported_targets)
        except Exception as err:
            raise RegistryLoadError(path=self._path) from err

    def _load_bits(self, bit_models: List[BitModel], common_tags: List[str]):
        for bit_model in bit_models:
            src: str = bit_model.src
            meta: dict = bit_model.dict(exclude={"src"})
            bit: Bit = Bit(src, **meta)
            bit.tags.extend(common_tags)
            self._bits.append(bit)

        for bit in self._bits:
            try:
                bd = bit.defaults or {}
                # Preserve raw defaults (for presets overrides on queries AST)
                try:
                    bit._defaults_raw = copy.deepcopy(bd)  # pylint: disable=protected-access
                except Exception:  # pragma: no cover
                    bit._defaults_raw = bd
                if "context" in bd or "queries" in bd:
                    # New schema: defaults.context + defaults.queries
                    ctx = self._resolve_context(bd.get("context", {}))
                    if "queries" in bd:
                        ctx.update(self._resolve_inline_queries(bd.get("queries") or {}))
                    # Merge legacy query-style defaults if present at top-level
                    legacy_q = {
                        k: bd[k] for k in ["blocks", "constants"] if k in bd
                    }
                    if legacy_q:
                        ctx.update(self._resolve_context(legacy_q))
                    bit.defaults = ctx
                else:
                    # Legacy: blocks/constants directly in defaults
                    bit.defaults = self._resolve_context(bd)
            except Exception as err:
                raise TemplateContextError(
                    f"Could not resolve bit defaults: \n\n{bit.defaults}\n"
                ) from err

    def _load_constants(
        self, constant_models: List[ConstantModel], common_tags: List[str]
    ):
        for constant_model in constant_models:
            constant: Constant = Constant.from_model(constant_model)
            constant.tags.extend(common_tags)
            self._constants.append(constant)

    def _load_targets(self, target_models: List[TargetModel], common_tags: List[str]):
        for target_model in target_models:
            target: Target = self._resolve_target(target_model)
            target.tags.extend(common_tags)
            self._targets.append(target)

    def _import_registry_data(self, imports):
        imported_bits: List[Bit] = []
        imported_constants: List[Constant] = []
        imported_targets: List[Target] = []

        for import_entry in imports:
            imported_registry = self._resolve_registry(import_entry["registry"])
            imported_bits.extend(imported_registry.bits)
            imported_constants.extend(imported_registry.constants)
            imported_targets.extend(imported_registry.targets)

        return imported_bits, imported_constants, imported_targets

    def _resolve_path(self, path: str) -> Path:
        return normalize_path(path, relative_to=self._path)

    def _resolve_registry(self, path: str) -> Registry:
        registry_path: Path = self._resolve_path(path)
        registry: Registry = RegistryFactory.get(registry_path, as_dep=True)
        self.add_dep(registry)
        return registry

    def _resolve_template(self, path: str) -> jinja2.Template:
        try:
            template_path: Path = self._resolve_path(path)
            env = EnvironmentFactory.get(templates_folder=template_path.parent)
            template: jinja2.Template = env.get_template(template_path.name)
            return template
        except Exception as err:
            raise TemplateLoadError(
                f"Error loading template at {template_path}"
            ) from err

    def _resolve_context(self, data: dict) -> dict:
        context: dict = {
            k: v for k, v in data.items() if k not in ["blocks", "constants"]
        }

        if "blocks" in data:
            warnings.warn(
                "context.blocks is deprecated; map to queries.blocks + compose.blocks.flatten/as",
                DeprecationWarning,
            )
            blocks: List[Block] = [
                block
                for blocks_data in data["blocks"]
                for block in self._resolve_blocks(BlocksModel(**blocks_data))
            ]
            context["blocks"] = blocks

        if "constants" in data:
            warnings.warn(
                "context.constants is deprecated; map to queries.constants + compose",
                DeprecationWarning,
            )
            constants: List[Constant] = [
                constant
                for constants_data in data["constants"]
                for constant in self._resolve_constants(
                    ConstantsModel(**constants_data)
                )
            ]
            context["constants"] = constants

        return context

    def _resolve_blocks(self, data: BlocksModel) -> List[Block]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        # Resolve candidate bits using legacy query or new where
        if data.query:
            bits: Collection[Bit] = registry.bits.query(**data.query.dict())
        elif getattr(data, "where", None):
            bits = self._filter_bits_with_where(registry.bits, data.where)  # type: ignore[arg-type]
        else:
            bits = registry.bits

        # Apply select if provided
        seq: list[Bit] = list(bits)
        if getattr(data, "select", None):
            seq = self._apply_select(seq, data.select)  # type: ignore[arg-type]

        # Resolve nested context and with_ overrides
        try:
            context: dict = self._resolve_context(data.context)
        except Exception as err:
            raise TemplateContextError("Could not resolve block context.") from err

        with_ctx: dict = {}
        with_queries_ctx: dict = {}
        if getattr(data, "with_", None):
            if data.with_.context:
                try:
                    with_ctx = self._resolve_context(data.with_.context)
                except Exception as err:
                    raise TemplateContextError("Could not resolve block 'with.context'.") from err
            if data.with_.queries:
                try:
                    with_queries_ctx = self._resolve_inline_queries(data.with_.queries)
                except Exception as err:
                    raise TemplateContextError("Could not resolve block 'with.queries'.") from err

        metadata: dict = data.metadata
        blocks: List[Block] = []
        for bit in seq:
            pctx = self._preset_context(bit, getattr(data, "preset", None))
            merged_context = self._deep_merge(context, pctx)
            merged_context = self._deep_merge(merged_context, with_ctx)
            merged_context = self._deep_merge(merged_context, with_queries_ctx)
            blocks.append(Block(bit, context=merged_context, metadata=metadata))
        return blocks

    def _resolve_constants(self, data: ConstantsModel) -> List[Constant]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        # Resolve candidate constants using legacy query or new where
        if data.query:
            const_coll = registry.constants.query(**data.query.dict())
        elif getattr(data, "where", None):
            const_coll = self._filter_constants_with_where(registry.constants, data.where)  # type: ignore[arg-type]
        else:
            const_coll = registry.constants

        seq: list[Constant] = list(const_coll)
        if getattr(data, "select", None):
            seq = self._apply_select(seq, data.select)  # type: ignore[arg-type]

        return seq

    @staticmethod
    def _select_preset(bit: Bit, selector: str | int | None):
        if selector is None:
            return None
        presets = getattr(bit, "presets", []) or []
        if not presets:
            return None
        # Try id first when selector is str
        if isinstance(selector, str):
            for p in presets:
                if p.get("id") == selector:
                    return p
            # If numeric string and id not found, try as index
            try:
                selector = int(selector)
            except ValueError:
                raise ValueError(f"Preset '{selector}' not found for bit '{bit.name}'")
        # Index path (1-based)
        if isinstance(selector, int):
            idx = selector - 1
            if 0 <= idx < len(presets):
                return presets[idx]
            raise ValueError(f"Preset index {selector} out of range for bit '{bit.name}'")
        return None

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        out = dict(base)
        for k, v in (override or {}).items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = RegistryFile._deep_merge(out[k], v)
            else:
                out[k] = v
        return out

    def _preset_context(self, bit: Bit, selector: str | int | None) -> dict:
        """Resolve preset overlays for a single bit.

        Returns a dict of variables to overlay into the block context (both context and
        resolved queries like blocks/constants). For queries lists, replacement semantics
        apply (preset-provided lists replace defaults silently at this overlay level).
        """
        preset = self._select_preset(bit, selector)
        if not preset:
            return {}

        out: dict = {}

        # context overlay (maps deep-merge done later via plain overlay precedence)
        ctx = preset.get("context") or {}
        if ctx:
            out.update(self._resolve_context(ctx))

        # queries overlay (evaluated and exposed into variables) with merge semantics
        # Base queries from defaults (AST), if provided
        defaults_raw = getattr(bit, "_defaults_raw", {})  # pylint: disable=protected-access
        q_base = {}
        if isinstance(defaults_raw, dict):
            if "queries" in defaults_raw:
                q_base = copy.deepcopy(defaults_raw.get("queries") or {})
            else:
                # Support legacy defaults containing resolved lists at top-level is skipped here
                q_base = {}

        pqueries = preset.get("queries") or {}
        # Merge base + preset (maps deep-merge, lists replace)
        q_merged = self._deep_merge(q_base, pqueries) if (q_base or pqueries) else {}

        # Apply overrides (path,value) on merged queries before resolving
        overrides = preset.get("overrides") or []
        if overrides:
            if not q_merged:
                raise ValueError("Preset overrides require 'queries' (from defaults or preset).")
            for ov in overrides:
                path = ov.get("path")
                value = ov.get("value")
                if not path:
                    continue
                self._apply_path_override(q_merged, path, value)

        if q_merged:
            out.update(self._resolve_inline_queries(q_merged))

        return out

    def _apply_path_override(self, root: dict, path: str, value):
        import re

        # Allow paths prefixed with 'queries.' even when root is already the queries map
        if path.startswith("queries."):
            path = path[len("queries."):]

        cur = root
        tokens = path.split(".")
        for i, tok in enumerate(tokens):
            m = re.match(r"^([A-Za-z0-9_]+)(?:\[(\d+)\])?$", tok)
            if not m:
                raise ValueError(f"Invalid override path token: {tok}")
            key = m.group(1)
            idx = m.group(2)
            if key not in cur:
                raise ValueError(f"Override path not found: {path}")
            if i == len(tokens) - 1:
                # Final token: set value (possibly into list item)
                target = cur[key]
                if idx is not None:
                    index = int(idx) - 1
                    if not isinstance(target, list) or not (0 <= index < len(target)):
                        raise ValueError(f"Override list index out of range: {path}")
                    target[index] = value
                else:
                    cur[key] = value
                return
            # Intermediate navigation
            cur = cur[key]
            if idx is not None:
                index = int(idx) - 1
                if not isinstance(cur, list) or not (0 <= index < len(cur)):
                    raise ValueError(f"Override list index out of range: {path}")
                cur = cur[index]

    def _filter_bits_with_where(
        self, coll: Collection[Bit], where: WhereBitsModel
    ) -> Collection[Bit]:
        # Start with collection-level filter for the fields we already support
        filter_kwargs = {}
        wd = where.dict(exclude={"has", "missing"})
        filter_kwargs.update({k: v for k, v in wd.items() if v is not None})
        # If no primary filters provided, start from full collection
        if not any(filter_kwargs.values()):
            result = coll
        else:
            result = coll.filter(**filter_kwargs)

        has = where.has or []
        missing = where.missing or []
        if not has and not missing:
            return result

        def present(value) -> bool:
            return value is not None and value != "" and value != [] and value != {}

        def has_field(bit: Bit, field: str) -> bool:
            if field == "src":
                return present(getattr(bit, "src", None))
            return present(bit._metadata.get(field))  # pylint: disable=protected-access

        filtered = [
            b
            for b in result
            if all(has_field(b, f) for f in has)
            and all(not has_field(b, f) for f in missing)
        ]
        return Collection(Bit, filtered)

    def _filter_constants_with_where(
        self, coll: Collection[Constant], where: WhereConstantsModel
    ) -> Collection[Constant]:
        filter_kwargs = {}
        wd = where.dict(exclude={"has", "missing"})
        filter_kwargs.update({k: v for k, v in wd.items() if v is not None})
        if not any(filter_kwargs.values()):
            result = coll
        else:
            result = coll.filter(**filter_kwargs)

        has = where.has or []
        missing = where.missing or []

        def present(value) -> bool:
            return value is not None and value != "" and value != [] and value != {}

        def has_field(c: Constant, field: str) -> bool:
            if field in ("symbol", "value"):
                return present(getattr(c, field, None))
            return present(c._metadata.get(field))  # pylint: disable=protected-access

        if not has and not missing:
            return result

        filtered = [
            c
            for c in result
            if all(has_field(c, f) for f in has)
            and all(not has_field(c, f) for f in missing)
        ]
        return Collection(Constant, filtered)

    def _apply_select(self, items: list, select: SelectModel) -> list:
        import random

        if not items:
            return items

        rng = random.Random(select.seed) if select.seed is not None else random.Random()

        # Indices have precedence (1-based)
        if select.indices:
            out = []
            for idx in select.indices:
                i = idx - 1
                if 0 <= i < len(items):
                    out.append(items[i])
            return out

        seq = list(items)

        if select.shuffle:
            rng.shuffle(seq)

        if select.sample is not None:
            k = max(0, min(select.sample, len(seq)))
            seq = rng.sample(seq, k)

        offset = select.offset or 0
        seq = seq[offset:]
        k = select.k if select.k is not None else select.limit
        if k is not None:
            seq = seq[: max(0, int(k))]
        return seq

    def _resolve_target(self, data: TargetModel) -> Target:
        name: str | None = data.name
        tags: List[str] = data.tags or []

        template: jinja2.Template = self._resolve_template(
            data.template or config.get("DEFAULT", "template")
        )

        # Prepare base context (static only). Avoid resolving legacy top-level blocks/constants here;
        # they are handled via queries mapping below.
        raw_context = data.context or {}
        base_context_input = {k: v for k, v in raw_context.items() if k not in ["blocks", "constants"]}
        try:
            context: dict = self._resolve_context(base_context_input)
        except Exception as err:
            raise TemplateContextError("Could not resolve target context.") from err

        # Back-compat: map legacy context.blocks/constants into queries if present
        queries = dict(data.queries or {})
        compose_cfg = dict(data.compose or {})

        if "blocks" in raw_context and "blocks" not in queries:
            queries["blocks"] = raw_context["blocks"]
            # Ensure default compose matches legacy behavior
            c = compose_cfg.get("blocks", {})
            c.setdefault("flatten", True)
            c.setdefault("as", "blocks")
            compose_cfg["blocks"] = c

        if "constants" in raw_context and "constants" not in queries:
            queries["constants"] = raw_context["constants"]
            c = compose_cfg.get("constants", {})
            c.setdefault("as", "constants")
            compose_cfg["constants"] = c

        # Resolve queries and compose results into context
        if queries:
            composed_vars = self._resolve_and_compose_queries(queries, compose_cfg)
            context.update(composed_vars)

        dest: Path = self._resolve_path(data.dest or ".")
        dest = dest / f"{self._path.stem}-{name}.pdf" if dest.suffix == "" else dest

        target: Target = Target(template, context, dest, name=name, tags=tags)
        return target

    def _resolve_and_compose_queries(self, queries: dict, compose_cfg: dict) -> dict:
        """Resolve named queries (blocks/constants) and compose into final variables.

        Supported:
        - blocks: a dict (single sub-query) or a list of sub-queries
        - constants: a dict (single) or list of sub-queries
        Compose keys per query: { flatten, merge: concat|interleave, as }
        Also supports aggregate compose entries with { from: [var1, var2], ... }.
        """
        results: dict = {}

        def _resolve_blocks_spec(spec):
            if isinstance(spec, list):
                return [self._resolve_blocks(BlocksModel(**q)) for q in spec]
            if isinstance(spec, dict):
                return self._resolve_blocks(BlocksModel(**spec))
            raise ValueError("Invalid blocks query spec")

        def _resolve_constants_spec(spec):
            if isinstance(spec, list):
                return [self._resolve_constants(ConstantsModel(**q)) for q in spec]
            if isinstance(spec, dict):
                return self._resolve_constants(ConstantsModel(**spec))
            raise ValueError("Invalid constants query spec")

        # First pass: resolve known named queries
        for qname, spec in queries.items():
            if qname == "blocks":
                results[qname] = _resolve_blocks_spec(spec)
            elif qname == "constants":
                results[qname] = _resolve_constants_spec(spec)
            else:
                # Unknown query types are ignored for now (future extension)
                continue

        # Compose per-query
        composed: dict = {}

        def _interleave(lists: List[List]):
            out = []
            # round-robin
            lists_copy = [list(lst) for lst in lists]
            while any(lists_copy):
                for lst in lists_copy:
                    if lst:
                        out.append(lst.pop(0))
            return out

        for qname, res in results.items():
            cfg = compose_cfg.get(qname, {}) if compose_cfg else {}
            as_name = cfg.get("as", qname)
            flatten = cfg.get("flatten", None)
            merge = cfg.get("merge", "concat")
            dedupe = cfg.get("dedupe")
            do_shuffle = cfg.get("shuffle")
            seed = cfg.get("seed")
            limit = cfg.get("limit")
            flat_list = None
            if isinstance(res, list) and res and isinstance(res[0], list):
                # list-of-lists
                if flatten is None:
                    warnings.warn(
                        f"compose.{qname}.flatten not set; defaulting to true for back-compat",
                        DeprecationWarning,
                    )
                    flatten = True
                if flatten:
                    if merge == "concat":
                        flat_list = [item for lst in res for item in lst]
                    elif merge == "interleave":
                        flat_list = _interleave(res)
                    else:
                        raise ValueError(f"Unsupported merge mode: {merge}")
                else:
                    flat_list = res
            else:
                flat_list = res

            # Dedupe if requested
            if dedupe in ("by:id", "by:name", "by:hash") and isinstance(flat_list, list):
                seen = set()

                def key_fn(x):
                    try:
                        if dedupe == "by:id":
                            return getattr(x, "bit", x).id
                        if dedupe == "by:name":
                            return getattr(getattr(x, "bit", x), "name", None)
                        if dedupe == "by:hash":
                            return hash(repr(x))
                    except Exception:
                        return repr(x)
                    return repr(x)

                new_list = []
                for el in flat_list:
                    k = key_fn(el)
                    if k not in seen:
                        seen.add(k)
                        new_list.append(el)
                flat_list = new_list

            # Shuffle/limit
            if do_shuffle and isinstance(flat_list, list):
                import random

                rnd = random.Random(seed) if seed is not None else random.Random()
                rnd.shuffle(flat_list)

            if isinstance(flat_list, list) and limit is not None:
                flat_list = flat_list[: max(0, int(limit))]

            composed[as_name] = flat_list

        # Aggregate compose entries: keys with 'from'
        for cname, cfg in compose_cfg.items():
            if "from" in cfg:
                sources = cfg.get("from", [])
                src_lists = [composed.get(src) or results.get(src) for src in sources]
                src_lists = [lst for lst in src_lists if lst is not None]
                flatten = cfg.get("flatten", True)
                merge = cfg.get("merge", "concat")
                as_name = cfg.get("as", cname)

                if not src_lists:
                    continue

                if flatten:
                    if merge == "concat":
                        agg = []
                        for lst in src_lists:
                            if isinstance(lst, list) and lst and isinstance(lst[0], list):
                                agg.extend([item for sub in lst for item in sub])
                            else:
                                agg.extend(lst)
                    elif merge == "interleave":
                        # normalize to list-of-lists
                        norm_lists = []
                        for lst in src_lists:
                            if isinstance(lst, list) and lst and isinstance(lst[0], list):
                                norm_lists.extend(lst)
                            else:
                                norm_lists.append(list(lst))
                        agg = _interleave(norm_lists)
                    else:
                        raise ValueError(f"Unsupported merge mode: {merge}")
                else:
                    agg = src_lists

                composed[as_name] = agg

        return composed

    def _resolve_inline_queries(self, queries: dict) -> dict:
        """Resolve a lightweight queries object (no compose block). Defaults to flatten.

        Supports known names: blocks, constants. If a list of sub-queries is provided,
        flatten with concat and expose under its name.
        """
        out: dict = {}

        if not queries:
            return out

        if "blocks" in queries:
            spec = queries["blocks"]
            if isinstance(spec, list):
                lists = [self._resolve_blocks(BlocksModel(**q)) for q in spec]
                flat = [item for lst in lists for item in lst]
                out["blocks"] = flat
            elif isinstance(spec, dict):
                out["blocks"] = self._resolve_blocks(BlocksModel(**spec))

        if "constants" in queries:
            spec = queries["constants"]
            if isinstance(spec, list):
                lists = [self._resolve_constants(ConstantsModel(**q)) for q in spec]
                flat = [item for lst in lists for item in lst]
                out["constants"] = flat
            elif isinstance(spec, dict):
                out["constants"] = self._resolve_constants(ConstantsModel(**spec))

        return out

    def to_registry_data_model(self) -> RegistryDataModel:
        bits = [bit.to_bit_model() for bit in self.bits]
        constants = [constant.to_constant_model() for constant in self.constants]
        targets = [target.to_target_model() for target in self.targets]
        return RegistryDataModel(bits=bits, constants=constants, targets=targets)

    def dump(self, path: Path):
        dumper = RegistryFileDumperFactory.get(path)
        dumper.dump(self.registryfile_model, path)

    def add_listener(self, on_event: Callable, recursive=True) -> None:
        self._watcher.add_listener(on_event)
        if recursive:
            for dep in self._deps:
                dep.add_listener(on_event, recursive=True)

    def watch(self, recursive=True) -> None:
        self._watcher.start()
        if recursive:
            for dep in self._deps:
                dep.watch(recursive=recursive)

    def stop(self, recursive=True) -> None:
        self._watcher.stop()
        if recursive:
            for dep in self._deps:
                dep.stop(recursive=True)
