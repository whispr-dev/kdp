# markdown_to_pdf.py — A Markdown to PDF/EPUB/HTML Converter

**Cross-platform**: PC Mac (untested) Linux (untested)  
Version: `v0.1.0` — 20250324214522 Mon


---


## Features

Fully-featured, beautifully typeset manuscript generator from a simple `.md` or `.txt` file!

### Cover Page
- Custom **title** and **author**
- Optional **cover image**
- Optional **logo**

### Auto Table of Contents
- Generated from your Markdown headings (`#`, `##`)

### Markdown Rendering
- `#`, `##`, `###` → Large, medium, and small headings
- `> quote` → *Grey italic blockquotes*
- `- item` → Bulleted lists
- `*italic*`, `**bold**` → Styled text
- `---` → Horizontal divider
- `![alt](image.jpg)` → Inline images
- <code>```code```</code> → Monospaced code blocks

### Bonus Features
- File picker GUI if no file is passed via command line
- Output includes:
  - PDF
  - EPUB (auto-launched)
  - HTML


---


## Installation

### If using the `.exe`:
No installation required! Just run and go

### If using the `.py` script:

You'll need to install the following dependencies:

```
pip install fpdf2 markdown2 ebooklib pillow
fpdf2 replaces the old fpdf library
Pillow is used for image handling
```


---


## How to Use
Command Line (recommended)
`python markdown_to_pdf.py "C:\path\to\your\story.md"`

Or just:
`python markdown_to_pdf.py`

…to open a file picker GUI.

Output will include:
`C:\path\to\your\story.pdf     ← your typeset printable manuscript`
`C:\path\to\your\story.epub    ← auto-launched for preview (KDP ready!)`
`C:\path\to\your\story.html    ← web-viewable version`


---


## Example Markdown Syntax

```
---
title: The Quack Side of the Law
author: Wofl
cover: cover.jpg
logo: logo.png
---

# The Quack Side of the Law

## Chapter 1: A Taste of Escape

This is *italic* and **bold**, or even a *bit of **bold inside italic***.

---

- Bullet point one
- Bullet point two

> This is a quote, isn't it?

![Detective Mallard](mallard.jpg)

def duck_waddle(): print("flap flap")
```


---


## Pro Tips
Add title, author, cover, and logo at the top of your Markdown using the --- metadata block.

If something breaks, check if you're using fancy Unicode symbols that don't fit the page (PDFs are picky about width).

Make sure images are in the same folder as your .md file or use full paths!


---


## Developer Notes
Built with fpdf2, markdown2, ebooklib, and Pillow

Designed to work inside a PyInstaller .exe with bundled fonts and assets

Unicode font compatibility via DejaVuSerif/Mono included


---


### Written with love for frens who publish
Happy writing, happy typesetting!