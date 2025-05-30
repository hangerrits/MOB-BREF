#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/improved_bat_extractor.py

"""
Improved BAT Extractor for Real BREF Content
Demonstrates extracting actual BAT conclusions from ENE BREF
"""

import fitz
import os
import re
import json
from typing import List, Dict, Tuple

def extract_real_ene_bats_improved():
    """Extract real BAT conclusions from ENE BREF with improved pattern matching"""
    
    print("🔍 === IMPROVED ENE BAT EXTRACTION ===" )
    
    ene_path = "/Users/han/Code/MOB-BREF/regulatory_data/brefs/ENE_bref.pdf"
    
    if not os.path.exists(ene_path):
        print(f"❌ ENE BREF not found at: {ene_path}")
        return None
    
    try:
        # Open PDF
        doc = fitz.open(ene_path)
        total_pages = len(doc)
        print(f"📄 ENE BREF opened: {total_pages} pages")
        
        # Based on user input: "PDF page 303, document page 272" has overview of 29 BATs
        # Let's search more broadly around this area
        start_page = 300  # Start a bit earlier
        end_page = 350    # Search more pages
        
        all_bat_text = []
        extracted_bats = []
        
        print(f"🔍 Searching pages {start_page+1} to {end_page} for BAT definitions...")
        
        for page_num in range(start_page, min(end_page, total_pages)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for BAT patterns in this page
            if 'BAT' in page_text:
                all_bat_text.append({
                    'page': page_num + 1,
                    'text': page_text
                })
                
                # Extract individual BATs from this page
                page_bats = extract_bats_from_page_text(page_text, page_num + 1)
                extracted_bats.extend(page_bats)
        
        # Try to find the overview section specifically mentioned by user
        overview_bats = find_bat_overview_section(all_bat_text)
        if overview_bats:
            extracted_bats.extend(overview_bats)
        
        # Remove duplicates and clean up
        unique_bats = remove_duplicates(extracted_bats)
        
        print(f"\n📋 === FOUND {len(unique_bats)} UNIQUE BAT REFERENCES ===")
        
        for i, bat in enumerate(unique_bats[:15]):  # Show first 15
            print(f"\n{i+1}. {bat['bat_id']}: {bat['title']}")
            print(f"   Page: {bat['page']}")
            print(f"   Text: {bat['text'][:150]}...")
        
        if len(unique_bats) > 15:
            print(f"\n... and {len(unique_bats) - 15} more BAT references")
        
        # Save results
        save_extracted_bats(unique_bats, "ENE_improved")
        
        # Demonstrate the gap with current system
        demonstrate_real_vs_mock_gap(unique_bats)
        
        doc.close()
        return unique_bats
        
    except Exception as e:
        print(f"❌ Error extracting BATs: {e}")
        return None

def extract_bats_from_page_text(text: str, page_num: int) -> List[Dict]:
    """Extract BAT references from page text"""
    
    bats = []
    
    # Pattern 1: "BAT X:" followed by description
    pattern1 = r'BAT\s+(\d+):\s*([^\n]+)'
    matches1 = re.finditer(pattern1, text, re.IGNORECASE)
    
    for match in matches1:
        bat_num = match.group(1)
        bat_desc = match.group(2).strip()
        
        bats.append({
            'bat_id': f'BAT {bat_num}',
            'title': bat_desc,
            'text': match.group(0),
            'page': page_num,
            'extraction_method': 'Pattern 1: BAT X:'
        })
    
    # Pattern 2: "BAT X" standalone references
    pattern2 = r'BAT\s+(\d+)(?:\s|$)'
    matches2 = re.finditer(pattern2, text, re.IGNORECASE)
    
    for match in matches2:
        bat_num = match.group(1)
        
        # Try to find context around this BAT reference
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 200)
        context = text[start:end].strip()
        
        bats.append({
            'bat_id': f'BAT {bat_num}',
            'title': f'BAT {bat_num} reference',
            'text': context,
            'page': page_num,
            'extraction_method': 'Pattern 2: BAT reference'
        })
    
    # Pattern 3: Look for ENEMS and other energy efficiency terms
    if 'ENEMS' in text or 'energy efficiency management' in text.lower():
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'ENEMS' in line or 'energy efficiency management' in line.lower():
                context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                context = '\n'.join(context_lines)
                
                bats.append({
                    'bat_id': 'BAT 1',
                    'title': 'Energy Efficiency Management System (ENEMS)',
                    'text': context,
                    'page': page_num,
                    'extraction_method': 'Pattern 3: ENEMS detection'
                })
                break
    
    return bats

def find_bat_overview_section(all_bat_text: List[Dict]) -> List[Dict]:
    """Find the BAT overview section with the 29 BATs"""
    
    overview_bats = []
    
    for page_data in all_bat_text:
        text = page_data['text']
        page_num = page_data['page']
        
        # Look for overview indicators
        if any(indicator in text.lower() for indicator in [
            'overview', 'summary', 'list of bat', 'bat conclusions',
            '29 bat', 'energy efficiency', 'chapter 4'
        ]):
            print(f"📍 Found potential overview on page {page_num}")
            
            # Extract all BAT references from this overview
            lines = text.split('\n')
            current_bat = None
            current_desc = []
            
            for line in lines:
                line = line.strip()
                
                # Check if line contains BAT reference
                bat_match = re.search(r'BAT\s+(\d+)', line, re.IGNORECASE)
                if bat_match:
                    # Save previous BAT if exists
                    if current_bat and current_desc:
                        overview_bats.append({
                            'bat_id': current_bat,
                            'title': ' '.join(current_desc),
                            'text': f"{current_bat}: {' '.join(current_desc)}",
                            'page': page_num,
                            'extraction_method': 'Overview section'
                        })
                    
                    # Start new BAT
                    current_bat = f"BAT {bat_match.group(1)}"
                    current_desc = [line.replace(bat_match.group(0), '').strip()]
                
                elif current_bat and line and not re.match(r'^(Chapter|Page|\d+)', line):
                    # Continue current BAT description
                    current_desc.append(line)
            
            # Save last BAT
            if current_bat and current_desc:
                overview_bats.append({
                    'bat_id': current_bat,
                    'title': ' '.join(current_desc),
                    'text': f"{current_bat}: {' '.join(current_desc)}",
                    'page': page_num,
                    'extraction_method': 'Overview section'
                })
    
    return overview_bats

def remove_duplicates(bats: List[Dict]) -> List[Dict]:
    """Remove duplicate BAT entries"""
    
    seen = set()
    unique_bats = []
    
    for bat in bats:
        bat_key = bat['bat_id']
        if bat_key not in seen:
            seen.add(bat_key)
            unique_bats.append(bat)
    
    # Sort by BAT number
    def get_bat_number(bat):
        match = re.search(r'(\d+)', bat['bat_id'])
        return int(match.group(1)) if match else 999
    
    unique_bats.sort(key=get_bat_number)
    return unique_bats

def save_extracted_bats(bats: List[Dict], filename_suffix: str):
    """Save extracted BATs to JSON file"""
    
    filename = f"extracted_{filename_suffix}_bats.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(bats, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Extracted BATs saved to: {filename}")

def demonstrate_real_vs_mock_gap(real_bats: List[Dict]):
    """Demonstrate the gap between real and mock systems"""
    
    print(f"\n🎯 === REAL vs MOCK SYSTEM COMPARISON ===")
    
    print(f"\n📋 CURRENT MOCK SYSTEM:")
    print(f"   - Uses {30} generic BAT titles like 'BAT 1: Energie management systeem'")
    print(f"   - Simple keyword matching: 'energie' → Partially Compliant")
    print(f"   - No actual BREF content verification")
    print(f"   - Generic compliance assessments")
    
    print(f"\n📋 REAL SYSTEM WITH EXTRACTED CONTENT:")
    print(f"   - Found {len(real_bats)} actual BAT references from ENE BREF")
    print(f"   - Uses real BAT text from official EU documents")
    print(f"   - Can verify specific requirements like ENEMS implementation")
    print(f"   - Provides accurate compliance against actual BAT conclusions")
    
    if real_bats:
        print(f"\n🔍 EXAMPLE REAL BAT:")
        example_bat = real_bats[0]
        print(f"   Mock: 'BAT 1: Energie management systeem'")
        print(f"   Real: '{example_bat['bat_id']}: {example_bat['title'][:100]}...'")
        print(f"   Source: Page {example_bat['page']} of ENE BREF")
    
    print(f"\n⚠️  IMPLEMENTATION GAP:")
    print(f"   1. Current system needs real BAT content integration")
    print(f"   2. Pattern matching needs improvement for full extraction")
    print(f"   3. Compliance logic should use actual BAT requirements")
    print(f"   4. All 29 ENE BATs need to be properly extracted and structured")

def create_integration_proposal():
    """Create proposal for integrating real BAT extraction"""
    
    print(f"\n🔧 === INTEGRATION PROPOSAL ===")
    
    proposal = """
PHASE 1: Enhanced BAT Extraction
- Improve PDF parsing for all BREF formats
- Extract all 29 ENE BATs with full text
- Structure BAT requirements and applicability conditions
- Create BAT database with real content

PHASE 2: Compliance Engine Upgrade  
- Replace mock BAT generation with real BAT loading
- Implement requirement-specific compliance checks
- Use actual BAT text for permit comparison
- Generate evidence-based compliance assessments

PHASE 3: Complete System Integration
- Connect real BAT extraction to compliance system
- Validate against all applicable BREFs
- Generate reports with actual BAT text citations
- Ensure accuracy against official EU documents

BENEFITS:
✅ True compliance verification against real BREF requirements
✅ Accurate BAT-specific assessments instead of generic ones  
✅ Legal defensibility through official document citations
✅ Complete coverage of all 29 ENE BATs (and other BREFs)
"""
    
    print(proposal)

if __name__ == "__main__":
    print("🎯 === IMPROVED BAT EXTRACTION DEMONSTRATION ===\n")
    
    # Extract real BATs
    real_bats = extract_real_ene_bats_improved()
    
    print("\n" + "="*60)
    
    # Create integration proposal
    create_integration_proposal()
    
    print(f"\n📊 === CONCLUSION ===")
    print(f"The current system uses mock BAT conclusions.")
    print(f"This demonstration shows how to extract real BAT content.")
    print(f"Integration would provide true compliance verification.")
    print(f"Next step: Implement full BAT extraction for all 29 ENE BATs.")