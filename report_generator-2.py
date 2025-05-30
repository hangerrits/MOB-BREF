# /home/ubuntu/bat_rie_checker_app/src/core_logic/report_generator.py
import json
import os
from datetime import datetime
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

# Ensure the output directory for reports (for module's own test)
REPORTS_DIR_MODULE_TEST = os.path.join(os.path.dirname(__file__), "test_generated_reports_rg")
if not os.path.exists(REPORTS_DIR_MODULE_TEST):
    os.makedirs(REPORTS_DIR_MODULE_TEST)

def generate_markdown_report(permit_data: dict, applicable_brefs: list, compliance_results: list, report_id: str) -> str:
    """
    Generates a compliance verification report in Markdown format.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_md = f"# Compliance Verification Report\n\n"
    report_md += f"**Report ID:** {report_id}\n"
    report_md += f"**Generated on:** {timestamp}\n\n"

    report_md += f"## 1. Permit Information\n\n"
    report_md += f"- **Permit ID/Reference:** {permit_data.get('permit_id', 'N/A')}\n"
    report_md += f"- **Permit Title:** {permit_data.get('title', 'N/A')}\n"
    report_md += f"- **Source File:** {permit_data.get('file_path', 'N/A')}\n"
    report_md += f"- **Activity Description:**\n```\n{permit_data.get('activity_description', 'N/A')}\n```\n\n"

    report_md += f"## 2. Applicable BREF Documents\n\n"
    if applicable_brefs:
        for bref in applicable_brefs:
            report_md += f"### BREF ID: {bref.get('bref_id', 'N/A')}\n"
            report_md += f"- **Applicability:** {bref.get('applicability', 'N/A')}\n"
            report_md += f"- **Justification:** {bref.get('justification', 'N/A')}\n\n"
    else:
        report_md += "No BREF documents were analyzed or found applicable.\n\n"

    report_md += f"## 3. BAT Compliance Verification Details\n\n"
    if compliance_results:
        for bat_result in compliance_results:
            report_md += f"### BAT Conclusion ID: {bat_result.get('bat_id', 'N/A')}\n"
            report_md += f"- **Compliance Status:** {bat_result.get('compliance_status', 'N/A')}\n"
            report_md += f"- **Detailed Findings:**\n```\n{bat_result.get('detailed_findings', 'N/A')}\n```\n\n"
    else:
        report_md += "No BAT conclusions were verified against the permit.\n\n"
    
    report_md += "---\nEnd of Report\n"
    return report_md

def generate_pdf_report(markdown_content: str, report_id: str, output_full_path: str) -> str | None:
    """
    Generates a PDF report from Markdown content using WeasyPrint.

    Args:
        markdown_content: The report content in Markdown format.
        report_id: A unique identifier for this report (used in HTML title).
        output_full_path: The absolute path where the PDF file should be saved.

    Returns:
        The absolute path to the generated PDF file, or None if an error occurs.
    """
    try:
        import markdown2 # For converting Markdown to HTML
    except ImportError:
        print("ERROR: markdown2 library is not installed. Please install it: pip3 install markdown2")
        return None

    html_content = markdown2.markdown(markdown_content, extras=["tables", "fenced-code-blocks", "break-on-newline"])
    
    css_style = """
    @page { size: A4; margin: 2cm; }
    body { font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif; line-height: 1.6; font-size: 11pt; }
    h1, h2, h3 { color: #333; line-height: 1.2; }
    h1 { font-size: 24pt; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
    h2 { font-size: 18pt; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    h3 { font-size: 14pt; margin-top: 20px; }
    pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; border-radius: 4px; white-space: pre-wrap; white-space: -moz-pre-wrap; white-space: -pre-wrap; white-space: -o-pre-wrap; word-wrap: break-word; }
    code { font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", monospace; }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Compliance Report - {report_id}</title>
        <style>{css_style}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    try:
        output_dir = os.path.dirname(output_full_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        font_config = FontConfiguration()
        html_doc = HTML(string=full_html, base_url=output_dir)
        html_doc.write_pdf(output_full_path, font_config=font_config)
        print(f"PDF report generated successfully: {output_full_path}")
        return output_full_path
    except Exception as e:
        print(f"Error generating PDF with WeasyPrint: {e}")
        if "font" in str(e).lower():
            print("This might be related to font configuration or missing fonts. Ensure NotoSansCJK-Regular.ttc and wqy-zenhei.ttc are available.")
            print("Expected paths: /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc and /usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
        return None

if __name__ == '__main__':
    print("Testing Report Generator...")
    sample_report_id = "TEST_REPORT_RG_001"
    sample_permit_data = {
        "permit_id": "XYZ/123/2025",
        "title": "Permit for Facility Alpha",
        "file_path": "/path/to/dummy_permit.pdf",
        "activity_description": "The installation is a chemical production facility. Key activities include reaction, distillation, and packaging of product Z. The annual production capacity is 10,000 tonnes of product Z."
    }
    sample_applicable_brefs = [
        {
            "bref_id": "BREF_CHEM_XXL",
            "applicability": "Likely Applicable",
            "justification": "The permit activities (chemical production, distillation) fall directly within the scope of this BREF which covers large volume organic chemical production."
        },
        {
            "bref_id": "BREF_WASTE_INCINERATION",
            "applicability": "Not Applicable",
            "justification": "The permit activities do not mention waste incineration."
        }
    ]
    sample_compliance_results = [
        {
            "bat_id": "BAT_CHEM_VOC_3",
            "compliance_status": "Partially Compliant",
            "detailed_findings": "The permit mentions VOC monitoring (Section 4.2) but does not specify the use of leak detection and repair (LDAR) programs as recommended by BAT 3 for distillation units. Permit condition 3.1 sets a general VOC limit but does not detail specific techniques for fugitive emissions."
        },
        {
            "bat_id": "BAT_CHEM_ENERGY_5",
            "compliance_status": "Compliant",
            "detailed_findings": "The permit requires an annual energy efficiency audit (Section 5.1) and implementation of a heat recovery system for the main reactor (Condition 3.5), aligning with BAT 5 recommendations."
        }
    ]

    print("\n--- Generating Markdown Report ---")
    markdown_report_content = generate_markdown_report(sample_permit_data, sample_applicable_brefs, sample_compliance_results, sample_report_id)
    md_filename = f"{sample_report_id}.md"
    md_path = os.path.join(REPORTS_DIR_MODULE_TEST, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_report_content)
    print(f"Markdown report saved to: {md_path}")

    print("\n--- Generating PDF Report ---")
    try:
        import markdown2
    except ImportError:
        print("markdown2 library not found. PDF generation test will be skipped.")
        print("Please install it using: pip3 install markdown2")
    else:
        pdf_output_filename = f"{sample_report_id}.pdf"
        pdf_full_output_path_test = os.path.join(REPORTS_DIR_MODULE_TEST, pdf_output_filename)
        generated_pdf_path = generate_pdf_report(markdown_report_content, sample_report_id, pdf_full_output_path_test)
        if generated_pdf_path:
            print(f"PDF report should be available at: {generated_pdf_path}")
        else:
            print("PDF report generation failed.")

