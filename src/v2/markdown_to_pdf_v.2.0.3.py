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

class PDF(FPDF):
    def __init__(self, title, author, logo_path=None, cover_image_path=None):
        super().__init__()
        self.title = title
        self.author = author
        self.logo_path = logo_path
        self.cover_image_path = cover_image_path
        self.set_auto_page_break(auto=True, margin=15)
        self.chapter_titles = []
        self.subchapter_titles = []

        self.add_font(DEFAULT_FONT_NAME, "", font_regular)
        self.add_font(DEFAULT_FONT_NAME, "B", font_bold)
        self.add_font(DEFAULT_FONT_NAME, "I", font_italic)
        self.add_font(DEFAULT_FONT_NAME, "BI", font_bolditalic)
        self.add_font("DejaVuSansMono", "", font_mono)

    def add_cover_page(self):
        self.add_page()
        self.set_margin(0)
        self.set_font(DEFAULT_FONT_NAME, "", 16)
        if self.cover_image_path and os.path.exists(self.cover_image_path):
            try:
                # Add a black rectangle for the cover
                self.set_fill_color(0, 0, 0)
                self.rect(0, 0, self.w, self.h, 'F')
                # Load the cover image
                cover_img = Image.open(self.cover_image_path)
                img_width, img_height = cover_img.size
                
                # Check for landscape orientation and rotate
                if img_width > img_height:
                    cover_img = cover_img.rotate(90, expand=True)
                    img_width, img_height = cover_img.size
                
                # Resize the image to fit the page while maintaining aspect ratio
                page_width = self.w - 20
                page_height = self.h - 20
                aspect_ratio = img_width / img_height
                
                if img_width > page_width:
                    img_width = page_width
                    img_height = page_width / aspect_ratio
                if img_height > page_height:
                    img_height = page_height
                    img_width = page_height * aspect_ratio

                x = (self.w - img_width) / 2
                y = (self.h - img_height) / 2
                self.image(cover_img, x, y, img_width, img_height)

            except Exception as e:
                print(f"⚠️ Warning: Could not add cover image. {e}")
                self.text(10, 100, "Image not available or corrupted.")
        
        # Add a semi-transparent black overlay
        self.set_fill_color(0, 0, 0)
        self.set_alpha(0.5)
        self.rect(0, 0, self.w, self.h, 'F')
        self.set_alpha(1)
        
        # Add the logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo_img = Image.open(self.logo_path)
                logo_width, logo_height = logo_img.size
                
                # Calculate new size to fit within a 2-inch square
                max_size = 50.8 # 2 inches in mm
                if logo_width > logo_height:
                    new_width = max_size
                    new_height = logo_height * (new_width / logo_width)
                else:
                    new_height = max_size
                    new_width = logo_width * (new_height / logo_height)
                
                logo_x = (self.w - new_width) / 2
                logo_y = self.h / 3 - new_height
                self.image(self.logo_path, x=logo_x, y=logo_y, w=new_width, h=new_height)
            except Exception as e:
                print(f"⚠️ Warning: Could not add logo. {e}")
        
        # Add the title and author text
        self.set_text_color(255, 255, 255)
        self.set_y(self.h / 2)
        self.set_font(DEFAULT_FONT_NAME, "B", 48)
        self.multi_cell(0, 20, self.title, align="C")
        self.ln(20)
        self.set_font(DEFAULT_FONT_NAME, "", 24)
        self.multi_cell(0, 10, f"by {self.author}", align="C")

    def header(self):
        if self.page_no() > 2:
            self.set_y(15)
            self.set_font(DEFAULT_FONT_NAME, "I", 10)
            self.set_text_color(128)
            self.cell(0, 5, self.title, new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.cell(0, 5, self.author, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font(DEFAULT_FONT_NAME, "I", 10)
            self.set_text_color(128)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_toc_page(self):
        self.add_page()
        self.set_font(DEFAULT_FONT_NAME, "B", 24)
        self.cell(0, 10, "Table of Contents", align="C")
        self.ln(20)
        self.set_font(DEFAULT_FONT_NAME, "", 14)
        for chapter, page in self.chapter_titles:
            self.cell(10)
            self.cell(0, 10, f"{chapter} . . . {page}")
            self.ln()
        self.ln(10)
        self.set_font(DEFAULT_FONT_NAME, "", 12)
        for subchapter, page in self.subchapter_titles:
            self.cell(20)
            self.cell(0, 10, f"{subchapter} . . . {page}")
            self.ln()

    def add_chapter(self, title):
        self.add_page()
        self.set_font(DEFAULT_FONT_NAME, "B", 18)
        self.chapter_titles.append((title, self.page_no()))
        self.cell(0, 10, title, align="L")
        self.ln(15)

    def add_subchapter(self, title):
        self.set_font(DEFAULT_FONT_NAME, "I", 14)
        self.subchapter_titles.append((title, self.page_no()))
        self.cell(0, 10, title, align="L")
        self.ln(10)

def safe_multicell(pdf, w, h, txt, border=0, align="J"):
    """
    A hardened multi_cell function that handles long words
    without crashing the PDF renderer.
    """
    pdf.set_font(DEFAULT_FONT_NAME, "", 12)
    max_width = w if w != 0 else pdf.w - pdf.l_margin - pdf.r_margin
    lines = textwrap.wrap(txt, width=int(max_width / (pdf.font_size * 0.6)))
    for line in lines:
        pdf.cell(w, h, line, border=border, align=align)
        pdf.ln(h)

def generate_epub(title, author, content, output_path):
    book = epub.EpubBook()
    book.set_identifier(f"id{title.replace(' ', '')}{author.replace(' ', '')}")
    book.set_title(title)
    book.add_author(author)
    book.set_language('en')
    
    c1 = epub.EpubHtml(title='Content', file_name='content.xhtml', lang='en')
    c1.content = markdown2.markdown(content)
    book.add_item(c1)
    
    book.toc = (epub.Link('content.xhtml', 'Content', 'content'),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    book.spine = ['nav', c1]
    
    epub.write_epub(output_path, book, {})

def process_markdown_file(input_path):
    print(f"ℹ️ Processing '{input_path}'...")
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    title = DEFAULT_TITLE
    author = DEFAULT_AUTHOR
    cover = None
    logo = None
    
    # Parse metadata from top of file
    metadata_match = re.search(r"^---\s*?\n(.*?)---\s*?\n", content, re.DOTALL)
    if metadata_match:
        metadata_block = metadata_match.group(1)
        content = content[metadata_match.end():].lstrip()
        for line in metadata_block.splitlines():
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
        elif platform.system() == "Darwin": # macOS
            subprocess.Popen(['open', epub_path])
        else: # Linux and others
            subprocess.Popen(['xdg-open', epub_path])
    except Exception as e:
        print(f"⚠️ Warning: Could not auto-open EPUB file. {e}")
        
    html_path = os.path.splitext(input_path)[0] + ".html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(markdown2.markdown(content))
    print(f"✅ HTML created: {html_path}")

if __name__ == "__main__":
    input_file_path = None
    
    # Try to get the file path from the command line argument
    if len(sys.argv) > 1:
        input_file_path = sys.argv[1]
        if not os.path.exists(input_file_path):
            print(f"❌ Error: The file '{input_file_path}' does not exist.")
            input_file_path = None # Fallback to GUI

    # If no file path was provided or the file doesn't exist, open a GUI
    if not input_file_path:
        root = tk.Tk()
        root.withdraw()
        input_file_path = filedialog.askopenfilename(
            title="Select a Markdown file",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")]
        )
        if not input_file_path:
            print("ℹ️ File selection cancelled. Exiting.")
            sys.exit()

    try:
        process_markdown_file(input_file_path)
    except Exception as e:
        print(f"❌ An error occurred during file processing: {e}")
