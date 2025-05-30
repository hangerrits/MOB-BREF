#!/usr/bin/env python3
"""
Comprehensive BREF Extractor for Chapter 5 BATs
Extracts BAT entries from English BREF documents, focusing on Chapter 5
"""

import fitz
import requests
import json
import re
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time
from datetime import datetime

class ComprehensiveBREFExtractor:
    """Extracts BAT entries from English BREF documents (Chapter 5 focus)"""
    
    def __init__(self):
        # Complete BREF document list
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
        
        # Results storage
        self.extraction_results = {}
        self.extraction_stats = {}
        
        # Create downloads directory
        self.downloads_dir = "bref_downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def extract_all_brefs(self, output_dir: str = "bref_extractions") -> Dict:
        """Extract BATs from all BREF documents"""
        
        print("🚀 === COMPREHENSIVE BREF EXTRACTION ===\n")
        print(f"📋 Processing {len(self.bref_documents)} BREF documents...")
        print("🎯 Focusing on Chapter 5 for BAT conclusions\n")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        total_bats = 0
        successful_docs = 0
        failed_docs = []
        
        for doc_code, url in self.bref_documents.items():
            print(f"\n🔍 Processing {doc_code}...")
            
            try:
                # Download and extract BATs
                bats = self.extract_bats_from_bref_url(url, doc_code)
                
                if bats:
                    # Save individual document results
                    doc_filename = f"{output_dir}/{doc_code.lower()}_bats.json"
                    self.save_document_results(bats, doc_filename, doc_code)
                    
                    # Store in overall results
                    self.extraction_results[doc_code] = bats
                    self.extraction_stats[doc_code] = {
                        'bat_count': len(bats),
                        'total_chars': sum(len(bat.get('full_text', '')) for bat in bats),
                        'has_tables': sum(1 for bat in bats if bat.get('has_tables', False)),
                        'chapter_5_bats': sum(1 for bat in bats if 'chapter 5' in bat.get('extraction_context', '').lower()),
                        'language': 'English',
                        'url': url,
                        'extraction_time': datetime.now().isoformat()
                    }
                    
                    total_bats += len(bats)
                    successful_docs += 1
                    
                    print(f"  ✅ {doc_code}: {len(bats)} BATs extracted")
                    
                else:
                    failed_docs.append(doc_code)
                    print(f"  ❌ {doc_code}: No BATs found")
                
                # Rate limiting to be respectful
                time.sleep(2)
                
            except Exception as e:
                failed_docs.append(doc_code)
                print(f"  ❌ {doc_code}: Error - {e}")
        
        # Save comprehensive results
        self.save_comprehensive_results(output_dir)
        
        # Print summary
        self.print_extraction_summary(total_bats, successful_docs, failed_docs)
        
        return self.extraction_results
    
    def extract_bats_from_bref_url(self, url: str, doc_code: str) -> List[Dict]:
        """Extract BATs from a single BREF document URL"""
        
        try:
            # Download PDF
            pdf_path = self.download_pdf(url, doc_code)
            
            if not pdf_path or not os.path.exists(pdf_path):
                print(f"    Failed to download {doc_code}")
                return []
            
            # Extract BATs using Chapter 5 focus
            return self.extract_bats_from_pdf(pdf_path, doc_code, url)
            
        except Exception as e:
            print(f"    Error processing {doc_code}: {e}")
            return []
    
    def download_pdf(self, url: str, doc_code: str) -> Optional[str]:
        """Download PDF file"""
        
        try:
            pdf_path = f"{self.downloads_dir}/{doc_code.lower()}_bref.pdf"
            
            # Skip if already downloaded
            if os.path.exists(pdf_path):
                print(f"    Using cached {doc_code}")
                return pdf_path
            
            print(f"    Downloading {doc_code}...")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            print(f"    Downloaded {doc_code} ({len(response.content):,} bytes)")
            return pdf_path
            
        except Exception as e:
            print(f"    Download failed for {doc_code}: {e}")
            return None
    
    def extract_bats_from_pdf(self, pdf_path: str, doc_code: str, source_url: str) -> List[Dict]:
        """Extract BATs from PDF using Chapter 5 focus and sequential approach"""
        
        try:
            doc = fitz.open(pdf_path)
            
            # Find BAT conclusions section (could be Chapter 4 or other)
            bat_pages = self.find_bat_conclusions_pages(doc)
            
            if not bat_pages:
                print(f"    No BAT conclusions found in {doc_code}, searching entire document")
                # Fallback to search entire document for BAT patterns
                bat_pages = list(range(len(doc)))
            else:
                print(f"    Found BAT conclusions in {doc_code}: pages {bat_pages[0]+1}-{bat_pages[-1]+1}")
            
            # Extract text from BAT pages
            full_text = self.extract_text_from_pages(doc, bat_pages)
            
            # Find BAT positions using multiple patterns
            bat_positions = self.find_bat_positions(full_text)
            
            # Extract complete BAT texts
            bats = self.extract_complete_bat_texts(full_text, bat_positions, doc_code, source_url, bat_pages)
            
            doc.close()
            return bats
            
        except Exception as e:
            print(f"    PDF extraction failed for {doc_code}: {e}")
            return []
    
    def find_bat_conclusions_pages(self, doc) -> List[int]:
        """Find pages containing BAT conclusions (could be Chapter 4, 5, or other)"""
        
        bat_pages = []
        
        # First pass: look for BAT conclusion sections
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()
            
            # Look for BAT conclusion indicators
            bat_patterns = [
                r'chapter\s+4.*bat',
                r'chapter\s+4.*energy\s+efficiency',
                r'bat\s+conclusions',
                r'best\s+available\s+techniques?\s+conclusions?',
                r'conclusions\s+on\s+bat',
                r'4\.\s+best\s+available\s+techniques?',
                r'chapter\s+4.*conclusions',
                r'general\s+bat'
            ]
            
            for pattern in bat_patterns:
                if re.search(pattern, text):
                    bat_pages.append(page_num)
                    break
        
        # Second pass: if no clear chapter found, look for pages with multiple BAT references
        if not bat_pages:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Count BAT mentions
                bat_mentions = len(re.findall(r'\bBAT\s+\d+', text, re.IGNORECASE))
                if bat_mentions >= 3:  # Page with multiple BAT references
                    bat_pages.append(page_num)
        
        # If we found BAT markers, extend to reasonable range
        if bat_pages:
            start_page = min(bat_pages)
            # Look for a reasonable end point
            end_page = len(doc)
            
            # Try to find logical end (References, Annex, etc.)
            for page_num in range(start_page + 1, len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()
                
                if any(end_marker in text for end_marker in ['references', 'annex', 'glossary', 'bibliography']):
                    end_page = page_num
                    break
            
            # Limit to reasonable range
            end_page = min(end_page, start_page + 150)
            return list(range(start_page, end_page))
        
        return []
    
    def extract_text_from_pages(self, doc, page_range: List[int]) -> str:
        """Extract text from specified pages"""
        
        texts = []
        
        for page_num in page_range:
            if page_num < len(doc):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Add page marker
                page_marker = f"\n[PAGE_{page_num + 1}]\n"
                texts.append(page_marker)
                texts.append(page_text)
        
        return "".join(texts)
    
    def find_bat_positions(self, text: str) -> List[tuple]:
        """Find BAT start positions using multiple patterns"""
        
        positions = []
        
        # Pattern 1: "X. BAT is to..."
        pattern1 = re.compile(r'^\s*(\d+)\.\s*BAT\s+is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        for match in pattern1.finditer(text):
            bat_num = int(match.group(1))
            positions.append((match.start(), bat_num, match.group(0), 'standard'))
        
        # Pattern 2: "BAT X is to..." or "BAT X:"
        pattern2 = re.compile(r'\bBAT\s+(\d+)\s+(?:is\s+to|:)', re.IGNORECASE)
        for match in pattern2.finditer(text):
            bat_num = int(match.group(1))
            # Avoid duplicates
            if not any(pos[1] == bat_num and abs(pos[0] - match.start()) < 100 for pos in positions):
                positions.append((match.start(), bat_num, match.group(0), 'alternative'))
        
        # Pattern 3: "BAT for [system] is to..." (like ENE BAT 18)
        pattern3 = re.compile(r'^\s*(\d+)\.\s*BAT\s+for\s+\w+.*?is\s+to\s+', re.MULTILINE | re.IGNORECASE)
        for match in pattern3.finditer(text):
            bat_num = int(match.group(1))
            if not any(pos[1] == bat_num for pos in positions):
                positions.append((match.start(), bat_num, match.group(0), 'specialized'))
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        return positions
    
    def extract_complete_bat_texts(self, full_text: str, bat_positions: List[tuple], 
                                 doc_code: str, source_url: str, page_range: List[int]) -> List[Dict]:
        """Extract complete BAT texts using sequential approach"""
        
        bats = []
        processed_numbers = set()
        
        for i, (start_pos, bat_num, match_text, pattern_type) in enumerate(bat_positions):
            
            # Skip duplicates
            if bat_num in processed_numbers:
                continue
            
            # Find end position
            if i + 1 < len(bat_positions):
                end_pos = bat_positions[i + 1][0]
            else:
                end_pos = self.find_logical_end_position(full_text, start_pos)
            
            # Extract BAT text
            bat_text = full_text[start_pos:end_pos].strip()
            
            # Validate minimum content
            if len(bat_text) < 100:
                continue
            
            # Clean text
            bat_text = self.clean_bat_text(bat_text)
            
            # Extract title
            title = self.extract_bat_title(bat_text, bat_num)
            
            # Find page number
            page_num = self.find_page_number(full_text, start_pos)
            
            # Detect tables and technical content
            has_tables = self.detect_tables(bat_text)
            table_count = bat_text.lower().count('table')
            
            # Check if from Chapter 5
            extraction_context = "Chapter 5" if page_num in page_range else "Other section"
            
            bat_dict = {
                'bat_number': bat_num,
                'bat_id': f'BAT {bat_num}',
                'title': title,
                'full_text': bat_text,
                'text_length': len(bat_text),
                'has_tables': has_tables,
                'table_count': table_count,
                'page': page_num,
                'document_code': doc_code,
                'extraction_method': f'BREF sequential parsing ({pattern_type})',
                'extraction_context': extraction_context,
                'source_url': source_url,
                'language': 'English'
            }
            
            bats.append(bat_dict)
            processed_numbers.add(bat_num)
        
        # Sort by BAT number
        bats.sort(key=lambda x: x['bat_number'])
        
        return bats
    
    def clean_bat_text(self, text: str) -> str:
        """Clean BAT text"""
        
        # Remove page markers
        text = re.sub(r'\[PAGE_\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove standalone page numbers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def extract_bat_title(self, bat_text: str, bat_num: int) -> str:
        """Extract meaningful title from BAT text"""
        
        lines = bat_text.split('\n')
        
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 20 and not re.match(r'^\d+\.?\s*$', line):
                # Clean title
                title = re.sub(rf'^\d+\.\s*BAT\s+(?:is\s+to\s*)?', '', line, flags=re.IGNORECASE)
                title = re.sub(rf'^BAT\s+{bat_num}\s*:?\s*', '', title, flags=re.IGNORECASE)
                
                if title.strip():
                    return title.strip()[:200]
        
        return f"BAT {bat_num} from Chapter 5"
    
    def detect_tables(self, text: str) -> bool:
        """Detect if BAT contains tables"""
        
        table_indicators = [
            'table', 'emission limit', 'parameter', 'value', 'unit',
            'monitoring', 'measurement', 'limit value', 'technique'
        ]
        
        text_lower = text.lower()
        return sum(text_lower.count(indicator) for indicator in table_indicators) >= 3
    
    def find_logical_end_position(self, text: str, start_pos: int) -> int:
        """Find logical end for BAT content"""
        
        search_text = text[start_pos:]
        
        end_patterns = [
            r'Chapter\s+[6-9]',
            r'Annex\s+[A-Z]',
            r'References\s*$',
            r'Glossary\s*$',
            r'Bibliography'
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                return start_pos + match.start()
        
        # Default limit
        return min(len(text), start_pos + 20000)
    
    def find_page_number(self, text: str, position: int) -> int:
        """Find page number for given position"""
        
        text_before = text[:position]
        page_matches = list(re.finditer(r'\[PAGE_(\d+)\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1
    
    def save_document_results(self, bats: List[Dict], filename: str, doc_code: str):
        """Save results for individual document"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bats, f, indent=2, ensure_ascii=False)
    
    def save_comprehensive_results(self, output_dir: str):
        """Save comprehensive extraction results"""
        
        # Save all BATs
        all_bats_file = f"{output_dir}/all_bref_bats.json"
        with open(all_bats_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_results, f, indent=2, ensure_ascii=False)
        
        # Save statistics
        stats_file = f"{output_dir}/bref_extraction_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive BREF results saved:")
        print(f"   📄 All BATs: {all_bats_file}")
        print(f"   📊 Statistics: {stats_file}")
    
    def print_extraction_summary(self, total_bats: int, successful_docs: int, failed_docs: List[str]):
        """Print comprehensive extraction summary"""
        
        print(f"\n🎯 === COMPREHENSIVE BREF EXTRACTION SUMMARY ===")
        print(f"📋 Documents processed: {len(self.bref_documents)}")
        print(f"✅ Successful extractions: {successful_docs}")
        print(f"❌ Failed extractions: {len(failed_docs)}")
        print(f"📝 Total BATs extracted: {total_bats}")
        
        if failed_docs:
            print(f"\n⚠️  Failed documents: {', '.join(failed_docs)}")
        
        print(f"\n📊 By Document:")
        for doc_code, stats in self.extraction_stats.items():
            ch5_info = f" ({stats['chapter_5_bats']} from Ch.5)" if stats['chapter_5_bats'] > 0 else ""
            table_info = f" [{stats['has_tables']} with tables]" if stats['has_tables'] > 0 else ""
            print(f"   🇬🇧 {doc_code:8s}: {stats['bat_count']:2d} BATs{ch5_info}{table_info}")


def main():
    """Main BREF extraction function"""
    
    print("🌟 === COMPREHENSIVE BREF BAT EXTRACTION SYSTEM ===\n")
    print("🎯 Targeting Chapter 5 for BAT conclusions")
    print("🇬🇧 Processing English BREF documents\n")
    
    extractor = ComprehensiveBREFExtractor()
    
    # Extract from all BREF documents
    results = extractor.extract_all_brefs()
    
    if results:
        print(f"\n🎉 === BREF EXTRACTION COMPLETE ===")
        print(f"✅ Successfully processed English BREF documents")
        print(f"📚 Chapter 5 BAT database created")
        print(f"🔍 Ready for integration with Dutch BBT database")
    else:
        print(f"\n❌ === BREF EXTRACTION FAILED ===")
        print(f"No results obtained from BREF documents")


if __name__ == "__main__":
    main()