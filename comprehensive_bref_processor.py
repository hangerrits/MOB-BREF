# /Users/han/Code/MOB-BREF/comprehensive_bref_processor.py

import os
import json
import requests
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3

from regulatory_data_manager import RegulatoryDataManager, BATConclusion
from pdf_processor import extract_text_and_metadata
from llm_handler import verify_permit_compliance_with_bat

@dataclass
class DetailedBATConclusion:
    """Enhanced BAT conclusion with all details"""
    bat_id: str
    bref_source: str
    bat_number: str
    title: str
    description: str
    applicability: str
    emission_levels: Optional[str] = None
    monitoring_requirements: Optional[str] = None
    techniques: Optional[str] = None
    performance_levels: Optional[str] = None
    implementation_notes: Optional[str] = None
    source_section: Optional[str] = None

class ComprehensiveBREFProcessor:
    """Downloads and processes complete BREF documents with all BAT conclusions"""
    
    def __init__(self, reg_manager: RegulatoryDataManager):
        self.reg_manager = reg_manager
        self.bref_urls = {
            "FDM": {
                "title": "Food, Drink and Milk Industries",
                "bat_conclusions_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32019D2031",
                "full_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/FDM_bref_2019.pdf"
            },
            "IRPP": {
                "title": "Intensive Rearing of Poultry or Pigs", 
                "bat_conclusions_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32017D0302",
                "full_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC107189_IRPP_bref_2017.pdf"
            },
            "LCP": {
                "title": "Large Combustion Plants",
                "bat_conclusions_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32017D1442",
                "full_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107769_LCPBref_2017.pdf"
            },
            "WT": {
                "title": "Waste Treatment",
                "bat_conclusions_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32018D1147", 
                "full_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC113018_WTBref_2018.pdf"
            }
        }
    
    def download_bat_conclusions_document(self, bref_id: str) -> bool:
        """Download the official BAT conclusions document for a BREF"""
        if bref_id not in self.bref_urls:
            print(f"BREF {bref_id} not found in known BREFs")
            return False
        
        bref_info = self.bref_urls[bref_id]
        url = bref_info["bat_conclusions_url"]
        
        try:
            print(f"Downloading BAT conclusions for {bref_id} from {url}")
            response = requests.get(url, timeout=60, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # Save PDF
            filename = f"{bref_id}_BAT_conclusions.pdf"
            local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"BAT conclusions for {bref_id} saved to: {local_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading BAT conclusions for {bref_id}: {e}")
            return False
    
    def extract_bat_conclusions_from_document(self, bref_id: str) -> List[DetailedBATConclusion]:
        """Extract all BAT conclusions from downloaded document"""
        filename = f"{bref_id}_BAT_conclusions.pdf"
        local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
        
        if not os.path.exists(local_path):
            print(f"BAT conclusions document not found for {bref_id}: {local_path}")
            return []
        
        try:
            # Extract text from PDF
            extracted_data = extract_text_and_metadata(local_path)
            
            if not extracted_data or 'full_text' not in extracted_data:
                print(f"Failed to extract text from {local_path}")
                return []
            
            full_text = extracted_data['full_text']
            
            # Parse BAT conclusions systematically
            bat_conclusions = self._parse_comprehensive_bat_conclusions(full_text, bref_id)
            
            # Store in database
            self._store_bat_conclusions(bat_conclusions)
            
            print(f"Extracted {len(bat_conclusions)} BAT conclusions from {bref_id}")
            return bat_conclusions
            
        except Exception as e:
            print(f"Error extracting BAT conclusions from {bref_id}: {e}")
            return []
    
    def _parse_comprehensive_bat_conclusions(self, text: str, bref_id: str) -> List[DetailedBATConclusion]:
        """Comprehensive parsing of BAT conclusions from official documents"""
        bat_conclusions = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        # Patterns for different BREF document structures
        bat_patterns = [
            r'^BAT\s+(\d+(?:\.\d+)?)\.\s*(.*?)$',  # BAT 1. Title
            r'^(\d+(?:\.\d+)?)\.\s*BAT\s*(.*?)$',  # 1. BAT Title
            r'^\*\*BAT\s+(\d+(?:\.\d+)?)\*\*\s*(.*?)$',  # **BAT 1** Title
        ]
        
        current_bat = None
        current_section = ""
        in_bat_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if this line starts a new BAT conclusion
            bat_match = None
            for pattern in bat_patterns:
                bat_match = re.match(pattern, line, re.IGNORECASE)
                if bat_match:
                    break
            
            if bat_match:
                # Save previous BAT if exists
                if current_bat:
                    bat_conclusions.append(current_bat)
                
                # Start new BAT
                bat_number = bat_match.group(1)
                title = bat_match.group(2).strip() if len(bat_match.groups()) > 1 else ""
                
                current_bat = DetailedBATConclusion(
                    bat_id=f"{bref_id}_BAT_{bat_number}",
                    bref_source=bref_id,
                    bat_number=bat_number,
                    title=title,
                    description="",
                    applicability="",
                    source_section=current_section
                )
                in_bat_section = True
                continue
            
            # Track sections
            if line.upper().startswith('CHAPTER') or line.upper().startswith('SECTION'):
                current_section = line
                in_bat_section = False
                continue
            
            # Accumulate BAT content
            if current_bat and in_bat_section and line:
                # Check for specific subsections
                if line.lower().startswith('applicability'):
                    current_bat.applicability += line + " "
                elif any(keyword in line.lower() for keyword in ['emission', 'limit', 'level']):
                    current_bat.emission_levels = (current_bat.emission_levels or "") + line + " "
                elif any(keyword in line.lower() for keyword in ['monitor', 'measure']):
                    current_bat.monitoring_requirements = (current_bat.monitoring_requirements or "") + line + " "
                elif any(keyword in line.lower() for keyword in ['technique', 'method']):
                    current_bat.techniques = (current_bat.techniques or "") + line + " "
                else:
                    current_bat.description += line + " "
        
        # Don't forget the last BAT
        if current_bat:
            bat_conclusions.append(current_bat)
        
        # If no BAT conclusions found with patterns, try alternative extraction
        if not bat_conclusions:
            bat_conclusions = self._extract_bat_conclusions_alternative(text, bref_id)
        
        return bat_conclusions
    
    def _extract_bat_conclusions_alternative(self, text: str, bref_id: str) -> List[DetailedBATConclusion]:
        """Alternative extraction method for different document formats"""
        bat_conclusions = []
        
        # Look for numbered sections that might be BAT conclusions
        lines = text.split('\n')
        
        # Find sections that look like BAT conclusions
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for patterns like "In order to...", "To reduce...", "For..."
            if (line.startswith('In order to') or line.startswith('To reduce') or 
                line.startswith('To prevent') or line.startswith('For')):
                
                # This might be a BAT conclusion - collect surrounding context
                bat_text = line
                
                # Look ahead for continuation
                j = i + 1
                while j < len(lines) and j < i + 10:  # Look up to 10 lines ahead
                    next_line = lines[j].strip()
                    if (next_line and not next_line.startswith('In order to') and 
                        not next_line.startswith('To reduce') and len(next_line) > 10):
                        bat_text += " " + next_line
                        j += 1
                    else:
                        break
                
                if len(bat_text) > 50:  # Only if substantial content
                    bat_number = str(len(bat_conclusions) + 1)
                    
                    bat_conclusion = DetailedBATConclusion(
                        bat_id=f"{bref_id}_BAT_{bat_number}",
                        bref_source=bref_id,
                        bat_number=bat_number,
                        title=f"BAT {bat_number}",
                        description=bat_text,
                        applicability="Generally applicable"
                    )
                    bat_conclusions.append(bat_conclusion)
        
        return bat_conclusions
    
    def _store_bat_conclusions(self, bat_conclusions: List[DetailedBATConclusion]):
        """Store detailed BAT conclusions in database"""
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        # Create enhanced table if needed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detailed_bat_conclusions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bat_id TEXT UNIQUE NOT NULL,
                bref_source TEXT NOT NULL,
                bat_number TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                applicability TEXT,
                emission_levels TEXT,
                monitoring_requirements TEXT,
                techniques TEXT,
                performance_levels TEXT,
                implementation_notes TEXT,
                source_section TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        for bat in bat_conclusions:
            cursor.execute('''
                INSERT OR REPLACE INTO detailed_bat_conclusions 
                (bat_id, bref_source, bat_number, title, description, applicability,
                 emission_levels, monitoring_requirements, techniques, performance_levels,
                 implementation_notes, source_section)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bat.bat_id, bat.bref_source, bat.bat_number, bat.title,
                bat.description, bat.applicability, bat.emission_levels,
                bat.monitoring_requirements, bat.techniques, bat.performance_levels,
                bat.implementation_notes, bat.source_section
            ))
        
        conn.commit()
        conn.close()
    
    def get_all_bat_conclusions_for_bref(self, bref_id: str) -> List[DetailedBATConclusion]:
        """Get all detailed BAT conclusions for a BREF"""
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bat_id, bref_source, bat_number, title, description, applicability,
                   emission_levels, monitoring_requirements, techniques, performance_levels,
                   implementation_notes, source_section
            FROM detailed_bat_conclusions 
            WHERE bref_source = ?
            ORDER BY bat_number
        ''', (bref_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        bat_conclusions = []
        for result in results:
            bat_conclusions.append(DetailedBATConclusion(
                bat_id=result[0],
                bref_source=result[1], 
                bat_number=result[2],
                title=result[3],
                description=result[4],
                applicability=result[5],
                emission_levels=result[6],
                monitoring_requirements=result[7],
                techniques=result[8],
                performance_levels=result[9],
                implementation_notes=result[10],
                source_section=result[11]
            ))
        
        return bat_conclusions
    
    def comprehensive_bat_compliance_check(self, permit_content: str, bref_id: str) -> List[Dict[str, Any]]:
        """Systematic compliance check against ALL BAT conclusions for a BREF"""
        print(f"\n=== COMPREHENSIVE BAT COMPLIANCE CHECK FOR {bref_id} ===")
        
        # Get all BAT conclusions for this BREF
        bat_conclusions = self.get_all_bat_conclusions_for_bref(bref_id)
        
        if not bat_conclusions:
            print(f"No BAT conclusions found for {bref_id} - downloading and extracting...")
            # Download and extract if not available
            if self.download_bat_conclusions_document(bref_id):
                bat_conclusions = self.extract_bat_conclusions_from_document(bref_id)
        
        compliance_results = []
        
        print(f"Checking compliance against {len(bat_conclusions)} BAT conclusions...")
        
        for i, bat in enumerate(bat_conclusions, 1):
            print(f"\nChecking BAT {bat.bat_number}: {bat.title[:50]}...")
            
            # Prepare BAT conclusion for LLM analysis
            bat_for_llm = {
                "bat_id": bat.bat_id,
                "bat_text_description": f"{bat.title}. {bat.description}",
                "source_metadata": {
                    "page_number": bat.source_section or "Unknown",
                    "paragraph_id": bat.bat_number
                }
            }
            
            try:
                # Use LLM to verify compliance
                compliance_result = verify_permit_compliance_with_bat(permit_content, bat_for_llm)
                
                # Enhance with additional details
                compliance_result.update({
                    "bat_number": bat.bat_number,
                    "bat_title": bat.title,
                    "applicability": bat.applicability,
                    "emission_levels": bat.emission_levels,
                    "monitoring_requirements": bat.monitoring_requirements,
                    "techniques": bat.techniques,
                    "bref_source": bref_id
                })
                
                compliance_results.append(compliance_result)
                
                # Print summary
                status = compliance_result.get('compliance_status', 'Unknown')
                print(f"  → {status}")
                
            except Exception as e:
                print(f"  → Error: {e}")
                compliance_results.append({
                    "bat_id": bat.bat_id,
                    "bat_number": bat.bat_number,
                    "bat_title": bat.title,
                    "compliance_status": "Error",
                    "detailed_findings": f"Analysis failed: {e}",
                    "bref_source": bref_id
                })
        
        return compliance_results
    
    def process_bref_comprehensive(self, bref_id: str):
        """Process a BREF comprehensively - download, extract, store all BAT conclusions"""
        print(f"\n=== COMPREHENSIVE PROCESSING OF {bref_id} BREF ===")
        
        # Download BAT conclusions document
        if self.download_bat_conclusions_document(bref_id):
            # Extract all BAT conclusions
            bat_conclusions = self.extract_bat_conclusions_from_document(bref_id)
            
            if bat_conclusions:
                print(f"\n{bref_id} BAT CONCLUSIONS SUMMARY:")
                print(f"Total BAT conclusions extracted: {len(bat_conclusions)}")
                
                for bat in bat_conclusions[:5]:  # Show first 5
                    print(f"  - BAT {bat.bat_number}: {bat.title}")
                    if bat.emission_levels:
                        print(f"    Emission levels: {bat.emission_levels[:100]}...")
                    if bat.monitoring_requirements:
                        print(f"    Monitoring: {bat.monitoring_requirements[:100]}...")
                
                if len(bat_conclusions) > 5:
                    print(f"  ... and {len(bat_conclusions) - 5} more BAT conclusions")
                
                return True
            else:
                print(f"No BAT conclusions extracted for {bref_id}")
                return False
        else:
            print(f"Failed to download BAT conclusions for {bref_id}")
            return False

# Test function
def test_comprehensive_system():
    """Test the comprehensive BREF processing system"""
    print("=== TESTING COMPREHENSIVE BREF PROCESSING ===")
    
    reg_manager = RegulatoryDataManager()
    processor = ComprehensiveBREFProcessor(reg_manager)
    
    # Test with FDM (Food, Drink and Milk Industries)
    bref_id = "FDM"
    
    # Process FDM comprehensively
    success = processor.process_bref_comprehensive(bref_id)
    
    if success:
        # Test comprehensive compliance check
        sample_permit = """
        The dairy farm processes 1000 tons of milk per year. The facility includes:
        - Milk reception and storage tanks with refrigeration
        - Pasteurization equipment with heat recovery system  
        - Cleaning-in-place (CIP) systems for equipment cleaning
        - Wastewater treatment plant treating dairy processing wastewater
        - Energy management system monitoring electricity and steam consumption
        - Waste heat recovery from pasteurization for preheating
        - Automated control systems for temperature and pH monitoring
        """
        
        print(f"\n=== TESTING COMPREHENSIVE COMPLIANCE CHECK ===")
        compliance_results = processor.comprehensive_bat_compliance_check(sample_permit, bref_id)
        
        # Generate summary report
        compliant = len([r for r in compliance_results if r.get('compliance_status') == 'Compliant'])
        partial = len([r for r in compliance_results if r.get('compliance_status') == 'Partially Compliant'])
        non_compliant = len([r for r in compliance_results if r.get('compliance_status') == 'Non-Compliant'])
        review_needed = len([r for r in compliance_results if r.get('compliance_status') == 'Requires Review'])
        
        print(f"\n=== COMPREHENSIVE COMPLIANCE SUMMARY ===")
        print(f"Total BAT conclusions checked: {len(compliance_results)}")
        print(f"Compliant: {compliant}")
        print(f"Partially Compliant: {partial}")
        print(f"Non-Compliant: {non_compliant}")
        print(f"Requires Review: {review_needed}")
        
        # Save detailed results
        report_path = f"/Users/han/Code/MOB-BREF/reports/comprehensive_bat_compliance_{bref_id}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(compliance_results, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed compliance report saved to: {report_path}")

if __name__ == "__main__":
    test_comprehensive_system()