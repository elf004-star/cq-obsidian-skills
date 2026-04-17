"""Regression tests for plain-markdown-skill/scripts/normalize_math.py.

Freezes a cross-section drawn from the Lagrange test document so that any
future change to the three reusable transforms (math-whitespace collapse,
integration-symbol unification, bold-term stripping) can be caught
immediately.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCRIPT = SKILL_ROOT / "scripts" / "normalize_math.py"
FIXTURES = HERE / "fixtures"
INPUT_FILE = FIXTURES / "math_section_input.md"
EXPECTED_FILE = FIXTURES / "math_section_expected.md"
TERMS_FILE = FIXTURES / "bold_terms.txt"

# `conftest.py` prepends SKILL_ROOT / "scripts" to sys.path.
import normalize_math  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_full_fixture_via_cli(tmp_path: Path) -> None:
    target = tmp_path / INPUT_FILE.name
    target.write_text(_read(INPUT_FILE), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(target), "--terms", str(TERMS_FILE)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "wrote" in result.stdout

    assert _read(target) == _read(EXPECTED_FILE)


def test_full_fixture_via_module() -> None:
    source = _read(INPUT_FILE)
    terms = normalize_math._load_terms(TERMS_FILE)
    out = normalize_math.normalize(source, bold_terms=terms)
    assert out == _read(EXPECTED_FILE)


class TestCollapseMathWhitespace:
    def test_cmd_brace(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"\mathrm {d}") == r"\mathrm{d}"

    def test_caret_brace(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"\Omega^ {\prime}") == r"\Omega^{\prime}"

    def test_underscore_brace(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"z _ {I}") == r"z_{I}"

    def test_adjacent_commands(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"\lambda \cdot \mu") == r"\lambda\cdot\mu"

    def test_nested_inside_braces(self) -> None:
        assert (
            normalize_math.collapse_math_whitespace(r"\Omega^ {\prime \prime}")
            == r"\Omega^{\prime\prime}"
        )

    def test_preserves_command_with_argument(self) -> None:
        # A command followed by a brace without a space must be left alone.
        assert normalize_math.collapse_math_whitespace(r"\mathrm{d}\delta x") == r"\mathrm{d}\delta x"

    def test_space_before_caret_after_letter(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"y ^ {\prime}") == r"y^{\prime}"

    def test_space_before_underscore_after_letter(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"z _ {I}") == r"z_{I}"

    def test_space_before_caret_after_brace(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"\mathrm{d} ^ {2}") == r"\mathrm{d}^{2}"

    def test_space_before_caret_after_paren(self) -> None:
        assert normalize_math.collapse_math_whitespace(r"(x - a) ^ {2}") == r"(x - a)^{2}"


class TestUnifyIntegrationSymbol:
    def test_mathrm_single(self) -> None:
        assert normalize_math.unify_integration_symbol(r"\mathrm{S}") == r"\mathbf{S}"

    def test_mathbb_single(self) -> None:
        assert normalize_math.unify_integration_symbol(r"\mathbb{S}") == r"\mathbf{S}"

    def test_mathbf_double_with_space(self) -> None:
        assert normalize_math.unify_integration_symbol(r"\mathbf{S S}") == r"\mathbf{SS}"

    def test_mathrm_double(self) -> None:
        assert normalize_math.unify_integration_symbol(r"\mathrm{SS}") == r"\mathbf{SS}"

    def test_double_rewritten_before_single(self) -> None:
        # Verifies ordering: if the single-S rule ran first on \mathrm{SS},
        # we would get \mathbf{S}S} instead of \mathbf{SS}.
        assert (
            normalize_math.unify_integration_symbol(r"x \mathrm{SS} y")
            == r"x \mathbf{SS} y"
        )


class TestStripBoldTerms:
    def test_single_term(self) -> None:
        assert normalize_math.strip_bold_terms("call **variations** the", ["variations"]) == "call variations the"

    def test_multiple_terms_in_list(self) -> None:
        out = normalize_math.strip_bold_terms(
            "**Foo** and **Bar**",
            ["Foo", "Bar"],
        )
        assert out == "Foo and Bar"

    def test_unlisted_term_untouched(self) -> None:
        assert (
            normalize_math.strip_bold_terms("**Foo** and **Unknown**", ["Foo"])
            == "Foo and **Unknown**"
        )


class TestUnicodeToLatex:
    def test_middle_dot(self) -> None:
        assert normalize_math.unicode_to_latex("a·b") == r"a\cdot b"

    def test_partial_and_greek(self) -> None:
        assert normalize_math.unicode_to_latex("∂λ/∂μ") == r"\partial\lambda/\partial\mu"

    def test_superscript_digit(self) -> None:
        assert normalize_math.unicode_to_latex("x²+y³") == "x^{2}+y^{3}"

    def test_subscript_digit(self) -> None:
        assert normalize_math.unicode_to_latex("H₂O") == "H_{2}O"

    def test_ellipsis(self) -> None:
        assert normalize_math.unicode_to_latex("a…b") == r"a\dots b"

    def test_inequality_and_arrow(self) -> None:
        assert normalize_math.unicode_to_latex("x≤y→z") == r"x\leq y\to z"

    def test_custom_mapping_overrides_default(self) -> None:
        out = normalize_math.unicode_to_latex("·", mapping={"·": r"\bullet"})
        assert out == r"\bullet"

    def test_unmapped_glyph_preserved(self) -> None:
        # a character deliberately absent from the map stays as-is
        assert normalize_math.unicode_to_latex("ℵ") == "ℵ"


class TestReplaceInMathRegions:
    def test_inline_region(self) -> None:
        out = normalize_math.replace_in_math_regions("a $x·y$ b", normalize_math.unicode_to_latex)
        assert out == r"a $x\cdot y$ b"

    def test_block_region(self) -> None:
        src = "before\n\n$$\nα + β\n$$\n\nafter"
        out = normalize_math.replace_in_math_regions(src, normalize_math.unicode_to_latex)
        assert out == "before\n\n$$\n\\alpha + \\beta\n$$\n\nafter"

    def test_prose_unchanged(self) -> None:
        src = "中文·间隔 and arrows→here without math"
        assert normalize_math.replace_in_math_regions(src, normalize_math.unicode_to_latex) == src

    def test_multiple_inline_regions(self) -> None:
        out = normalize_math.replace_in_math_regions(
            "$α$ and $β$ together",
            normalize_math.unicode_to_latex,
        )
        assert out == r"$\alpha$ and $\beta$ together"

    def test_block_preferred_over_inline(self) -> None:
        # `$$...$$` must be captured as a block, not two inline matches
        out = normalize_math.replace_in_math_regions(
            "$$α·β$$", normalize_math.unicode_to_latex
        )
        assert out == r"$$\alpha\cdot\beta$$"


class TestSplitBlockMath:
    def test_single_line_expanded(self) -> None:
        assert normalize_math.split_block_math("$$x = 1$$") == "$$\nx = 1\n$$"

    def test_body_stripped(self) -> None:
        assert normalize_math.split_block_math("$$   x = 1   $$") == "$$\nx = 1\n$$"

    def test_trailing_whitespace_tolerated(self) -> None:
        assert normalize_math.split_block_math("$$x = 1$$   ") == "$$\nx = 1\n$$"

    def test_already_split_untouched(self) -> None:
        src = "$$\nx = 1\n$$"
        assert normalize_math.split_block_math(src) == src

    def test_mid_paragraph_inline_dollars_untouched(self) -> None:
        # Not a line on its own -> not a display block, leave alone.
        src = "see $$x=1$$ inline"
        assert normalize_math.split_block_math(src) == src

    def test_multiple_blocks(self) -> None:
        src = "before\n\n$$a=1$$\n\nmiddle\n\n$$b=2$$\n\nafter"
        out = normalize_math.split_block_math(src)
        assert out == "before\n\n$$\na=1\n$$\n\nmiddle\n\n$$\nb=2\n$$\n\nafter"

    def test_preserves_neighbouring_blank_lines(self) -> None:
        src = "text\n\n$$x$$\n\nmore text\n"
        out = normalize_math.split_block_math(src)
        assert out == "text\n\n$$\nx\n$$\n\nmore text\n"


class TestToggles:
    def test_skip_whitespace_collapse(self) -> None:
        src = r"\mathrm {S}"
        out = normalize_math.normalize(src, collapse_ws=False, unify_s=False)
        assert out == src

    def test_skip_s_unify(self) -> None:
        src = r"\mathbb{S}"
        out = normalize_math.normalize(src, unify_s=False)
        assert out == src

    def test_no_bold_terms_default(self) -> None:
        src = "**Foo**"
        assert normalize_math.normalize(src) == src

    def test_convert_unicode_off_by_default(self) -> None:
        src = "prose $α$ more"
        assert normalize_math.normalize(src, collapse_ws=False, unify_s=False) == src

    def test_convert_unicode_opt_in(self) -> None:
        src = "prose $α·β$ more"
        out = normalize_math.normalize(
            src, collapse_ws=False, unify_s=False, convert_unicode=True
        )
        assert out == r"prose $\alpha\cdot\beta$ more"

    def test_convert_unicode_leaves_prose_alone(self) -> None:
        # Unicode glyphs outside $...$ are not touched even with the flag on
        src = "prose·word stays"
        out = normalize_math.normalize(
            src, collapse_ws=False, unify_s=False, convert_unicode=True
        )
        assert out == src

    def test_split_blocks_on_by_default(self) -> None:
        src = "$$x=1$$"
        assert normalize_math.normalize(src) == "$$\nx=1\n$$"

    def test_skip_split_blocks(self) -> None:
        src = "$$x=1$$"
        out = normalize_math.normalize(
            src, collapse_ws=False, unify_s=False, split_blocks=False
        )
        assert out == src

    def test_standalone_inline_to_block_single(self) -> None:
        src = "$x+1$"
        assert normalize_math.normalize(src) == "$$\nx+1\n$$"

    def test_standalone_inline_to_block_complex(self) -> None:
        src = "$\\frac{1}{2}$"
        assert normalize_math.normalize(src) == "$$\n\\frac{1}{2}\n$$"

    def test_standalone_inline_to_block_preserves_neighbouring_blank_lines(self) -> None:
        src = "para\n\n$x=1$\n\nmore"
        out = normalize_math.normalize(src)
        assert out == "para\n\n$$\nx=1\n$$\n\nmore"

    def test_standalone_inline_to_block_noop_when_inline(self) -> None:
        # mid-paragraph inline math must NOT be promoted
        src = "prose $x=1$ more"
        out = normalize_math.normalize(src)
        assert out == src

    def test_skip_standalone_inline_to_block(self) -> None:
        src = "$x+1$"
        out = normalize_math.normalize(
            src, collapse_ws=False, unify_s=False, standalone_inline_to_block=False
        )
        assert out == src

    def test_split_blocks_runs_after_promote(self) -> None:
        # promote_standalone_inline runs before split_block_math,
        # so a $$body$$ that was inline becomes three-line
        src = "$$\nx=1\n$$"
        assert normalize_math.normalize(src) == "$$\nx=1\n$$"


class TestFrontmatterProtection:
    def test_frontmatter_untouched(self) -> None:
        src = (
            '---\n'
            'title: "My Doc"\n'
            'tags: [foo, **bar**]\n'
            '---\n'
            '\n'
            r'$\mathrm {S}$'
        )
        out = normalize_math.normalize(src)
        assert out.startswith(
            '---\n'
            'title: "My Doc"\n'
            'tags: [foo, **bar**]\n'
            '---\n'
        )
        # Body should still be processed (S unified + standalone promoted)
        assert r'\mathbf{S}' in out

    def test_no_frontmatter_passthrough(self) -> None:
        src = r'$\mathrm{S}$'
        out = normalize_math.normalize(src)
        # standalone inline gets promoted to block, S gets unified
        assert r'\mathbf{S}' in out

    def test_frontmatter_with_bold_terms(self) -> None:
        src = (
            '---\n'
            'title: "**General Equation of Equilibrium**"\n'
            '---\n'
            '\n'
            '**General Equation of Equilibrium** in body'
        )
        out = normalize_math.normalize(
            src, bold_terms=["General Equation of Equilibrium"]
        )
        # Frontmatter stays intact
        assert '"**General Equation of Equilibrium**"' in out
        # Body gets stripped
        assert 'General Equation of Equilibrium in body' in out

    def test_frontmatter_preserves_trailing_newline(self) -> None:
        src = (
            '---\n'
            'key: val\n'
            '---\n'
            '\n'
            'body\n'
        )
        out = normalize_math.normalize(src)
        assert out.endswith('\n')

    def test_split_frontmatter_and_rejoin(self) -> None:
        fm, body = normalize_math._split_frontmatter(
            '---\na: 1\n---\nhello'
        )
        assert fm == '---\na: 1\n---\n'
        assert body == 'hello'
        assert normalize_math._join_frontmatter(fm, body) == '---\na: 1\n---\nhello'

    def test_split_frontmatter_none(self) -> None:
        fm, body = normalize_math._split_frontmatter('no frontmatter')
        assert fm == ''
        assert body == 'no frontmatter'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
