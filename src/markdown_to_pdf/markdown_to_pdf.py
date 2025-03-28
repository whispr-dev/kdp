# markdown_to_pdf.py
# See README.md for full instructions.

# markdown_to_pdf.py 
# -(PyInstaller-compatible version) 
# -(DejaVuSerif version with full font family support)
# -(patched with hardened multi_cell)
import os
import sys
import re
import tkinter as tk
from tkinter import filedialog
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image
import markdown2
from ebooklib import epub
import platform
import subprocess
import textwrap

DEFAULT_TITLE = "Untitled Manuscript"
DEFAULT_AUTHOR = "Ano Nymous"
DEFAULT_FONT_NAME = "DejaVuSerif"

if getattr(sys, 'frozen', False):
    # When running from PyInstaller bundle
    BASE_PATH = sys._MEIPASS
else:
    # When running from source
    BASE_PATH = os.path.dirname(__file__)

font_dir = os.path.join(BASE_PATH, "fonts")
font_regular = os.path.join(font_dir, "DejaVuSerif.ttf")
font_bold = os.path.join(font_dir, "DejaVuSerif-Bold.ttf")
font_italic = os.path.join(font_dir, "DejaVuSerif-Italic.ttf")
font_bolditalic = os.path.join(font_dir, "DejaVuSerif-BoldItalic.ttf")
font_mono = os.path.join(font_dir, "DejaVuSansMono.ttf")

for path in [font_regular, font_bold, font_italic, font_bolditalic, font_mono]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required font: {path}")

class PDF(FPDF):
    def __init__(self, title, author, logo_path=None, cover_image_path=None):
        super().__init__()
        self.title = title or DEFAULT_TITLE
        self.author = author or DEFAULT_AUTHOR
        self.logo_path = logo_path
        self.cover_image_path = cover_image_path
        self.toc = []
        self.chapter_counter = 0
        self.subchapter_counter = 0

        self.add_font(DEFAULT_FONT_NAME, "", font_regular)
        self.add_font(DEFAULT_FONT_NAME, "B", font_bold)
        self.add_font(DEFAULT_FONT_NAME, "I", font_italic)
        self.add_font(DEFAULT_FONT_NAME, "BI", font_bolditalic)
        self.add_font("DejaVuMono", "", font_mono)

        self.set_auto_page_break(auto=True, margin=15)

    def add_cover_page(self):
        self.add_page()
        if self.cover_image_path and os.path.exists(self.cover_image_path):
            self.image(self.cover_image_path, x=0, y=0, w=self.w)
            self.ln(self.h / 2)
        else:
            self.ln(self.h / 3)

        self.set_font(DEFAULT_FONT_NAME, "B", 28)
        self.cell(0, 20, self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        self.ln(10)
        self.set_font(DEFAULT_FONT_NAME, "I", 18)
        self.cell(0, 10, f"by {self.author}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        if self.logo_path:
            logo_full = os.path.join(BASE_PATH, self.logo_path) if not os.path.isabs(self.logo_path) else self.logo_path
            if os.path.exists(logo_full):
                self.image(logo_full, x=self.w - 50, y=self.h - 40, w=30)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font(DEFAULT_FONT_NAME, "", 10)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_chapter(self, title):
        self.chapter_counter += 1
        self.subchapter_counter = 0
        numbered_title = f"Chapter {self.chapter_counter}: {title}"
        self.set_font(DEFAULT_FONT_NAME, "B", 16)
        self.ln(10)
        self.cell(0, 10, numbered_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.toc.append((numbered_title, self.page_no()))

    def add_subchapter(self, title):
        self.subchapter_counter += 1
        numbered_title = f"{self.chapter_counter}.{self.subchapter_counter} {title}"
        self.set_font(DEFAULT_FONT_NAME, "B", 14)
        self.cell(0, 8, numbered_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def add_toc_page(self):
        self.add_page()
        self.set_font(DEFAULT_FONT_NAME, "B", 16)
        self.cell(0, 10, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)
        self.set_font(DEFAULT_FONT_NAME, "", 12)
        for title, page in self.toc:
            self.cell(0, 8, f"{title} .......... {page}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

def generate_epub(title, author, markdown_text, output_path):
    book = epub.EpubBook()
    book.set_identifier("id123456")
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)

    html = markdown2.markdown(markdown_text)
    chapter = epub.EpubHtml(title=title, file_name="chap_01.xhtml", lang="en")
    chapter.content = html
    book.add_item(chapter)
    book.toc = (epub.Link("chap_01.xhtml", title, "chap1"),)
    book.spine = ["nav", chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(output_path, book)

def generate_html(markdown_text, output_path):
    html = markdown2.markdown(markdown_text)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"<html><head><meta charset='utf-8'><title>Document</title></head><body>{html}</body></html>")

def pick_markdown_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")],
        title="Select your markdown file",
    )
    return file_path

def safe_multicell(pdf, width, height, text):
    try:
        pdf.multi_cell(width, height, text)
    except Exception as e:
        print(f"[WARN] Failed to render text, attempting forced wrap: {e}")
        # Calculate max chars per line based on width of page and average char width
        try:
            max_width = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.set_font(DEFAULT_FONT_NAME, "", 12)
            avg_char_width = pdf.get_string_width("M")  # Safe average
            max_chars = max(int(max_width / avg_char_width), 20)

            wrapped = textwrap.fill(text, width=max_chars, break_long_words=True, replace_whitespace=False)
            pdf.multi_cell(0, height, wrapped)
        except Exception as final_fail:
            print(f"[FAIL] Still couldn't render. Skipping line: {final_fail}")
            pdf.ln(4)

def main():
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        input_path = pick_markdown_file()

    if not input_path or not os.path.exists(input_path):
        print("❌ File not found.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    title, author, cover, logo = DEFAULT_TITLE, DEFAULT_AUTHOR, None, None
    if content.startswith("---"):
        lines = content.splitlines()
        for line in lines:
            if line.strip() == "---":
                break
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip()
            if line.startswith("author:"):
                author = line.split(":", 1)[1].strip()
            if line.startswith("cover:"):
                cover = line.split(":", 1)[1].strip()
            if line.startswith("logo:"):
                logo = line.split(":", 1)[1].strip()

    pdf = PDF(title=title, author=author, logo_path=logo, cover_image_path=cover)
    pdf.add_cover_page()
    pdf.add_toc_page()

    for line in content.splitlines():
        if line.startswith("# "):
            pdf.add_chapter(line[2:].strip())
        elif line.startswith("## "):
            pdf.add_subchapter(line[3:].strip())
        elif line.strip():
            pdf.set_font(DEFAULT_FONT_NAME, "", 12)
            safe_multicell(pdf, 0, 8, line)
        else:
            pdf.ln(4)

    pdf_path = os.path.splitext(input_path)[0] + ".pdf"
    pdf.output(pdf_path)
    print(f"✅ PDF created: {pdf_path}")

    epub_path = os.path.splitext(input_path)[0] + ".epub"
    generate_epub(title, author, content, epub_path)
    print(f"✅ EPUB created: {epub_path}")

    try:
        if platform.system() == "Windows":
            os.startfile(epub_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", epub_path])
        else:
            subprocess.run(["xdg-open", epub_path])
    except Exception as e:
        print(f"⚠️ Could not open EPUB automatically: {e}")

    html_path = os.path.splitext(input_path)[0] + ".html"
    generate_html(content, html_path)
    print(f"✅ HTML created: {html_path}")

if __name__ == "__main__":
    main()