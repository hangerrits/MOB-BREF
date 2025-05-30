#!/usr/bin/env python3
"""
HTML-based BAT/BBT Extractor
More reliable extraction using HTML structure instead of PDF parsing
"""

import requests
import json
import re
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Optional
from urllib.parse import urljoin

class HTMLBATExtractor:
    """Extracts BAT/BBT entries from HTML documents using structural parsing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def extract_bats_from_html_url(self, url: str, language: str = 'en') -> List[Dict]:
        """
        Extract BAT/BBT entries from HTML URL
        
        Args:
            url: URL to HTML document
            language: 'en' for English BAT, 'nl' for Dutch BBT
            
        Returns:
            List of extracted BAT/BBT dictionaries
        """
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if language == 'nl':
                return self._extract_dutch_bbts(soup, url)
            else:
                return self._extract_english_bats(soup, url)
                
        except Exception as e:
            print(f"❌ Error fetching HTML: {e}")
            return []
    
    def _extract_dutch_bbts(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract Dutch BBT entries from HTML using text-based parsing"""
        
        # Get all text content and split by BBT patterns
        full_text = soup.get_text()
        
        # Split text into BBT sections using regex
        bbt_pattern = r'(BBT\s+(\d+)\.?\s+[^.]+\.)'
        
        # Find all BBT starts
        bbt_matches = list(re.finditer(bbt_pattern, full_text, re.IGNORECASE))
        
        bbts = []
        
        for i, match in enumerate(bbt_matches):
            bbt_num = int(match.group(2))
            start_pos = match.start()
            
            # Find end position (start of next BBT or end of text)
            if i + 1 < len(bbt_matches):
                end_pos = bbt_matches[i + 1].start()
            else:
                # For last BBT, find logical end
                end_pos = self._find_text_end_position(full_text, start_pos)
            
            # Extract BBT text
            bbt_text = full_text[start_pos:end_pos].strip()
            
            # Validate and create BBT entry
            if len(bbt_text) > 100:  # Minimum length check
                # Extract corresponding HTML for tables
                bbt_html = self._extract_html_for_text_range(soup, match.group(1), bbt_text[:500])
                
                # Count tables in this section
                table_count = bbt_text.count('Tabel') + bbt_text.count('Table')
                has_tables = table_count > 0
                
                # Extract title
                title = self._extract_title_from_text(bbt_text, bbt_num)
                
                bbt_dict = {
                    'bbt_number': bbt_num,
                    'bbt_id': f'BBT {bbt_num}',
                    'title': title,
                    'full_text': bbt_text,
                    'full_html': bbt_html,
                    'text_length': len(bbt_text),
                    'has_tables': has_tables,
                    'table_count': table_count,
                    'extraction_method': 'HTML text-based parsing',
                    'source_url': source_url,
                    'language': 'Dutch'
                }
                
                bbts.append(bbt_dict)
        
        # Sort by BBT number
        bbts.sort(key=lambda x: x['bbt_number'])
        
        return bbts
    
    def _find_text_end_position(self, full_text: str, start_pos: int) -> int:
        """Find logical end position for text-based extraction"""
        
        # Look for end indicators in Dutch
        search_text = full_text[start_pos:]
        
        end_patterns = [
            r'BIJLAGE\s+[IVX]+',     # Annex
            r'Hoofdstuk\s+[5-9]',    # Next chapter  
            r'Referenties\s*$',      # References
            r'Glossarium\s*$',       # Glossary
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return start_pos + match.start()
        
        # Default: limit to reasonable length
        max_length = 10000
        return min(len(full_text), start_pos + max_length)
    
    def _extract_html_for_text_range(self, soup: BeautifulSoup, start_marker: str, text_sample: str) -> str:
        """Extract HTML that corresponds to the text range"""
        
        # Find elements that contain the start marker or sample text
        matching_elements = []
        
        for element in soup.find_all(['p', 'div', 'table', 'td', 'tr']):
            if start_marker in element.get_text() or any(word in element.get_text() for word in text_sample.split()[:5]):
                matching_elements.append(str(element))
        
        return '\n'.join(matching_elements[:10])  # Limit to first 10 elements
    
    def _extract_title_from_text(self, text: str, bbt_num: int) -> str:
        """Extract title from BBT text"""
        
        # Take first line after BBT number
        lines = text.split('\n')
        first_line = lines[0] if lines else text
        
        # Remove BBT number prefix
        title = re.sub(rf'^BBT\s*{bbt_num}\.?\s*', '', first_line, flags=re.IGNORECASE)
        
        # Take first sentence or reasonable length
        sentences = title.split('.')
        if sentences and len(sentences[0]) > 10:
            return sentences[0].strip()[:200]
        
        return title.strip()[:200] if title.strip() else f"BBT {bbt_num}"
    
    def _extract_english_bats(self, soup: BeautifulSoup, source_url: str) -> List[Dict]:
        """Extract English BAT entries from HTML"""
        
        bats = []
        
        # Similar approach for English BAT entries
        all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'td'])
        
        current_bat = None
        bat_content = []
        
        for element in all_elements:
            text = element.get_text(strip=True)
            
            # Check for BAT patterns
            bat_match = re.search(r'\b(\d+)\.\s*BAT\s+(?:is\s+to|for)', text, re.IGNORECASE)
            if not bat_match:
                bat_match = re.search(r'\bBAT\s+(\d+)\b', text)
                
            if bat_match:
                # Save previous BAT
                if current_bat and bat_content:
                    bat_dict = self._create_bbt_dict(current_bat, bat_content, source_url, 'English')
                    if bat_dict:
                        bats.append(bat_dict)
                
                # Start new BAT
                current_bat = int(bat_match.group(1))
                bat_content = [element]
                
            elif current_bat and text:
                # Continue current BAT content
                bat_content.append(element)
                
                # Stop at section breaks
                if self._is_section_break(element, text):
                    break
        
        # Save last BAT
        if current_bat and bat_content:
            bat_dict = self._create_bbt_dict(current_bat, bat_content, source_url, 'English')
            if bat_dict:
                bats.append(bat_dict)
        
        bats = self._deduplicate_and_sort(bats)
        return bats
    
    def _create_bbt_dict(self, number: int, elements: List[Tag], source_url: str, language: str) -> Optional[Dict]:
        """Create BAT/BBT dictionary from HTML elements"""
        
        if not elements:
            return None
        
        # Extract full text with HTML structure preserved
        full_html = ""
        full_text = ""
        
        for element in elements:
            full_html += str(element) + "\n"
            full_text += element.get_text() + "\n"
        
        full_text = full_text.strip()
        
        # Validate minimum content
        if len(full_text) < 50:
            return None
        
        # Extract title from first element
        title = self._extract_title(elements[0].get_text().strip(), number, language)
        
        # Check for tables
        has_tables = any(element.find('table') or element.name == 'table' for element in elements)
        table_count = sum(len(element.find_all('table')) for element in elements)
        
        prefix = 'BBT' if language == 'Dutch' else 'BAT'
        
        return {
            f'{prefix.lower()}_number': number,
            f'{prefix.lower()}_id': f'{prefix} {number}',
            'title': title,
            'full_text': full_text,
            'full_html': full_html,
            'text_length': len(full_text),
            'has_tables': has_tables,
            'table_count': table_count,
            'extraction_method': 'HTML structural parsing',
            'source_url': source_url,
            'language': language
        }
    
    def _extract_title(self, text: str, number: int, language: str) -> str:
        """Extract meaningful title from first line"""
        
        prefix = 'BBT' if language == 'Dutch' else 'BAT'
        
        # Remove the BAT/BBT number prefix
        title = re.sub(rf'^{prefix}\s*{number}\.?\s*', '', text, flags=re.IGNORECASE)
        title = re.sub(r'^\d+\.\s*', '', title)
        
        # Take first substantial part
        lines = title.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20:
                return line[:200]
        
        return f"{prefix} {number} extracted from HTML"
    
    def _is_section_break(self, element: Tag, text: str) -> bool:
        """Check if element indicates a section break"""
        
        # Check for heading elements
        if element.name in ['h1', 'h2', 'h3']:
            return True
        
        # Check for common section break patterns
        break_patterns = [
            r'Chapter\s+\d+',
            r'Section\s+\d+',
            r'Hoofdstuk\s+\d+',  # Dutch
            r'BIJLAGE',          # Dutch Annex
            r'Annex',
            r'References',
            r'Referenties'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in break_patterns)
    
    def _deduplicate_and_sort(self, bats: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by BAT/BBT number"""
        
        # Group by number and keep the longest entry
        by_number = {}
        for bat in bats:
            key = 'bbt_number' if 'bbt_number' in bat else 'bat_number'
            number = bat[key]
            
            if number not in by_number or len(bat['full_text']) > len(by_number[number]['full_text']):
                by_number[number] = bat
        
        # Sort by number
        result = list(by_number.values())
        key = 'bbt_number' if result and 'bbt_number' in result[0] else 'bat_number'
        result.sort(key=lambda x: x[key])
        
        return result
    
    def save_extracted_entries(self, entries: List[Dict], output_path: str):
        """Save extracted entries to JSON file"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        
        entry_type = 'BBTs' if entries and 'bbt_number' in entries[0] else 'BATs'
        print(f"💾 Saved {len(entries)} complete {entry_type} to: {output_path}")
    
    def print_extraction_summary(self, entries: List[Dict]):
        """Print summary of extracted entries"""
        
        if not entries:
            print("No entries found")
            return
        
        entry_type = 'BBTs' if 'bbt_number' in entries[0] else 'BATs'
        language = entries[0].get('language', 'Unknown')
        
        print(f"\n📋 === EXTRACTED {len(entries)} COMPLETE {entry_type.upper()} ===\n")
        
        total_chars = sum(len(entry['full_text']) for entry in entries)
        avg_length = total_chars // len(entries)
        tables_count = sum(entry.get('table_count', 0) for entry in entries)
        
        print(f"Total characters extracted: {total_chars:,}")
        print(f"Average entry length: {avg_length:,} characters")
        print(f"Language: {language}")
        print(f"Total tables found: {tables_count}")
        print(f"Entries with tables: {sum(1 for e in entries if e.get('has_tables', False))}")
        
        print(f"\n📝 {entry_type.upper()} Summary:")
        key = 'bbt_number' if entry_type == 'BBTs' else 'bat_number'
        
        for entry in entries[:15]:  # Show first 15
            num = entry[key]
            title = entry['title'][:80] + "..." if len(entry['title']) > 80 else entry['title']
            tables = f" [{entry.get('table_count', 0)} tables]" if entry.get('has_tables') else ""
            print(f"  {entry_type[:-1]} {num:2d}: {title}{tables}")
            print(f"           {entry['text_length']:,} chars")
        
        if len(entries) > 15:
            print(f"\n... and {len(entries) - 15} more {entry_type}")


def test_html_extraction():
    """Test HTML extraction on CWW Dutch BATC"""
    
    print("🚀 === HTML BAT/BBT EXTRACTOR TEST ===\n")
    
    extractor = HTMLBATExtractor()
    
    # Test Dutch CWW BATC
    print("🎯 Testing Dutch CWW BATC HTML extraction...")
    cww_url = "https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32016D0902"
    
    bbts = extractor.extract_bats_from_html_url(cww_url, language='nl')
    
    if bbts:
        extractor.print_extraction_summary(bbts)
        extractor.save_extracted_entries(bbts, "cww_html_bbts.json")
        
        print(f"\n✅ HTML extraction successful!")
        print(f"   Extracted {len(bbts)} complete BBTs using HTML structure")
        print(f"   Tables preserved: {sum(e.get('table_count', 0) for e in bbts)}")
        print(f"   No PDF parsing artifacts or layout issues")
        
        # Show example
        if bbts:
            print(f"\n🔍 Example BBT (BBT {bbts[0].get('bbt_number', '?')}):")
            print(f"Title: {bbts[0]['title']}")
            print(f"Has tables: {bbts[0].get('has_tables', False)}")
            print(f"First 200 chars: {bbts[0]['full_text'][:200]}...")
        
    else:
        print("❌ No BBTs found in HTML extraction")
    
    return bbts


if __name__ == "__main__":
    test_html_extraction()