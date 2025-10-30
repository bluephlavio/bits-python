from pydantic import BaseModel  # pylint: disable=no-name-in-module


class TargetModel(BaseModel):  # pylint: disable=too-few-public-methods
    name: str | None = None
    tags: list[str] = []
    template: str | None = None
    dest: str | None = None
    # Static variables only (no blocks/constants at top level in new schema)
    context: dict = {}
    # Dynamic queries (e.g., blocks/constants); new schema field
    queries: dict = {}
    # Compose options for named queries or aggregations
    compose: dict = {}
    # Optional per-node merge policy: { context: deep|replace, queries: deep|replace }
    # Defaults to deep; validated at runtime by resolver for allowed values.
    merge: dict = {}
    # Optional inheritance mechanism: this target extends one or more base targets
    # Accepts: string (single), list of strings, possibly cross-file refs: "path/file.yml::Name"
    extends: str | list[str] | None = None
    # Optional path-based overrides applied after merge (on queries/context/compose)
    overrides: list[dict] = []
