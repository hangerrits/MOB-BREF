#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/extract_real_bats_from_bref.py

"""
Extract Real BAT Conclusions from BREF Documents
Shows how to properly extract actual BATs from the PDF documents
"""

import fitz
import os
import re
from typing import List, Dict, Tuple

def extract_real_ene_bats():
    """Extract real BAT conclusions from ENE BREF document"""
    
    print("📋 === EXTRACTING REAL BAT CONCLUSIONS FROM ENE BREF ===")
    
    ene_path = "/Users/han/Code/MOB-BREF/regulatory_data/brefs/ENE_bref.pdf"
    
    if not os.path.exists(ene_path):
        print(f"❌ ENE BREF not found at: {ene_path}")
        return None
    
    try:
        # Open PDF
        doc = fitz.open(ene_path)
        total_pages = len(doc)
        print(f"📄 ENE BREF opened: {total_pages} pages")
        
        # You mentioned page 303 (PDF page) = document page 272
        # Let's extract that specific page first
        target_page = 302  # 0-indexed, so PDF page 303 = index 302
        
        if target_page < total_pages:
            page = doc[target_page]
            page_text = page.get_text()
            
            print(f"\\n📃 === PAGE {target_page + 1} (PDF page 303, doc page 272) ===")
            print("First 1000 characters:")
            print(page_text[:1000])
            print("\\n" + "="*50)
            
            # Look for BAT overview pattern
            bat_overview_lines = []
            lines = page_text.split('\\n')
            
            in_bat_section = False
            for line in lines:
                line = line.strip()
                if 'BAT' in line and ('overview' in line.lower() or 'list' in line.lower()):
                    in_bat_section = True
                    print(f"Found BAT overview section: {line}")
                
                if in_bat_section:
                    bat_overview_lines.append(line)
                    
                    # Look for numbered BAT entries
                    if re.match(r'^\\d+\\.', line):
                        print(f"Found BAT entry: {line}")
        
        # Now extract actual BAT text sections
        print(f"\\n🔍 === SEARCHING FOR ACTUAL BAT DEFINITIONS ===")
        
        extracted_bats = []
        
        # Search through pages around and after the overview
        start_page = max(0, target_page - 5)
        end_page = min(total_pages, target_page + 50)
        
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for BAT definition patterns
            bat_definitions = find_bat_definitions(page_text, page_num + 1)
            extracted_bats.extend(bat_definitions)
        
        # Print found BATs
        print(f"\\n📋 === EXTRACTED {len(extracted_bats)} REAL BAT CONCLUSIONS ===")
        
        for i, bat in enumerate(extracted_bats[:10]):  # Show first 10
            print(f"\\n{i+1}. {bat['bat_number']}")
            print(f"   Text: {bat['text'][:200]}...")
            print(f"   Page: {bat['page']}")
        
        if len(extracted_bats) > 10:
            print(f"\\n... and {len(extracted_bats) - 10} more BATs")
        
        doc.close()
        
        # Save extracted BATs to file
        save_extracted_bats(extracted_bats, "ENE")
        
        return extracted_bats
        
    except Exception as e:
        print(f"❌ Error extracting BATs: {e}")
        return None

def find_bat_definitions(text: str, page_num: int) -> List[Dict]:
    """Find BAT definitions in text using pattern matching"""
    
    bat_definitions = []
    
    # Pattern 1: "1. BAT is to..." or "BAT 1 is to..."
    pattern1 = r'(\\d+\\.\\s*BAT\\s+is\\s+to\\s+[^\\n]+(?:\\n[^\\n]*)*?)(?=\\d+\\.\\s*BAT\\s+is\\s+to|$)'
    matches1 = re.finditer(pattern1, text, re.IGNORECASE | re.MULTILINE)
    
    for match in matches1:
        bat_text = match.group(1).strip()
        bat_number_match = re.match(r'(\\d+)', bat_text)
        if bat_number_match:
            bat_number = f"BAT {bat_number_match.group(1)}"
            bat_definitions.append({
                "bat_number": bat_number,
                "text": bat_text,
                "page": page_num,
                "extraction_method": "Pattern 1"
            })
    
    # Pattern 2: "BAT X. [description]"
    pattern2 = r'(BAT\\s+\\d+\\.\\s+[^\\n]+(?:\\n[^\\n]*)*?)(?=BAT\\s+\\d+\\.|$)'
    matches2 = re.finditer(pattern2, text, re.IGNORECASE | re.MULTILINE)
    
    for match in matches2:
        bat_text = match.group(1).strip()
        bat_number_match = re.search(r'BAT\\s+(\\d+)', bat_text)
        if bat_number_match:
            bat_number = f"BAT {bat_number_match.group(1)}"
            # Avoid duplicates
            if not any(existing['bat_number'] == bat_number for existing in bat_definitions):
                bat_definitions.append({
                    "bat_number": bat_number,
                    "text": bat_text,
                    "page": page_num,
                    "extraction_method": "Pattern 2"
                })
    
    # Pattern 3: Simple numbered list starting with digit
    lines = text.split('\\n')
    current_bat = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line starts with number followed by BAT
        if re.match(r'^\\d+\\.\\s*BAT\\s+is\\s+to', line, re.IGNORECASE):
            # Save previous BAT if exists
            if current_bat and current_text:
                full_text = '\\n'.join(current_text)
                if not any(existing['bat_number'] == current_bat for existing in bat_definitions):
                    bat_definitions.append({
                        "bat_number": current_bat,
                        "text": full_text,
                        "page": page_num,
                        "extraction_method": "Pattern 3"
                    })
            
            # Start new BAT
            bat_match = re.match(r'^(\\d+)\\.', line)
            if bat_match:
                current_bat = f"BAT {bat_match.group(1)}"
                current_text = [line]
        elif current_bat and line and not re.match(r'^\\d+\\.', line):
            # Continue current BAT text
            current_text.append(line)
        elif re.match(r'^\\d+\\.', line):
            # New numbered item, finish current BAT
            if current_bat and current_text:
                full_text = '\\n'.join(current_text)
                if not any(existing['bat_number'] == current_bat for existing in bat_definitions):
                    bat_definitions.append({
                        "bat_number": current_bat,
                        "text": full_text,
                        "page": page_num,
                        "extraction_method": "Pattern 3"
                    })
                current_bat = None
                current_text = []
    
    # Save last BAT if exists
    if current_bat and current_text:
        full_text = '\\n'.join(current_text)
        if not any(existing['bat_number'] == current_bat for existing in bat_definitions):
            bat_definitions.append({
                "bat_number": current_bat,
                "text": full_text,
                "page": page_num,
                "extraction_method": "Pattern 3"
            })
    
    return bat_definitions

def save_extracted_bats(bats: List[Dict], bref_id: str):
    """Save extracted BATs to JSON file"""
    
    import json
    
    filename = f"extracted_{bref_id}_bats.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(bats, f, indent=2, ensure_ascii=False)
    
    print(f"\\n💾 Extracted BATs saved to: {filename}")

def demonstrate_extraction_process():
    """Demonstrate how the extraction process works vs current mock system"""
    
    print("🔍 === DEMONSTRATION: REAL vs MOCK BAT EXTRACTION ===\\n")
    
    print("📋 CURRENT SYSTEM (Mock):")
    print("- Creates predefined list of generic BAT titles")
    print("- Uses simple keyword matching against permit text")
    print("- Does NOT extract real BATs from BREF PDFs")
    print("- Example: 'BAT 1: Management systeem' (generic)")
    
    print("\\n📋 IMPROVED SYSTEM (Real):")
    print("- Extracts actual BAT text from BREF PDF documents")
    print("- Uses pattern matching to find real BAT definitions")
    print("- Compares permit against actual BREF requirements")
    print("- Example: 'BAT 1 is to implement and adhere to an energy efficiency management system (ENEMS)'")
    
    print("\\n🔧 HOW TO IMPLEMENT REAL EXTRACTION:")
    print("1. Download BREF PDFs (✅ Already done)")
    print("2. Extract BAT text using PDF processing (⚠️ Needs implementation)")
    print("3. Parse and structure BAT conclusions (⚠️ Needs implementation)")
    print("4. Compare permit text against real BAT requirements (⚠️ Needs implementation)")
    print("5. Generate compliance assessment based on actual BREF text (⚠️ Needs implementation)")

def create_real_bat_extractor():
    """Create a real BAT extractor that works with actual BREF content"""
    
    print("\\n🔧 === CREATING REAL BAT EXTRACTOR ===")
    
    extractor_code = '''
class RealBATExtractor:
    """Extract real BAT conclusions from BREF PDFs"""
    
    def __init__(self):
        self.bref_cache = {}
    
    def extract_bats_from_bref(self, bref_id: str, pdf_path: str) -> List[Dict]:
        """Extract real BATs from BREF PDF"""
        
        if bref_id in self.bref_cache:
            return self.bref_cache[bref_id]
        
        # 1. Open PDF and extract text
        doc = fitz.open(pdf_path)
        
        # 2. Find BAT conclusions section
        bat_sections = self._find_bat_sections(doc)
        
        # 3. Extract individual BAT definitions
        bats = []
        for section in bat_sections:
            extracted = self._extract_bat_definitions(section)
            bats.extend(extracted)
        
        # 4. Structure and validate BATs
        structured_bats = self._structure_bats(bats)
        
        # 5. Cache results
        self.bref_cache[bref_id] = structured_bats
        
        return structured_bats
    
    def compare_permit_to_real_bats(self, permit_text: str, bref_bats: List[Dict]) -> List[Dict]:
        """Compare permit against real BAT requirements"""
        
        compliance_results = []
        
        for bat in bref_bats:
            # Extract key requirements from BAT text
            requirements = self._extract_bat_requirements(bat['text'])
            
            # Check permit compliance against each requirement
            compliance = self._assess_compliance(permit_text, requirements)
            
            compliance_results.append({
                'bat_number': bat['bat_number'],
                'bat_text': bat['text'],
                'requirements': requirements,
                'compliance_status': compliance['status'],
                'compliance_details': compliance['details'],
                'evidence': compliance['evidence']
            })
        
        return compliance_results
    '''
    
    print("📝 Real BAT Extractor structure created")
    print("💡 This would replace the current mock system")

if __name__ == "__main__":
    print("🔍 === UNDERSTANDING THE CURRENT SYSTEM ===\\n")
    
    demonstrate_extraction_process()
    
    print("\\n" + "="*60)
    
    # Try to extract real BATs from ENE BREF
    extracted_bats = extract_real_ene_bats()
    
    print("\\n" + "="*60)
    
    create_real_bat_extractor()
    
    print("\\n📊 === SUMMARY ===")
    print("Current system: Uses mock/generic BAT conclusions")
    print("Real system needed: Extract actual BAT text from BREF PDFs")
    print("Implementation: Requires PDF parsing and pattern matching")
    print("Benefit: True compliance verification against real BREF requirements")