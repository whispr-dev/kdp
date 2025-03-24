import sys
import os
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Set font path relative to script location
script_dir = os.path.dirname(__file__)
font_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "fonts"))
font_path = os.path.join(font_dir, "DejaVuSans.ttf")
bold_font_path = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
italic_font_path = os.path.join(font_dir, "DejaVuSans-Oblique.ttf")

# Check fonts exist
if not os.path.exists(font_path):
    raise FileNotFoundError(f"Regular font not found at {font_path}")
if not os.path.exists(bold_font_path):
    raise FileNotFoundError(f"Bold font not found at {bold_font_path}")
if not os.path.exists(italic_font_path):
    raise FileNotFoundError(f"Italic font not found at {italic_font_path}")

class PDF(FPDF):
    def __init__(self, title_text="Untitled"):
        super().__init__()
        self.title_text = title_text
        self.add_font("DejaVu", "", font_path)
        self.add_font("DejaVu", "B", bold_font_path)
        self.add_font("DejaVu", "I", italic_font_path)
        self.set_font("DejaVu", "", 12)

    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, self.title_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def render_inline_formatting(self, text):
        """Replace *italic*, **bold** with styled text in PDF"""
        bold_pattern = r"\*\*(.+?)\*\*"
        italic_pattern = r"\*(.+?)\*"

        parts = []
        pos = 0

        # Handle bold first
        for match in re.finditer(bold_pattern, text):
            if match.start() > pos:
                parts.append(("normal", text[pos:match.start()]))
            parts.append(("bold", match.group(1)))
            pos = match.end()

        text_after_bold = text[pos:] if pos < len(text) else ""

        final_parts = []
        pos = 0
        for match in re.finditer(italic_pattern, text_after_bold):
            if match.start() > pos:
                final_parts.append(("normal", text_after_bold[pos:match.start()]))
            final_parts.append(("italic", match.group(1)))
            pos = match.end()
        if pos < len(text_after_bold):
            final_parts.append(("normal", text_after_bold[pos:]))

        if not parts:
            parts = [("normal", text)]

        combined = []
        for style, segment in parts:
            if style == "normal":
                combined.extend(final_parts if final_parts else [("normal", segment)])
            else:
                combined.append((style, segment))

        return combined

    def write_styled_line(self, parts, font_size=12):
        for style, text in parts:
            if style == "bold":
                self.set_font("DejaVu", "B", font_size)
            elif style == "italic":
                self.set_font("DejaVu", "", font_size)
                self.set_text_color(80, 80, 80)
            else:
                self.set_font("DejaVu", "", font_size)
                self.set_text_color(0, 0, 0)

            self.write(10, text)
        self.ln(10)
        self.set_text_color(0, 0, 0)  # Reset to default

    def chapter_body(self, body):
        self.set_font("DejaVu", "", 12)
        lines = body.splitlines()

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("### "):
                self.set_font("DejaVu", "B", 12)
                self.ln(4)
                self.multi_cell(0, 8, stripped[4:])
                self.ln(1)
                self.set_font("DejaVu", "", 12)

            elif stripped.startswith("## "):
                self.set_font("DejaVu", "B", 14)
                self.ln(6)
                self.multi_cell(0, 10, stripped[3:])
                self.ln(2)
                self.set_font("DejaVu", "", 12)

            elif stripped.startswith("# "):
                self.set_font("DejaVu", "B", 16)
                self.ln(10)
                self.multi_cell(0, 12, stripped[2:], align="C")
                self.ln(4)
                self.set_font("DejaVu", "", 12)

            elif stripped.startswith("> "):
                self.set_text_color(100, 100, 100)
                self.set_font("DejaVu", "I", 12)
                self.multi_cell(0, 10, stripped[2:])
                self.set_font("DejaVu", "", 12)
                self.set_text_color(0, 0, 0)

            elif stripped.startswith("- "):
                parts = self.render_inline_formatting(stripped[2:])
                self.cell(5)  # Indent
                self.write(10, u"\u2022 ")  # Bullet character
                self.write_styled_line(parts)

            elif stripped == "---":
                self.ln(4)
                self.set_draw_color(100, 100, 100)
                self.set_line_width(0.4)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.ln(6)

            elif stripped == "":
                self.ln(5)

            else:
                parts = self.render_inline_formatting(line)
                self.write_styled_line(parts)

def create_pdf_from_file(input_path):
    base_name = os.path.basename(input_path)
    name_no_ext = os.path.splitext(base_name)[0]

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pdf = PDF(title_text=name_no_ext)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_title(name_no_ext)
    pdf.set_author("Written for my fren")

    pdf.chapter_body(content)

    output_path = os.path.splitext(input_path)[0] + ".pdf"
    pdf.output(output_path)
    print(f"✅ PDF created: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_pdf.py \"path/to/your/file.md\"")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: File not found — {input_file}")
        print("💡 Hint: If the path has spaces, wrap it in quotes!")
        sys.exit(1)

    create_pdf_from_file(input_file)
