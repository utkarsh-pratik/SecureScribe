# pdf_exporter.py
from fpdf import FPDF
from io import BytesIO
import datetime

def generate_pdf(title: str, content: str):
    """
    Generates a PDF document from a title and content string.
    Handles special Unicode characters by replacing them.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Set font that supports a wider range of characters
    pdf.set_font("Arial", size=12)

    # --- Title ---
    # Replace special characters in the title before adding it
    safe_title = title.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, safe_title, 0, 1, 'C')
    pdf.ln(10)

    # --- Content ---
    # Replace special characters in the content before adding it
    safe_content = content.encode('latin-1', 'replace').decode('latin-1')
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, safe_content)

    # --- Generate PDF in memory ---
    pdf_buffer = BytesIO()
    # The FPDF output must be encoded to latin-1 to be written to the buffer
    pdf_buffer.write(pdf.output(dest='S').encode('latin-1'))
    pdf_buffer.seek(0) # Rewind the buffer to the beginning

    # --- Create a filename ---
    safe_filename_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"{safe_filename_title}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"

    return pdf_buffer, filename