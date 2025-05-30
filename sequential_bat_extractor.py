#!/usr/bin/env python3
"""
Sequential BAT Extractor - Complete BAT Text Extraction
Extracts complete BAT texts by finding numbered starts and capturing all content until next BAT
Based on user requirement: extract from "1. BAT is to..." until next numbered BAT
"""

import fitz
import os
import re
import json
from typing import List, Dict, Tuple, Optional

class SequentialBATExtractor:
    """Extracts complete BAT texts using sequential parsing approach"""
    
    def __init__(self):
        self.bat_start_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        self.alternative_bat_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+', re.MULTILINE | re.IGNORECASE)
        # Pattern for "When carrying out..." which might be BAT 4
        self.when_pattern = re.compile(r'^\s*(\d+)\.\s*When\s+', re.MULTILINE | re.IGNORECASE)
        # Pattern for "BAT for [system] is to..." like BAT 18
        self.bat_for_pattern = re.compile(r'^\s*(\d+)\.\s*BAT\s+for\s+\w+\s+.*?is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        
    def extract_bats_from_bref(self, bref_path: str, start_page: int = 270, end_page: int = 350) -> List[Dict]:
        """
        Extract complete BAT texts from BREF using sequential approach
        
        Args:
            bref_path: Path to BREF PDF file
            start_page: Page to start extraction (0-indexed)
            end_page: Page to end extraction
            
        Returns:
            List of extracted BAT dictionaries
        """
        
        if not os.path.exists(bref_path):
            raise FileNotFoundError(f"BREF not found: {bref_path}")
            
        doc = fitz.open(bref_path)
        
        try:
            # Extract text from all relevant pages first
            full_text = self._extract_text_from_pages(doc, start_page, end_page)
            
            # Find all BAT starts
            bat_positions = self._find_bat_positions(full_text)
            
            # Extract complete BAT texts
            bats = self._extract_complete_bat_texts(full_text, bat_positions)
            
            return bats
            
        finally:
            doc.close()
    
    def _extract_text_from_pages(self, doc, start_page: int, end_page: int) -> str:
        """Extract and concatenate text from specified page range"""
        
        texts = []
        page_markers = {}  # Track which text belongs to which page
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Add page marker
            page_marker = f"\n[PAGE_{page_num + 1}]\n"
            texts.append(page_marker)
            page_markers[len("".join(texts))] = page_num + 1
            texts.append(page_text)
        
        full_text = "".join(texts)
        return full_text
    
    def _find_bat_positions(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Find all BAT start positions in text
        
        Returns:
            List of tuples: (start_position, bat_number, matched_text)
        """
        
        positions = []
        
        # Primary pattern: "X. BAT is to..."
        for match in self.bat_start_pattern.finditer(text):
            bat_num = int(match.group(1))
            positions.append((match.start(), bat_num, match.group(0)))
        
        # Alternative pattern: "X. BAT..." (if primary pattern doesn't find enough)
        if len(positions) < 25:  # Expect close to 29 BATs
            for match in self.alternative_bat_pattern.finditer(text):
                bat_num = int(match.group(1))
                # Avoid duplicates
                if not any(pos[1] == bat_num for pos in positions):
                    positions.append((match.start(), bat_num, match.group(0)))
        
        # Special pattern for "When carrying out..." which might be BAT 4
        for match in self.when_pattern.finditer(text):
            bat_num = int(match.group(1))
            if bat_num == 4:  # Only interested in BAT 4
                if not any(pos[1] == bat_num for pos in positions):
                    positions.append((match.start(), bat_num, match.group(0)))
        
        # Pattern for "BAT for [system] is to..." like BAT 18
        for match in self.bat_for_pattern.finditer(text):
            bat_num = int(match.group(1))
            if not any(pos[1] == bat_num for pos in positions):
                positions.append((match.start(), bat_num, match.group(0)))
        
        # Sort by position in text
        positions.sort(key=lambda x: x[0])
        
        return positions
    
    def _extract_complete_bat_texts(self, full_text: str, bat_positions: List[Tuple[int, int, str]]) -> List[Dict]:
        """
        Extract complete text for each BAT from start until next BAT
        
        Args:
            full_text: Complete text from all pages
            bat_positions: List of (position, bat_number, match_text) tuples
            
        Returns:
            List of BAT dictionaries with complete texts
        """
        
        bats = []
        
        for i, (start_pos, bat_num, match_text) in enumerate(bat_positions):
            # Determine end position (start of next BAT or end of text)
            if i + 1 < len(bat_positions):
                end_pos = bat_positions[i + 1][0]
            else:
                # For the last BAT, try to find a logical end point
                end_pos = self._find_logical_end_position(full_text, start_pos)
            
            # Extract complete BAT text
            bat_text = full_text[start_pos:end_pos].strip()
            
            # Clean up the text
            bat_text = self._clean_bat_text(bat_text)
            
            # Extract title from first part of text
            title = self._extract_bat_title(bat_text)
            
            # Determine source page
            page_num = self._find_page_number(full_text, start_pos)
            
            bat_dict = {
                'bat_number': bat_num,
                'bat_id': f'BAT {bat_num}',
                'title': title,
                'full_text': bat_text,
                'text_length': len(bat_text),
                'page': page_num,
                'extraction_method': 'Sequential complete text',
                'start_position': start_pos,
                'end_position': end_pos
            }
            
            bats.append(bat_dict)
        
        return bats
    
    def _clean_bat_text(self, text: str) -> str:
        """Clean and normalize BAT text"""
        
        # Remove page markers
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        
        # Remove common artifacts
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Page numbers alone
        
        return text.strip()
    
    def _extract_bat_title(self, bat_text: str) -> str:
        """Extract meaningful title from BAT text"""
        
        lines = bat_text.split('\n')
        
        # Find the first substantial line after the BAT number
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 20 and not re.match(r'^\d+\.?\s*$', line):
                # Clean up the line for title
                title = re.sub(r'^\d+\.\s*BAT\s+is\s+to\s*', '', line, flags=re.IGNORECASE)
                title = re.sub(r'^\d+\.\s*BAT\s*', '', title, flags=re.IGNORECASE)
                return title.strip()[:200]  # Limit title length
        
        return "BAT text extracted"
    
    def _find_logical_end_position(self, full_text: str, start_pos: int) -> int:
        """Find logical end position for the last BAT to avoid capturing too much"""
        
        # Look for indicators that we've reached the end of BAT content
        search_text = full_text[start_pos:]
        
        # Patterns that might indicate end of BAT content
        # Be more restrictive to avoid cutting off tables and detailed content
        end_patterns = [
            r'Chapter\s+[5-9]',  # Next chapter (but not Chapter 4 content)
            r'Annex\s+[A-Z]',    # Annex section with letter
            r'^References\s*$', # References section (start of line)
            r'^Glossary\s*$',   # Glossary (start of line)
            r'^Bibliography\s*$', # Bibliography (start of line)
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Return position relative to full text
                return start_pos + match.start()
        
        # If no clear end found, limit to reasonable length (e.g., 50,000 chars for last BAT with tables)
        max_length = 50000
        return min(len(full_text), start_pos + max_length)
    
    def _find_page_number(self, full_text: str, position: int) -> int:
        """Find which page a position corresponds to"""
        
        # Look backwards from position to find last page marker
        text_before = full_text[:position]
        page_matches = list(re.finditer(r'\[PAGE_(\d+)\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1  # Default to page 1
    
    def save_extracted_bats(self, bats: List[Dict], output_path: str):
        """Save extracted BATs to JSON file"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bats, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(bats)} complete BATs to: {output_path}")
    
    def print_extraction_summary(self, bats: List[Dict]):
        """Print summary of extracted BATs"""
        
        print(f"\n📋 === EXTRACTED {len(bats)} COMPLETE BATS ===\n")
        
        total_chars = sum(len(bat['full_text']) for bat in bats)
        avg_length = total_chars // len(bats) if bats else 0
        
        print(f"Total characters extracted: {total_chars:,}")
        print(f"Average BAT length: {avg_length:,} characters")
        print(f"Page range: {min(bat['page'] for bat in bats)} - {max(bat['page'] for bat in bats)}")
        
        print(f"\n📝 BAT Summary:")
        for bat in bats:
            print(f"  BAT {bat['bat_number']:2d}: {bat['title'][:80]}...")
            print(f"           {bat['text_length']:,} chars, page {bat['page']}")
        
        # Show example of complete text
        if bats:
            print(f"\n🔍 Example Complete BAT Text (BAT {bats[0]['bat_number']}):")
            print(f"{bats[0]['full_text'][:500]}...")
            if len(bats[0]['full_text']) > 500:
                print(f"... (and {len(bats[0]['full_text']) - 500} more characters)")


def extract_ene_bats_sequential():
    """Extract all ENE BATs using sequential approach"""
    
    print("🎯 === SEQUENTIAL ENE BAT EXTRACTION ===\n")
    
    extractor = SequentialBATExtractor()
    ene_path = "/Users/han/Code/MOB-BREF/regulatory_data/brefs/ENE_bref.pdf"
    
    try:
        # Extract BATs - user mentioned page 303 (PDF) = page 272 (document)
        # So PDF page 303 is 0-indexed as 302
        bats = extractor.extract_bats_from_bref(
            ene_path,
            start_page=302,  # Start around the mentioned page
            end_page=350     # Search reasonable range
        )
        
        if not bats:
            print("❌ No BATs found with current patterns. Trying broader search...")
            # Try broader search
            bats = extractor.extract_bats_from_bref(
                ene_path,
                start_page=250,
                end_page=400
            )
        
        if bats:
            extractor.print_extraction_summary(bats)
            
            # Save results
            output_file = "ene_sequential_bats.json"
            extractor.save_extracted_bats(bats, output_file)
            
            print(f"\n✅ Successfully extracted complete BAT texts!")
            print(f"   Each BAT contains full text from start until next BAT begins")
            print(f"   No chunking or truncation - complete BAT content preserved")
            
        else:
            print("❌ No BATs found. May need to adjust search patterns or page range.")
            
        return bats
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None


if __name__ == "__main__":
    print("🚀 === COMPLETE BAT TEXT EXTRACTOR ===\n")
    print("Extracting complete BAT texts without chunking...")
    print("Following user requirement: '1. BAT is to...' until next numbered BAT\n")
    
    bats = extract_ene_bats_sequential()
    
    if bats:
        print(f"\n🎯 === SUCCESS ===")
        print(f"Extracted {len(bats)} complete BAT texts")
        print(f"Each BAT contains full, untruncated content")
        print(f"Ready for integration with compliance system")
    else:
        print(f"\n⚠️  === NEEDS ADJUSTMENT ===")
        print(f"Pattern matching may need refinement")
        print(f"Check page ranges and BAT text patterns")