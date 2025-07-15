# utils/multimodal_parser.py

import fitz  # PyMuPDF
from PIL import Image
import io

def parse_pdf_for_text_and_images(pdf_bytes: bytes) -> list:
    """
    Parses a PDF file's bytes and extracts text and images in order of appearance.

    Args:
        pdf_bytes: The raw bytes of the PDF file.

    Returns:
        A list of dictionaries, where each dictionary represents a block of
        content, e.g., {'type': 'text', 'content': '...'} or
        {'type': 'image', 'content': <image_bytes>}.
    """
    content_blocks = []
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Extract all content blocks (text and images) in order
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
            
            page_content = []
            for block in blocks['blocks']:
                if block['type'] == 0:  # Text block
                    for line in block['lines']:
                        for span in line['spans']:
                            page_content.append({'type': 'text', 'y0': span['bbox'][1], 'content': span['text']})
                elif block['type'] == 1:  # Image block
                    try:
                        img_bytes = block['image']
                        page_content.append({'type': 'image', 'y0': block['bbox'][1], 'content': img_bytes})
                    except Exception:
                        # Ignore images that fail to extract
                        continue
            
            # Sort blocks on the page by their vertical position
            page_content.sort(key=lambda b: b['y0'])
            
            # Add the sorted blocks to the final list
            content_blocks.extend(page_content)

        return content_blocks

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return [{'type': 'text', 'content': f"[Error parsing PDF: {e}]"}]
