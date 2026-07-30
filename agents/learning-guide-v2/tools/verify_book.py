"""Verify guide structure, links, HTML, and PDF."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PDF = REPO / "output" / "pdf" / "Reinforce-Tactics-RL-Learning-Guide-v2.pdf"
HTML = ROOT / "export" / "Reinforce-Tactics-RL-Learning-Guide.html"
REQUIRED_ALGORITHMS = [
    "DQN",
    "A2C",
    "PPO",
    "MaskablePPO",
    "Bootstrap",
    "行为克隆",
    "自对弈",
    "Feudal",
    "MCTS",
    "AlphaZero",
]


def local_links(text: str) -> list[str]:
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
    return [link.split("#", 1)[0] for link in links if link and not re.match(r"^(https?|mailto):", link)]


def main() -> None:
    manifest = json.loads((ROOT / "book.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    all_text: list[str] = []

    if len(manifest["chapters"]) != 33:
        errors.append(f"Expected 28 chapters + 5 appendices, got {len(manifest['chapters'])} files")

    for name in manifest["chapters"]:
        path = ROOT / name
        if not path.exists():
            errors.append(f"Missing chapter: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        all_text.append(text)
        if not re.search(r"^# ", text, flags=re.MULTILINE):
            errors.append(f"No H1 heading: {name}")
        for link in local_links(text):
            target = (path.parent / link).resolve()
            if not target.exists():
                errors.append(f"Broken link in {name}: {link}")
        for forbidden in ("../learning-guide/", "../algorithms/", "../source-analysis/", "../../docs/"):
            if forbidden in text:
                errors.append(f"External knowledge dependency in {name}: {forbidden}")

    for name in ("README.md", "VALIDATION.md"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        for link in local_links(text):
            target = (path.parent / link).resolve()
            if not target.exists():
                errors.append(f"Broken link in {name}: {link}")

    corpus = "\n".join(all_text)
    for algorithm in REQUIRED_ALGORITHMS:
        if algorithm not in corpus:
            errors.append(f"Missing required algorithm coverage: {algorithm}")
    if re.search(r"参数名以.*help.*为准|TODO|TBD|待补充|占位", corpus, flags=re.IGNORECASE):
        errors.append("Placeholder or ambiguous command wording remains in manuscript")

    html_text = HTML.read_text(encoding="utf-8") if HTML.exists() else ""
    math_count = html_text.count("<math")
    if not HTML.exists() or HTML.stat().st_size < 100_000:
        errors.append("HTML output is missing or unexpectedly small")
    elif math_count < 500:
        errors.append(f"HTML MathML coverage is unexpectedly low: {math_count}")
    if "<p>[ G_t" in html_text or r"\theta" in re.sub(
        r"<annotation\b[^>]*>.*?</annotation>", "", html_text, flags=re.DOTALL
    ):
        errors.append("Rendered HTML still contains degraded LaTeX formula text")
    if not PDF.exists() or PDF.stat().st_size < 100_000:
        errors.append("PDF output is missing or unexpectedly small")
    else:
        reader = PdfReader(str(PDF))
        if len(reader.pages) < 80:
            errors.append(f"PDF unexpectedly short: {len(reader.pages)} pages")
        if not reader.outline:
            errors.append("PDF has no outline/bookmarks")
        with pdfplumber.open(str(PDF)) as document:
            sample_pages = [0, min(5, len(document.pages) - 1), len(document.pages) - 1]
            extracted = "\n".join(document.pages[index].extract_text() or "" for index in sample_pages)
            if "Reinforce Tactics" not in extracted or len(extracted) < 500:
                errors.append("PDF text extraction check failed")
            full_text = "\n".join(page.extract_text() or "" for page in document.pages)
            for expected in (
                "conda activate reinforce-tactics",
                "创建单位",
                "移动单位",
                "结束回合",
            ):
                if expected not in full_text:
                    errors.append(f"PDF is missing expected wrapped/CJK content: {expected}")
            if re.search(r"\\(?:theta|gamma|frac|mathbb|operatorname)|_\{", full_text):
                errors.append("PDF still contains raw LaTeX commands instead of typeset mathematics")

    if PDF.exists():
        pdfinfo = shutil.which("pdfinfo") or shutil.which("pdfinfo.cmd")
        if not pdfinfo:
            errors.append("pdfinfo executable was not found")
        else:
            pdfinfo_path = Path(pdfinfo)
            bundled_exe = (
                pdfinfo_path.parents[2] / "native" / "poppler" / "Library" / "bin" / "pdfinfo.exe"
                if len(pdfinfo_path.parents) >= 3
                else Path()
            )
            if bundled_exe.exists():
                command = [str(bundled_exe), str(PDF)]
            elif pdfinfo.lower().endswith(".cmd"):
                command = ["cmd", "/c", pdfinfo, str(PDF)]
            else:
                command = [pdfinfo, str(PDF)]
            info = subprocess.run(command, capture_output=True, text=True, errors="replace", check=False)
            if info.returncode != 0:
                errors.append(f"pdfinfo failed: {info.stderr.strip()}")
            elif not re.search(r"^Tagged:\s+yes\s*$", info.stdout, flags=re.MULTILINE | re.IGNORECASE):
                errors.append("PDF is not tagged")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        raise SystemExit(1)
    print(f"Verified {len(manifest['chapters'])} manuscript files")
    print(f"HTML: {HTML.stat().st_size:,} bytes, {math_count} MathML formulas")
    print(f"PDF: {len(PdfReader(str(PDF)).pages)} pages, {PDF.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
