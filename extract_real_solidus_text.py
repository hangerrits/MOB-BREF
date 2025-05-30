#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/extract_real_solidus_text.py

"""
Extract volledige tekst van Solidus vergunning
"""

import fitz
import os
from complete_compliance_system import CompleteComplianceSystem

def extract_and_analyze_solidus():
    """Extract en analyseer volledige Solidus vergunning"""
    
    pdf_path = '/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Industrie/250113-0 Ontwerpbesluit.pdf'
    
    print("📄 === EXTRACTIE VOLLEDIGE SOLIDUS VERGUNNING ===")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF niet gevonden: {pdf_path}")
        return None
    
    try:
        # Extract complete text
        doc = fitz.open(pdf_path)
        full_text = ""
        
        print(f"📖 Extracting tekst van {len(doc)} pagina's...")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text += f"\\n--- PAGINA {page_num + 1} ---\\n"
            full_text += text
        
        doc.close()
        
        print(f"✅ Tekst geëxtraheerd: {len(full_text):,} karakters")
        
        # Save extracted text
        with open('solidus_full_text.txt', 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"💾 Tekst opgeslagen in solidus_full_text.txt")
        
        # Analyze key terms
        text_lower = full_text.lower()
        
        print(f"\\n🔍 === KEY TERMS ANALYSE ===")
        
        # Industry type analysis
        industry_terms = {
            'afval': full_text.lower().count('afval'),
            'reject': full_text.lower().count('reject'),
            'verwerking': full_text.lower().count('verwerking'),
            'thermisch': full_text.lower().count('thermisch'),
            'verbranding': full_text.lower().count('verbranding'),
            'emissie': full_text.lower().count('emissie'),
            'energie': full_text.lower().count('energie'),
            'monitoring': full_text.lower().count('monitoring'),
            'bref': full_text.lower().count('bref'),
            'bat': full_text.lower().count('bat'),
            'beste beschikbare': full_text.lower().count('beste beschikbare')
        }
        
        print("Gevonden termen:")
        for term, count in industry_terms.items():
            if count > 0:
                print(f"  {term}: {count}x")
        
        # Capacity analysis
        capacity_terms = ['ton/jaar', 'mw', 'thermisch vermogen', 'capaciteit']
        print(f"\\nCapaciteits indicatoren:")
        for term in capacity_terms:
            if term in text_lower:
                print(f"  ✅ {term} gevonden")
        
        # Run compliance analysis with real text
        print(f"\\n🔬 === COMPLIANCE ANALYSE MET ECHTE TEKST ===")
        
        system = CompleteComplianceSystem()
        
        # Mock extraction to use real text
        def mock_extract_text_and_metadata(pdf_path):
            return {
                'full_text': full_text,
                'title': 'Ontwerpbesluit Solidus Solutions Rejectverwerker',
                'pages': [{'page_number': i+1, 'text': full_text} for i in range(47)]
            }
        
        # Replace function temporarily
        original_extract = system.analyze_complete_permit.__globals__['extract_text_and_metadata']
        system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = mock_extract_text_and_metadata
        
        try:
            results = system.analyze_complete_permit(
                pdf_path, 
                output_dir="analysis_outputs/solidus_real_analysis"
            )
            
            print(f"\\n🎉 === RESULTATEN MET ECHTE TEKST ===")
            
            if "applicability_analysis" in results:
                analysis = results["applicability_analysis"]
                print(f"📊 Toepasselijkheidsanalyse:")
                print(f"  🏭 Primaire sector: {analysis['permit_classification']['primary_sector']}")
                print(f"  🔍 Activiteiten: {', '.join(analysis['permit_classification']['detected_categories'])}")
                print(f"  ✅ Van toepassing: {len(analysis['applicable_brefs'])} BREFs")
                print(f"  🏛️ RIE activiteiten: {len(analysis['applicable_rie'])}")
                
                print(f"\\n📋 Belangrijkste van toepassing zijnde BREFs:")
                for bref in analysis['applicable_brefs'][:8]:  # Top 8
                    type_icon = "🔄" if bref['type'] == "HORIZONTAAL" else "🏭"
                    print(f"  {type_icon} {bref['bref_id']}: {bref['title']}")
                    print(f"     └─ {bref['applicability']}")
            
            if "report_files" in results:
                files = results["report_files"]
                print(f"\\n📄 Rapporten met echte tekst:")
                if files.get("html_path"):
                    print(f"  📝 HTML: {files['html_path']}")
                if files.get("pdf_path"):
                    print(f"  📄 PDF: {files['pdf_path']}")
            
            return results
            
        finally:
            # Restore original function
            system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = original_extract
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    extract_and_analyze_solidus()