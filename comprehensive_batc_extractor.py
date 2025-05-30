#!/usr/bin/env python3
"""
Comprehensive BATC Extractor for All EU BAT Conclusions Documents
Extracts all BBT entries from the complete list of BATC HTML documents
"""

import requests
import json
import re
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time
from datetime import datetime

class ComprehensiveBATCExtractor:
    """Extracts BBT entries from all BATC documents"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Complete BATC document list
        self.batc_documents = {
            'CAK': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32013D0732',
            'CLM': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32013D0732',
            'CWW': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32016D0902',
            'FDM': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32019D2031',
            'FMP': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32019D2031',
            'GLS': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32012D0134',
            'IRPP': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32017D0302',
            'IS': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32012D0135',
            'LCP': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32021D2326',
            'LVOC': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32017D2117',
            'NFM': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32016D1032',
            'PP': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32016D1032',
            'REF': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32014D0738',
            'SA': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:02023D2749-20231218&qid=1748586721823',
            'SF': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=OJ:L_202402974',
            'STS': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32020D2009',
            'TAN': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32013D0084',
            'TXT': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32022D2508',
            'WBP': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32015D2119',
            'WGC': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32022D2427',
            'WI': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32019D2010',
            'WT': 'https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32018D1147'
        }
        
        # Results storage
        self.extraction_results = {}
        self.extraction_stats = {}
    
    def extract_all_batcs(self, output_dir: str = "batc_extractions") -> Dict:
        """Extract BBTs from all BATC documents"""
        
        print("🚀 === COMPREHENSIVE BATC EXTRACTION ===\n")
        print(f"📋 Processing {len(self.batc_documents)} BATC documents...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        total_bbts = 0
        successful_docs = 0
        failed_docs = []
        
        for doc_code, url in self.batc_documents.items():
            print(f"\n🔍 Processing {doc_code}...")
            
            try:
                # Determine language
                language = 'English' if '/EN/' in url else 'Dutch'
                
                # Extract BBTs from this document
                bbts = self.extract_bbts_from_url(url, doc_code, language)
                
                if bbts:
                    # Save individual document results
                    doc_filename = f"{output_dir}/{doc_code.lower()}_bbts.json"
                    self.save_document_results(bbts, doc_filename, doc_code)
                    
                    # Store in overall results
                    self.extraction_results[doc_code] = bbts
                    self.extraction_stats[doc_code] = {
                        'bbt_count': len(bbts),
                        'total_chars': sum(len(bbt.get('full_text', '')) for bbt in bbts),
                        'has_tables': sum(1 for bbt in bbts if bbt.get('has_tables', False)),
                        'language': language,
                        'url': url,
                        'extraction_time': datetime.now().isoformat()
                    }
                    
                    total_bbts += len(bbts)
                    successful_docs += 1
                    
                    print(f"  ✅ {doc_code}: {len(bbts)} BBTs extracted")
                    
                else:
                    failed_docs.append(doc_code)
                    print(f"  ❌ {doc_code}: No BBTs found")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                failed_docs.append(doc_code)
                print(f"  ❌ {doc_code}: Error - {e}")
        
        # Save comprehensive results
        self.save_comprehensive_results(output_dir)
        
        # Print summary
        self.print_extraction_summary(total_bbts, successful_docs, failed_docs)
        
        return self.extraction_results
    
    def extract_bbts_from_url(self, url: str, doc_code: str, language: str) -> List[Dict]:
        """Extract BBTs from a single BATC document URL"""
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use text-based extraction for consistent results
            return self._extract_bbts_from_html(soup, url, doc_code, language)
            
        except Exception as e:
            print(f"    Error fetching {doc_code}: {e}")
            return []
    
    def _extract_bbts_from_html(self, soup: BeautifulSoup, source_url: str, doc_code: str, language: str) -> List[Dict]:
        """Extract BBT entries using improved HTML parsing"""
        
        # Get full text content
        full_text = soup.get_text()
        
        # Determine BBT pattern based on language
        if language == 'English':
            # English: "BAT X" or "X. BAT"
            bbt_pattern = r'(?:(\d+)\.\s*)?(?:BAT|BBT)\s+(\d+)\.?\s+[^.]*\.'
            prefix = 'BAT'
        else:
            # Dutch: "BBT X"
            bbt_pattern = r'(?:BBT|BAT)\s+(\d+)\.?\s+[^.]*\.'
            prefix = 'BBT'
        
        # Find all BBT matches
        bbt_matches = list(re.finditer(bbt_pattern, full_text, re.IGNORECASE | re.MULTILINE))
        
        bbts = []
        processed_numbers = set()
        
        for i, match in enumerate(bbt_matches):
            # Extract BBT number
            if language == 'English':
                bbt_num = int(match.group(2) if match.group(2) else match.group(1))
            else:
                bbt_num = int(match.group(1))
            
            # Skip duplicates
            if bbt_num in processed_numbers:
                continue
            
            # Extract BBT content
            start_pos = match.start()
            
            # Find end position
            if i + 1 < len(bbt_matches):
                end_pos = bbt_matches[i + 1].start()
            else:
                end_pos = self._find_logical_end(full_text, start_pos)
            
            bbt_text = full_text[start_pos:end_pos].strip()
            
            # Validate content
            if len(bbt_text) > 100:  # Minimum length
                # Extract title
                title = self._extract_title(bbt_text, bbt_num, prefix)
                
                # Detect tables
                table_indicators = ['Table', 'Tabel', 'table']
                table_count = sum(bbt_text.lower().count(indicator.lower()) for indicator in table_indicators)
                has_tables = table_count > 0
                
                bbt_dict = {
                    f'{prefix.lower()}_number': bbt_num,
                    f'{prefix.lower()}_id': f'{prefix} {bbt_num}',
                    'title': title,
                    'full_text': bbt_text,
                    'text_length': len(bbt_text),
                    'has_tables': has_tables,
                    'table_count': table_count,
                    'document_code': doc_code,
                    'language': language,
                    'source_url': source_url,
                    'extraction_method': 'HTML comprehensive parsing'
                }
                
                bbts.append(bbt_dict)
                processed_numbers.add(bbt_num)
        
        # Sort by number
        key = f'{prefix.lower()}_number'
        bbts.sort(key=lambda x: x[key])
        
        return bbts
    
    def _find_logical_end(self, text: str, start_pos: int) -> int:
        """Find logical end position for BBT content"""
        
        search_text = text[start_pos:]
        
        # Look for section end patterns
        end_patterns = [
            r'BIJLAGE\s+[IVX]+',     # Dutch Annex
            r'ANNEX\s+[IVX]+',       # English Annex
            r'References',           # References section
            r'Referenties',          # Dutch References
            r'Glossary',            # Glossary
            r'Glossarium',          # Dutch Glossary
            r'Chapter\s+[5-9]',     # Next chapter
            r'Hoofdstuk\s+[5-9]'    # Dutch chapter
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return start_pos + match.start()
        
        # Default limit
        return min(len(text), start_pos + 15000)
    
    def _extract_title(self, text: str, number: int, prefix: str) -> str:
        """Extract meaningful title from BBT text"""
        
        lines = text.split('\n')
        first_line = lines[0] if lines else text[:200]
        
        # Clean up title
        title = re.sub(rf'^{prefix}\s*{number}\.?\s*', '', first_line, flags=re.IGNORECASE)
        title = re.sub(r'^\d+\.\s*', '', title)
        
        # Take first sentence
        sentences = title.split('.')
        if sentences and len(sentences[0].strip()) > 10:
            return sentences[0].strip()[:200]
        
        return title.strip()[:200] if title.strip() else f"{prefix} {number}"
    
    def save_document_results(self, bbts: List[Dict], filename: str, doc_code: str):
        """Save results for individual document"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bbts, f, indent=2, ensure_ascii=False)
    
    def save_comprehensive_results(self, output_dir: str):
        """Save comprehensive extraction results"""
        
        # Save all BBTs in one file
        all_bbts_file = f"{output_dir}/all_batc_bbts.json"
        with open(all_bbts_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_results, f, indent=2, ensure_ascii=False)
        
        # Save extraction statistics
        stats_file = f"{output_dir}/extraction_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive results saved:")
        print(f"   📄 All BBTs: {all_bbts_file}")
        print(f"   📊 Statistics: {stats_file}")
    
    def print_extraction_summary(self, total_bbts: int, successful_docs: int, failed_docs: List[str]):
        """Print comprehensive extraction summary"""
        
        print(f"\n🎯 === COMPREHENSIVE EXTRACTION SUMMARY ===")
        print(f"📋 Documents processed: {len(self.batc_documents)}")
        print(f"✅ Successful extractions: {successful_docs}")
        print(f"❌ Failed extractions: {len(failed_docs)}")
        print(f"📝 Total BBTs extracted: {total_bbts}")
        
        if failed_docs:
            print(f"\n⚠️  Failed documents: {', '.join(failed_docs)}")
        
        print(f"\n📊 By Document:")
        for doc_code, stats in self.extraction_stats.items():
            lang_emoji = "🇬🇧" if stats['language'] == 'English' else "🇳🇱"
            table_info = f" ({stats['has_tables']} with tables)" if stats['has_tables'] > 0 else ""
            print(f"   {lang_emoji} {doc_code:4s}: {stats['bbt_count']:2d} BBTs{table_info}")
        
        print(f"\n🌍 Language distribution:")
        lang_counts = {}
        for stats in self.extraction_stats.values():
            lang = stats['language']
            lang_counts[lang] = lang_counts.get(lang, 0) + stats['bbt_count']
        
        for lang, count in lang_counts.items():
            emoji = "🇬🇧" if lang == 'English' else "🇳🇱"
            print(f"   {emoji} {lang}: {count} BBTs")


def main():
    """Main extraction function"""
    
    print("🌟 === COMPREHENSIVE BATC BBT EXTRACTION SYSTEM ===\n")
    
    extractor = ComprehensiveBATCExtractor()
    
    # Extract from all BATC documents
    results = extractor.extract_all_batcs()
    
    if results:
        print(f"\n🎉 === EXTRACTION COMPLETE ===")
        print(f"✅ Successfully processed EU BATC documents")
        print(f"📚 Complete BBT database created")
        print(f"🔍 Ready for compliance verification system")
    else:
        print(f"\n❌ === EXTRACTION FAILED ===")
        print(f"No results obtained from BATC documents")


if __name__ == "__main__":
    main()