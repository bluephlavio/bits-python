from __future__ import annotations

from pathlib import Path
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
                bit.defaults = self._resolve_context(bit.defaults)
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

        if data.query:
            bits: Collection[Bit] = registry.bits.query(**data.query.dict())
        else:
            bits: Collection[Bit] = registry.bits

        try:
            context: dict = self._resolve_context(data.context)
        except Exception as err:
            raise TemplateContextError("Could not resolve block context.") from err

        metadata: dict = data.metadata

        blocks: List[Block] = [
            Block(bit, context=context, metadata=metadata) for bit in bits
        ]
        return blocks

    def _resolve_constants(self, data: ConstantsModel) -> List[Constant]:
        registry: Registry = (
            self._resolve_registry(data.registry) if data.registry else self
        )

        constants: List[Constant] = registry.constants.query(**data.query.dict())

        return constants

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
