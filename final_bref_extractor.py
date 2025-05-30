#!/usr/bin/env python3
"""
Final BREF Extractor - Technical Guidance Focus
Extracts technical guidance and BAT information from Chapter 5 and other BAT sections
"""

import fitz
import json
import re
import os
from typing import List, Dict, Tuple

class FinalBREFExtractor:
    """Extracts technical guidance from BREFs (Chapter 5 focus)"""
    
    def __init__(self):
        # Remaining failed BREFs
        self.remaining_brefs = ['CER', 'ECM', 'LVIC-AAF', 'OFC', 'ROM', 'SIC', 'STM']
        self.downloads_dir = "bref_downloads"
        self.results = {}
    
    def extract_final_brefs(self) -> Dict:
        """Extract technical guidance from remaining BREFs"""
        
        print("🎯 === FINAL BREF EXTRACTION ===\n")
        print("Extracting technical guidance from Chapter 5 and BAT sections")
        print(f"Processing {len(self.remaining_brefs)} remaining BREFs\n")
        
        total_techniques = 0
        
        for doc_code in self.remaining_brefs:
            print(f"🔍 Processing {doc_code} (technical guidance)...")
            
            try:
                pdf_path = f"{self.downloads_dir}/{doc_code.lower()}_bref.pdf"
                
                if not os.path.exists(pdf_path):
                    print(f"    PDF not found: {pdf_path}")
                    continue
                
                # Extract technical guidance
                techniques = self.extract_technical_guidance(pdf_path, doc_code)
                
                if techniques:
                    self.results[doc_code] = techniques
                    total_techniques += len(techniques)
                    
                    print(f"  ✅ {doc_code}: {len(techniques)} techniques extracted")
                    
                    # Save individual results
                    self.save_individual_results(techniques, doc_code)
                    
                else:
                    print(f"  ❌ {doc_code}: No techniques found")
                
            except Exception as e:
                print(f"  ❌ {doc_code}: Error - {e}")
        
        # Merge with complete BREF results
        self.merge_all_results()
        
        print(f"\n🎯 === FINAL EXTRACTION SUMMARY ===")
        print(f"📝 New techniques extracted: {total_techniques}")
        
        return self.results
    
    def extract_technical_guidance(self, pdf_path: str, doc_code: str) -> List[Dict]:
        """Extract technical guidance focusing on Chapter 5"""
        
        doc = fitz.open(pdf_path)
        
        try:
            # Find Chapter 5 or BAT sections
            chapter5_pages = self.find_chapter5_pages(doc)
            
            if not chapter5_pages:
                print(f"    No Chapter 5 found, using fallback strategy")
                # Fallback: search for technical content throughout document
                return self.extract_fallback_techniques(doc, doc_code)
            
            print(f"    Found Chapter 5: pages {chapter5_pages[0]+1}-{chapter5_pages[-1]+1}")
            
            # Extract content from Chapter 5
            chapter5_text = self.extract_chapter5_text(doc, chapter5_pages)
            
            # Find technical sections
            techniques = self.extract_techniques_from_chapter5(chapter5_text, doc_code, chapter5_pages)
            
            return techniques
            
        finally:
            doc.close()
    
    def find_chapter5_pages(self, doc) -> List[int]:
        """Find Chapter 5 pages"""
        
        chapter5_pages = []
        found_start = False
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()
            
            # Look for Chapter 5 start
            if not found_start:
                if re.search(r'chapter\s+5\b', text) or re.search(r'5\.\s+.*bat', text):
                    found_start = True
                    chapter5_pages.append(page_num)
                    continue
            
            # If we found start, continue until next chapter or end
            if found_start:
                if re.search(r'chapter\s+[6-9]', text) or re.search(r'annex', text):
                    break
                chapter5_pages.append(page_num)
        
        return chapter5_pages
    
    def extract_chapter5_text(self, doc, pages: List[int]) -> str:
        """Extract text from Chapter 5 pages"""
        
        texts = []
        
        for page_num in pages:
            if page_num < len(doc):
                page = doc[page_num]
                page_text = page.get_text()
                texts.append(f"\\n[PAGE_{page_num + 1}]\\n")
                texts.append(page_text)
        
        return "".join(texts)
    
    def extract_techniques_from_chapter5(self, text: str, doc_code: str, pages: List[int]) -> List[Dict]:
        """Extract techniques from Chapter 5 text"""
        
        techniques = []
        
        # Look for different patterns of technical guidance
        patterns = [
            # BAT sections
            r'(BAT\\s+(?:is\\s+)?to\\s+[^\\n]+(?:\\n[^\\n]*)*?)(?=\\n\\s*BAT\\s|\\n\\s*\\d+\\.|$)',
            
            # Numbered sections with techniques
            r'(\\d+\\.\\d+\\.\\d+\\s+[^\\n]+(?:\\n(?!\\d+\\.\\d+\\.).*)*)',
            
            # Technical guidance sections
            r'((?:Reduce|Control|Monitor|Apply|Use)\\s+[^\\n]+(?:\\n[^\\n]*)*?)(?=\\n\\s*(?:Reduce|Control|Monitor|Apply|Use)|\\n\\s*\\d+\\.|$)',
            
            # Bullet point techniques
            r'([•-]\\s*[^\\n]+(?:\\n(?![•-]|\\d+\\.).*)*)',
        ]
        
        technique_count = 0
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                technique_text = match.group(1).strip()
                
                if len(technique_text) > 100:  # Minimum meaningful content
                    technique_count += 1
                    
                    # Extract title
                    title = self.extract_technique_title(technique_text)
                    
                    # Find page
                    page_num = self.find_page_in_text(text, match.start())
                    
                    technique = {
                        'technique_number': technique_count,
                        'technique_id': f'{doc_code} Technique {technique_count}',
                        'title': title,
                        'full_text': technique_text,
                        'text_length': len(technique_text),
                        'page': page_num,
                        'document_code': doc_code,
                        'extraction_method': 'Chapter 5 technical guidance',
                        'source_url': f'BREF {doc_code}',
                        'language': 'English',
                        'type': 'technical_guidance'
                    }
                    
                    techniques.append(technique)
        
        # Deduplicate by similarity
        return self.deduplicate_techniques(techniques)
    
    def extract_fallback_techniques(self, doc, doc_code: str) -> List[Dict]:
        """Fallback: extract any technical content from entire document"""
        
        techniques = []
        technique_count = 0
        
        # Search entire document for technical content
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Look for technical sentences
            sentences = re.split(r'[.!?]+', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # Check if sentence contains technical guidance
                if (len(sentence) > 50 and 
                    any(word in sentence.lower() for word in 
                        ['technique', 'reduce', 'control', 'monitor', 'apply', 'emission', 'limit'])):
                    
                    technique_count += 1
                    
                    technique = {
                        'technique_number': technique_count,
                        'technique_id': f'{doc_code} Guidance {technique_count}',
                        'title': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'full_text': sentence,
                        'text_length': len(sentence),
                        'page': page_num + 1,
                        'document_code': doc_code,
                        'extraction_method': 'Fallback technical guidance',
                        'source_url': f'BREF {doc_code}',
                        'language': 'English',
                        'type': 'technical_guidance'
                    }
                    
                    techniques.append(technique)
                    
                    # Limit fallback extractions
                    if technique_count >= 20:
                        break
            
            if technique_count >= 20:
                break
        
        return techniques
    
    def extract_technique_title(self, text: str) -> str:
        """Extract title from technique text"""
        
        lines = text.split('\\n')
        first_line = lines[0].strip() if lines else text[:100]
        
        # Clean up title
        title = re.sub(r'^\\d+\\.\\d+\\.\\d+\\s*', '', first_line)
        title = re.sub(r'^BAT\\s+(?:is\\s+)?to\\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^[•-]\\s*', '', title)
        
        return title[:150] if title else "Technical guidance"
    
    def find_page_in_text(self, text: str, position: int) -> int:
        """Find page number for position in text"""
        
        text_before = text[:position]
        page_matches = list(re.finditer(r'\\[PAGE_(\\d+)\\]', text_before))
        
        if page_matches:
            return int(page_matches[-1].group(1))
        
        return 1
    
    def deduplicate_techniques(self, techniques: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar techniques"""
        
        # Simple deduplication by title similarity
        unique_techniques = []
        seen_titles = set()
        
        for technique in techniques:
            title_key = technique['title'][:50].lower()
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_techniques.append(technique)
        
        return unique_techniques
    
    def save_individual_results(self, techniques: List[Dict], doc_code: str):
        """Save individual results"""
        
        os.makedirs("bref_extractions", exist_ok=True)
        filename = f"bref_extractions/{doc_code.lower()}_techniques_final.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(techniques, f, indent=2, ensure_ascii=False)
    
    def merge_all_results(self):
        """Merge with all existing BREF results"""
        
        # Load existing complete results
        existing_file = "bref_extractions/all_bref_bats_complete.json"
        if os.path.exists(existing_file):
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        else:
            existing_results = {}
        
        # Merge with new results
        final_results = {**existing_results, **self.results}
        
        # Save final complete results
        with open("bref_extractions/all_bref_final_complete.json", 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        # Calculate totals
        total_docs = len(final_results)
        total_entries = sum(len(entries) for entries in final_results.values())
        
        print(f"\\n💾 Final complete BREF results:")
        print(f"   📄 Documents: {total_docs}")
        print(f"   📝 Total BATs/Techniques: {total_entries}")
        print(f"   💫 File: bref_extractions/all_bref_final_complete.json")


def main():
    """Extract remaining BREFs with technical guidance approach"""
    
    extractor = FinalBREFExtractor()
    results = extractor.extract_final_brefs()
    
    return results


if __name__ == "__main__":
    main()