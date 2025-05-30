#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/complete_compliance_system.py

"""
Complete Compliance System
1. Toepasselijkheidsanalyse (1 pagina tabel)
2. Gedetailleerde BAT controles per BREF
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from enhanced_compliance_reporter import EnhancedComplianceReporter
from comprehensive_all_bref_system import Uitgebreide_BREF_Processor
from regulatory_data_manager import RegulatoryDataManager
from pdf_processor import extract_text_and_metadata
import weasyprint

class CompleteComplianceSystem:
    """Complete systeem voor EU BAT/RIE compliance verificatie"""
    
    def __init__(self):
        self.applicability_reporter = EnhancedComplianceReporter()
        self.reg_manager = RegulatoryDataManager()
        self.bref_processor = Uitgebreide_BREF_Processor(self.reg_manager)
        
    def analyze_complete_permit(self, pdf_path: str, output_dir: str = "reports") -> Dict[str, Any]:
        """Complete permit analyse: toepasselijkheid + gedetailleerde BAT controles"""
        
        print("🚀 === COMPLETE EU BAT/RIE COMPLIANCE ANALYSE ===")
        
        # Extract permit text
        print("📄 Extracting permit text...")
        extracted_data = extract_text_and_metadata(pdf_path)
        permit_text = extracted_data.get('full_text', '')
        
        if not permit_text:
            print("❌ Failed to extract text from permit")
            return {"error": "Could not extract permit text"}
        
        # Basic permit info
        permit_info = {
            "filename": os.path.basename(pdf_path),
            "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text_length": len(permit_text)
        }
        
        print(f"✅ Extracted {len(permit_text):,} characters")
        
        # Step 1: Toepasselijkheidsanalyse
        print("\n🔍 === STAP 1: TOEPASSELIJKHEIDSANALYSE ===")
        applicability_analysis = self.applicability_reporter.analyze_permit_applicability(permit_text, permit_info)
        
        print(f"✅ Analyse voltooid:")
        print(f"  - Van toepassing: {len(applicability_analysis['applicable_brefs'])} BREFs")
        print(f"  - Mogelijk van toepassing: {len(applicability_analysis['potentially_applicable_brefs'])} BREFs")
        print(f"  - RIE activiteiten: {len(applicability_analysis['applicable_rie'])}")
        
        # Step 2: Gedetailleerde BAT controles voor van toepassing zijnde BREFs
        print("\n🔬 === STAP 2: GEDETAILLEERDE BAT CONTROLES ===")
        
        detailed_results = {}
        applicable_brefs = [bref["bref_id"] for bref in applicability_analysis["applicable_brefs"] if bref["downloaded"]]
        
        print(f"Uitvoeren van gedetailleerde controles voor {len(applicable_brefs)} BREFs...")
        
        for bref_id in applicable_brefs:
            print(f"\n📋 Analyzing {bref_id}...")
            try:
                if bref_id in self.bref_processor.alle_nederlandse_brefs:
                    result = self.bref_processor.nederlandse_bbt_compliance_controle(
                        permit_text, bref_id, permit_info.get("filename", "Unknown")
                    )
                    detailed_results[bref_id] = result
                    print(f"  ✅ {bref_id}: {result.get('total_conclusions', 0)} BBT conclusies gecontroleerd")
                else:
                    print(f"  ⚠️ {bref_id}: BREF niet geconfigureerd voor gedetailleerde analyse")
            except Exception as e:
                print(f"  ❌ {bref_id}: Error - {e}")
                detailed_results[bref_id] = {"error": str(e)}
        
        # Step 3: Generate comprehensive report
        print("\n📊 === STAP 3: RAPPORT GENERATIE ===")
        
        complete_results = {
            "permit_info": permit_info,
            "applicability_analysis": applicability_analysis,
            "detailed_bat_results": detailed_results,
            "report_metadata": {
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_version": "Complete Compliance System v2.0",
                "total_brefs_analyzed": len(detailed_results),
                "total_bat_conclusions": sum(r.get("total_conclusions", 0) for r in detailed_results.values() if isinstance(r, dict))
            }
        }
        
        # Generate HTML report
        html_report = self.generate_complete_html_report(complete_results)
        
        # Save reports
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # HTML report
        html_filename = f"Complete_Compliance_Report_{timestamp}.html"
        html_path = os.path.join(output_dir, html_filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # PDF report
        pdf_filename = f"Complete_Compliance_Report_{timestamp}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        try:
            weasyprint.HTML(string=html_report).write_pdf(pdf_path)
            print(f"📄 PDF report saved: {pdf_path}")
        except Exception as e:
            print(f"⚠️ PDF generation failed: {e}")
            pdf_path = None
        
        print(f"📄 HTML report saved: {html_path}")
        
        complete_results["report_files"] = {
            "html_path": html_path,
            "pdf_path": pdf_path
        }
        
        return complete_results
    
    def generate_complete_html_report(self, results: Dict[str, Any]) -> str:
        """Generate complete HTML report with applicability table + detailed BAT analysis"""
        
        permit_info = results["permit_info"]
        applicability = results["applicability_analysis"]
        detailed_results = results["detailed_bat_results"]
        metadata = results["report_metadata"]
        
        # Header
        html = f"""
        <!DOCTYPE html>
        <html lang="nl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Complete EU BAT/RIE Compliance Rapport</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.4; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 2.2em; }}
                .header p {{ margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9; }}
                .section {{ margin: 30px 0; page-break-inside: avoid; }}
                .section h2 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }}
                .summary-stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; background: #e8f4f8; border-radius: 8px; flex: 1; margin: 0 10px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #2980b9; }}
                .stat-label {{ color: #7f8c8d; text-transform: uppercase; font-size: 0.9em; }}
                .page-break {{ page-break-before: always; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; font-weight: bold; }}
                .compliant {{ background-color: #d4edda; }}
                .partial {{ background-color: #fff3cd; }}
                .non-compliant {{ background-color: #f8d7da; }}
                .bref-section {{ margin: 40px 0; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
                .bref-header {{ background: #2c3e50; color: white; padding: 15px; margin: -20px -20px 20px -20px; border-radius: 10px 10px 0 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏭 Complete EU BAT/RIE Compliance Rapport</h1>
                <p>Volledige analyse conform Industriële Emissies Richtlijn</p>
            </div>
            
            <div class="info-grid">
                <div class="info-box">
                    <h3>📄 Document Informatie</h3>
                    <p><strong>Bestand:</strong> {permit_info["filename"]}</p>
                    <p><strong>Tekst lengte:</strong> {permit_info["text_length"]:,} karakters</p>
                    <p><strong>Extractie datum:</strong> {permit_info["extraction_date"]}</p>
                </div>
                <div class="info-box">
                    <h3>⚙️ Systeem Informatie</h3>
                    <p><strong>Systeem:</strong> {metadata["system_version"]}</p>
                    <p><strong>Rapport datum:</strong> {metadata["generation_time"]}</p>
                    <p><strong>BREFs geanalyseerd:</strong> {metadata["total_brefs_analyzed"]}</p>
                </div>
            </div>
            
            <div class="summary-stats">
                <div class="stat-box">
                    <div class="stat-number">{applicability["analysis_summary"]["applicable_count"]}</div>
                    <div class="stat-label">Van Toepassing</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{applicability["analysis_summary"]["potentially_applicable_count"]}</div>
                    <div class="stat-label">Mogelijk Toepassing</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{metadata["total_bat_conclusions"]}</div>
                    <div class="stat-label">BBT Conclusies</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{len(applicability["applicable_rie"])}</div>
                    <div class="stat-label">RIE Activiteiten</div>
                </div>
            </div>
        """
        
        # Add applicability table
        html += self.applicability_reporter.generate_applicability_table_html(applicability)
        
        # Add page break before detailed analysis
        html += '<div class="page-break"></div>'
        
        # Add detailed BAT analysis
        html += """
            <div class="section">
                <h2>🔬 Gedetailleerde BAT Compliance Analyse</h2>
                <p>Voor elk van toepassing zijnde BREF worden alle BBT conclusies individueel gecontroleerd:</p>
            </div>
        """
        
        for bref_id, bref_result in detailed_results.items():
            if isinstance(bref_result, dict) and "error" not in bref_result:
                html += self._generate_bref_section_html(bref_id, bref_result)
        
        # Footer
        html += f"""
            <div class="section" style="margin-top: 50px; text-align: center; color: #7f8c8d;">
                <hr>
                <p>Rapport gegenereerd op {metadata["generation_time"]} door {metadata["system_version"]}</p>
                <p>🏭 Complete EU BAT/RIE Compliance Verificatie | 🇳🇱 Nederlandse Implementatie</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_bref_section_html(self, bref_id: str, bref_result: Dict[str, Any]) -> str:
        """Generate HTML for detailed BREF analysis section"""
        
        bref_info = self.applicability_reporter.all_brefs.get(bref_id, {})
        
        # Count compliance
        total = bref_result.get("total_conclusions", 0)
        compliant = bref_result.get("compliant_count", 0)
        partial = bref_result.get("partially_compliant_count", 0)
        non_compliant = bref_result.get("non_compliant_count", 0)
        
        html = f"""
        <div class="bref-section">
            <div class="bref-header">
                <h3>📋 {bref_id}: {bref_info.get("title", "Unknown BREF")}</h3>
                <p>Type: {bref_info.get("type", "Unknown")} | BBT Conclusies Geanalyseerd: {total}</p>
            </div>
            
            <div class="summary-stats">
                <div class="stat-box compliant">
                    <div class="stat-number">{compliant}</div>
                    <div class="stat-label">Conform</div>
                </div>
                <div class="stat-box partial">
                    <div class="stat-number">{partial}</div>
                    <div class="stat-label">Gedeeltelijk</div>
                </div>
                <div class="stat-box non-compliant">
                    <div class="stat-number">{non_compliant}</div>
                    <div class="stat-label">Niet-Conform</div>
                </div>
            </div>
        """
        
        # Add important findings
        if "important_findings" in bref_result and bref_result["important_findings"]:
            html += """
            <h4>🎯 Belangrijkste Bevindingen</h4>
            <table>
                <thead>
                    <tr>
                        <th style="width: 15%">BBT</th>
                        <th style="width: 15%">Status</th>
                        <th>Bevindingen</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for finding in bref_result["important_findings"][:10]:  # Show top 10
                status_class = finding["compliance_status"].lower().replace(" ", "-").replace("ë", "e")
                html += f"""
                    <tr class="{status_class}">
                        <td><strong>{finding["bat_id"]}</strong></td>
                        <td>{finding["compliance_status"]}</td>
                        <td>{finding["assessment"][:200]}...</td>
                    </tr>
                """
            
            html += "</tbody></table>"
        
        html += "</div>"
        return html

def test_complete_system():
    """Test complete system with sample permit"""
    system = CompleteComplianceSystem()
    
    # Test with existing permit
    test_permit = "/Users/han/Code/MOB-BREF/permit_sample.pdf"
    if os.path.exists(test_permit):
        print("🧪 Testing complete compliance system...")
        results = system.analyze_complete_permit(test_permit)
        
        print(f"\n✅ Analysis complete!")
        print(f"Reports saved to: {results.get('report_files', {})}")
        return results
    else:
        print("❌ Test permit not found")
        return None

if __name__ == "__main__":
    test_complete_system()