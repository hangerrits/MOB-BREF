#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/comprehensive_bat_extractor.py

"""
Comprehensive BAT Extractor
Extracts complete BAT conclusions from all BREF PDFs including referenced sections
Creates JSON database with individual BAT entries for permit checking
"""

import fitz
import os
import re
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class ComprehensiveBATExtractor:
    def __init__(self):
        self.bref_dir = "/Users/han/Code/MOB-BREF/regulatory_data/brefs"
        self.extracted_bats = []
        self.bref_documents = {}
        
    def extract_all_bats(self):
        """Extract BATs from all available BREF documents"""
        
        print("🔍 === COMPREHENSIVE BAT EXTRACTION ===")
        print("Extracting complete BAT conclusions including referenced sections\n")
        
        # Find all BREF PDFs
        bref_files = self.find_bref_files()
        
        for bref_file in bref_files:
            print(f"📋 Processing {bref_file['bref_id']} BREF...")
            bats = self.extract_bats_from_bref(bref_file)
            self.extracted_bats.extend(bats)
            print(f"   ✅ Extracted {len(bats)} BATs from {bref_file['bref_id']}")
        
        print(f"\n📊 === EXTRACTION COMPLETE ===")
        print(f"Total BATs extracted: {len(self.extracted_bats)}")
        print(f"BREFs processed: {len(bref_files)}")
        
        return self.extracted_bats
    
    def find_bref_files(self) -> List[Dict]:
        """Find all BREF PDF files"""
        
        bref_files = []
        
        if not os.path.exists(self.bref_dir):
            print(f"❌ BREF directory not found: {self.bref_dir}")
            return bref_files
        
        # Map filename patterns to BREF IDs
        bref_mapping = {
            'ENE': 'ENE_bref.pdf',
            'WT': 'WT_bref.pdf', 
            'WI': 'WI_bref.pdf',
            'EMS': 'EMS_bref.pdf',
            'CWW': 'CWW_bref.pdf',
            'LCP': 'LCP_bref.pdf',
            'STM': 'STM_bref.pdf',
            'STP': 'STP_bref.pdf',
            'STS': 'STS_bref.pdf'
        }
        
        for bref_id, filename in bref_mapping.items():
            filepath = os.path.join(self.bref_dir, filename)
            if os.path.exists(filepath):
                bref_files.append({
                    'bref_id': bref_id,
                    'filepath': filepath,
                    'filename': filename
                })
        
        print(f"📁 Found {len(bref_files)} BREF files: {[f['bref_id'] for f in bref_files]}")
        return bref_files
    
    def extract_bats_from_bref(self, bref_file: Dict) -> List[Dict]:
        """Extract BATs from a specific BREF document"""
        
        bref_id = bref_file['bref_id']
        filepath = bref_file['filepath']
        
        try:
            # Open PDF and cache for reference resolution
            doc = fitz.open(filepath)
            self.bref_documents[bref_id] = doc
            
            total_pages = len(doc)
            print(f"   📄 Opened {bref_id}: {total_pages} pages")
            
            # Extract BATs using BREF-specific logic
            if bref_id == 'ENE':
                bats = self.extract_ene_bats(doc, bref_id)
            elif bref_id == 'WT':
                bats = self.extract_wt_bats(doc, bref_id)
            elif bref_id == 'WI':
                bats = self.extract_wi_bats(doc, bref_id)
            elif bref_id == 'EMS':
                bats = self.extract_ems_bats(doc, bref_id)
            else:
                bats = self.extract_generic_bats(doc, bref_id)
            
            # Resolve references for all BATs
            for bat in bats:
                bat['complete_text'] = self.resolve_bat_references(bat, doc, bref_id)
            
            return bats
            
        except Exception as e:
            print(f"   ❌ Error processing {bref_id}: {e}")
            return []
    
    def extract_ene_bats(self, doc, bref_id: str) -> List[Dict]:
        """Extract ENE BATs with specific logic for energy efficiency BREF"""
        
        bats = []
        
        # ENE BATs are around pages 300-350 based on previous analysis
        start_page = 295
        end_page = 360
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for BAT patterns
            bat_matches = re.finditer(r'BAT\s+(\d+):\s*([^\n]+)', page_text, re.IGNORECASE)
            
            for match in bat_matches:
                bat_number = match.group(1)
                bat_title = match.group(2).strip()
                
                # Get context around the BAT
                start_pos = max(0, match.start() - 200)
                end_pos = min(len(page_text), match.end() + 500)
                context = page_text[start_pos:end_pos].strip()
                
                # Look for section references in the context
                section_refs = self.find_section_references(context)
                
                bat_entry = {
                    'bref_id': bref_id,
                    'bat_number': int(bat_number),
                    'bat_id': f"{bref_id}-BAT-{bat_number}",
                    'title': bat_title,
                    'raw_text': context,
                    'page': page_num + 1,
                    'section_references': section_refs,
                    'extraction_date': datetime.now().isoformat()
                }
                
                bats.append(bat_entry)
        
        # Remove duplicates and sort
        unique_bats = self.remove_duplicate_bats(bats)
        unique_bats.sort(key=lambda x: x['bat_number'])
        
        return unique_bats
    
    def extract_wt_bats(self, doc, bref_id: str) -> List[Dict]:
        """Extract Waste Treatment BATs"""
        
        bats = []
        
        # Search for WT BATs in conclusion sections
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for conclusion sections
            if any(term in page_text.lower() for term in ['conclusion', 'bat conclusion', 'best available']):
                
                # Extract BAT patterns
                bat_matches = re.finditer(r'(\d+\.\d+)\s+BAT\s+is\s+to\s+([^\n]+)', page_text, re.IGNORECASE)
                
                for match in bat_matches:
                    section_num = match.group(1)
                    bat_desc = match.group(2).strip()
                    
                    # Extract BAT number from section
                    bat_number_match = re.search(r'(\d+)', section_num)
                    if bat_number_match:
                        bat_number = bat_number_match.group(1)
                        
                        # Get extended context
                        start_pos = max(0, match.start() - 300)
                        end_pos = min(len(page_text), match.end() + 600)
                        context = page_text[start_pos:end_pos].strip()
                        
                        bat_entry = {
                            'bref_id': bref_id,
                            'bat_number': int(bat_number),
                            'bat_id': f"{bref_id}-BAT-{bat_number}",
                            'title': bat_desc,
                            'raw_text': context,
                            'page': page_num + 1,
                            'section_number': section_num,
                            'section_references': [],
                            'extraction_date': datetime.now().isoformat()
                        }
                        
                        bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def extract_wi_bats(self, doc, bref_id: str) -> List[Dict]:
        """Extract Waste Incineration BATs"""
        return self.extract_generic_bats(doc, bref_id)
    
    def extract_ems_bats(self, doc, bref_id: str) -> List[Dict]:
        """Extract Emissions Monitoring BATs"""
        return self.extract_generic_bats(doc, bref_id)
    
    def extract_generic_bats(self, doc, bref_id: str) -> List[Dict]:
        """Generic BAT extraction for other BREFs"""
        
        bats = []
        
        # Search through all pages for BAT patterns
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Multiple BAT patterns
            patterns = [
                r'BAT\s+(\d+)\s+is\s+to\s+([^\n]+)',
                r'BAT\s+(\d+):\s*([^\n]+)',
                r'(\d+\.\d+)\s+BAT\s+([^\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                
                for match in matches:
                    if 'BAT' in pattern and 'is to' in pattern:
                        bat_number = match.group(1)
                        bat_desc = match.group(2).strip()
                    elif ':' in pattern:
                        bat_number = match.group(1)
                        bat_desc = match.group(2).strip()
                    else:
                        # Extract number from section
                        section_num = match.group(1)
                        bat_desc = match.group(2).strip()
                        bat_number_match = re.search(r'(\d+)', section_num)
                        if bat_number_match:
                            bat_number = bat_number_match.group(1)
                        else:
                            continue
                    
                    # Get context
                    start_pos = max(0, match.start() - 200)
                    end_pos = min(len(page_text), match.end() + 400)
                    context = page_text[start_pos:end_pos].strip()
                    
                    bat_entry = {
                        'bref_id': bref_id,
                        'bat_number': int(bat_number),
                        'bat_id': f"{bref_id}-BAT-{bat_number}",
                        'title': bat_desc,
                        'raw_text': context,
                        'page': page_num + 1,
                        'section_references': [],
                        'extraction_date': datetime.now().isoformat()
                    }
                    
                    bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def find_section_references(self, text: str) -> List[str]:
        """Find section references in BAT text"""
        
        references = []
        
        # Look for section reference patterns
        patterns = [
            r'[Ss]ection\s+(\d+\.?\d*\.?\d*)',
            r'[Cc]hapter\s+(\d+\.?\d*)',
            r'[Aa]nnex\s+([A-Z]+)',
            r'[Tt]able\s+(\d+\.?\d*)',
            r'[Ff]igure\s+(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                ref_type = match.group(0).split()[0].lower()
                ref_number = match.group(1)
                references.append(f"{ref_type} {ref_number}")
        
        return list(set(references))  # Remove duplicates
    
    def resolve_bat_references(self, bat: Dict, doc, bref_id: str) -> str:
        """Resolve section references and include referenced text"""
        
        complete_text = bat['raw_text']
        
        if not bat.get('section_references'):
            return complete_text
        
        print(f"   🔍 Resolving references for {bat['bat_id']}: {bat['section_references']}")
        
        for reference in bat['section_references']:
            referenced_text = self.find_referenced_section(reference, doc, bref_id)
            if referenced_text:
                complete_text += f"\n\n--- REFERENCED {reference.upper()} ---\n{referenced_text}"
        
        return complete_text
    
    def find_referenced_section(self, reference: str, doc, bref_id: str) -> Optional[str]:
        """Find the text of a referenced section"""
        
        # Simple section finding - could be enhanced
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for the section heading
            if reference.lower() in page_text.lower():
                # Extract some context around the reference
                ref_pos = page_text.lower().find(reference.lower())
                if ref_pos != -1:
                    start = max(0, ref_pos - 100)
                    end = min(len(page_text), ref_pos + 1000)
                    return page_text[start:end].strip()
        
        return None
    
    def remove_duplicate_bats(self, bats: List[Dict]) -> List[Dict]:
        """Remove duplicate BAT entries"""
        
        seen = set()
        unique_bats = []
        
        for bat in bats:
            bat_key = (bat['bref_id'], bat['bat_number'])
            if bat_key not in seen:
                seen.add(bat_key)
                unique_bats.append(bat)
        
        return unique_bats
    
    def save_bat_database(self, filename: str = "comprehensive_bat_database.json"):
        """Save extracted BATs to JSON database"""
        
        database = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_bats': len(self.extracted_bats),
                'brefs_processed': list(set(bat['bref_id'] for bat in self.extracted_bats)),
                'extractor_version': 'ComprehensiveBATExtractor v1.0'
            },
            'bats': self.extracted_bats
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 BAT database saved to: {filename}")
        return filename
    
    def generate_review_report(self, filename: str = "bat_extraction_review_report.html"):
        """Generate HTML report for BAT review and validation"""
        
        # Group BATs by BREF
        bats_by_bref = {}
        for bat in self.extracted_bats:
            bref_id = bat['bref_id']
            if bref_id not in bats_by_bref:
                bats_by_bref[bref_id] = []
            bats_by_bref[bref_id].append(bat)
        
        # Sort BATs within each BREF
        for bref_id in bats_by_bref:
            bats_by_bref[bref_id].sort(key=lambda x: x['bat_number'])
        
        html = self.create_review_html(bats_by_bref)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📋 Review report generated: {filename}")
        return filename
    
    def create_review_html(self, bats_by_bref: Dict) -> str:
        """Create HTML review report"""
        
        total_bats = len(self.extracted_bats)
        total_brefs = len(bats_by_bref)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BAT Extraction Review Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .bref-section {{ margin: 30px 0; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }}
        .bref-header {{ background: #2c3e50; color: white; padding: 15px; }}
        .bat-entry {{ border-bottom: 1px solid #eee; padding: 20px; }}
        .bat-entry:last-child {{ border-bottom: none; }}
        .bat-header {{ background: #e8f4f8; padding: 10px; border-radius: 5px; margin-bottom: 10px; }}
        .bat-text {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .references {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 10px; }}
        .validation-box {{ background: #d1ecf1; padding: 15px; border-radius: 5px; margin-top: 15px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 15px; background: #e8f4f8; border-radius: 8px; flex: 1; margin: 0 10px; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #2980b9; }}
        .stat-label {{ color: #7f8c8d; text-transform: uppercase; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 BAT Extraction Review Report</h1>
        <p>Comprehensive review of extracted BAT conclusions from EU BREF documents</p>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Extraction Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{total_bats}</div>
                <div class="stat-label">Total BATs</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_brefs}</div>
                <div class="stat-label">BREFs Processed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len([b for b in self.extracted_bats if b.get('section_references')])}</div>
                <div class="stat-label">With References</div>
            </div>
        </div>
        
        <h3>🎯 Validation Instructions</h3>
        <p><strong>Please review each BAT entry below:</strong></p>
        <ul>
            <li>✅ Check if BAT number and title are correct</li>
            <li>✅ Verify the extracted text captures the complete BAT requirement</li>
            <li>✅ Confirm referenced sections are properly identified</li>
            <li>✅ Validate page numbers are accurate</li>
            <li>❌ Mark any BATs that need correction or re-extraction</li>
        </ul>
    </div>
"""
        
        # Add each BREF section
        for bref_id, bats in bats_by_bref.items():
            html += f"""
    <div class="bref-section">
        <div class="bref-header">
            <h2>📋 {bref_id} BREF - {len(bats)} BATs Extracted</h2>
        </div>
"""
            
            for bat in bats:
                references_html = ""
                if bat.get('section_references'):
                    refs = ", ".join(bat['section_references'])
                    references_html = f'<div class="references"><strong>References:</strong> {refs}</div>'
                
                html += f"""
        <div class="bat-entry">
            <div class="bat-header">
                <h3>{bat['bat_id']}: {bat['title']}</h3>
                <p><strong>Page:</strong> {bat['page']} | <strong>BAT Number:</strong> {bat['bat_number']}</p>
            </div>
            
            <div class="bat-text">{bat.get('complete_text', bat['raw_text'])}</div>
            
            {references_html}
            
            <div class="validation-box">
                <strong>🔍 Validation Checklist:</strong><br>
                □ BAT number correct<br>
                □ Title accurate<br>
                □ Text complete<br>
                □ References resolved<br>
                □ Page number correct<br>
                <strong>Notes:</strong> ___________________________
            </div>
        </div>
"""
            
            html += "</div>"
        
        html += """
    <div style="margin-top: 50px; text-align: center; color: #7f8c8d;">
        <hr>
        <p>🔍 <strong>Review Complete:</strong> Please validate each BAT entry above</p>
        <p>📝 <strong>Next Steps:</strong> Correct any extraction errors and integrate validated BATs into compliance system</p>
        <p>🏭 Generated by ComprehensiveBATExtractor v1.0</p>
    </div>
</body>
</html>
"""
        
        return html

def main():
    """Main extraction process"""
    
    print("🚀 === COMPREHENSIVE BAT EXTRACTION PROCESS ===\n")
    
    # Initialize extractor
    extractor = ComprehensiveBATExtractor()
    
    # Extract all BATs
    extracted_bats = extractor.extract_all_bats()
    
    if not extracted_bats:
        print("❌ No BATs extracted. Check BREF files and extraction logic.")
        return
    
    # Save database
    db_filename = extractor.save_bat_database()
    
    # Generate review report
    report_filename = extractor.generate_review_report()
    
    # Summary
    print(f"\n🎯 === EXTRACTION COMPLETE ===")
    print(f"📊 Total BATs extracted: {len(extracted_bats)}")
    print(f"📁 Database saved: {db_filename}")
    print(f"📋 Review report: {report_filename}")
    
    # Show sample BATs
    print(f"\n📋 Sample extracted BATs:")
    for bat in extracted_bats[:5]:
        print(f"   ✓ {bat['bat_id']}: {bat['title'][:50]}...")
    
    if len(extracted_bats) > 5:
        print(f"   ... and {len(extracted_bats) - 5} more BATs")
    
    print(f"\n🔍 Please review the report: {report_filename}")
    print(f"📝 Validate each BAT entry and provide feedback for corrections")

if __name__ == "__main__":
    main()