# /home/ubuntu/bat_rie_checker/core_logic/permit_processor.py

import json
import os
from .pdf_processor import extract_text_and_metadata # Use relative import

def extract_activity_description(full_text_markdown: str) -> tuple[str, dict | None]:
    """Placeholder function to find activity description from permit text."""
    # This would involve searching for sections describing the facility's activities.
    # For now, returning a placeholder.
    activity_text = "Placeholder: Activity description to be extracted from the permit. "
    activity_text += "This typically includes details about the type of operations, capacity, etc."
    if full_text_markdown:
        # A very naive approach for demonstration, e.g. looking for common phrases
        if "activities of the installation" in full_text_markdown.lower():
            try:
                start_index = full_text_markdown.lower().index("activities of the installation")
                end_index = start_index + 300 # take a chunk
                activity_text = full_text_markdown[start_index:end_index] + "... (truncated for placeholder)"
            except ValueError:
                pass # Phrase not found
    return activity_text, {"page_number": "P1", "paragraph_id": "Q_activity"} # Placeholder metadata

def extract_permit_conditions(full_text_markdown: str) -> list[dict]:
    """Placeholder function to find specific conditions from permit text."""
    # Permit conditions are usually listed and numbered.
    # Real implementation needs to parse markdown and identify these structured items.
    conditions = [
        {
            "condition_id": "C1",
            "condition_text": "Placeholder: Condition 1 related to emission limits for pollutant X.",
            "source_metadata": {"page_number": "P2", "paragraph_id": "R_cond1"}
        },
        {
            "condition_id": "C2",
            "condition_text": "Placeholder: Condition 2 regarding monitoring and reporting requirements.",
            "source_metadata": {"page_number": "P3", "paragraph_id": "S_cond2"}
        }
    ]
    if full_text_markdown and "conditions" in full_text_markdown.lower():
        conditions[0]["condition_text"] = "Extracted (simplified): First condition found..."
    return conditions

def process_permit_to_data(pdf_path: str, permit_id: str = "UNKNOWN_PERMIT") -> dict | None:
    """
    Processes a permit PDF, extracts information, and structures it.

    Args:
        pdf_path: Path to the permit PDF file.
        permit_id: (Optional) A unique identifier for this permit.

    Returns:
        A dictionary structured for permit data, or None if processing fails.
    """
    print(f"Processing Permit PDF: {pdf_path}")
    extraction_result = extract_text_and_metadata(pdf_path)

    if extraction_result.get("error"):
        print(f"Error extracting text from Permit PDF {pdf_path}: {extraction_result['error']}")
        return None

    full_text_markdown = extraction_result.get("full_text", "")
    document_title = extraction_result.get("title", "Unknown Permit Title")

    print(f"Successfully extracted text from permit. Title: {document_title}. Length: {len(full_text_markdown)} chars.")

    activity_description, activity_metadata = extract_activity_description(full_text_markdown)
    permit_conditions = extract_permit_conditions(full_text_markdown)

    permit_data = {
        "permit_id": permit_id,
        "title": document_title,
        "file_path": pdf_path,
        "activity_description": activity_description,
        "activity_source_metadata": activity_metadata,
        "conditions": permit_conditions,
        "full_text_markdown": full_text_markdown # Storing the full text for later detailed analysis
    }

    return permit_data

if __name__ == '__main__':
    print("Testing Permit Processor...")
    # Create a dummy Permit PDF for testing
    dummy_permit_pdf_path = "/home/ubuntu/bat_rie_checker/dummy_permit.pdf"
    # Directory for temporary uploads, as per architecture
    uploads_dir = "/home/ubuntu/bat_rie_checker/uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # For testing, we can place the dummy permit in the main project dir or uploads
    # For this test, let's use the main project directory for simplicity of the test script.

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph

        c = canvas.Canvas(dummy_permit_pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleH1 = styles['h1']
        styleH2 = styles['h2']

        # Page 1: Permit Info and Activities
        c.setTitle("Dummy Environmental Permit for Facility Alpha")
        title = Paragraph("Permit No: XYZ/123/2025 - Facility Alpha", styleH1)
        title.wrapOn(c, A4[0] - 100, 50)
        title.drawOn(c, 50, A4[1] - 100)

        activity_heading = Paragraph("2. Description of Activities of the Installation", styleH2)
        activity_heading.wrapOn(c, A4[0] - 100, 30)
        activity_heading.drawOn(c, 50, A4[1] - 150)
        activity_text_lines = [
            "The installation is a chemical production facility. Key activities include...",
            "The annual production capacity is 10,000 tonnes of product Z."
        ]
        y_pos = A4[1] - 180
        for line in activity_text_lines:
            p = Paragraph(line, styleN)
            p.wrapOn(c, A4[0] - 100, 20)
            p.drawOn(c, 50, y_pos)
            y_pos -= 20
        c.showPage()

        # Page 2: Permit Conditions
        conditions_heading = Paragraph("3. Permit Conditions", styleH2)
        conditions_heading.wrapOn(c, A4[0] - 100, 30)
        conditions_heading.drawOn(c, 50, A4[1] - 100)
        
        cond1_text = Paragraph("3.1 Emissions to air shall not exceed the following limits: NOx - 50 mg/m3.", styleN)
        cond1_text.wrapOn(c, A4[0] - 100, 50)
        cond1_text.drawOn(c, 50, A4[1] - 150)

        cond2_text = Paragraph("3.2 The operator shall monitor emissions in accordance with EN 12345.", styleN)
        cond2_text.wrapOn(c, A4[0] - 100, 50)
        cond2_text.drawOn(c, 50, A4[1] - 200)
        c.save()
        print(f"Dummy Permit PDF created at {dummy_permit_pdf_path}")

        # Process the dummy Permit PDF
        permit_data = process_permit_to_data(
            pdf_path=dummy_permit_pdf_path, 
            permit_id="XYZ_123_2025"
        )

        if permit_data:
            # In a real application, this data would be used by the backend, not necessarily saved to a file here.
            # For testing, we can print it.
            print("\nSuccessfully processed dummy Permit:")
            print(json.dumps(permit_data, indent=2))
        else:
            print("Failed to process dummy Permit PDF.")

    except ImportError:
        print("ReportLab not found. Skipping dummy Permit PDF creation and test.")
    except Exception as e:
        print(f"Error during Permit processor test: {e}")

