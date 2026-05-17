from pydantic import BaseModel, validator  # pylint: disable=no-name-in-module


class TargetOutputModel(BaseModel):  # pylint: disable=too-few-public-methods
    name: str
    template: str | None = None
    dest: str | None = None
    suffix: str | None = None
    context: dict = {}
    default: bool = False


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
    # Accepts: string (single), list of strings, or cross-file ref "file.yml::Name"
    extends: str | list[str] | None = None
    # Optional path-based overrides applied after merge (on queries/context/compose)
    overrides: list[dict] = []
    # Optional rendering variants: each output shares the resolved context/queries
    # but may use a different template, dest, suffix, or context overlay.
    outputs: list[TargetOutputModel] = []

    @validator("outputs", always=True)
    @classmethod
    def _validate_outputs(cls, outputs, values):  # pylint: disable=no-self-argument
        defaults = [o for o in outputs if o.default]
        if len(defaults) > 1:
            name = values.get("name")
            raise ValueError(
                f"Target '{name}': multiple outputs have default=True;"
                " at most one is allowed"
            )
        return outputs
