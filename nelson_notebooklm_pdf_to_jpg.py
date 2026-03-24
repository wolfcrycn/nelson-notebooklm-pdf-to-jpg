"""
PDF to JPG Stitch - Convert PDF pages to JPG, remove watermarks, stitch to long image
"""
import os
import sys
import shutil
import argparse

try:
    import fitz  # PyMuPDF
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required package - {e}")
    print("Please install: pip install pymupdf opencv-python pillow numpy")
    sys.exit(1)


def process_pdf(pdf_path, output_dir="./output", watermark_width=500, 
                watermark_height=100, quality=95, dpi=150):
    """
    Process PDF: convert to JPG, remove watermark, stitch to long image
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Output directory for JPGs
        watermark_width: Width of watermark area (px)
        watermark_height: Height of watermark area (px)
        quality: JPEG quality (1-100)
        dpi: Rendering DPI
    """
    
    # Create output directories
    jpg_dir = os.path.join(output_dir, "jpgs")
    os.makedirs(jpg_dir, exist_ok=True)
    
    print(f"📄 PDF: {os.path.basename(pdf_path)}")
    
    # Step 1: Detect correct page count and dimensions
    print(f"\n🔍 Step 1: Detecting PDF structure...")
    doc = fitz.open(pdf_path)
    
    # Get page count from PDF structure
    total_pages = len(doc)
    
    # Analyze each page to detect actual content pages
    valid_pages = []
    for i in range(total_pages):
        page = doc[i]
        rect = page.rect
        
        # Get page text content
        text = page.get_text()
        text_len = len(text.strip())
        
        # Get page images
        images = page.get_images()
        
        # Check if page has actual content
        has_content = text_len > 0 or len(images) > 0
        
        page_info = {
            'index': i,
            'number': i + 1,
            'width': rect.width,
            'height': rect.height,
            'rotation': page.rotation,
            'text_chars': text_len,
            'images': len(images),
            'has_content': has_content
        }
        valid_pages.append(page_info)
        
        if i < 3 or i >= total_pages - 2:  # Show first 3 and last 2 pages
            print(f"   Page {i+1}: {rect.width:.0f}x{rect.height:.0f}pt, "
                  f"text:{text_len} chars, images:{len(images)}, "
                  f"{'✓' if has_content else '✗'}")
        elif i == 3:
            print(f"   ... ({total_pages - 5} pages) ...")
    
    # Filter to only content pages (optional, can be disabled)
    content_pages = [p for p in valid_pages if p['has_content']]
    
    print(f"\n📊 Detection Results:")
    print(f"   Total PDF pages: {total_pages}")
    print(f"   Pages with content: {len(content_pages)}")
    
    # Use all pages by default (can change to use only content_pages)
    pages_to_process = valid_pages  # or content_pages
    total = len(pages_to_process)
    
    print(f"\n📄 Processing {total} pages...")
    
    # Calculate zoom based on DPI
    zoom = dpi / 72
    
    # Process each page
    print(f"\n🔄 Converting {total} pages to JPG...")
    jpg_paths = []
    
    for page_info in pages_to_process:
        page_idx = page_info['index']
        page_num = page_info['number']
        
        if page_num % 5 == 0 or page_num == 1:
            print(f"   Page {page_num}/{total}...")
        
        # Render page
        page = doc[page_idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Save temporary
        temp_path = os.path.join(jpg_dir, f"page_{page_num:03d}_temp.jpg")
        img.save(temp_path, "JPEG", quality=quality)
        
        jpg_paths.append(temp_path)
    
    doc.close()
    
    # Remove watermarks using OpenCV
    print(f"\n🧹 Removing watermarks with OpenCV...")
    final_paths = []
    
    for i, jpg_path in enumerate(jpg_paths):
        page_num = i + 1
        
        # Read with OpenCV
        img = cv2.imread(jpg_path)
        h, w = img.shape[:2]
        
        # Define watermark region (bottom-right)
        x1 = max(0, w - watermark_width)
        y1 = max(0, h - watermark_height)
        x2 = w
        y2 = h
        
        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        
        # Inpaint
        result = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
        
        # Save final
        final_path = os.path.join(jpg_dir, f"page_{page_num:03d}.jpg")
        cv2.imwrite(final_path, result, [cv2.IMWRITE_JPEG_QUALITY, quality])
        final_paths.append(final_path)
        
        # Remove temp file
        os.remove(jpg_path)
        
        if page_num % 5 == 0:
            print(f"   {page_num}/{total}")
    
    print(f"✅ JPGs saved to: {jpg_dir}")
    
    # Stitch to long image
    print(f"\n🧩 Stitching long image...")
    
    images = [Image.open(p) for p in final_paths]
    total_h = sum(img.height for img in images)
    max_w = max(img.width for img in images)
    
    # JPEG max height is 65500px
    MAX_HEIGHT = 65000
    
    if total_h <= MAX_HEIGHT:
        # Single long image
        long_img = Image.new("RGB", (max_w, total_h), (255, 255, 255))
        y = 0
        for img in images:
            long_img.paste(img, (0, y))
            y += img.height
        
        long_path = os.path.join(output_dir, "pdf_long.jpg")
        long_img.save(long_path, "JPEG", quality=90)
        
        file_kb = os.path.getsize(long_path) / 1024
        print(f"✅ Long image: {max_w}x{total_h}px ({file_kb:.0f}KB)")
        print(f"   Saved: {long_path}")
    else:
        # Multiple segments
        pages_per_segment = MAX_HEIGHT // images[0].height
        num_segments = (len(images) + pages_per_segment - 1) // pages_per_segment
        
        print(f"   Creating {num_segments} segments...")
        
        for seg in range(num_segments):
            start = seg * pages_per_segment
            end = min(start + pages_per_segment, len(images))
            seg_images = images[start:end]
            
            seg_h = sum(img.height for img in seg_images)
            seg_img = Image.new("RGB", (max_w, seg_h), (255, 255, 255))
            
            y = 0
            for img in seg_images:
                seg_img.paste(img, (0, y))
                y += img.height
            
            long_path = os.path.join(output_dir, f"pdf_long_part{seg+1}.jpg")
            seg_img.save(long_path, "JPEG", quality=90)
            
            file_kb = os.path.getsize(long_path) / 1024
            print(f"   Part {seg+1}: {max_w}x{seg_h}px ({file_kb:.0f}KB)")
    
    print(f"\n🎉 Done!")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to JPG, remove watermarks, stitch to long image")
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    parser.add_argument("--watermark", "-w", default="500x100", help="Watermark size (WxH)")
    parser.add_argument("--quality", "-q", type=int, default=95, help="JPEG quality (1-100)")
    parser.add_argument("--dpi", type=int, default=150, help="Rendering DPI")
    
    args = parser.parse_args()
    
    # Parse watermark size
    wm_parts = args.watermark.split("x")
    wm_width = int(wm_parts[0])
    wm_height = int(wm_parts[1])
    
    process_pdf(
        pdf_path=args.pdf_path,
        output_dir=args.output,
        watermark_width=wm_width,
        watermark_height=wm_height,
        quality=args.quality,
        dpi=args.dpi
    )


if __name__ == "__main__":
    main()
