#!/usr/bin/env python3
"""
Improved BREF Extractor - Complete Document Search
Searches entire BREF documents for BAT content using multiple strategies
"""

import fitz
import requests
import json
import re
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class ImprovedBREFExtractor:
    """Improved BREF extractor that searches entire documents intelligently"""
    
    def __init__(self):
        # BREF documents that failed in previous extraction
        self.failed_brefs = {
            'CER': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/cer_bref_0807.pdf',
            'ECM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/ecm_bref_0706.pdf',
            'EFS': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2022-03/efs_bref_0706_0.pdf',
            'ICS': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/cvs_bref_1201.pdf',
            'LVIC-AAF': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2022-03/LVIC-AAF.pdf',
            'OFC': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/ofc_bref_0806.pdf',
            'ROM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-12/ROM_2018_08_20.pdf',
            'SIC': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/sic_bref_0907.pdf',
            'STM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/stm_bref_0806.pdf'
        }
        
        # Multiple BAT patterns for comprehensive detection
        self.bat_patterns = [
            # Standard numbered BAT patterns
            re.compile(r'^\s*(\d+)\.\s*BAT\s+is\s+to\s+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^\s*(\d+)\.\s*BAT\s+for\s+.*?is\s+to\s+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^\s*(\d+)\.\s*When\s+.*?BAT\s+', re.MULTILINE | re.IGNORECASE),
            
            # BAT conclusion patterns
            re.compile(r'BAT\s+(\d+)\s*[:\-]\s*', re.IGNORECASE),
            re.compile(r'BAT\s+(\d+)\s+is\s+to\s+', re.IGNORECASE),
            re.compile(r'^\s*BAT\s+(\d+)\b', re.MULTILINE | re.IGNORECASE),
            
            # Alternative patterns
            re.compile(r'Best\s+Available\s+Technique\s+(\d+)', re.IGNORECASE),
            re.compile(r'Technique\s+(\d+):\s*BAT', re.IGNORECASE),
        ]
        
        self.downloads_dir = "bref_downloads"
        self.results = {}
    
    def extract_remaining_brefs(self) -> Dict:
        """Extract BATs from previously failed BREFs using improved method"""
        
        print("🔄 === IMPROVED BREF EXTRACTION ===\n")
        print("Targeting 9 BREFs that failed in previous extraction")
        print("Using comprehensive document search with multiple patterns\n")
        
        total_new_bats = 0
        successful_docs = 0
        
        for doc_code, url in self.failed_brefs.items():
            print(f"🔍 Processing {doc_code} (improved method)...")
            
            try:
                # Use cached PDF
                pdf_path = f"{self.downloads_dir}/{doc_code.lower()}_bref.pdf"
                
                if not os.path.exists(pdf_path):
                    print(f"    PDF not found, downloading...")
                    pdf_path = self.download_pdf(url, doc_code)
                
                # Extract using improved comprehensive method
                bats = self.extract_bats_comprehensive(pdf_path, doc_code, url)
                
                if bats:
                    self.results[doc_code] = bats
                    total_new_bats += len(bats)
                    successful_docs += 1
                    
                    print(f"  ✅ {doc_code}: {len(bats)} BATs extracted")
                    
                    # Save individual results
                    self.save_individual_results(bats, doc_code)
                    
                else:
                    print(f"  ❌ {doc_code}: No BATs found")
                
            except Exception as e:
                print(f"  ❌ {doc_code}: Error - {e}")
        
        # Merge with existing successful extractions
        self.merge_with_existing_results()
        
        print(f"\n🎯 === IMPROVED EXTRACTION SUMMARY ===")
        print(f"✅ New successful extractions: {successful_docs}/{len(self.failed_brefs)}")
        print(f"📝 New BATs extracted: {total_new_bats}")
        
        return self.results
    
    def extract_bats_comprehensive(self, pdf_path: str, doc_code: str, source_url: str) -> List[Dict]:
        """Comprehensive BAT extraction using multiple strategies"""
        
        doc = fitz.open(pdf_path)
        
        try:
            print(f"    Document: {len(doc)} pages")
            
            # Strategy 1: Full document text extraction
            full_text = self.extract_full_document_text(doc)
            
            # Strategy 2: Find all potential BAT locations using multiple patterns
            all_bat_matches = self.find_all_bat_patterns(full_text)
            
            print(f"    Found {len(all_bat_matches)} potential BAT matches")
            
            if not all_bat_matches:
                print(f"    No BAT patterns found with current methods")
                return []
            
            # Strategy 3: Extract complete BAT texts
            bats = self.extract_complete_bats_comprehensive(full_text, all_bat_matches, doc_code, source_url)
            
            # Strategy 4: Validate and deduplicate
            validated_bats = self.validate_and_deduplicate_bats(bats)
            
            return validated_bats
            
        finally:
            doc.close()
    
    def extract_full_document_text(self, doc) -> str:
        """Extract text from entire document with page markers"""
        
        texts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Add page marker
            page_marker = f"\n[PAGE_{page_num + 1}]\n"
            texts.append(page_marker)
            texts.append(page_text)
        
        return "".join(texts)
    
    def find_all_bat_patterns(self, text: str) -> List[Tuple[int, int, str, str]]:
        """Find all BAT matches using multiple patterns"""
        
        all_matches = []
        
        for i, pattern in enumerate(self.bat_patterns):
            for match in pattern.finditer(text):
                try:
                    bat_num = int(match.group(1))
                    match_info = (
                        match.start(),
                        bat_num,
                        match.group(0),
                        f'pattern_{i+1}'
                    )
                    all_matches.append(match_info)
                except (ValueError, IndexError):
                    # Skip invalid matches
                    continue
        
        # Sort by position and remove nearby duplicates
        all_matches.sort(key=lambda x: x[0])
        
        # Remove duplicates (same BAT number within 500 characters)
        deduplicated = []
        for match in all_matches:
            is_duplicate = False
            for existing in deduplicated:
                if (match[1] == existing[1] and  # Same BAT number
                    abs(match[0] - existing[0]) < 500):  # Within 500 chars
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(match)
        
        return deduplicated
    
    def extract_complete_bats_comprehensive(self, full_text: str, bat_matches: List[Tuple], 
                                         doc_code: str, source_url: str) -> List[Dict]:
        """Extract complete BAT texts using comprehensive approach"""
        
        bats = []
        
        for i, (start_pos, bat_num, match_text, pattern_type) in enumerate(bat_matches):
            
            # Find end position
            if i + 1 < len(bat_matches):
                end_pos = bat_matches[i + 1][0]
            else:
                end_pos = self.find_intelligent_end_position(full_text, start_pos)
            
            # Extract BAT content
            bat_text = full_text[start_pos:end_pos].strip()
            
            # Validate minimum content
            if len(bat_text) < 50:
                continue
            
            # Clean and process text
            bat_text = self.clean_bat_text_comprehensive(bat_text)
            
            # Extract meaningful title
            title = self.extract_intelligent_title(bat_text, bat_num, match_text)
            
            # Find page number
            page_num = self.find_page_number(full_text, start_pos)
            
            # Analyze content
            content_analysis = self.analyze_bat_content(bat_text)
            
            bat_dict = {
                'bat_number': bat_num,
                'bat_id': f'BAT {bat_num}',
                'title': title,
                'full_text': bat_text,
                'text_length': len(bat_text),
                'page': page_num,
                'document_code': doc_code,
                'extraction_method': f'Comprehensive extraction ({pattern_type})',
                'pattern_type': pattern_type,
                'source_url': source_url,
                'language': 'English',
                'content_indicators': content_analysis
            }
            
            bats.append(bat_dict)
        
        return bats
    
    def find_intelligent_end_position(self, text: str, start_pos: int) -> int:
        """Find intelligent end position for BAT content"""
        
        search_text = text[start_pos:]
        
        # Look for next section indicators
        end_patterns = [
            r'\n\s*\d+\.\s*BAT\s+',  # Next numbered BAT
            r'\n\s*BAT\s+\d+',       # Next BAT reference
            r'\n\s*\d+\.\s*When\s+', # Next "When" clause
            r'\n\s*Chapter\s+\d+',   # Next chapter
            r'\n\s*\d+\.\d+\s+',     # Next numbered section
            r'\n\s*Annex\s+',        # Annex
            r'\n\s*References\s*$',  # References
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return start_pos + match.start()
        
        # Default: reasonable length limit
        return min(len(text), start_pos + 15000)
    
    def clean_bat_text_comprehensive(self, text: str) -> str:
        """Comprehensive text cleaning"""
        
        # Remove page markers
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove standalone page numbers and footers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove common PDF artifacts
        text = re.sub(r'\x0c', '', text)  # Form feed characters
        
        return text.strip()
    
    def extract_intelligent_title(self, bat_text: str, bat_num: int, match_text: str) -> str:
        """Extract intelligent title from BAT content"""
        
        lines = bat_text.split('\n')
        
        # Try to find a meaningful title in first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 15 and len(line) < 200:
                # Clean up title
                title = re.sub(rf'^\d+\.\s*', '', line)
                title = re.sub(r'^BAT\s+is\s+to\s*', '', title, flags=re.IGNORECASE)
                title = re.sub(r'^BAT\s+\d+\s*:?\s*', '', title, flags=re.IGNORECASE)
                title = re.sub(r'^When\s+', '', title, flags=re.IGNORECASE)
                
                if title.strip() and not re.match(r'^\d+\.?\s*$', title.strip()):
                    return title.strip()
        
        # Fallback: extract from match text
        if 'is to' in match_text.lower():
            parts = match_text.lower().split('is to')
            if len(parts) > 1:
                return f"is to {parts[1][:100].strip()}"
        
        return f"BAT {bat_num} technique"
    
    def analyze_bat_content(self, text: str) -> Dict:
        """Analyze BAT content for indicators"""
        
        text_lower = text.lower()
        
        return {
            'has_tables': any(indicator in text_lower for indicator in ['table', 'emission limit', 'monitoring']),
            'has_techniques': text_lower.count('technique') > 0,
            'has_applicability': any(word in text_lower for word in ['applicable', 'applicability']),
            'has_monitoring': any(word in text_lower for word in ['monitor', 'measurement']),
            'has_limits': any(word in text_lower for word in ['limit', 'value', 'range']),
            'word_count': len(text.split())
        }
    
    def validate_and_deduplicate_bats(self, bats: List[Dict]) -> List[Dict]:
        """Validate and deduplicate extracted BATs"""
        
        # Remove very short BATs
        validated = [bat for bat in bats if len(bat['full_text']) > 100]
        
        # Group by BAT number and keep the longest/most complete version
        by_number = {}
        for bat in validated:
            bat_num = bat['bat_number']
            if (bat_num not in by_number or 
                len(bat['full_text']) > len(by_number[bat_num]['full_text'])):
                by_number[bat_num] = bat
        
        # Sort by BAT number
        result = list(by_number.values())
        result.sort(key=lambda x: x['bat_number'])
        
        return result
    
    def find_page_number(self, text: str, position: int) -> int:
        """Find page number for position"""
        
        text_before = text[:position]
        page_matches = list(re.finditer(r'\[PAGE_(\d+)\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1
    
    def download_pdf(self, url: str, doc_code: str) -> str:
        """Download PDF if needed"""
        
        pdf_path = f"{self.downloads_dir}/{doc_code.lower()}_bref.pdf"
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        return pdf_path
    
    def save_individual_results(self, bats: List[Dict], doc_code: str):
        """Save individual document results"""
        
        os.makedirs("bref_extractions", exist_ok=True)
        filename = f"bref_extractions/{doc_code.lower()}_bats_improved.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bats, f, indent=2, ensure_ascii=False)
    
    def merge_with_existing_results(self):
        """Merge new results with existing successful extractions"""
        
        # Load existing results
        existing_file = "bref_extractions/all_bref_bats_proven.json"
        if os.path.exists(existing_file):
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
            
            # Merge results
            merged_results = {**existing_results, **self.results}
            
            # Save merged results
            with open("bref_extractions/all_bref_bats_complete.json", 'w', encoding='utf-8') as f:
                json.dump(merged_results, f, indent=2, ensure_ascii=False)
            
            total_docs = len(merged_results)
            total_bats = sum(len(bats) for bats in merged_results.values())
            
            print(f"\n💾 Complete BREF results saved:")
            print(f"   📄 All documents: {total_docs}")
            print(f"   📝 Total BATs: {total_bats}")
            print(f"   💫 File: bref_extractions/all_bref_bats_complete.json")


def main():
    """Extract remaining failed BREFs"""
    
    extractor = ImprovedBREFExtractor()
    results = extractor.extract_remaining_brefs()
    
    return results


if __name__ == "__main__":
    main()