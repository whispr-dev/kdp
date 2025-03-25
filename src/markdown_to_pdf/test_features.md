---
title: Test Manuscript — Feature Showcase
author: Your Best Fren
cover: cover.jpg
logo: logo.png
---

# Test Manuscript — Feature Showcase

Welcome to the ultimate test file for `markdown_to_pdf.py`!  
Let’s try out every supported feature, one by one 🧪🛠️

---

## Chapter 1: Headings & TOC

# Level 1 Heading (Title Page Only)

## Level 2 Heading (Chapter)

### Level 3 Heading (Subsection)

#### Level 4 Heading (Should still render as plain)

---

## Chapter 2: Quotes

> This is a quote.  
> It should be italic, grey, and softly indented.

> Multiline quotes work too.  
Even if they’re staggered.

---

## Chapter 3: Inline Styling

- *Italic text* works!
- **Bold text** works!
- Mixed: *a bit of **bold inside italic** is fun*
- Even emojis 🧠✨💾 should be supported.

---

## Chapter 4: Lists

- List item one
- List item two
  - Nested item (will render flat)
- Item three

---

## Chapter 5: Horizontal Rules

Before the rule.

---

After the rule.

---

## Chapter 6: Image Support

Inline image below should render in PDF, EPUB and HTML:

![Sample Alt Text](sample-image.jpg)

Make sure `sample-image.jpg` is in the same folder as this `.md` file.

---

## Chapter 7: Code Blocks

```python
def hello_fren(name):
    print(f"Hello, {name}! 🐍")

hello_fren("world")
And inline code like print("hello") too!

Chapter 8: Cover & Logo
You should have seen the cover image and logo appear on the title page when this was compiled.

Chapter 9: Unicode, Wrapping & Safety
ThisIsAReallyReallyReallyReallyReallyReallyReallyLongUnbrokenStringThatShouldTriggerWrapping

👋🌍🎉🐱‍🏍🦖🚀 — Unicode glyph test

Chapter 10: End of Test
"If you see this, everything worked beautifully."