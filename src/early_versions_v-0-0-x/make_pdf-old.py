import sys
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Set font path relative to script location
script_dir = os.path.dirname(__file__)
font_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "fonts"))
font_path = os.path.join(font_dir, "DejaVuSans.ttf")
bold_font_path = os.path.join(font_dir, "DejaVuSans-Bold.ttf")

# Check fonts exist
if not os.path.exists(font_path):
    raise FileNotFoundError(f"Regular font not found at {font_path}")
if not os.path.exists(bold_font_path):
    raise FileNotFoundError(f"Bold font not found at {bold_font_path}")

class PDF(FPDF):
    def __init__(self, title_text="Untitled"):
        super().__init__()
        self.title_text = title_text

        # Add Unicode fonts using full paths
        self.add_font("DejaVu", "", font_path)
        self.add_font("DejaVu", "B", bold_font_path)

        # Set base font
        self.set_font("DejaVu", "", 12)

    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, self.title_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

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

            elif stripped == "":
                self.ln(5)  # Paragraph break

            else:
                self.multi_cell(0, 10, line)

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
    print(f"PDF created: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_pdf.py /path/to/input_file.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: File not found — {input_file}")
        sys.exit(1)

    create_pdf_from_file(input_file)
