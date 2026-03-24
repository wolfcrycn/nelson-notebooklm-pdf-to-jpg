---
name: nelson-notebooklm-pdf-to-jpg
description: Convert PDF pages to JPG images, remove NotebookLM watermarks, and stitch into a long image. Uses PyMuPDF for rendering and OpenCV for watermark removal.
version: 1.0.0
homepage: https://clawic.com/skills/nelson-notebooklm-pdf-to-jpg
metadata:
  emoji: 📄
  requires:
    python_packages:
      - pymupdf
      - opencv-python
      - pillow
      - numpy
---

# Nelson NotebookLM PDF to JPG

Convert PDF pages to JPG images, remove watermarks, and stitch into a long image.

## Features

- 📄 Convert PDF pages to high-quality JPG images
- 🧹 Remove watermarks using OpenCV inpainting
- 🧩 Stitch all pages into a single long image
- 📐 Auto-detect page dimensions
- ⚡ Fast processing with PyMuPDF

## Installation

```bash
pip install pymupdf opencv-python pillow numpy
```

## Usage

### Basic Usage

```python
from nelson_notebooklm_pdf_to_jpg import process_pdf

process_pdf(
    pdf_path="input.pdf",
    output_dir="./output",
    watermark_width=500,
    watermark_height=100,
    quality=95
)
```

### Command Line

```bash
python -m nelson_notebooklm_pdf_to_jpg input.pdf --watermark 500x100 --quality 95
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pdf_path` | required | Path to input PDF file |
| `output_dir` | `./output` | Output directory for JPGs |
| `watermark_width` | 500 | Width of watermark area (px) |
| `watermark_height` | 100 | Height of watermark area (px) |
| `quality` | 95 | JPEG quality (1-100) |
| `dpi` | 150 | Rendering DPI |

## Output

- Individual JPG files: `page_001.jpg`, `page_002.jpg`, ...
- Stitched long image: `pdf_long.jpg`

## Example

```bash
# Process PDF with default settings
python -m nelson_notebooklm_pdf_to_jpg "document.pdf"

# Custom watermark size
python -m nelson_notebooklm_pdf_to_jpg "document.pdf" --watermark 400x80 --quality 90
```

## Notes

- Watermark is assumed to be in bottom-right corner
- Long image height limited to 65500px (JPEG max)
- If PDF has more pages, multiple long images will be created
