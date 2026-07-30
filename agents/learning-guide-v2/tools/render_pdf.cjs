"use strict";

const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright");

async function main() {
  const [htmlPath, pdfPath, browserPath] = process.argv.slice(2);
  if (!htmlPath || !pdfPath) {
    throw new Error("Usage: node render_pdf.cjs <input.html> <output.pdf> [browser.exe]");
  }

  const executablePath =
    browserPath && fs.existsSync(browserPath)
      ? browserPath
      : chromium.executablePath();
  if (!fs.existsSync(executablePath)) {
    throw new Error(
      `Chromium-family browser not found: ${executablePath}. ` +
        "Set GUIDE_BROWSER to Chrome or Edge."
    );
  }

  fs.mkdirSync(path.dirname(pdfPath), { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.resolve(htmlPath)).href, {
      waitUntil: "load",
    });
    await page.emulateMedia({ media: "print" });

    // Pandoc places its generated TOC before the manuscript's own cover
    // elements.  Keep one formal cover, then the TOC, and hide the duplicate
    // cover content before the first chapter.
    await page.evaluate(() => {
      document.documentElement.lang = "zh-CN";
      const toc = document.querySelector("#TOC");
      if (!toc) return;
      let element = toc.nextElementSibling;
      while (element && !element.classList.contains("chapter-break")) {
        element.classList.add("pdf-duplicate-cover");
        element = element.nextElementSibling;
      }
    });

    await page.addStyleTag({
      content: `
        @media print {
          @page { size: A4; }
          #title-block-header {
            min-height: 245mm;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            break-after: page;
          }
          #title-block-header h1 {
            max-width: 165mm;
            margin: 0;
            padding: 0;
            border: 0;
            font-size: 28pt;
            line-height: 1.45;
            page-break-before: auto;
          }
          #TOC::before {
            content: "目录";
            display: block;
            margin: 0 0 1.2rem;
            color: #173f5f;
            font-size: 22pt;
            font-weight: 700;
          }
          #TOC {
            border: 0;
            background: #fff;
          }
          #TOC a {
            color: #172033;
            text-decoration: none;
          }
          .pdf-duplicate-cover,
          .chapter-break {
            display: none !important;
          }
          pre {
            white-space: pre-wrap !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
            overflow-x: visible !important;
          }
          pre code,
          pre code span {
            padding: 0 !important;
            color: inherit !important;
            background: transparent !important;
          }
          div.sourceCode {
            overflow: visible !important;
          }
          pre > code.sourceCode {
            position: static !important;
            white-space: pre-wrap !important;
          }
          pre > code.sourceCode > span {
            display: block !important;
            padding-left: 0 !important;
            text-indent: 0 !important;
            overflow-wrap: anywhere !important;
          }
          pre > code.sourceCode > span > a:first-child::before {
            display: none !important;
          }
        }
      `,
    });

    await page.evaluate(async () => {
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }
    });

    await page.pdf({
      path: path.resolve(pdfPath),
      format: "A4",
      printBackground: true,
      margin: {
        top: "18mm",
        bottom: "18mm",
        left: "16mm",
        right: "16mm",
      },
      displayHeaderFooter: true,
      headerTemplate:
        '<div style="width:100%;font:8px Arial,sans-serif;color:#7a8796;text-align:center;">' +
        "Reinforce Tactics - Reinforcement Learning Guide</div>",
      footerTemplate:
        '<div style="width:100%;font:8px Arial,sans-serif;color:#7a8796;' +
        'padding:0 16mm;display:flex;justify-content:space-between;">' +
        '<span>Reinforce Tactics</span><span><span class="pageNumber"></span> / ' +
        '<span class="totalPages"></span></span></div>',
      tagged: true,
      outline: true,
    });
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
