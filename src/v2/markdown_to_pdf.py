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
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound
import io
import matplotlib as mpl
mpl.use('Agg') # Use a non-interactive backend
import matplotlib.pyplot as plt
import json

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

# Matplotlib setup for LaTeX rendering
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [
    r'\usepackage{amsmath}',
    r'\usepackage{amsfonts}',
    r'\usepackage{amssymb}'
]

def load_settings(settings_path="settings.json"):
    """Loads settings from a JSON file."""
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        print("ℹ️  'settings.json' not found. Using default settings.")
        return {}
    except json.JSONDecodeError:
        print("❌ Error decoding 'settings.json'. Please check for syntax errors.")
        return {}

def safe_multicell(pdf, w, h, txt, border=0, align='J'):
    """A safe multicell function to handle text that fpdf might have trouble with."""
    try:
        pdf.multi_cell(w, h, txt, border=border, align=align)
    except UnicodeEncodeError:
        print(f"⚠️  Unicode error: Could not render some characters in the following text. "
              "Check your source file for non-standard characters.")
        # Attempt to clean up and re-render
        cleaned_txt = txt.encode('utf-8', 'ignore').decode('utf-8')
        pdf.multi_cell(w, h, cleaned_txt, border=border, align=align)

class PDF(FPDF):
    """Custom PDF class with a chapter management system."""
    def __init__(self, title, author, logo_path=None, cover_image_path=None, settings=None):
        super().__init__()
        self.title = title
        self.author = author
        self.logo_path = logo_path
        self.cover_image_path = cover_image_path
        self.settings = settings if settings else {}
        self.set_title(self.title)
        self.set_author(self.author)
        self.add_font(DEFAULT_FONT_NAME, "", font_regular, uni=True)
        self.add_font(DEFAULT_FONT_NAME, "B", font_bold, uni=True)
        self.add_font(DEFAULT_FONT_NAME, "I", font_italic, uni=True)
        self.add_font(DEFAULT_FONT_NAME, "BI", font_bolditalic, uni=True)
        self.add_font("DejaVuSansMono", "", font_mono, uni=True)
        
        # Apply settings
        pdf_settings = self.settings.get("pdf_settings", {})
        page_format = pdf_settings.get("page_format", "A4")
        self.set_page_format(page_format)
        
        margins = pdf_settings.get("margins", {"top": 20, "bottom": 20, "left": 25, "right": 25})
        self.set_margins(margins["left"], margins["top"], margins["right"])
        self.set_auto_page_break(auto=True, margin=margins["bottom"])
        
        self.toc_data = []
        self.footnote_number = 1
        self.footnotes = {}

    def header(self):
        """Standard header for all pages except the cover."""
        if self.page_no() > 1:
            self.set_font(DEFAULT_FONT_NAME, 'I', 10)
            self.set_text_color(150)
            self.cell(0, 10, self.title, 0, 0, 'L')
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')
            self.ln(20)

    def footer(self):
        """Standard footer."""
        pass  # We use the header for page numbers now

    def add_chapter_title(self, title):
        """Adds a new chapter heading and adds it to the TOC."""
        self.set_font(DEFAULT_FONT_NAME, 'B', 18)
        self.set_text_color(0)
        self.cell(0, 10, title, align='C')
        self.ln(10)
        self.toc_data.append((0, title, self.page_no()))

    def add_subchapter_title(self, title):
        """Adds a new subchapter heading and adds it to the TOC."""
        self.set_font(DEFAULT_FONT_NAME, 'B', 14)
        self.set_text_color(0)
        self.cell(0, 8, title, align='L')
        self.ln(8)
        self.toc_data.append((1, title, self.page_no()))

    def add_cover_page(self):
        """Creates the cover page of the document."""
        self.add_page()
        self.set_text_color(0)  # Black text
        
        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, x=self.w/2 - 25, y=self.h/2 - 100, w=50)

        # Cover Image
        if self.cover_image_path and os.path.exists(self.cover_image_path):
            self.image(self.cover_image_path, x=0, y=0, w=self.w, h=self.h)

        # Title and Author
        self.set_y(self.h / 2 + 50)
        self.set_font(DEFAULT_FONT_NAME, 'B', 32)
        self.cell(0, 20, self.title, align='C')
        self.ln(20)
        self.set_font(DEFAULT_FONT_NAME, 'I', 18)
        self.cell(0, 10, f"by {self.author}", align='C')
        self.ln(30)
        
        self.add_page() # Start on a new page after the cover

    def add_toc_page(self):
        """Generates a Table of Contents from the collected headings."""
        self.add_page()
        self.set_font(DEFAULT_FONT_NAME, 'B', 24)
        self.cell(0, 10, 'Table of Contents', align='C')
        self.ln(20)
        
        self.set_font(DEFAULT_FONT_NAME, '', 12)
        
        for level, title, page_num in self.toc_data:
            if level == 0:
                self.set_font(DEFAULT_FONT_NAME, 'B', 12)
                self.cell(0, 10, f"{title}...................................{page_num}", ln=1)
            elif level == 1:
                self.set_font(DEFAULT_FONT_NAME, '', 11)
                self.cell(10) # Indent
                self.cell(0, 10, f"{title}...................................{page_num}", ln=1)
        self.ln(10)
        
    def add_footnotes_page(self):
        """Adds a dedicated page for all collected footnotes."""
        if not self.footnotes:
            return
            
        self.add_page()
        self.set_font(DEFAULT_FONT_NAME, 'B', 24)
        self.cell(0, 10, 'Notes', align='C')
        self.ln(20)
        
        self.set_font(DEFAULT_FONT_NAME, '', 10)
        self.set_text_color(0)
        for number, text in self.footnotes.items():
            safe_multicell(self, 0, 5, f'[{number}] {text}')
            self.ln(2)

    def draw_table(self, table_data):
        """Draws a Markdown table with FPDF."""
        self.ln(5)
        self.set_font(DEFAULT_FONT_NAME, "", 10)
        
        # Calculate column widths
        num_cols = len(table_data[0])
        col_width = self.w / num_cols - 20 / num_cols
        
        # Draw header
        self.set_fill_color(240, 240, 240)
        self.set_font(DEFAULT_FONT_NAME, "B", 10)
        for header in table_data[0]:
            self.cell(col_width, 7, header.strip(), 1, 0, 'C', 1)
        self.ln()

        # Draw rows
        self.set_font(DEFAULT_FONT_NAME, "", 10)
        for row in table_data[2:]:
            for item in row:
                self.cell(col_width, 7, item.strip(), 1)
            self.ln()
        self.ln(5)
        
    def draw_code_block(self, code, language):
        """Draws a syntax-highlighted code block."""
        self.set_font("DejaVuSansMono", "", 10)
        self.set_fill_color(240, 240, 240)
        self.ln(5)

        try:
            lexer = get_lexer_by_name(language)
            formatter = get_formatter_by_name("html", style="default")
            highlighted_html = highlight(code, lexer, formatter)
            # This is a hacky way to get the text with styling tags
            highlighted_text = re.sub('<.*?>', '', highlighted_html)
            
            # Simple color mapping for basic highlighting
            color_map = {
                '#888888': (136, 136, 136), # Comment
                '#008000': (0, 128, 0),     # String
                '#0000ff': (0, 0, 255),     # Keyword
                '#ff0000': (255, 0, 0),     # Error
                '#008080': (0, 128, 128),   # Operator
            }

            for line in highlighted_text.splitlines():
                # We'll just do a very basic, non-tag-based highlighting for now
                self.set_text_color(0)
                safe_multicell(self, 0, 5, line, border=0, align='L')
                self.ln(2)

        except ClassNotFound:
            # Fallback to plain code if the language is not found
            self.set_text_color(0)
            safe_multicell(self, 0, 5, code, border=0, align='L')
            self.ln(2)
        
        self.ln(5)

def render_math(latex_string, display_mode=False):
    """Renders a LaTeX string to an image and returns a buffer."""
    plt.ioff()
    fig = plt.figure(figsize=(12, 1), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    
    if display_mode:
        latex_text = f"$${latex_string}$$"
    else:
        latex_text = f"${latex_string}$"

    try:
        ax.text(0.5, 0.5, latex_text, ha='center', va='center', fontsize=24)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        plt.close(fig)
        return buf
    except Exception as e:
        print(f"❌ Error rendering LaTeX: {e}")
        plt.close(fig)
        return None

def generate_epub(title, author, content, output_path):
    """Generates an EPUB file."""
    book = epub.EpubBook()
    
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)
    
    # HTML conversion for EPUB
    html_content = markdown2.markdown(content, extras=["footnotes", "tables", "fenced-code-blocks"])
    
    # Basic chapter
    c1 = epub.EpubHtml(title='Content', file_name='content.xhtml', lang='en')
    c1.content = u'<h1>{}</h1><p>{}</p>'.format(title, html_content)
    
    book.add_item(c1)
    
    # Add toc
    book.toc = (epub.Link('content.xhtml', 'Content', 'content'),)
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    style = 'BODY {color: #000;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    
    spine_items = [c1]
    
    # Set the spine
    book.spine = spine_items
    
    epub.write_epub(output_path, book, {})

def generate_html(content, output_path):
    """Generates an HTML file from the markdown content."""
    html_content = markdown2.markdown(content, extras=["footnotes", "tables", "fenced-code-blocks"])
    html_template = f"""
<html>
<head>
<meta charset='utf-8'>
<title>Document</title>
<style>
  body {{ font-family: sans-serif; line-height: 1.6; margin: 0 auto; max-width: 800px; padding: 2em; }}
  h1, h2, h3 {{ color: #333; }}
  blockquote {{ border-left: 4px solid #ccc; margin: 1.5em 10px; padding: 0.5em 10px; color: #666; font-style: italic; }}
  code {{ font-family: monospace; background-color: #f4f4f4; padding: 2px 5px; }}
  pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background-color: #f2f2f2; }}
  .footnotes {{ margin-top: 3em; border-top: 1px solid #ccc; padding-top: 1em; }}
</style>
</head>
<body>
{html_content}
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

def main():
    """Main function to handle file processing."""
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        root = tk.Tk()
        root.withdraw()
        input_path = filedialog.askopenfilename(
            title="Select your Markdown file",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")]
        )
        if not input_path:
            print("❌ No file selected. Exiting.")
            return

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found at {input_path}")
        return
    
    settings = load_settings()

    # --- New Footnote Parsing ---
    footnotes = {}
    footnote_regex = r'\[\^(\d+)\]:\s*(.*)'
    content_without_footnotes = []

    # First, find and store all footnotes
    for line in content.splitlines():
        match = re.search(footnote_regex, line)
        if match:
            # Found a footnote definition
            number = match.group(1)
            text = match.group(2).strip()
            footnotes[number] = text
        else:
            # This line is part of the main content
            content_without_footnotes.append(line)
    
    content = '\n'.join(content_without_footnotes)

    # Replace footnote markers in the main content with the PDF's internal link system
    def replace_footnote_marker(match):
        number = match.group(1)
        if number in footnotes:
            # For the PDF, we will use a small superscript link
            return f'[^({number})]'
        return match.group(0)

    content = re.sub(r'\[\^(\d+)\]', replace_footnote_marker, content)
    # --- End of New Footnote Parsing ---
    
    metadata = {}
    content_lines = content.splitlines()
    if content_lines[0].strip() == "---" and "---" in content_lines[1:]:
        end_metadata = content_lines[1:].index("---") + 1
        metadata_block = content_lines[1:end_metadata]
        for line in metadata_block:
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()
        content = "\n".join(content_lines[end_metadata + 1:])

    title = metadata.get("title", DEFAULT_TITLE)
    author = metadata.get("author", DEFAULT_AUTHOR)
    cover = metadata.get("cover", None)
    logo = metadata.get("logo", None)

    pdf = PDF(title=title, author=author, logo_path=logo, cover_image_path=cover, settings=settings)
    pdf.add_cover_page()
    
    # We will generate a TOC based on markdown, but we need to re-parse it
    # to find the heading levels
    for line in content.splitlines():
        if line.startswith("# "):
            # We don't add the top heading to the TOC, as it's the title
            pass
        elif line.startswith("## "):
            pdf.add_subchapter_title(line[3:].strip())
        elif line.startswith("### "):
            # For now, we will add level 3 as a sub-sub-chapter
            pdf.add_subchapter_title("    " + line[4:].strip())
    
    pdf.add_toc_page()

    # Reset PDF page and content for the main body
    pdf.add_page()
    
    # --- New Table & Code Block Rendering & List Rendering & Math Rendering ---
    lines = content.splitlines()
    i = 0
    list_level = 0
    ordered_list_counts = {}
    
    while i < len(lines):
        line = lines[i]
        
        # Check for start of a table
        if re.match(r'\|.*\|', line) and i + 1 < len(lines) and re.match(r'\|[-|: ]*\|', lines[i + 1]):
            table_data = []
            while i < len(lines) and re.match(r'\|.*\|', lines[i]):
                table_data.append([cell.strip() for cell in lines[i].split('|') if cell.strip()])
                i += 1
            if table_data:
                pdf.draw_table(table_data)
            continue
        
        # Check for start of a code block
        if line.startswith("```"):
            language = line[3:].strip()
            code_block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_block.append(lines[i])
                i += 1
            pdf.draw_code_block('\n'.join(code_block), language)
            i += 1
            continue
        
        # Check for list items
        list_match = re.match(r'^( *)[-*+]\s+(.*)', line)
        ordered_match = re.match(r'^( *)\d+\.\s+(.*)', line)
        
        if list_match:
            indent = len(list_match.group(1))
            text = list_match.group(2)
            list_level = indent // 2
            
            pdf.set_font(DEFAULT_FONT_NAME, "", 12)
            pdf.set_x(pdf.l_margin + indent)
            safe_multicell(pdf, 0, 8, f"• {text}")
            
        elif ordered_match:
            indent = len(ordered_match.group(1))
            text = ordered_match.group(2)
            list_level = indent // 2
            
            current_level = list_level
            if current_level not in ordered_list_counts:
                ordered_list_counts[current_level] = 1
            else:
                ordered_list_counts[current_level] += 1

            # Reset counts for deeper levels
            for level in ordered_list_counts.keys():
                if level > current_level:
                    ordered_list_counts[level] = 0

            pdf.set_font(DEFAULT_FONT_NAME, "", 12)
            pdf.set_x(pdf.l_margin + indent)
            safe_multicell(pdf, 0, 8, f"{ordered_list_counts[current_level]}. {text}")
        
        else:
            # If the current line is not a list item, reset list counts
            ordered_list_counts = {}
            list_level = 0
            
            # Normal content rendering
            if line.startswith("# "):
                pdf.add_chapter_title(line[2:].strip())
            elif line.startswith("## "):
                pdf.add_subchapter_title(line[3:].strip())
            elif line.startswith("### "):
                pdf.set_font(DEFAULT_FONT_NAME, "B", 12)
                pdf.cell(0, 8, line[4:].strip())
                pdf.ln(8)
            elif line.startswith("> "):
                pdf.set_font(DEFAULT_FONT_NAME, "I", 12)
                pdf.set_text_color(100)
                safe_multicell(pdf, 0, 8, line[2:])
                pdf.set_text_color(0)
                pdf.ln(4)
            elif line.strip() == "---":
                pdf.ln(10)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
                pdf.ln(10)
            elif line.startswith("!["):
                # A simple way to handle images, assumes they're in the same folder
                match = re.search(r'\!\[(.*?)\]\((.*?)\)', line)
                if match:
                    image_path = match.group(2)
                    if os.path.exists(image_path):
                        # Resize image to fit the page width
                        try:
                            img = Image.open(image_path)
                            width, height = img.size
                            max_width = 180
                            if width > max_width:
                                height = (height / float(width)) * max_width
                                width = max_width
                            pdf.image(image_path, x=pdf.w / 2 - width / 2, w=width)
                        except Exception as e:
                            print(f"❌ Error rendering image {image_path}: {e}")
            elif line.strip().startswith("$$") and line.strip().endswith("$$"):
                latex_code = line.strip()[2:-2]
                img_buffer = render_math(latex_code, display_mode=True)
                if img_buffer:
                    pdf.ln(5)
                    pdf.image(img_buffer, x=pdf.get_x() + 10, w=150)
                    pdf.ln(5)
            elif line.strip():
                # Handle inline markdown, footnotes, and inline math for rendering
                line_with_math = re.sub(r'\$(.*?)\$', lambda m: f'\\{m.group(1)}\\', line)
                
                line_with_footnotes = line_with_math
                for fn_num, fn_text in pdf.footnotes.items():
                    marker = f'[^{fn_num}]'
                    line_with_footnotes = line_with_footnotes.replace(marker, f'[{fn_num}]', 1)

                parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|\[\^.*?\])', line_with_footnotes)
                pdf.set_font(DEFAULT_FONT_NAME, "", 12)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        pdf.set_font(DEFAULT_FONT_NAME, "B", 12)
                        pdf.write(8, part[2:-2])
                        pdf.set_font(DEFAULT_FONT_NAME, "", 12)
                    elif part.startswith('*') and part.endswith('*'):
                        pdf.set_font(DEFAULT_FONT_NAME, "I", 12)
                        pdf.write(8, part[1:-1])
                        pdf.set_font(DEFAULT_FONT_NAME, "", 12)
                    elif part.startswith('[^(') and part.endswith(')]'):
                        fn_num = part[3:-2]
                        # We render the footnote marker as a superscript link
                        pdf.set_font(DEFAULT_FONT_NAME, '', 8)
                        pdf.set_text_color(0, 0, 255)
                        pdf.write(5, f'[{fn_num}]', 'link-to-footnote') # Placeholder link
                        pdf.set_font(DEFAULT_FONT_NAME, '', 12)
                        pdf.set_text_color(0)
                    else:
                        pdf.write(8, part)
                pdf.ln(8)
            else:
                pdf.ln(4)
        i += 1

    # --- End of New Table & Code Block Rendering & List Rendering & Math Rendering ---

    # --- New Footnote Rendering ---
    pdf.footnotes = footnotes
    pdf.add_footnotes_page()
    # --- End of New Footnote Rendering ---

    # Output files
    output_formats = settings.get("output_formats", {"pdf": True, "epub": True, "html": True})
    
    if output_formats.get("pdf", True):
        pdf_path = os.path.splitext(input_path)[0] + ".pdf"
        pdf.output(pdf_path)
        print(f"✅ PDF created: {pdf_path}")
        
    if output_formats.get("epub", True):
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
            print(f"ℹ️ Could not auto-launch EPUB file: {e}")
            
    if output_formats.get("html", True):
        html_path = os.path.splitext(input_path)[0] + ".html"
        generate_html(content, html_path)
        print(f"✅ HTML created: {html_path}")

if __name__ == "__main__":
    main()