"""Render POST.md to a PDF. Plain document typography, no decoration."""
import pathlib, re
import markdown
from weasyprint import HTML, CSS

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "POST.md"
OUT = ROOT / "output" / "AI Debt and the Treasury Curve.pdf"

CSS_TEXT = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm;
        @bottom-center { content: counter(page); font-family: Georgia, serif;
                         font-size: 9pt; color: #666; } }
body { font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt;
       line-height: 1.55; color: #111; }
h1 { font-size: 19pt; font-weight: normal; margin: 0 0 2mm 0; line-height: 1.25; }
h2 { font-size: 12.5pt; font-weight: bold; margin: 9mm 0 2.5mm 0;
     page-break-after: avoid; }
p { orphans: 3; widows: 3; }
p { margin: 0 0 3.2mm 0; text-align: left; }
/* byline */
body > p:first-of-type { color: #555; font-size: 9.5pt; margin-bottom: 7mm; }
ul { margin: 0 0 3.5mm 0; padding-left: 5mm; }
li { margin-bottom: 1.6mm; }
table { border-collapse: collapse; margin: 4mm 0 5mm 0; font-size: 9.5pt;
        page-break-inside: avoid; }
/* keep a table with the sentence that introduces it, but not glued to a figure */
p + table { page-break-before: avoid; }
th, td { border-bottom: 0.4pt solid #ccc; padding: 1.6mm 4mm 1.6mm 0;
         text-align: left; }
th { border-bottom: 0.7pt solid #555; font-weight: bold; }
blockquote { margin: 4mm 0 4mm 4mm; padding-left: 4mm;
             border-left: 1.2pt solid #bbb; color: #333; font-size: 9.8pt; }
blockquote p { margin: 0; }
blockquote p + p { margin-top: 2.2mm; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 9pt; }
pre { background: #f6f6f6; padding: 3mm 4mm; font-size: 8.8pt;
      line-height: 1.4; margin: 3.5mm 0 4.5mm 0; page-break-inside: avoid;
      white-space: pre-wrap; }
img { max-width: 100%; max-height: 78mm; display: block;
      margin: 2mm auto 0 auto; }
figure { margin: 4mm 0 5mm 0; page-break-inside: avoid; }
figure p.cap { font-style: italic; margin: 0 0 1.5mm 0; font-size: 9.8pt; }
em { font-style: italic; }
/* figure captions are italic paragraphs immediately before an image */
a { color: #111; text-decoration: underline; }
"""


def main():
    text = SRC.read_text()
    # strip the h1 out of the flow so the title sits tight with the byline
    html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    # Keep each italic "Figure N." caption glued to the image that follows it,
    # otherwise weasyprint orphans the caption at a page break.
    html_body = re.sub(
        r"<p><em>(Figure \d+\..*?)</em></p>\s*<p>(<img[^>]*/?>)</p>",
        r'<figure><p class="cap">\1</p>\2</figure>',
        html_body, flags=re.S)
    html = f"<html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(ROOT)).write_pdf(OUT, stylesheets=[CSS(string=CSS_TEXT)])
    print("wrote", OUT, f"({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
