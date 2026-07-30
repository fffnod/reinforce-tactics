"""Build the Reinforce Tactics RL guide as combined Markdown, HTML, and PDF."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    # Retained only for the legacy ReportLab renderer below.  The production
    # path uses browser MathML and therefore does not require ReportLab.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        Image,
        PageBreak,
        PageTemplate,
        Paragraph,
        Preformatted,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
except ModuleNotFoundError:
    # Function bodies resolve their ReportLab names only if the legacy path is
    # called.  This stub keeps the production builder importable in the project
    # Conda environment, where ReportLab is not installed.
    BaseDocTemplate = object


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
EXPORT = ROOT / "export"
PDF_DIR = REPO / "output" / "pdf"


def load_manifest() -> dict:
    return json.loads((ROOT / "book.json").read_text(encoding="utf-8"))


def combined_markdown(manifest: dict) -> str:
    cover = (
        f"# {manifest['title']}\n\n"
        f"## {manifest['subtitle']}\n\n"
        f"版本 {manifest['version']}　基准日期 {manifest['baseline_date']}\n\n"
        "> 本合订本由分章 Markdown 自动生成。正文、图表和实验材料均来自新版目录。\n"
    )
    parts = [cover]
    for name in manifest["chapters"]:
        path = ROOT / name
        if not path.exists():
            raise FileNotFoundError(f"Missing chapter: {path}")
        text = path.read_text(encoding="utf-8").strip()
        parts.append(f"\n\n<div class=\"chapter-break\"></div>\n\n{text}\n")
    return "\n".join(parts) + "\n"


def normalize_math_for_pandoc(text: str) -> str:
    """Translate the guide's LaTeX delimiters for the bundled Pandoc 2.12.

    Pandoc 2.12 accepts ``$...$`` and ``$$...$$`` reliably, but its
    ``tex_math_single_backslash`` extension does not recognize delimiters split
    across lines.  The manuscript keeps ``\\(...\\)`` and ``\\[...\\]`` because
    they are unambiguous in prose, so the HTML path normalizes only text outside
    fenced code blocks and inline code spans.
    """
    normalized: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        marker_match = re.match(r"(```+|~~~+)", stripped)
        if marker_match:
            marker = marker_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
            normalized.append(line)
            continue
        if in_fence:
            normalized.append(line)
            continue
        if stripped.strip() in (r"\[", r"\]"):
            indent = line[: len(line) - len(stripped)]
            normalized.append(indent + "$$")
            continue
        parts = re.split(r"(`[^`]*`)", line)
        for index in range(0, len(parts), 2):
            parts[index] = re.sub(r"\\\((.+?)\\\)", r"$\1$", parts[index])
        normalized.append("".join(parts))
    return "\n".join(normalized) + ("\n" if text.endswith("\n") else "")


def build_html(combined_path: Path, output_path: Path) -> None:
    conda_exe = Path(os.environ["CONDA_EXE"]) if os.environ.get("CONDA_EXE") else Path()
    pandoc_candidates = [
        Path(shutil.which("pandoc") or ""),
        conda_exe.parent / "pandoc.exe" if conda_exe else Path(),
        Path.home() / "anaconda3" / "Scripts" / "pandoc.exe",
        Path.home() / "miniconda3" / "Scripts" / "pandoc.exe",
    ]
    pandoc = next((candidate for candidate in pandoc_candidates if candidate.is_file()), None)
    if pandoc is None:
        raise RuntimeError("pandoc was not found on PATH")
    cmd = [
        str(pandoc),
        "-",
        "--from=markdown+tex_math_dollars+pipe_tables+fenced_code_blocks",
        "--to=html5",
        "--standalone",
        "--self-contained",
        "--toc",
        "--toc-depth=3",
        "--mathml",
        f"--css={ROOT / 'guide.css'}",
        f"--metadata=title:{load_manifest()['title']}",
        f"--resource-path={ROOT}",
        "-o",
        str(output_path),
    ]
    source = normalize_math_for_pandoc(combined_path.read_text(encoding="utf-8"))
    subprocess.run(cmd, cwd=ROOT, input=source, text=True, encoding="utf-8", check=True)


def register_fonts() -> None:
    candidates = {
        "Guide": Path(r"C:\Windows\Fonts\Deng.ttf"),
        "GuideBold": Path(r"C:\Windows\Fonts\Dengb.ttf"),
        "GuideCode": Path(r"C:\Windows\Fonts\consola.ttf"),
    }
    fallbacks = {
        "Guide": Path(r"C:\Windows\Fonts\simhei.ttf"),
        "GuideBold": Path(r"C:\Windows\Fonts\simhei.ttf"),
        "GuideCode": Path(r"C:\Windows\Fonts\consola.ttf"),
    }
    for name, candidate in candidates.items():
        font_path = candidate if candidate.exists() else fallbacks[name]
        pdfmetrics.registerFont(TTFont(name, str(font_path), subfontIndex=0))


_MATH_MAP = {
    r"\gamma": "γ",
    r"\lambda": "λ",
    r"\theta": "θ",
    r"\pi": "π",
    r"\tau": "τ",
    r"\epsilon": "ε",
    r"\alpha": "α",
    r"\beta": "β",
    r"\delta": "δ",
    r"\nabla": "∇",
    r"\mathbb{E}": "E",
    r"\sum": "Σ",
    r"\approx": "≈",
    r"\ge": "≥",
    r"\le": "≤",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\cdot": "·",
    r"\times": "×",
    r"\infty": "∞",
}


def clean_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="GuideCode">\1</font>', text)

    def math_sub(match: re.Match[str]) -> str:
        value = match.group(1)
        for src, dst in _MATH_MAP.items():
            value = value.replace(src, dst)
        value = value.replace(r"\mid", "|").replace(r"\text", "")
        value = value.replace(r"\operatorname", "").replace(r"\mathrm", "")
        value = value.replace(r"\hat", "").replace(r"\left", "").replace(r"\right", "")
        value = re.sub(r"\\([A-Za-z]+)", r"\1", value)
        value = value.replace("{", "").replace("}", "")
        return f'<font name="GuideCode">{value}</font>'

    text = re.sub(r"\\\((.+?)\\\)", math_sub, text)
    return re.sub(r"\$([^$]+)\$", math_sub, text)


def clean_formula(text: str) -> str:
    """Convert a display-math block to readable, font-safe PDF text.

    HTML keeps full MathML through Pandoc.  The PDF path deliberately uses a
    conservative text representation so formulas stay searchable and never
    depend on a TeX installation.
    """
    value = " ".join(part.strip() for part in text.splitlines())
    for src, dst in _MATH_MAP.items():
        value = value.replace(src, dst)
    replacements = {
        r"\operatorname": "",
        r"\mathrm": "",
        r"\mathbf": "",
        r"\boldsymbol": "",
        r"\mathcal": "",
        r"\mathbb": "",
        r"\hat": "",
        r"\text": "",
        r"\begin{cases}": "",
        r"\end{cases}": "",
        r"\begin{bmatrix}": "[",
        r"\end{bmatrix}": "]",
        r"\begin{aligned}": "",
        r"\end{aligned}": "",
        r"\left": "",
        r"\right": "",
        r"\quad": "  ",
        r"\qquad": "    ",
        r"\mid": "|",
        r"\Vert": "‖",
        r"\lVert": "‖",
        r"\rVert": "‖",
        r"\sqrt": "√",
        r"\frac": "frac",
        r"\\": " ; ",
        "&": " ",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"\\([A-Za-z]+)", r"\1", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\s+", " ", value).strip()
    return html.escape(value)


class GuideDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, title: str):
        super().__init__(
            filename,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=19 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="Reinforce Tactics project",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._header_footer))
        self._heading_id = 0

    def beforeDocument(self) -> None:
        # ``multiBuild`` performs multiple passes to resolve the TOC.  Heading
        # bookmark keys must be identical on every pass.
        self._heading_id = 0

    def _header_footer(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Guide", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        if doc.page > 1:
            canvas.drawString(self.leftMargin, 10 * mm, "Reinforce Tactics 策略类强化学习学习指南")
            canvas.drawRightString(A4[0] - self.rightMargin, 10 * mm, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if isinstance(flowable, Paragraph) and flowable.style.name in {"H1", "H2", "H3"}:
            level = {"H1": 0, "H2": 1, "H3": 2}[flowable.style.name]
            text = flowable.getPlainText()
            key = f"heading-{self._heading_id}"
            self._heading_id += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
            self.notify("TOCEntry", (level, text, self.page, key))


def paragraph_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Guide",
            fontSize=10.2,
            leading=17,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
            wordWrap="CJK",
            textColor=colors.HexColor("#172033"),
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="GuideBold",
            fontSize=20,
            leading=28,
            textColor=colors.HexColor("#173F5F"),
            spaceBefore=10,
            spaceAfter=12,
            wordWrap="CJK",
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="GuideBold",
            fontSize=15,
            leading=22,
            textColor=colors.HexColor("#1F5D8F"),
            spaceBefore=12,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="GuideBold",
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#244D69"),
            spaceBefore=9,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Guide",
            fontSize=9.5,
            leading=15,
            leftIndent=10 * mm,
            rightIndent=5 * mm,
            borderColor=colors.HexColor("#1F5D8F"),
            borderWidth=1,
            borderPadding=6,
            backColor=colors.HexColor("#EAF3F9"),
            wordWrap="CJK",
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="GuideCode",
            fontSize=7.2,
            leading=10,
            leftIndent=3 * mm,
            rightIndent=3 * mm,
            borderPadding=5,
            backColor=colors.HexColor("#F3F4F6"),
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Guide",
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#5F6B7A"),
            wordWrap="CJK",
        ),
        "Math": ParagraphStyle(
            "Math",
            parent=base["BodyText"],
            fontName="Guide",
            fontSize=9.2,
            leading=15,
            alignment=TA_CENTER,
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            spaceBefore=3,
            spaceAfter=6,
            wordWrap="CJK",
            textColor=colors.HexColor("#172033"),
        ),
    }


def add_markdown_table(story: list, rows: list[list[str]], styles: dict[str, ParagraphStyle], doc_width: float) -> None:
    if len(rows) < 2:
        return
    if all(re.fullmatch(r"\s*:?-+:?\s*", cell or "-") for cell in rows[1]):
        rows = [rows[0], *rows[2:]]
    if not rows:
        return
    columns = max(len(row) for row in rows)
    normalized = [row + [""] * (columns - len(row)) for row in rows]
    data = [[Paragraph(clean_inline(cell.strip()), styles["Body"]) for cell in row] for row in normalized]
    table = Table(data, colWidths=[doc_width / columns] * columns, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "GuideBold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF3F9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#173F5F")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend([table, Spacer(1, 4 * mm)])


def markdown_to_story(text: str, styles: dict[str, ParagraphStyle], doc_width: float) -> list:
    story: list = []
    lines = text.splitlines()
    i = 0
    in_code = False
    code_lines: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(clean_inline(" ".join(part.strip() for part in paragraph)), styles["Body"]))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                story.extend([Preformatted("\n".join(code_lines), styles["Code"]), Spacer(1, 3 * mm)])
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            table_rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_rows.append([cell for cell in lines[i].strip().strip("|").split("|")])
                i += 1
            add_markdown_table(story, table_rows, styles, doc_width)
            continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            caption, rel = image_match.groups()
            image_path = (ROOT / rel).resolve()
            if image_path.exists():
                img = Image(str(image_path))
                max_w, max_h = doc_width * 0.9, 165 * mm
                scale = min(max_w / img.imageWidth, max_h / img.imageHeight, 1.0)
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                story.append(img)
                if caption:
                    story.append(Paragraph(clean_inline(caption), styles["Caption"]))
                story.append(Spacer(1, 4 * mm))
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            if level == 1 and story:
                story.append(PageBreak())
            style = styles["H1" if level == 1 else "H2" if level == 2 else "H3"]
            story.append(Paragraph(clean_inline(heading.group(2)), style))
            i += 1
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            story.append(Paragraph(clean_inline(stripped.lstrip("> ")), styles["Quote"]))
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            item = re.sub(r"^[-*]\s+", "", stripped)
            story.append(Paragraph("• " + clean_inline(item), styles["Body"]))
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            story.append(Paragraph(clean_inline(stripped), styles["Body"]))
            i += 1
            continue
        if stripped == r"\[":
            flush_paragraph()
            formula_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != r"\]":
                formula_lines.append(lines[i])
                i += 1
            story.append(Paragraph(clean_formula("\n".join(formula_lines)), styles["Math"]))
            i += 1
            continue
        if stripped == r"\]":
            flush_paragraph()
            i += 1
            continue
        if stripped == "---" or stripped.startswith("<div"):
            flush_paragraph()
            story.append(Spacer(1, 3 * mm))
            i += 1
            continue
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        paragraph.append(line)
        i += 1
    flush_paragraph()
    return story


def build_pdf(manifest: dict, output_path: Path) -> None:
    register_fonts()
    styles = paragraph_styles()
    doc = GuideDocTemplate(str(output_path), manifest["title"])
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="GuideBold",
            fontSize=10,
            leading=16,
            leftIndent=0,
            firstLineIndent=0,
            textColor=colors.HexColor("#173F5F"),
        ),
        ParagraphStyle("TOC2", fontName="Guide", fontSize=9, leading=14, leftIndent=12, firstLineIndent=0),
        ParagraphStyle("TOC3", fontName="Guide", fontSize=8, leading=12, leftIndent=24, firstLineIndent=0),
    ]
    story = [
        Spacer(1, 32 * mm),
        Paragraph(manifest["title"], ParagraphStyle("Cover", parent=styles["H1"], fontSize=26, leading=38, alignment=TA_CENTER)),
        Spacer(1, 8 * mm),
        Paragraph(manifest["subtitle"], ParagraphStyle("Subtitle", parent=styles["H2"], fontSize=15, alignment=TA_CENTER)),
        Spacer(1, 20 * mm),
        Paragraph(
            f"版本 {manifest['version']}　基准日期 {manifest['baseline_date']}",
            ParagraphStyle("Meta", parent=styles["Body"], alignment=TA_CENTER, textColor=colors.HexColor("#5F6B7A")),
        ),
        PageBreak(),
        Paragraph("目录", styles["H1"]),
        toc,
        PageBreak(),
    ]
    for chapter in manifest["chapters"]:
        story.extend(markdown_to_story((ROOT / chapter).read_text(encoding="utf-8"), styles, doc.width))
    doc.multiBuild(story)


def build_pdf_from_html(html_path: Path, output_path: Path) -> None:
    """Print the MathML HTML with a Chromium-family browser.

    The browser engine preserves real mathematical layout in the PDF,
    including subscripts, superscripts, fractions and radicals.  It also
    supplies font fallback for Chinese text inside preformatted diagrams.
    """
    node_candidates = [
        Path(shutil.which("node") or ""),
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / "node.exe",
        Path(r"C:\Program Files\nodejs\node.exe"),
    ]
    node = next((candidate for candidate in node_candidates if candidate.is_file()), None)
    if node is None:
        raise RuntimeError("Node.js was not found; it is required for browser PDF rendering")

    module_candidates = [
        REPO / "node_modules",
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules",
    ]
    module_dirs = [path for path in module_candidates if (path / "playwright").is_dir()]
    existing_node_path = os.environ.get("NODE_PATH")
    if existing_node_path:
        module_dirs.extend(Path(item) for item in existing_node_path.split(os.pathsep) if item)
    if not any((path / "playwright").is_dir() for path in module_dirs):
        raise RuntimeError(
            "Playwright was not found; install it in node_modules or provide its directory through NODE_PATH"
        )

    configured_browser = os.environ.get("GUIDE_BROWSER")
    browser_candidates = [
        Path(configured_browser) if configured_browser else Path(),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    browser = next((candidate for candidate in browser_candidates if candidate.is_file()), None)

    env = os.environ.copy()
    env["NODE_PATH"] = os.pathsep.join(str(path) for path in module_dirs)
    command = [
        str(node),
        str(ROOT / "tools" / "render_pdf.cjs"),
        str(html_path),
        str(output_path),
    ]
    if browser is not None:
        command.append(str(browser))
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> None:
    manifest = load_manifest()
    EXPORT.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    combined_path = EXPORT / "Reinforce-Tactics-RL-Learning-Guide-combined.md"
    html_path = EXPORT / "Reinforce-Tactics-RL-Learning-Guide.html"
    pdf_path = PDF_DIR / "Reinforce-Tactics-RL-Learning-Guide-v2.pdf"

    combined_path.write_text(combined_markdown(manifest), encoding="utf-8")
    build_html(combined_path, html_path)
    build_pdf_from_html(html_path, pdf_path)
    print(f"Combined Markdown: {combined_path}")
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")


if __name__ == "__main__":
    main()
