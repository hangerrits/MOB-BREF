# /home/ubuntu/bat_rie_checker/core_logic/pdf_processor.py

from docling.document_converter import DocumentConverter
import json

def extract_text_and_metadata(pdf_path: str) -> dict:
    try:
        converter = DocumentConverter()
        result = converter.convert(source=pdf_path)
        doc = result.document # This should be a DoclingDocument instance

        extracted_data = {
            "title": None,
            "full_text": "",
            "pages": []
        }

        if hasattr(doc, 'metadata') and doc.metadata and 'title' in doc.metadata:
            extracted_data["title"] = doc.metadata['title']
        elif hasattr(doc, 'title') and doc.title:
             extracted_data["title"] = doc.title

        if hasattr(doc, 'export_to_markdown'):
            extracted_data["full_text"] = doc.export_to_markdown()
        else:
            extracted_data["full_text"] = "DoclingDocument has no export_to_markdown method."
            print("DEBUG: DoclingDocument has no export_to_markdown method.")

        print(f"DEBUG: doc object type: {type(doc)}")
        if hasattr(doc, 'pages') and isinstance(doc.pages, dict):
            print(f"DEBUG: doc.pages is a dictionary. Iterating through its values.")
            
            for page_number_key, page_object in doc.pages.items():
                page_md = ""
                # The key from doc.pages dict is likely the 0-indexed page number or a 1-indexed page number.
                # Let's assume it's 1-indexed for now or use page_object.page_idx if available.
                current_page_display_number = page_number_key 

                try:
                    if hasattr(page_object, 'page_idx'): # docling page objects usually have page_idx (0-indexed)
                         current_page_display_number = page_object.page_idx + 1
                    
                    if hasattr(page_object, 'export_to_markdown'):
                        page_md = page_object.export_to_markdown()
                        print(f"DEBUG: Page (key {page_number_key}, display {current_page_display_number}) exported to markdown.")
                    elif hasattr(page_object, 'text'):
                        page_md = page_object.text
                        print(f"DEBUG: Page (key {page_number_key}, display {current_page_display_number}) .text attribute used.")
                    else:
                        page_md = "Page object has no export_to_markdown or text method."
                        print(f"DEBUG: Page (key {page_number_key}, display {current_page_display_number}) has no direct text export method. Type: {type(page_object)}")
                    
                    page_data = {
                        "page_number": current_page_display_number,
                        "text": page_md
                    }
                    extracted_data["pages"].append(page_data)

                except Exception as page_processing_e:
                    error_msg = f"Error processing page_object (key {page_number_key}): {page_processing_e}. Type: {type(page_object)}"
                    print(f"ERROR: {error_msg}")
                    extracted_data["pages"].append({
                        "page_number": current_page_display_number,
                        "text": f"Error processing this page: {page_processing_e}",
                        "error_detail": str(page_processing_e)
                    })
            # Sort pages by page_number just in case the dictionary iteration order wasn't sequential
            extracted_data["pages"] = sorted(extracted_data["pages"], key=lambda p: p["page_number"])
        else:
            print(f"DEBUG: doc object has no 'pages' attribute or it's not a dictionary. Type: {type(doc.pages) if hasattr(doc, 'pages') else 'N/A'}")
            
        return extracted_data

    except Exception as e:
        fatal_error_msg = f"FATAL SCRIPT-LEVEL Error extracting PDF with Docling: {e}"
        print(fatal_error_msg)
        return {
            "error": fatal_error_msg,
            "title": None,
            "full_text": None,
            "pages": []
        }

if __name__ == '__main__':
    print("Attempting to create a dummy PDF for testing...")
    try:
        from reportlab.pdfgen import canvas
        sample_pdf_path = "/home/ubuntu/bat_rie_checker/sample_test.pdf"
        c = canvas.Canvas(sample_pdf_path)
        c.setTitle("Sample Test Document")
        c.drawString(100, 750, "Page 1: This is a sample PDF document for Docling testing.")
        c.drawString(100, 730, "This is the first paragraph on the first page.")
        c.showPage()
        c.drawString(100, 750, "Page 2: This is the second page of the sample document.")
        c.drawString(100, 730, "Another paragraph here, on the second page.")
        c.save()
        print(f"Dummy PDF '{sample_pdf_path}' created.")
        
        print(f"\nTesting extraction for: {sample_pdf_path}")
        extraction_result = extract_text_and_metadata(sample_pdf_path)
        
        print("\nExtraction Result (JSON):")
        print(json.dumps(extraction_result, indent=2))

    except ImportError:
        print("ReportLab not found. Skipping dummy PDF creation and test.")
    except Exception as e:
        print(f"Error during __main__ execution: {e}")

