from pathlib import Path

from typer.testing import CliRunner

from bits.bit import Bit
from bits.block import Block
from bits.cli.main import app


def test_bit_render_fragments_simple():
    bit = Bit(
        src={
            "equation": r"x=\VAR{ x }",
            "plot": r"Plot: \VAR{ title }",
        },
        defaults={"x": 7, "title": "T"},
        name="MF",
    )
    blk = Block(bit, context={})
    assert blk.render("equation") == "x=7"
    assert blk.render("plot") == "Plot: T"


def test_yaml_registry_build_with_multi_fragment_and_single(resources, tmp_path):
    # Build a registry on the fly with one multi-fragment bit and one single bit
    reg = tmp_path / "mf.yaml"
    tpl = Path("tests/resources/templates/multi-fragments.tex.j2").resolve()
    outdir = Path("tests/artifacts").resolve()
    reg.write_text(
        f"""
targets:
  - name: mf
    template: {tpl.as_posix()}
    dest: {outdir.as_posix()}
    queries:
      blocks:
        - where: {{ name: MF1 }}
        - where: {{ name: Single }}
    compose:
      blocks: {{ flatten: false, as: groups }}

bits:
  - name: MF1
    src:
      equation: "$a + $b = $c"  # Not Jinja; just ensure raw text allowed
      plot: 'Plot(\\VAR{{ a }},\\VAR{{ b }})'
    defaults: {{ a: 1, b: 2, c: 3 }}

  - name: Single
    src: "SingleBit"
        """,
        encoding="utf-8",
    )

    runner = CliRunner()
    res = runner.invoke(app, ["build", str(reg), "--tex"], prog_name="bits")
    assert res.exit_code == 0, res.output

    # Expect readable name 'mf.tex' in outdir
    tex = outdir / "mf.tex"
    assert tex.exists(), f"missing: {tex}"

    s = tex.read_text(encoding="utf-8")
    # Should include both fragment renders and the single bit
    assert "P: Plot(1,2)" in s
    assert "E: $a + $b = $c" in s
    assert "S: SingleBit" in s


def test_src_mapping_must_not_be_empty(tmp_path):
    # Validate failure mode for empty fragment dict
    reg = tmp_path / "bad.yaml"
    reg.write_text(
        """
bits:
  - name: Bad
    src: {}
        """,
        encoding="utf-8",
    )

    runner = CliRunner()
    res = runner.invoke(app, ["build", str(reg), "--tex"], prog_name="bits")
    assert res.exit_code != 0
