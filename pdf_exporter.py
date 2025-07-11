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
    
    # IMPORTANT: Add a font that supports Unicode characters.
    # This requires the 'DejaVuSans.ttf' file to be in your project's root directory.
    try:
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        pdf.add_font('DejaVu', 'I', 'DejaVuSans-Oblique.ttf', uni=True)    
    except RuntimeError:
        # Fallback to Arial if DejaVu is not found, with a warning.
        print("WARNING: DejaVuSans.ttf not found. Falling back to Arial. Special characters may not render correctly.")
        pdf.set_font("Arial", size=12)


    # --- Title ---
    # Replace special characters in the title before adding it
    pdf.set_font('DejaVu', 'B', 16)
    pdf.multi_cell(0, 10, title, 0, 'C')
    pdf.ln(10)


    # --- Content ---
    # Replace special characters in the content before adding it
    pdf.set_font('DejaVu', '', 16)
    pdf.multi_cell(0, 10, content)

    # --- Generate PDF in memory ---
    pdf_buffer = BytesIO()
    # The FPDF output must be encoded to latin-1 to be written to the buffer
    pdf_buffer.write(pdf.output(dest='S'))
    pdf_buffer.seek(0) # Rewind the buffer to the beginning

    # --- Create a filename ---
    safe_filename_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"{safe_filename_title}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"

    return pdf_buffer, filename
