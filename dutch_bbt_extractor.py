#!/usr/bin/env python3
"""
Dutch BBT (BAT) Extractor for BATC Documents
Extracts complete BBT texts from Dutch BAT Conclusions documents
"""

import fitz
import os
import re
import json
from typing import List, Dict, Tuple, Optional

class DutchBBTExtractor:
    """Extracts complete BBT texts from Dutch BATC documents"""
    
    def __init__(self):
        # Pattern for "BBT X" entries in Dutch
        self.bbt_start_pattern = re.compile(r'^\s*BBT\s+(\d+)', re.MULTILINE | re.IGNORECASE)
        # Alternative patterns for numbered BBT entries
        self.numbered_bbt_pattern = re.compile(r'^\s*(\d+)\.\s*BBT\s+', re.MULTILINE | re.IGNORECASE)
        
    def extract_bbts_from_batc(self, batc_path: str, start_page: int = 0, end_page: int = None) -> List[Dict]:
        """
        Extract complete BBT texts from BATC PDF using sequential approach
        
        Args:
            batc_path: Path to BATC PDF file
            start_page: Page to start extraction (0-indexed)
            end_page: Page to end extraction (None for all pages)
            
        Returns:
            List of extracted BBT dictionaries
        """
        
        if not os.path.exists(batc_path):
            raise FileNotFoundError(f"BATC not found: {batc_path}")
            
        doc = fitz.open(batc_path)
        
        try:
            if end_page is None:
                end_page = len(doc)
                
            # Extract text from all relevant pages first
            full_text = self._extract_text_from_pages(doc, start_page, end_page)
            
            # Find all BBT starts
            bbt_positions = self._find_bbt_positions(full_text)
            
            # Extract complete BBT texts
            bbts = self._extract_complete_bbt_texts(full_text, bbt_positions)
            
            return bbts
            
        finally:
            doc.close()
    
    def _extract_text_from_pages(self, doc, start_page: int, end_page: int) -> str:
        """Extract and concatenate text from specified page range"""
        
        texts = []
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Add page marker
            page_marker = f"\n[PAGE_{page_num + 1}]\n"
            texts.append(page_marker)
            texts.append(page_text)
        
        return "".join(texts)
    
    def _find_bbt_positions(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Find all BBT start positions in text
        
        Returns:
            List of tuples: (start_position, bbt_number, matched_text)
        """
        
        positions = []
        
        # Primary pattern: "BBT X"
        for match in self.bbt_start_pattern.finditer(text):
            bbt_num = int(match.group(1))
            positions.append((match.start(), bbt_num, match.group(0)))
        
        # Alternative pattern: "X. BBT" 
        for match in self.numbered_bbt_pattern.finditer(text):
            bbt_num = int(match.group(1))
            # Avoid duplicates
            if not any(pos[1] == bbt_num for pos in positions):
                positions.append((match.start(), bbt_num, match.group(0)))
        
        # Sort by position in text
        positions.sort(key=lambda x: x[0])
        
        return positions
    
    def _extract_complete_bbt_texts(self, full_text: str, bbt_positions: List[Tuple[int, int, str]]) -> List[Dict]:
        """
        Extract complete text for each BBT from start until next BBT
        
        Args:
            full_text: Complete text from all pages
            bbt_positions: List of (position, bbt_number, match_text) tuples
            
        Returns:
            List of BBT dictionaries with complete texts
        """
        
        bbts = []
        processed_numbers = set()
        
        for i, (start_pos, bbt_num, match_text) in enumerate(bbt_positions):
            # Skip duplicates
            if bbt_num in processed_numbers:
                continue
                
            # Determine end position (start of next BBT or logical end)
            if i + 1 < len(bbt_positions):
                end_pos = bbt_positions[i + 1][0]
            else:
                # For the last BBT, find a logical end point
                end_pos = self._find_logical_end_position(full_text, start_pos)
            
            # Extract complete BBT text
            bbt_text = full_text[start_pos:end_pos].strip()
            
            # Validate that this looks like a complete BBT entry
            if not self._is_valid_bbt_entry(bbt_text, bbt_num):
                continue
            
            # Clean up the text
            bbt_text = self._clean_bbt_text(bbt_text)
            
            # Extract title from first part of text
            title = self._extract_bbt_title(bbt_text)
            
            # Determine source page
            page_num = self._find_page_number(full_text, start_pos)
            
            bbt_dict = {
                'bbt_number': bbt_num,
                'bbt_id': f'BBT {bbt_num}',
                'title': title,
                'full_text': bbt_text,
                'text_length': len(bbt_text),
                'page': page_num,
                'extraction_method': 'Sequential complete text',
                'start_position': start_pos,
                'end_position': end_pos,
                'language': 'Dutch'
            }
            
            bbts.append(bbt_dict)
            processed_numbers.add(bbt_num)
        
        # Sort by BBT number
        bbts.sort(key=lambda x: x['bbt_number'])
        return bbts
    
    def _is_valid_bbt_entry(self, bbt_text: str, bbt_num: int) -> bool:
        """Validate that this looks like a complete BBT entry"""
        
        # Check minimum length
        if len(bbt_text) < 50:
            return False
            
        # Should start with BBT number or contain meaningful BBT content
        first_lines = '\n'.join(bbt_text.split('\n')[:3])
        
        # Should contain "BBT" and the number, and Dutch BBT keywords
        contains_bbt = f'BBT {bbt_num}' in first_lines or f'BBT{bbt_num}' in first_lines
        contains_dutch_keywords = any(keyword in bbt_text.lower() for keyword in [
            'de bbt is', 'om de', 'ter vermindering', 'te voorkomen', 'het toepassen'
        ])
        
        # Reject if it looks like a fragment (starts with lowercase or partial sentence)
        first_real_line = next((line.strip() for line in bbt_text.split('\n') if len(line.strip()) > 10), "")
        if first_real_line and first_real_line[0].islower() and not first_real_line.startswith('c)'):
            return False
            
        return contains_bbt or contains_dutch_keywords
    
    def _clean_bbt_text(self, text: str) -> str:
        """Clean and normalize BBT text"""
        
        # Remove page markers
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        
        # Remove common artifacts
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Page numbers alone
        
        return text.strip()
    
    def _extract_bbt_title(self, bbt_text: str) -> str:
        """Extract meaningful title from BBT text"""
        
        lines = bbt_text.split('\n')
        
        # Find the first substantial line after the BBT number
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 20 and not re.match(r'^\d+\.?\s*$', line):
                # Clean up the line for title
                title = re.sub(r'^BBT\s+\d+\s*', '', line, flags=re.IGNORECASE)
                title = re.sub(r'^\d+\.\s*BBT\s*', '', title, flags=re.IGNORECASE)
                return title.strip()[:200]  # Limit title length
        
        return "BBT tekst geëxtraheerd"
    
    def _find_logical_end_position(self, full_text: str, start_pos: int) -> int:
        """Find logical end position for the last BBT"""
        
        search_text = full_text[start_pos:]
        
        # Patterns that might indicate end of BBT content in Dutch documents
        end_patterns = [
            r'BIJLAGE\s+[IVX]+',  # Annex/Bijlage
            r'Hoofdstuk\s+[5-9]',  # Next chapter
            r'^Referenties\s*$',   # References
            r'^Glossarium\s*$',    # Glossary
            r'^Bibliografie\s*$',  # Bibliography
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return start_pos + match.start()
        
        # If no clear end found, limit to reasonable length
        max_length = 50000
        return min(len(full_text), start_pos + max_length)
    
    def _find_page_number(self, full_text: str, position: int) -> int:
        """Find which page a position corresponds to"""
        
        text_before = full_text[:position]
        page_matches = list(re.finditer(r'\[PAGE_(\d+)\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1  # Default to page 1
    
    def save_extracted_bbts(self, bbts: List[Dict], output_path: str):
        """Save extracted BBTs to JSON file"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bbts, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(bbts)} complete BBTs to: {output_path}")
    
    def print_extraction_summary(self, bbts: List[Dict]):
        """Print summary of extracted BBTs"""
        
        print(f"\n📋 === EXTRACTED {len(bbts)} COMPLETE BBTs ===\n")
        
        total_chars = sum(len(bbt['full_text']) for bbt in bbts)
        avg_length = total_chars // len(bbts) if bbts else 0
        
        print(f"Total characters extracted: {total_chars:,}")
        print(f"Average BBT length: {avg_length:,} characters")
        print(f"Language: Dutch")
        if bbts:
            print(f"Page range: {min(bbt['page'] for bbt in bbts)} - {max(bbt['page'] for bbt in bbts)}")
        
        print(f"\n📝 BBT Summary:")
        for bbt in bbts:
            print(f"  BBT {bbt['bbt_number']:2d}: {bbt['title'][:80]}...")
            print(f"           {bbt['text_length']:,} chars, page {bbt['page']}")
        
        # Show example of complete text
        if bbts:
            print(f"\n🔍 Example Complete BBT Text (BBT {bbts[0]['bbt_number']}):")
            print(f"{bbts[0]['full_text'][:500]}...")
            if len(bbts[0]['full_text']) > 500:
                print(f"... (and {len(bbts[0]['full_text']) - 500} more characters)")


def extract_cww_bbts():
    """Extract all CWW BBTs from Dutch BATC using sequential approach"""
    
    print("🎯 === DUTCH CWW BBT EXTRACTION ===\n")
    
    extractor = DutchBBTExtractor()
    cww_path = "/Users/han/Code/MOB-BREF/regulatory_data/bat_conclusions/CWW_BATC_NL.pdf"
    
    try:
        # Extract BBTs from entire document
        bbts = extractor.extract_bbts_from_batc(cww_path)
        
        if bbts:
            extractor.print_extraction_summary(bbts)
            
            # Save results
            output_file = "cww_dutch_bbts.json"
            extractor.save_extracted_bbts(bbts, output_file)
            
            print(f"\n✅ Successfully extracted complete Dutch BBT texts!")
            print(f"   Each BBT contains full text from start until next BBT begins")
            print(f"   Includes any tables and technical details")
            
        else:
            print("❌ No BBTs found. May need to adjust search patterns.")
            
        return bbts
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None


if __name__ == "__main__":
    print("🚀 === DUTCH BBT EXTRACTOR ===\n")
    print("Extracting complete BBT texts from Dutch BATC documents...")
    print("Pattern: 'BBT X' entries with full content preservation\n")
    
    bbts = extract_cww_bbts()
    
    if bbts:
        print(f"\n🎯 === SUCCESS ===")
        print(f"Extracted {len(bbts)} complete Dutch BBT texts")
        print(f"Sequential parsing preserves complete content including tables")
        print(f"Ready for Dutch compliance system integration")
    else:
        print(f"\n⚠️  === NEEDS ADJUSTMENT ===")
        print(f"Pattern matching may need refinement for Dutch BATC format")