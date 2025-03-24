from fpdf import FPDF

# Define the text content for the PDF
title = "The Book Title"
author = "Me"
content = """
[Full story content from all parts combined goes here. Since we already wrote the parts we can now combine them.]

...
"""

# Create PDF document
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font("Arial", 'B', 14)
        self.ln(10)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("Times", '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_title(title)
pdf.set_author(author)

# Add content
pdf.chapter_body(content)

# Save the PDF
output_path = "/kdp/pdfs/Title_Here.pdf"
pdf.output(output_path)

output_path
