import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from .. import __version__
from ..registry import RegistryFactory, RegistryFile
from .helpers import initialize_registry, watch_for_changes
from ..env import EnvironmentFactory
from ..renderer import Renderer
from ..helpers import write as _write
from ..config import config
from ..registry.registryfile import RegistryFile as _RegistryFile
from ..block import Block
from ..helpers import normalize_path
from jinja2 import Environment as _J2Environment
from jinja2 import FileSystemLoader as _J2Loader
import re


def _supports_unicode_output(stream) -> bool:
    """Return True if the stream can safely render unicode box characters.

    Only enable rich styling when output is a TTY and can render box chars.
    This keeps CLI help plain when output is captured (e.g., in CI),
    ensuring stable, non-ANSI output for tests.
    """
    # Avoid rich styling when not attached to a TTY (e.g., subprocess pipes)
    is_tty = False
    try:
        is_tty = bool(getattr(stream, "isatty", lambda: False)())
    except Exception:  # pragma: no cover - conservative fallback
        is_tty = False

    if not is_tty:
        return False

    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        "\u2500".encode(encoding)
    except Exception:  # pragma: no cover - conservative fallback
        return False
    return True


_USE_RICH_STYLING = _supports_unicode_output(sys.stdout)

app = typer.Typer(
    rich_markup_mode="rich" if _USE_RICH_STYLING else None,
    pretty_exceptions_enable=_USE_RICH_STYLING,
    pretty_exceptions_show_locals=False,
)
console = Console(legacy_windows=not _USE_RICH_STYLING)
install(
    suppress=[SystemExit, KeyboardInterrupt],
    show_locals=_USE_RICH_STYLING,
)


def version_callback(ctx: typer.Context, param, value: Optional[bool]):
    if value:
        typer.echo(f"bits {__version__}")
        ctx.exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit",
    ),
):  # pylint: disable=unused-argument
    pass


@app.command(name="build")
def render(
    path: str,
    watch: bool = typer.Option(False),
    output_tex: bool = typer.Option(False, help="Legacy flag to output only TeX"),
    pdf: bool = typer.Option(False, help="Output PDF"),
    tex: bool = typer.Option(False, help="Output TeX"),
    both: bool = typer.Option(False, help="Output both PDF and TeX"),
    keep_intermediates: str = typer.Option(
        "none",
        help="Keep LaTeX intermediates: none|errors|all",
    ),
    intermediates_dir: Optional[Path] = typer.Option(None, help="Intermediates dir"),
    build_dir: Optional[Path] = typer.Option(None, help="Temporary build dir"),
    target: Optional[str] = typer.Option(None, help="Build a single target by name"),
    unique: Optional[str] = typer.Option(
        None,
        "--unique",
        help="Use unique naming for outputs: uuid|timestamped",
    ),
    no_plugins: bool = typer.Option(
        False,
        "--no-plugins",
        help="Disable loading Jinja plugins declared in .bitsrc",
    ),
):
    console.print("[bold green]Starting build process...[/bold green]")
    # Configure plugin loading before any template/env creation
    EnvironmentFactory.enable_plugins(not no_plugins)

    # Parse compact target syntax path::"Target Name"
    compact_target = None
    if "::" in str(path):
        p, t = str(path).split("::", 1)
        path = p
        compact_target = t.strip('"') if t else None

    # Compute output modes
    # Compute output modes with config fallbacks when all flags unset
    cfg_pdf = config.getboolean("output", "pdf", fallback=True)
    cfg_tex = config.getboolean("output", "tex", fallback=False)
    do_both = bool(both)
    any_set = any([pdf, tex, both, output_tex])
    do_tex = bool(tex or (not any_set and cfg_tex) or output_tex)
    do_pdf = bool(pdf or (not any_set and cfg_pdf and not do_tex and not do_both))

    EnvironmentFactory.enable_plugins(not no_plugins)

    if target or compact_target:
        # Render only selected target
        reg_path = Path(path)
        registry = RegistryFactory.get(reg_path)
        sel = target or compact_target
        tgt = None
        for t in registry.targets:
            if t.name == sel:
                tgt = t
                break
        if tgt is None:
            raise typer.BadParameter(f"Target not found: {sel}")
        console.rule("[bold]Build Started (single target)")
        tex_code = tgt.render_tex_code()
        if do_tex or do_both:
            from ..helpers import write as _write

            _write(tex_code, tgt.dest.with_suffix(".tex"))
        if do_pdf or do_both:
            Renderer.render(
                tex_code,
                tgt.dest,
                output_tex=False,
                build_dir=build_dir,
                intermediates_dir=intermediates_dir,
                keep_intermediates=keep_intermediates,
            )
        console.rule("[bold]Build Completed")
        return

    reg_path = Path(path)
    registry = initialize_registry(
        reg_path,
        console,
        watch,
        output_tex,
        pdf=do_pdf,
        tex=do_tex,
        both=do_both,
        build_dir=build_dir,
        intermediates_dir=intermediates_dir,
        keep_intermediates=keep_intermediates,
        unique_strategy=unique,
    )

    if watch:
        console.print("[bold yellow]Watching for file changes...[/bold yellow]")
        watch_for_changes(registry, console, output_tex)


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "item"


def _parse_preview_spec(spec: str):
    # Returns dict: { 'path': str, 'name': str|None, 'num': int|None, 'preset': str|int|None }
    path = spec
    name = None
    num = None
    preset = None

    if "[" in spec and spec.endswith("]"):
        path, rest = spec.split("[", 1)
        inner = rest[:-1]
        # Extract #num and :preset
        # Extract @idx first (1-based)
        midx = re.search(r"@(\d+)", inner)
        idx = int(midx.group(1)) if midx else None
        if midx:
            inner = inner.replace(midx.group(0), "")
        mnum = re.search(r"#(\d+)", inner)
        if mnum:
            num = int(mnum.group(1))
            inner = inner.replace(mnum.group(0), "")
        if ":" in inner:
            parts = inner.split(":", 1)
            name = parts[0]
            preset = parts[1]
        else:
            name = inner
        name = name.strip() if name else None
        preset = preset.strip() if isinstance(preset, str) else preset
        return {"path": path, "name": name or None, "num": num, "preset": preset, "idx": idx}

    # Colon form: file.yml:"Name"#2:default or file.yml:Name#2:3
    # Handle target form '::' elsewhere (not supported here)
    if ":" in spec and not "::" in spec:
        path, rest = spec.split(":", 1)
        # If quoted name
        if rest.startswith('"'):
            m = re.match(r'^"([^"]+)"(.*)$', rest)
            if m:
                name = m.group(1)
                rest = m.group(2)
        else:
            # Unquoted up to # or :
            m = re.match(r'^([^#:]+)(.*)$', rest)
            if m:
                name = m.group(1)
                rest = m.group(2)
        if rest:
            mnum = re.match(r'^#(\d+)(.*)$', rest)
            if mnum:
                num = int(mnum.group(1))
                rest = mnum.group(2)
        # Optional @idx
        if rest and rest.startswith("@"):
            midx = re.match(r'^@(\d+)(.*)$', rest)
            if midx:
                idx = int(midx.group(1))
                rest = midx.group(2)
        if rest.startswith(":"):
            preset = rest[1:] if len(rest) > 1 else None
        return {"path": path, "name": (name or "").strip() or None, "num": num, "preset": preset, "idx": idx}

    return {"path": path, "name": None, "num": None, "preset": None, "idx": None}


@app.command(name="preview")
def preview(
    spec: str = typer.Argument(..., help="Preview spec: file[Bit#num:preset] or file"),
    out: Optional[Path] = typer.Option(None, "--out"),
    pdf: bool = typer.Option(False, "--pdf"),
    tex: bool = typer.Option(False, "--tex"),
    both: bool = typer.Option(False, "--both"),
    naming: Optional[str] = typer.Option(None, help="readable|uuid|timestamped"),
    no_plugins: bool = typer.Option(
        False,
        "--no-plugins",
        help="Disable loading Jinja plugins declared in .bitsrc",
    ),
):
    """Build a quick preview for a bitsfile or a single bit."""
    EnvironmentFactory.enable_plugins(not no_plugins)

    sel = _parse_preview_spec(spec)
    reg_path = Path(sel["path"]).resolve()
    reg = RegistryFactory.get(reg_path)

    # Determine output format w/ config defaults
    preview_out = out or Path(config.get("preview", "out_dir", fallback=".bitsout/preview"))
    cfg_pdf = config.getboolean("preview", "pdf", fallback=False)
    cfg_tex = config.getboolean("preview", "tex", fallback=True)
    cfg_naming = config.get("preview", "naming", fallback="readable")
    naming = naming or cfg_naming
    if not any([pdf, tex, both]):
        pdf = cfg_pdf
        tex = cfg_tex
    do_pdf = pdf or both
    do_tex = tex or both or not do_pdf

    # Select template for preview
    pkg_templates = Path(__file__).resolve().parent.parent / "config" / "templates"
    bitsfile_tpl_path = config.get("preview.templates", "bitsfile", fallback=str(pkg_templates / "preview.tex.j2"))
    bit_tpl_path = config.get("preview.templates", "bit", fallback=str(pkg_templates / "bit-preview.tex.j2"))
    bitsfile_tpl = Path(bitsfile_tpl_path)
    bit_tpl = Path(bit_tpl_path)

    if sel["name"]:
        # Single bit preview
        # Find candidate bits by name and optional num
        bits = list(reg.bits.filter(name=sel["name"], num=sel["num"]))
        # Optional @idx (1-based) disambiguation
        if sel.get("idx") and 1 <= sel["idx"] <= len(bits):
            bits = [bits[sel["idx"] - 1]]
        if not bits:
            raise typer.BadParameter(
                f"Bit not found: name='{sel['name']}', num='{sel['num']}'"
            )
        bit = bits[0]

        # Resolve preset context if provided
        ctx = getattr(bit, "defaults", {})
        try:
            if isinstance(reg, _RegistryFile):
                overlay = reg._preset_context(bit, sel["preset"])  # pylint: disable=protected-access
                ctx = {**ctx, **overlay}
        except Exception as err:
            raise typer.BadParameter(f"Error resolving preset context: {err}")

        # Build Block with merged context
        block = Block(bit, context=ctx)

        # Build filename
        bitslug = _slugify(reg_path.stem)
        bslug = _slugify(bit.name or "bit")
        name_parts = [bitslug, bslug]
        if sel["num"]:
            name_parts.append(f"n-{sel['num']}")
        if sel["preset"] is not None:
            p = sel["preset"]
            pkey = f"p-{p}" if isinstance(p, str) else f"p-{p}"
            name_parts.append(pkey)
        base = "__".join(name_parts)

        # Render
        env = EnvironmentFactory.get(templates_folder=bit_tpl.parent)
        tpl = env.get_template(bit_tpl.name)
        tex_code = tpl.render(bit=block)

        # Apply naming strategy
        if naming in ("uuid", "timestamped"):
            import uuid, datetime as _dt
            suffix = uuid.uuid4().hex[:8] if naming == "uuid" else _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            base = f"{base}__{suffix}"
        preview_out.mkdir(parents=True, exist_ok=True)
        dest = preview_out / f"{base}.pdf"
        if do_tex:
            # Always write .tex for predictable preview
            _write(tex_code, dest.with_suffix('.tex'))
        if do_pdf:
            Renderer.render(tex_code, dest, output_tex=False)
        return

    # Bitsfile preview
    questions = [Block(b, context=getattr(b, "defaults", {})) for b in reg.bits]
    bitslug = _slugify(reg_path.stem)
    base = f"{bitslug}"

    env = EnvironmentFactory.get(templates_folder=bitsfile_tpl.parent)
    tpl = env.get_template(bitsfile_tpl.name)
    tex_code = tpl.render(questions=questions)

    if naming in ("uuid", "timestamped"):
        import uuid, datetime as _dt
        suffix = uuid.uuid4().hex[:8] if naming == "uuid" else _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"{base}__{suffix}"
    preview_out.mkdir(parents=True, exist_ok=True)
    dest = preview_out / f"{base}.pdf"
    if do_tex:
        _write(tex_code, dest.with_suffix('.tex'))
    if do_pdf:
        Renderer.render(tex_code, dest, output_tex=False)


@app.command(name="convert")
def convert(
    src: Path,
    out: Optional[Path] = typer.Option(None),
    fmt: Optional[str] = typer.Option(None),
):
    if out is None:
        if fmt is None:
            raise typer.BadParameter("Either --out or --fmt must be provided")
        out = src.with_suffix(f".{fmt}")

    registryfile: RegistryFile = RegistryFactory.get(src)
    registryfile.dump(out)


@app.command(name="init-config")
def init_config():
    """Copy packaged defaults into ~/.bits (on demand)."""
    import shutil as _sh
    from ..config import GLOBAL_BITS_CONFIG_DIR, GLOBAL_BITS_CONFIG_DIR_SRC

    GLOBAL_BITS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _sh.copytree(GLOBAL_BITS_CONFIG_DIR_SRC, GLOBAL_BITS_CONFIG_DIR, dirs_exist_ok=True)
    console.print(
        f"[green]Installed defaults to[/green] [bold]{GLOBAL_BITS_CONFIG_DIR}[/bold]"
    )
