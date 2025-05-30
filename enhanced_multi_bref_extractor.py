#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/enhanced_multi_bref_extractor.py

"""
Enhanced Multi-BREF BAT Extractor
Improved extraction patterns for different BREF document formats
"""

import fitz
import os
import re
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class EnhancedMultiBREFExtractor:
    def __init__(self):
        self.bref_dir = "/Users/han/Code/MOB-BREF/regulatory_data/brefs"
        self.extracted_bats = []
        
    def extract_all_bats(self):
        """Extract BATs from all available BREF documents with enhanced patterns"""
        
        print("🔍 === ENHANCED MULTI-BREF BAT EXTRACTION ===")
        print("Using improved patterns for different BREF document formats\n")
        
        # Find all BREF PDFs
        bref_files = self.find_bref_files()
        
        for bref_file in bref_files:
            print(f"📋 Processing {bref_file['bref_id']} BREF...")
            bats = self.extract_bats_with_enhanced_patterns(bref_file)
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
        
        # Check for any PDF files in the directory
        for filename in os.listdir(self.bref_dir):
            if filename.endswith('.pdf'):
                # Try to extract BREF ID from filename
                bref_id = self.extract_bref_id_from_filename(filename)
                if bref_id:
                    filepath = os.path.join(self.bref_dir, filename)
                    bref_files.append({
                        'bref_id': bref_id,
                        'filepath': filepath,
                        'filename': filename
                    })
        
        print(f"📁 Found {len(bref_files)} BREF files: {[f['bref_id'] for f in bref_files]}")
        return bref_files
    
    def extract_bref_id_from_filename(self, filename: str) -> Optional[str]:
        """Extract BREF ID from filename"""
        
        # Common BREF ID patterns
        bref_patterns = {
            'ENE': ['ENE', 'energy', 'efficiency'],
            'WT': ['WT', 'waste.*treatment', 'afvalbehandeling'],
            'WI': ['WI', 'waste.*incin', 'afvalverbranding'],
            'EMS': ['EMS', 'emission.*monitor', 'emissiemonitoring'],
            'CWW': ['CWW', 'common.*waste', 'water.*gas'],
            'LCP': ['LCP', 'large.*combustion', 'grote.*stook'],
            'STM': ['STM', 'surface.*metal', 'oppervlakte.*metaal'],
            'STP': ['STP', 'surface.*plastic', 'oppervlakte.*kunst'],
            'STS': ['STS', 'solvent', 'oplosmiddel']
        }
        
        filename_lower = filename.lower()
        
        for bref_id, patterns in bref_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return bref_id
        
        # Try to extract from common naming patterns
        match = re.search(r'([A-Z]{2,4})_?bref', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def extract_bats_with_enhanced_patterns(self, bref_file: Dict) -> List[Dict]:
        """Extract BATs using enhanced patterns for different BREF formats"""
        
        bref_id = bref_file['bref_id']
        filepath = bref_file['filepath']
        
        try:
            doc = fitz.open(filepath)
            total_pages = len(doc)
            print(f"   📄 Opened {bref_id}: {total_pages} pages")
            
            # Use BREF-specific extraction strategy
            if bref_id == 'ENE':
                bats = self.extract_ene_bats_enhanced(doc, bref_id)
            elif bref_id == 'WT':
                bats = self.extract_wt_bats_enhanced(doc, bref_id)
            elif bref_id == 'WI':
                bats = self.extract_wi_bats_enhanced(doc, bref_id)
            elif bref_id == 'EMS':
                bats = self.extract_ems_bats_enhanced(doc, bref_id)
            else:
                bats = self.extract_generic_bats_enhanced(doc, bref_id)
            
            doc.close()
            return bats
            
        except Exception as e:
            print(f"   ❌ Error processing {bref_id}: {e}")
            return []
    
    def extract_ene_bats_enhanced(self, doc, bref_id: str) -> List[Dict]:
        """Enhanced ENE BAT extraction"""
        
        bats = []
        
        # Search broader range for ENE BATs
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Multiple ENE-specific patterns
            patterns = [
                r'BAT\s+(\d+):\s*([^\n]+)',
                r'BAT\s+(\d+)\s+is\s+to\s+([^\n]+)',
                r'(\d+\.\d+)\s+BAT\s+is\s+to\s+([^\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                
                for match in matches:
                    if 'is to' in pattern:
                        bat_number = match.group(1)
                        bat_desc = match.group(2).strip()
                    elif ':' in pattern:
                        bat_number = match.group(1)
                        bat_desc = match.group(2).strip()
                    else:
                        section_num = match.group(1)
                        bat_desc = match.group(2).strip()
                        bat_number_match = re.search(r'(\d+)', section_num)
                        if bat_number_match:
                            bat_number = bat_number_match.group(1)
                        else:
                            continue
                    
                    # Get extended context
                    context = self.get_extended_context(page_text, match.start(), match.end())
                    
                    bat_entry = {
                        'bref_id': bref_id,
                        'bat_number': int(bat_number),
                        'bat_id': f"{bref_id}-BAT-{bat_number}",
                        'title': bat_desc,
                        'raw_text': context,
                        'page': page_num + 1,
                        'extraction_method': f'Enhanced pattern: {pattern}',
                        'extraction_date': datetime.now().isoformat()
                    }
                    
                    bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def extract_wt_bats_enhanced(self, doc, bref_id: str) -> List[Dict]:
        """Enhanced Waste Treatment BAT extraction"""
        
        bats = []
        
        # Search for WT-specific patterns
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Look for conclusion and BAT sections
            if any(term in page_text.lower() for term in [
                'bat conclusion', 'best available', 'conclusion', 
                'technique', 'waste treatment', 'afvalbehandeling'
            ]):
                
                # WT-specific patterns
                patterns = [
                    r'(\d+\.\d+\.\d+)\s+([^0-9\n]+?)(?=\d+\.\d+\.\d+|$)',
                    r'BAT\s+is\s+to\s+([^\n]+)',
                    r'For\s+waste\s+treatment[,\s]+BAT\s+is\s+to\s+([^\n]+)',
                    r'The\s+following\s+techniques?\s+(?:are\s+)?BAT:([^\n]+)',
                    r'Best\s+available\s+techniques?\s+(?:are|is)[:]\s*([^\n]+)'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE | re.DOTALL)
                    
                    for match in matches:
                        # Extract BAT information
                        if match.group(0).startswith(tuple('0123456789')):
                            section_num = match.group(1)
                            bat_desc = match.group(2).strip()
                            bat_number = self.extract_number_from_section(section_num)
                        else:
                            bat_desc = match.group(1).strip()
                            bat_number = self.guess_bat_number_from_context(page_text, match.start())
                        
                        if bat_number:
                            context = self.get_extended_context(page_text, match.start(), match.end())
                            
                            bat_entry = {
                                'bref_id': bref_id,
                                'bat_number': bat_number,
                                'bat_id': f"{bref_id}-BAT-{bat_number}",
                                'title': bat_desc[:100] + '...' if len(bat_desc) > 100 else bat_desc,
                                'raw_text': context,
                                'page': page_num + 1,
                                'extraction_method': f'WT pattern: {pattern[:30]}...',
                                'extraction_date': datetime.now().isoformat()
                            }
                            
                            bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def extract_wi_bats_enhanced(self, doc, bref_id: str) -> List[Dict]:
        """Enhanced Waste Incineration BAT extraction"""
        
        bats = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # WI-specific terms
            if any(term in page_text.lower() for term in [
                'incineration', 'verbranding', 'combustion', 'temperature',
                'emission limit', 'stack', 'flue gas'
            ]):
                
                # WI-specific patterns
                patterns = [
                    r'BAT\s+(\d+)\s*[:\-]\s*([^\n]+)',
                    r'For\s+(?:waste\s+)?incineration[,\s]+([^\n]+)',
                    r'(\d+\.\d+)\s+([^0-9\n]+?)(?=\d+\.\d+|$)',
                    r'Best\s+available\s+technique[s]?\s+for\s+([^\n]+)'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    
                    for match in matches:
                        if 'BAT' in match.group(0):
                            bat_number = match.group(1)
                            bat_desc = match.group(2).strip()
                        else:
                            bat_desc = match.group(1).strip()
                            bat_number = self.guess_bat_number_from_context(page_text, match.start())
                        
                        if bat_number:
                            context = self.get_extended_context(page_text, match.start(), match.end())
                            
                            bat_entry = {
                                'bref_id': bref_id,
                                'bat_number': int(bat_number) if str(bat_number).isdigit() else 1,
                                'bat_id': f"{bref_id}-BAT-{bat_number}",
                                'title': bat_desc[:100] + '...' if len(bat_desc) > 100 else bat_desc,
                                'raw_text': context,
                                'page': page_num + 1,
                                'extraction_method': f'WI pattern: {pattern[:30]}...',
                                'extraction_date': datetime.now().isoformat()
                            }
                            
                            bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def extract_ems_bats_enhanced(self, doc, bref_id: str) -> List[Dict]:
        """Enhanced Emissions Monitoring BAT extraction"""
        
        bats = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # EMS-specific terms
            if any(term in page_text.lower() for term in [
                'monitoring', 'measurement', 'calibration', 'emission',
                'continuous', 'periodic', 'quality assurance'
            ]):
                
                # EMS-specific patterns
                patterns = [
                    r'BAT\s+for\s+monitoring\s+is\s+to\s+([^\n]+)',
                    r'BAT\s+(\d+)\s*[:\-]\s*([^\n]+)',
                    r'For\s+emission\s+monitoring[,\s]+([^\n]+)',
                    r'Monitoring\s+BAT\s+includes?\s+([^\n]+)'
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    
                    for match in matches:
                        if 'BAT' in match.group(0) and len(match.groups()) > 1:
                            bat_number = match.group(1)
                            bat_desc = match.group(2).strip()
                        else:
                            bat_desc = match.group(1).strip()
                            bat_number = self.guess_bat_number_from_context(page_text, match.start())
                        
                        if bat_number:
                            context = self.get_extended_context(page_text, match.start(), match.end())
                            
                            bat_entry = {
                                'bref_id': bref_id,
                                'bat_number': int(bat_number) if str(bat_number).isdigit() else 1,
                                'bat_id': f"{bref_id}-BAT-{bat_number}",
                                'title': bat_desc[:100] + '...' if len(bat_desc) > 100 else bat_desc,
                                'raw_text': context,
                                'page': page_num + 1,
                                'extraction_method': f'EMS pattern: {pattern[:30]}...',
                                'extraction_date': datetime.now().isoformat()
                            }
                            
                            bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def extract_generic_bats_enhanced(self, doc, bref_id: str) -> List[Dict]:
        """Enhanced generic BAT extraction"""
        
        bats = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Generic BAT patterns
            patterns = [
                r'BAT\s+(\d+)\s*[:\-]\s*([^\n]+)',
                r'BAT\s+is\s+to\s+([^\n]+)',
                r'Best\s+available\s+technique[s]?\s*[:\-]\s*([^\n]+)',
                r'(\d+\.\d+)\s+([^0-9\n]+?)(?=\d+\.\d+|$)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                
                for match in matches:
                    if 'BAT' in match.group(0) and len(match.groups()) > 1:
                        bat_number = match.group(1)
                        bat_desc = match.group(2).strip()
                    elif 'is to' in match.group(0):
                        bat_desc = match.group(1).strip()
                        bat_number = self.guess_bat_number_from_context(page_text, match.start())
                    else:
                        section_num = match.group(1)
                        bat_desc = match.group(2).strip()
                        bat_number = self.extract_number_from_section(section_num)
                    
                    if bat_number and len(bat_desc) > 10:  # Filter out very short descriptions
                        context = self.get_extended_context(page_text, match.start(), match.end())
                        
                        bat_entry = {
                            'bref_id': bref_id,
                            'bat_number': int(bat_number) if str(bat_number).isdigit() else 1,
                            'bat_id': f"{bref_id}-BAT-{bat_number}",
                            'title': bat_desc[:100] + '...' if len(bat_desc) > 100 else bat_desc,
                            'raw_text': context,
                            'page': page_num + 1,
                            'extraction_method': f'Generic pattern: {pattern[:30]}...',
                            'extraction_date': datetime.now().isoformat()
                        }
                        
                        bats.append(bat_entry)
        
        return self.remove_duplicate_bats(bats)
    
    def get_extended_context(self, text: str, start: int, end: int, context_size: int = 400) -> str:
        """Get extended context around a match"""
        
        start_pos = max(0, start - context_size)
        end_pos = min(len(text), end + context_size)
        return text[start_pos:end_pos].strip()
    
    def extract_number_from_section(self, section: str) -> Optional[int]:
        """Extract number from section like '4.2.3'"""
        
        numbers = re.findall(r'\d+', section)
        if numbers:
            # Use last number as BAT number
            return int(numbers[-1])
        return None
    
    def guess_bat_number_from_context(self, text: str, position: int) -> Optional[int]:
        """Guess BAT number from surrounding context"""
        
        # Look for numbers in surrounding text
        start = max(0, position - 200)
        end = min(len(text), position + 200)
        context = text[start:end]
        
        # Look for explicit BAT numbers
        bat_match = re.search(r'BAT\s+(\d+)', context, re.IGNORECASE)
        if bat_match:
            return int(bat_match.group(1))
        
        # Look for section numbers
        section_match = re.search(r'(\d+)\.(\d+)', context)
        if section_match:
            return int(section_match.group(2))
        
        # Default to 1 if no number found
        return 1
    
    def remove_duplicate_bats(self, bats: List[Dict]) -> List[Dict]:
        """Remove duplicate BAT entries"""
        
        seen = set()
        unique_bats = []
        
        for bat in bats:
            # Create key based on BREF, BAT number, and title similarity
            bat_key = (bat['bref_id'], bat['bat_number'], bat['title'][:50])
            if bat_key not in seen:
                seen.add(bat_key)
                unique_bats.append(bat)
        
        # Sort by BAT number
        unique_bats.sort(key=lambda x: x['bat_number'])
        return unique_bats
    
    def save_enhanced_database(self, filename: str = "enhanced_bat_database.json"):
        """Save enhanced BAT database"""
        
        # Group by BREF for better organization
        bats_by_bref = {}
        for bat in self.extracted_bats:
            bref_id = bat['bref_id']
            if bref_id not in bats_by_bref:
                bats_by_bref[bref_id] = []
            bats_by_bref[bref_id].append(bat)
        
        database = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_bats': len(self.extracted_bats),
                'brefs_processed': list(bats_by_bref.keys()),
                'bats_per_bref': {bref: len(bats) for bref, bats in bats_by_bref.items()},
                'extractor_version': 'EnhancedMultiBREFExtractor v1.0'
            },
            'bats_by_bref': bats_by_bref,
            'all_bats': self.extracted_bats
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Enhanced BAT database saved to: {filename}")
        return filename
    
    def generate_enhanced_review_report(self, filename: str = "enhanced_bat_review_report.html"):
        """Generate enhanced review report"""
        
        # Group BATs by BREF
        bats_by_bref = {}
        for bat in self.extracted_bats:
            bref_id = bat['bref_id']
            if bref_id not in bats_by_bref:
                bats_by_bref[bref_id] = []
            bats_by_bref[bref_id].append(bat)
        
        html = self.create_enhanced_review_html(bats_by_bref)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📋 Enhanced review report generated: {filename}")
        return filename
    
    def create_enhanced_review_html(self, bats_by_bref: Dict) -> str:
        """Create enhanced HTML review report"""
        
        total_bats = len(self.extracted_bats)
        total_brefs = len(bats_by_bref)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced BAT Extraction Review Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .bref-section {{ margin: 30px 0; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }}
        .bref-header {{ background: #34495e; color: white; padding: 15px; }}
        .bat-entry {{ border-bottom: 1px solid #eee; padding: 20px; }}
        .bat-entry:last-child {{ border-bottom: none; }}
        .bat-header {{ background: #e8f5e8; padding: 10px; border-radius: 5px; margin-bottom: 10px; }}
        .bat-text {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
        .extraction-info {{ background: #d1ecf1; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 11px; }}
        .validation-box {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 15px; background: #e8f5e8; border-radius: 8px; flex: 1; margin: 0 10px; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #27ae60; }}
        .stat-label {{ color: #7f8c8d; text-transform: uppercase; font-size: 0.9em; }}
        .progress-note {{ background: #d4edda; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Enhanced BAT Extraction Review Report</h1>
        <p>Multi-BREF BAT extraction with improved pattern recognition</p>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="progress-note">
        <h3>🎯 Extraction Progress</h3>
        <p><strong>Enhanced extraction patterns now capture BATs from multiple BREF formats.</strong></p>
        <p>Each BREF uses different document structures and terminology - the enhanced extractor adapts to these variations.</p>
    </div>
    
    <div class="summary">
        <h2>📊 Enhanced Extraction Summary</h2>
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
                <div class="stat-number">{len([b for b in self.extracted_bats if 'Enhanced' in b.get('extraction_method', '')])}</div>
                <div class="stat-label">Enhanced Extractions</div>
            </div>
        </div>
        
        <h3>📋 BREFs Summary</h3>
        <ul>
"""
        
        for bref_id, bats in bats_by_bref.items():
            html += f"<li><strong>{bref_id}:</strong> {len(bats)} BATs extracted</li>"
        
        html += f"""
        </ul>
        
        <h3>🎯 Review Instructions</h3>
        <p><strong>Please validate each extracted BAT:</strong></p>
        <ul>
            <li>✅ Verify BAT number and description accuracy</li>
            <li>✅ Check if complete requirement text is captured</li>
            <li>✅ Confirm extraction method is appropriate</li>
            <li>✅ Validate page references</li>
            <li>❌ Flag BATs needing re-extraction or correction</li>
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
                html += f"""
        <div class="bat-entry">
            <div class="bat-header">
                <h3>{bat['bat_id']}: {bat['title']}</h3>
                <p><strong>Page:</strong> {bat['page']} | <strong>BAT Number:</strong> {bat['bat_number']}</p>
            </div>
            
            <div class="bat-text">{bat['raw_text']}</div>
            
            <div class="extraction-info">
                <strong>Extraction Method:</strong> {bat.get('extraction_method', 'Standard')}<br>
                <strong>Date:</strong> {bat.get('extraction_date', 'Unknown')[:19]}
            </div>
            
            <div class="validation-box">
                <strong>🔍 Validation:</strong><br>
                □ BAT ID correct ({bat['bat_id']})<br>
                □ Description accurate<br>
                □ Text complete and relevant<br>
                □ Page number verified ({bat['page']})<br>
                <strong>Quality Rating:</strong> ⭐⭐⭐⭐⭐ (1-5 stars)<br>
                <strong>Comments:</strong> ________________________________
            </div>
        </div>
"""
            
            html += "</div>"
        
        html += f"""
    <div style="margin-top: 50px; text-align: center; color: #7f8c8d;">
        <hr>
        <h3>📊 Next Steps</h3>
        <p>🔍 <strong>Review Status:</strong> Please validate all {total_bats} extracted BATs</p>
        <p>📝 <strong>Corrections:</strong> Note any extraction errors for improvement</p>
        <p>🚀 <strong>Integration:</strong> Once validated, integrate into compliance system</p>
        <p>🏭 Generated by EnhancedMultiBREFExtractor v1.0</p>
    </div>
</body>
</html>
"""
        
        return html

def main():
    """Main enhanced extraction process"""
    
    print("🚀 === ENHANCED MULTI-BREF BAT EXTRACTION ===\n")
    
    # Initialize enhanced extractor
    extractor = EnhancedMultiBREFExtractor()
    
    # Extract all BATs with enhanced patterns
    extracted_bats = extractor.extract_all_bats()
    
    if not extracted_bats:
        print("❌ No BATs extracted. Check BREF files and extraction patterns.")
        return
    
    # Save enhanced database
    db_filename = extractor.save_enhanced_database()
    
    # Generate enhanced review report
    report_filename = extractor.generate_enhanced_review_report()
    
    # Summary
    print(f"\n🎯 === ENHANCED EXTRACTION COMPLETE ===")
    print(f"📊 Total BATs extracted: {len(extracted_bats)}")
    print(f"📁 Enhanced database: {db_filename}")
    print(f"📋 Review report: {report_filename}")
    
    # Show BATs by BREF
    bats_by_bref = {}
    for bat in extracted_bats:
        bref_id = bat['bref_id']
        if bref_id not in bats_by_bref:
            bats_by_bref[bref_id] = []
        bats_by_bref[bref_id].append(bat)
    
    print(f"\n📋 BATs extracted per BREF:")
    for bref_id, bats in bats_by_bref.items():
        print(f"   ✓ {bref_id}: {len(bats)} BATs")
        # Show sample BAT
        if bats:
            sample_bat = bats[0]
            print(f"     Example: {sample_bat['bat_id']} - {sample_bat['title'][:60]}...")
    
    print(f"\n🔍 Please review the enhanced report: {report_filename}")

if __name__ == "__main__":
    main()