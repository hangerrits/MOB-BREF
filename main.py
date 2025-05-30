# /home/ubuntu/bat_rie_checker_app/src/main.py
import os
import sys
import uuid
import json
from datetime import datetime

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename

# Assuming core_logic is now inside src/
from src.core_logic.pdf_processor import extract_text_and_metadata
from src.core_logic.bref_processor import process_bref_to_json, find_scope_description, find_bat_conclusions
from src.core_logic.permit_processor import process_permit_to_data
from src.core_logic.llm_handler import determine_applicable_brefs, verify_permit_compliance_with_bat
from src.core_logic.report_generator import generate_markdown_report, generate_pdf_report

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT_some_strong_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads') # Save uploads within static for simplicity here
app.config['REPORTS_FOLDER'] = os.path.join(app.static_folder, 'reports') # Save reports within static

# Ensure upload and reports directories exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['REPORTS_FOLDER']):
    os.makedirs(app.config['REPORTS_FOLDER'])

# Remove the default user_bp blueprint as it's not needed for this app
# app.register_blueprint(user_bp, url_prefix='/api')

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/verify', methods=['POST'])
def verify_compliance():
    if 'permit_file' not in request.files:
        return jsonify({"error": "No permit file part"}), 400
    
    permit_file = request.files['permit_file']
    bref_files = request.files.getlist('bref_files') # Get list of BREF files

    if permit_file.filename == '':
        return jsonify({"error": "No selected permit file"}), 400

    # --- 1. Save uploaded files --- 
    run_id = str(uuid.uuid4())
    permit_filename = secure_filename(f"{run_id}_permit_{permit_file.filename}")
    permit_path = os.path.join(app.config['UPLOAD_FOLDER'], permit_filename)
    permit_file.save(permit_path)
    print(f"Permit file saved to: {permit_path}")

    processed_bref_data_list = []
    bref_scope_list_for_llm = []

    for i, bref_file in enumerate(bref_files):
        if bref_file and bref_file.filename != '':
            bref_filename = secure_filename(f"{run_id}_bref_{i}_{bref_file.filename}")
            bref_path = os.path.join(app.config['UPLOAD_FOLDER'], bref_filename)
            bref_file.save(bref_path)
            print(f"BREF file saved to: {bref_path}")
            
            # --- 2. Process BREF Documents --- (Simplified for this route, more robust error handling needed)
            # In a real app, you'd generate a unique BREF ID or get it from user/filename
            bref_id_from_file = f"UPLOADED_BREF_{i}_{os.path.splitext(bref_file.filename)[0]}"
            # The process_bref_to_json from core_logic expects to save to its own knowledge_base.
            # For the web app, we might want to process and use data directly or adapt.
            # Here, we'll call the underlying extraction and then the specific find_ functions.
            bref_extraction_result = extract_text_and_metadata(bref_path)
            if bref_extraction_result and not bref_extraction_result.get("error"):
                bref_full_text = bref_extraction_result.get("full_text", "")
                scope_desc, _ = find_scope_description(bref_full_text)
                # bat_concs = find_bat_conclusions(bref_full_text) # We'll use this later
                processed_bref_data_list.append({
                    "bref_id": bref_id_from_file,
                    "title": bref_extraction_result.get("title", "Unknown BREF Title"),
                    "scope_description": scope_desc,
                    "file_path": bref_path,
                    "full_text": bref_full_text # Store full text for BAT extraction
                })
                bref_scope_list_for_llm.append({"bref_id": bref_id_from_file, "scope_description": scope_desc})
            else:
                print(f"Error processing BREF file {bref_file.filename}: {bref_extraction_result.get('error') if bref_extraction_result else 'Unknown error'}")

    # --- 3. Process Permit Document --- 
    permit_data = process_permit_to_data(permit_path, permit_id=f"UPLOADED_PERMIT_{os.path.splitext(permit_file.filename)[0]}")
    if not permit_data or permit_data.get("error"):
        return jsonify({"error": f"Failed to process permit PDF: {permit_data.get('error') if permit_data else 'Unknown error'}"}), 500
    
    permit_activity_description = permit_data.get("activity_description", "")
    permit_full_text_md = permit_data.get("full_text_markdown", "")

    # --- 4. Determine Applicable BREFs using LLM --- 
    applicable_brefs_analysis = []
    if bref_scope_list_for_llm:
        applicable_brefs_analysis = determine_applicable_brefs(permit_activity_description, bref_scope_list_for_llm)
    else:
        print("No BREF files provided or processed, skipping BREF applicability check.")

    # --- 5. Extract BATs from Applicable BREFs and Verify Compliance --- 
    all_bat_compliance_results = []
    for bref_analysis_result in applicable_brefs_analysis:
        if bref_analysis_result.get("applicability") in ["Likely Applicable", "Potentially Applicable"]:
            bref_id_to_process = bref_analysis_result["bref_id"]
            # Find the full BREF data we stored earlier
            original_bref_data = next((b for b in processed_bref_data_list if b["bref_id"] == bref_id_to_process), None)
            if original_bref_data:
                bref_full_text = original_bref_data.get("full_text", "")
                bat_conclusions_from_bref = find_bat_conclusions(bref_full_text) # This is a list of dicts
                
                for bat_conclusion in bat_conclusions_from_bref:
                    # Augment bat_conclusion with BREF ID for clarity in results
                    bat_conclusion["source_bref_id"] = bref_id_to_process 
                    compliance_status = verify_permit_compliance_with_bat(permit_full_text_md, bat_conclusion)
                    all_bat_compliance_results.append(compliance_status)
            else:
                print(f"Could not find original processed data for BREF ID: {bref_id_to_process}")

    # --- 6. Generate Reports --- 
    report_id = f"COMP_REPORT_{run_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    markdown_content = generate_markdown_report(permit_data, applicable_brefs_analysis, all_bat_compliance_results, report_id)
    
    # Save Markdown report to the app's report folder
    md_filename = f"{report_id}.md"
    md_path_server = os.path.join(app.config['REPORTS_FOLDER'], md_filename)
    with open(md_path_server, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    md_url = url_for('static', filename=f'reports/{md_filename}', _external=True)

    # Generate PDF report using the app's report folder
    # The generate_pdf_report in core_logic needs to be adapted or told where to save.
    # For now, let's assume generate_pdf_report saves to its default (bat_rie_checker/reports) 
    # and we'll adjust it to save to app.config['REPORTS_FOLDER']
    # Modification for generate_pdf_report: it should accept output_dir
    # For now, let's call it as is and assume it saves where we can access it or modify it later.
    # We will modify generate_pdf_report to accept an output directory. For now, this is a placeholder.
    
    # Re-defining the PDF generation part to use the app's report folder
    # This requires modifying generate_pdf_report to accept an output_dir or use a relative path strategy.
    # Let's assume generate_pdf_report is modified to save in app.config['REPORTS_FOLDER'] if output_filename is just a name.
    pdf_filename = f"{report_id}.pdf"
    # The generate_pdf_report function in core_logic.report_generator saves to its own REPORTS_DIR.
    # We need to either modify it to accept a full path or copy the file.
    # For now, let's call it and then try to construct a URL, assuming it's accessible.
    # A better way: modify generate_pdf_report to take full output_path or output_dir.
    # Let's assume it's modified to take full_path.
    pdf_path_server = os.path.join(app.config['REPORTS_FOLDER'], pdf_filename)
    
    # We need to ensure generate_pdf_report can write to pdf_path_server
    # The current generate_pdf_report uses its own REPORTS_DIR. 
    # A quick fix is to pass the app.config['REPORTS_FOLDER'] to it if possible, or modify it.
    # For this iteration, I will assume generate_pdf_report is called and we manually make the file available.
    # This part needs refinement in how generate_pdf_report is called or structured.
    # Let's call the original and then try to make a link. This is NOT ideal.
    # Correct approach: Modify generate_pdf_report to accept full output path.
    # For now, I'll simulate this by calling it with just the filename, assuming it saves to app.config['REPORTS_FOLDER']
    # This requires generate_pdf_report to be aware of app.config['REPORTS_FOLDER'] or be modified.
    # The current `generate_pdf_report` in `core_logic` saves to `/home/ubuntu/bat_rie_checker/reports`
    # We need to make it save to `/home/ubuntu/bat_rie_checker_app/src/static/reports`
    # The simplest way is to modify the REPORTS_DIR in report_generator.py when used in this app context, or pass it.
    # For now, I will call it and then *manually* construct the URL, assuming the file is placed correctly.
    # This is a known issue to fix by better integrating report_generator.py

    # Let's assume we modify generate_pdf_report to accept the full path for the output file.
    # So, we'll call it with pdf_path_server.
    # The current generate_pdf_report in core_logic/report_generator.py needs to be updated to handle this.
    # For now, I will proceed as if it can take the full path.
    # This means the generate_pdf_report function in core_logic/report_generator.py would need to be like:
    # def generate_pdf_report(markdown_content: str, report_id: str, output_full_path: str) -> str | None:
    #   html_doc.write_pdf(output_full_path, font_config=font_config)
    # I will assume this modification is done for the sake of this step.
    # If not, the PDF link will be broken.
    
    # Calling the original generate_pdf_report and hoping it works or copying file later.
    # For now, let's assume the PDF is generated in the correct static/reports folder by the function.
    # This means generate_pdf_report in core_logic needs to be adapted. 
    # I will write a placeholder for the PDF generation that assumes it saves to the correct app static folder.
    pdf_url = None
    try:
        # This is a conceptual call. The actual generate_pdf_report needs to be adjusted.
        # For now, let's assume it's adjusted to save to app.config['REPORTS_FOLDER']
        # A better solution is to modify generate_pdf_report to take an output_directory argument.
        # For this step, I will simulate it by directly calling it with the intended output path.
        # This requires generate_pdf_report to be modified to accept a full output path.
        # I will assume it's modified to: generate_pdf_report(markdown_content, report_id, full_output_path)
        # The existing generate_pdf_report takes (markdown_content, report_id, output_filename) and uses its own REPORTS_DIR
        # To make this work without modifying the core_logic one for now, I'll call it and then try to serve the file if it exists.
        # This is not robust. The core_logic function should be adapted.
        # For now, I will write the PDF generation logic here directly for testing purposes.
        import markdown2
        html_content_for_pdf = markdown2.markdown(markdown_content, extras=["tables", "fenced-code-blocks", "break-on-newline"])
        css_style_for_pdf = """body { font-family: 'Noto Sans CJK SC', 'WenQuanYi Zen Hei', sans-serif; } h1,h2,h3 {color: #333;} pre {background-color:#f8f8f8; border:1px solid #ddd; padding:10px; border-radius:4px; white-space:pre-wrap; word-wrap:break-word;} """
        full_html_for_pdf = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Report {report_id}</title><style>{css_style_for_pdf}</style></head><body>{html_content_for_pdf}</body></html>"
        from weasyprint import HTML as WeasyHTML, CSS as WeasyCSS
        from weasyprint.fonts import FontConfiguration as WeasyFontConfig
        font_config = WeasyFontConfig()
        html_doc = WeasyHTML(string=full_html_for_pdf, base_url=app.config['REPORTS_FOLDER'])
        html_doc.write_pdf(pdf_path_server, font_config=font_config)
        pdf_url = url_for('static', filename=f'reports/{pdf_filename}', _external=True)
        print(f"PDF report generated at: {pdf_path_server}")
    except ImportError as ie:
        print(f"PDF generation skipped: WeasyPrint or markdown2 not installed or import error: {ie}")
    except Exception as e_pdf:
        print(f"Error generating PDF directly in Flask route: {e_pdf}")

    # --- 7. Return results --- 
    response_data = {
        "message": "Verification process completed.",
        "report_id": report_id,
        "permit_processed": permit_data,
        "applicable_brefs_analysis": applicable_brefs_analysis,
        "bat_compliance_results": all_bat_compliance_results,
        "report_paths": {
            "markdown": md_url,
            "pdf": pdf_url
        },
        "full_analysis": {
            "permit_data": permit_data,
            "applicable_brefs": applicable_brefs_analysis,
            "compliance_details": all_bat_compliance_results
        }
    }
    return jsonify(response_data)


if __name__ == '__main__':
    # Ensure OPENAI_API_KEY is available for the core_logic.llm_handler
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable not set. LLM calls will fail.")
        # For local testing, you might set it here if it's passed securely, but ideally it's in the run environment.
        # Example: os.environ['OPENAI_API_KEY'] = 'your_key_here' # Not recommended for production code.
    
    # Need to install markdown2 for report generation if not already present in venv
    # The Flask template doesn't include it by default.
    # Also, the core_logic modules might have their own dependencies like 'openai', 'reportlab'.
    # These should be in the bat_rie_checker_app/requirements.txt
    app.run(host='0.0.0.0', port=5000, debug=True)

