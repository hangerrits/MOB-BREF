#!/usr/bin/env python3
"""
Proven BREF Extractor using Sequential Approach
Uses the exact method that successfully extracted 29 BATs from ENE BREF
"""

import fitz
import requests
import json
import re
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class ProvenBREFExtractor:
    """Uses proven sequential extraction method from ENE success"""
    
    def __init__(self):
        # BREF documents
        self.bref_documents = {
            'CER': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/cer_bref_0807.pdf',
            'ECM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/ecm_bref_0706.pdf',
            'EFS': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2022-03/efs_bref_0706_0.pdf',
            'ENE': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2021-09/ENE_Adopted_02-2009corrected20210914.pdf',
            'ICS': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/cvs_bref_1201.pdf',
            'LVIC-AAF': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2022-03/LVIC-AAF.pdf',
            'LVIC-S': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/lvic-s_bref_0907.pdf',
            'OFC': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/ofc_bref_0806.pdf',
            'POL': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/pol_bref_0807.pdf',
            'ROM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-12/ROM_2018_08_20.pdf',
            'SIC': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/sic_bref_0907.pdf',
            'STM': 'https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/stm_bref_0806.pdf'
        }
        
        # Use proven patterns from ENE extraction
        self.bat_start_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        self.alternative_bat_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+', re.MULTILINE | re.IGNORECASE)
        self.when_pattern = re.compile(r'^\s*(\d+)\.\s*When\s+', re.MULTILINE | re.IGNORECASE)
        self.bat_for_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+for\s+\w+\s+.*?is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        
        self.downloads_dir = "bref_downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        self.results = {}
    
    def extract_all_brefs(self) -> Dict:
        """Extract BATs from all BREF documents using proven method"""
        
        print("🎯 === PROVEN BREF EXTRACTION ===\n")
        print("Using exact method that successfully extracted 29 BATs from ENE")
        print(f"Processing {len(self.bref_documents)} BREF documents...\n")
        
        total_bats = 0
        successful_docs = 0
        
        for doc_code, url in self.bref_documents.items():
            print(f"🔍 Processing {doc_code}...")
            
            try:
                # Download if needed
                pdf_path = self.download_if_needed(url, doc_code)
                
                # Extract using proven method
                bats = self.extract_bats_proven_method(pdf_path, doc_code, url)
                
                if bats:
                    self.results[doc_code] = bats
                    total_bats += len(bats)
                    successful_docs += 1
                    
                    print(f"  ✅ {doc_code}: {len(bats)} BATs extracted")
                    
                    # Save individual results
                    self.save_individual_results(bats, doc_code)
                    
                else:
                    print(f"  ❌ {doc_code}: No BATs found")
                
            except Exception as e:
                print(f"  ❌ {doc_code}: Error - {e}")
        
        # Save comprehensive results
        self.save_comprehensive_results()
        
        print(f"\n🎯 === EXTRACTION SUMMARY ===")
        print(f"✅ Successful: {successful_docs}/{len(self.bref_documents)} documents")
        print(f"📝 Total BATs: {total_bats}")
        
        return self.results
    
    def download_if_needed(self, url: str, doc_code: str) -> str:
        """Download PDF if not already cached"""
        
        pdf_path = f"{self.downloads_dir}/{doc_code.lower()}_bref.pdf"
        
        if os.path.exists(pdf_path):
            return pdf_path
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        return pdf_path
    
    def extract_bats_proven_method(self, pdf_path: str, doc_code: str, source_url: str) -> List[Dict]:
        """Extract BATs using the exact proven method from ENE"""
        
        doc = fitz.open(pdf_path)
        
        try:
            # Use broad page range like successful ENE extraction
            # ENE BATs were found around pages 302-350, so search last third of document
            total_pages = len(doc)
            start_page = max(0, int(total_pages * 0.6))  # Start at 60% through document
            end_page = total_pages
            
            print(f"    Searching pages {start_page+1}-{end_page} of {total_pages}")
            
            # Extract text with page markers (proven approach)
            full_text = self.extract_text_with_markers(doc, start_page, end_page)
            
            # Find BAT positions using proven patterns
            bat_positions = self.find_bat_positions_proven(full_text)
            
            if not bat_positions:
                print(f"    No BAT patterns found, trying full document search...")
                # Fallback: search entire document
                full_text = self.extract_text_with_markers(doc, 0, total_pages)
                bat_positions = self.find_bat_positions_proven(full_text)
            
            # Extract complete BAT texts using proven method
            bats = self.extract_complete_bat_texts_proven(full_text, bat_positions, doc_code, source_url)
            
            return bats
            
        finally:
            doc.close()
    
    def extract_text_with_markers(self, doc, start_page: int, end_page: int) -> str:
        """Extract text with page markers (proven method)"""
        
        texts = []
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Add page marker
            page_marker = f"\n[PAGE_{page_num + 1}]\n"
            texts.append(page_marker)
            texts.append(page_text)
        
        return "".join(texts)
    
    def find_bat_positions_proven(self, text: str) -> List[Tuple[int, int, str]]:
        """Find BAT positions using proven patterns"""
        
        positions = []
        
        # Primary pattern: "X. BAT is to..."
        for match in self.bat_start_pattern.finditer(text):
            bat_num = int(match.group(1))
            positions.append((match.start(), bat_num, match.group(0)))
        
        # Alternative pattern: "X. BAT..."
        if len(positions) < 25:  # Expect substantial number of BATs
            for match in self.alternative_bat_pattern.finditer(text):
                bat_num = int(match.group(1))
                if not any(pos[1] == bat_num for pos in positions):
                    positions.append((match.start(), bat_num, match.group(0)))
        
        # Special patterns
        for match in self.when_pattern.finditer(text):
            bat_num = int(match.group(1))
            if not any(pos[1] == bat_num for pos in positions):
                positions.append((match.start(), bat_num, match.group(0)))
        
        for match in self.bat_for_pattern.finditer(text):
            bat_num = int(match.group(1))
            if not any(pos[1] == bat_num for pos in positions):
                positions.append((match.start(), bat_num, match.group(0)))
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        return positions
    
    def extract_complete_bat_texts_proven(self, full_text: str, bat_positions: List[Tuple[int, int, str]], 
                                        doc_code: str, source_url: str) -> List[Dict]:
        """Extract complete BAT texts using proven method"""
        
        bats = []
        processed_numbers = set()
        
        for i, (start_pos, bat_num, match_text) in enumerate(bat_positions):
            
            # Skip duplicates
            if bat_num in processed_numbers:
                continue
            
            # Determine end position
            if i + 1 < len(bat_positions):
                end_pos = bat_positions[i + 1][0]
            else:
                end_pos = self.find_logical_end_position_proven(full_text, start_pos)
            
            # Extract complete BAT text
            bat_text = full_text[start_pos:end_pos].strip()
            
            # Clean text (proven method)
            bat_text = self.clean_bat_text_proven(bat_text)
            
            # Extract title
            title = self.extract_bat_title_proven(bat_text, bat_num)
            
            # Find page number
            page_num = self.find_page_number_proven(full_text, start_pos)
            
            bat_dict = {
                'bat_number': bat_num,
                'bat_id': f'BAT {bat_num}',
                'title': title,
                'full_text': bat_text,
                'text_length': len(bat_text),
                'page': page_num,
                'document_code': doc_code,
                'extraction_method': 'Proven sequential parsing',
                'source_url': source_url,
                'language': 'English'
            }
            
            bats.append(bat_dict)
            processed_numbers.add(bat_num)
        
        # Sort by BAT number
        bats.sort(key=lambda x: x['bat_number'])
        
        return bats
    
    def clean_bat_text_proven(self, text: str) -> str:
        """Clean BAT text using proven method"""
        
        # Remove page markers
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove standalone page numbers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def extract_bat_title_proven(self, bat_text: str, bat_num: int) -> str:
        """Extract title using proven method"""
        
        lines = bat_text.split('\n')
        
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 20 and not re.match(r'^\d+\.?\s*$', line):
                title = re.sub(r'^\d+\.\s*BAT\s+is\s+to\s*', '', line, flags=re.IGNORECASE)
                title = re.sub(r'^\d+\.\s*BAT\s*', '', title, flags=re.IGNORECASE)
                return title.strip()[:200]
        
        return f"BAT {bat_num} extracted"
    
    def find_logical_end_position_proven(self, full_text: str, start_pos: int) -> int:
        """Find logical end using proven method"""
        
        search_text = full_text[start_pos:]
        
        end_patterns = [
            r'Chapter\s+[5-9]',
            r'Annex\s+[A-Z]',
            r'^References\s*$',
            r'^Glossary\s*$',
            r'^Bibliography\s*$'
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return start_pos + match.start()
        
        # Default limit
        return min(len(full_text), start_pos + 50000)
    
    def find_page_number_proven(self, full_text: str, position: int) -> int:
        """Find page number using proven method"""
        
        text_before = full_text[:position]
        page_matches = list(re.finditer(r'\[PAGE_(\d+)\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1
    
    def save_individual_results(self, bats: List[Dict], doc_code: str):
        """Save individual document results"""
        
        filename = f"bref_extractions/{doc_code.lower()}_bats_proven.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bats, f, indent=2, ensure_ascii=False)
    
    def save_comprehensive_results(self):
        """Save comprehensive results"""
        
        os.makedirs("bref_extractions", exist_ok=True)
        
        # Save all results
        with open("bref_extractions/all_bref_bats_proven.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Create statistics
        stats = {}
        for doc_code, bats in self.results.items():
            stats[doc_code] = {
                'bat_count': len(bats),
                'total_chars': sum(len(bat['full_text']) for bat in bats),
                'extraction_time': datetime.now().isoformat()
            }
        
        with open("bref_extractions/bref_proven_statistics.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to bref_extractions/")


def main():
    """Test proven BREF extraction method"""
    
    extractor = ProvenBREFExtractor()
    results = extractor.extract_all_brefs()
    
    if results:
        total_bats = sum(len(bats) for bats in results.values())
        print(f"\n🎉 Successfully extracted {total_bats} BATs from {len(results)} BREFs")
    else:
        print(f"\n❌ No BATs extracted")


if __name__ == "__main__":
    main()