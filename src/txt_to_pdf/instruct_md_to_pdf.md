# README.md for markdown_to_pdf.py
# a markdown to pdf/epub/html converter
# for PC, Mac and Linux [untested on Mac and Linux]

20250324181156

---

## Features:

---

New Features Fully Supported:
Cover page with:

Title

Author

Optional cover image

Optional logo

Auto-generated Table of Contents

Markdown parsing with:

#, ##, ### → Chapter headings

> quote → Italic grey blockquote

- list item → Bulleted list

*italic*, **bold** → Inline styling

--- → Horizontal rule

![alt](image.jpg) → Inline image rendering

``` blocks → Monospaced code sections

File picker GUI fallback if no file path is given on the command line
```

---


## To install
n.b. 
`from fpdf import FPDF  # fpdf2 keeps the same class name`

refers to fact that fpdf og i deprecate and fpdf2 must be installed hence:
`pip install fpdf2`


## To use:
If using CLI:

`python markdown_to_pdf.py "\path\to\your\story.txt"`

Or just:

`python markdown_to_pdf.py`

…and a file picker will let you choose!

Your output will include:
`\path\to\your\story.pdf`
`\path\to\your\story.epub`
`\path\to\your\story.html`

---

## Can Handle:
will convert md # to title and ## headings to chapter sections:


```
---
title: The Quack Side of the Law
author: wofl
cover: cover.jpg
logo: logo.png
---


# Title

## Chapter 1

This is *italic* and **bold**, or even a *bit of **bold inside italic***.

---

- Bullet point one
- Bullet point two

> This is a quote, isn't it?
```

---