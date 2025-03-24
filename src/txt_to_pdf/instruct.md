`python make_pdf.py "\path\to\your\story.txt"`

output is:
`\path\to\your\story.pdf`

will convert md headings to chapter sections:
# Title

## Chapter 1

This is *italic* and **bold**, or even a *bit of **bold inside italic***.

---

- Bullet point one
- Bullet point two

> This is a quote, isn't it?


n.b. 
`from fpdf import FPDF  # fpdf2 keeps the same class name`

refers to fact that fpdf og i deprecate and fpdf2 must be installed hence:
`pip install fpdf2`
