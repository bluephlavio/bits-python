## v0.14.1 (2024-11-26)

### Fix

- avoid resolution of defaults context on imported bits

## v0.14.0 (2024-11-26)

### Feat

- support resolving all bits from registry when query is absent in `blocks`
- introduce import field to registry files

## v0.13.0 (2024-11-03)

### Feat

- pick, render, enumerate and show custom jinja2 filters added
- output_tex option added to Target render and build cli command
- caching mechanism for target builds

### Fix

- folder index file feature fixed
- folder index file support feature fixed
- changed the rendering caching for same tex code targets with Renderer class implementation
- RegistryFactory caching mechanism fixed to allow refreshed instances
- registry deps cleared when starting loading
- added RegistryFactory caching to fix the proliferation of watchers

## v0.12.0 (2024-11-03)

## v0.11.0 (2024-10-10)

### Feat

- pick, render, enumerate and show custom jinja2 filters added

## v0.10.1 (2024-10-09)

## v0.10.0 (2024-10-08)

### Fix

- changed the rendering caching for same tex code targets with Renderer class implementation

## v0.9.2 (2024-10-08)

### Feat

- output_tex option added to Target render and build cli command
- caching mechanism for target builds

### Fix

- RegistryFactory caching mechanism fixed to allow refreshed instances
- registry deps cleared when starting loading

## v0.9.1 (2024-10-08)

### Fix

- added RegistryFactory caching to fix the proliferation of watchers
- watching system simplified by delegating only RegistryFile to have a watcher

## v0.9.0 (2024-10-08)

### Feat

- common registryfile tags feature added

### Fix

- watching system added to RegistryFolder where it delegates to files inside the folder
- watching system added to RegistryFolder where it delegates to files inside the folder
- watcher dependencies tracking and recursive listener attaching
- debounce mechanism added to watcher to avoid too fast rebuilding triggers

## v0.8.1 (2024-09-30)

### Fix

- minor shell fix into create-bitsrc.sh action file
- permissions for running github action create-bitsrc.sh script fixed

## v0.8.0 (2024-08-12)

### Feat

- constants definition in registry files and querying in targets as for blocks
- registry file dump method implemented by defining the RegistryFileDumper class hierarchy and convert cli command added
- yaml format now available for bitsfiles, tests improved

### Fix

- constants dump added in registryfile through dumpers implementation
- watching feature fixed

### Refactor

- registry file parsers introduce to abstract the different formats (.md and .yaml) from the registry itself

## v0.6.0 (2024-08-07)

### Feat

- local config added with variables, definition, interpolation and resolution inside registries

### Fix

- recurvise blocks queries now resolved even if passed in bit defaults

## v0.5.1 (2024-01-09)

### Fix

- constants data in context allowed to be used in templates
- minor pylint fix

## v0.5.0 (2023-10-09)

### Feat

- getitem filter added to jinja environment

## v0.4.0 (2023-10-08)

### Feat

- a FileSystemLoader is not associated with jinja2 environments that load templates to allow structuring of big templates

## v0.3.1 (2023-10-05)

### Feat

- nested bits queries are now supported

### Fix

- multiple criteria querying logic fixed
- matching by metadata other than name fixed by fixing a bug in match_by_name
- context processing in Block and Target removed

## v0.3.0 (2023-10-02)

### Feat

- floor and ceil filters added to jinja environment

### Fix

- fixed the bug related to bitsfiles without local bits and test suite updated
- name is a target property, not a bitsfile property
- name is a target property, not a bitsfile property

## v0.2.2 (2023-08-21)

### Fix

- fixed the bug related to bitsfiles without local bits and test suite updated
- name is a target property, not a bitsfile property
- name is a target property, not a bitsfile property
- target dest file name must contains the name of the bitsfile before the target name if a folder is provided
- name is a target property, not a bitsfile property

## v0.2.1 (2023-08-21)

### Fix

- target dest file name must contains the name of the bitsfile before the target name if a folder is provided
- minimum python version set to 3.10 in pyproject.toml

## v0.2.0 (2023-08-21)

### Feat

- support for regex when querying bits by name

## v0.1.3 (2023-08-20)

### Fix

- minimum python version set to 3.10 in pyproject.toml

## v0.1.0 (2023-08-20)
