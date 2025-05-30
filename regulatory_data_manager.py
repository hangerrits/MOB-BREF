# /Users/han/Code/MOB-BREF/regulatory_data_manager.py

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
from urllib.parse import urljoin, urlparse
import time

from pdf_processor import extract_text_and_metadata

@dataclass
class RIEActivity:
    """Represents an activity from RIE Annex I"""
    category: str
    activity_description: str
    threshold_values: str
    notes: Optional[str] = None

@dataclass
class BATConclusion:
    """Represents a BAT conclusion from a BREF document"""
    bat_id: str
    bref_source: str
    title: str
    description: str
    applicability: str
    emission_levels: Optional[str] = None
    monitoring_requirements: Optional[str] = None
    implementation_deadline: Optional[str] = None

@dataclass
class BREFDocument:
    """Represents a BREF document with metadata"""
    bref_id: str
    title: str
    sector: str
    adoption_date: Optional[str] = None
    document_url: Optional[str] = None
    bat_conclusions_url: Optional[str] = None
    local_path: Optional[str] = None
    last_updated: Optional[str] = None

class RegulatoryDataManager:
    """Manages RIE and BREF regulatory data for permit compliance checking"""
    
    def __init__(self, data_dir: str = "regulatory_data"):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "regulatory.db")
        self.ensure_directories()
        self.init_database()
        
        # BREF sectors mapping
        self.bref_sectors = {
            "CAM": "Ceramic Manufacturing",
            "CWW": "Chemical Sector (Waste Water/Gas Treatment)",
            "CAK": "Chlor-alkali Production", 
            "CLM": "Cement, Lime, Magnesium Oxide Production",
            "FDM": "Food, Drink and Milk Industries",
            "FMP": "Ferrous Metals Processing",
            "GLS": "Glass Manufacturing",
            "ICS": "Industrial Cooling Systems",
            "ISP": "Iron and Steel Production",
            "LCP": "Large Combustion Plants",
            "LVIC": "Large Volume Inorganic Chemicals",
            "LVOC": "Large Volume Organic Chemicals",
            "MIN": "Mining",
            "NFM": "Non-ferrous Metals",
            "OFC": "Organic Fine Chemicals",
            "POL": "Polymers Production",
            "PPB": "Pulp, Paper and Board",
            "REF": "Refining of Mineral Oil and Gas",
            "SA": "Slaughterhouses and Animal Products",
            "STM": "Surface Treatment of Metals",
            "STP": "Surface Treatment using Plastics",
            "STS": "Surface Treatment using Solvents",
            "TXT": "Textiles Industry",
            "WI": "Waste Incineration",
            "WT": "Waste Treatment",
            "WBP": "Wood-based Panels Production",
            "IRPP": "Intensive Rearing of Poultry or Pigs"
        }
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "rie"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "brefs"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "bat_conclusions"), exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database for regulatory data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # RIE Activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rie_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                activity_description TEXT NOT NULL,
                threshold_values TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # BREF Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bref_documents (
                bref_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                sector TEXT NOT NULL,
                adoption_date TEXT,
                document_url TEXT,
                bat_conclusions_url TEXT,
                local_path TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # BAT Conclusions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bat_conclusions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bat_id TEXT NOT NULL,
                bref_source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                applicability TEXT,
                emission_levels TEXT,
                monitoring_requirements TEXT,
                implementation_deadline TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bref_source) REFERENCES bref_documents (bref_id)
            )
        ''')
        
        # Create indexes for faster searches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rie_category ON rie_activities(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bref_sector ON bref_documents(sector)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bat_bref ON bat_conclusions(bref_source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bat_id ON bat_conclusions(bat_id)')
        
        conn.commit()
        conn.close()
    
    def download_rie_regulation(self) -> bool:
        """Download and parse RIE regulation"""
        try:
            # Download RIE HTML version (easier to parse than PDF)
            rie_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02010L0075-20240804"
            
            print("Downloading RIE regulation...")
            response = requests.get(rie_url, timeout=30)
            response.raise_for_status()
            
            # Save raw HTML
            rie_path = os.path.join(self.data_dir, "rie", "rie_regulation.html")
            with open(rie_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"RIE regulation saved to: {rie_path}")
            
            # Parse Annex I activities (this would need more sophisticated parsing)
            self._parse_rie_activities(response.text)
            
            return True
            
        except Exception as e:
            print(f"Error downloading RIE regulation: {e}")
            return False
    
    def _parse_rie_activities(self, html_content: str):
        """Parse RIE Annex I activities from HTML content"""
        # This is a simplified parser - in practice, you'd use BeautifulSoup or similar
        # For now, we'll add some common activities manually as examples
        
        sample_activities = [
            RIEActivity(
                category="1. Energy industries",
                activity_description="Combustion installations with a rated thermal input exceeding 50 MW",
                threshold_values="> 50 MW thermal input"
            ),
            RIEActivity(
                category="6. Other activities", 
                activity_description="Installations for the intensive rearing of poultry or pigs",
                threshold_values="(a) with more than 40 000 places for poultry, (b) with more than 2 000 places for production pigs (over 30 kg), or (c) with more than 750 places for sows"
            ),
            RIEActivity(
                category="5. Waste management",
                activity_description="Installations for the disposal or recovery of hazardous waste",
                threshold_values="with a capacity exceeding 10 tonnes per day"
            ),
            RIEActivity(
                category="2. Production and processing of metals",
                activity_description="Metal ore (including sulphide ore) roasting or sintering installations",
                threshold_values="Any capacity"
            ),
            RIEActivity(
                category="4. Chemical industry",
                activity_description="Chemical installations for the production on an industrial scale of basic organic chemicals",
                threshold_values="Industrial scale production"
            )
        ]
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for activity in sample_activities:
            cursor.execute('''
                INSERT OR REPLACE INTO rie_activities 
                (category, activity_description, threshold_values, notes)
                VALUES (?, ?, ?, ?)
            ''', (activity.category, activity.activity_description, 
                  activity.threshold_values, activity.notes))
        
        conn.commit()
        conn.close()
        print(f"Stored {len(sample_activities)} RIE activities in database")
    
    def download_bref_document(self, bref_id: str, document_url: str) -> bool:
        """Download a specific BREF document"""
        try:
            print(f"Downloading BREF {bref_id}...")
            response = requests.get(document_url, timeout=60)
            response.raise_for_status()
            
            # Save PDF
            filename = f"{bref_id}_bref.pdf"
            local_path = os.path.join(self.data_dir, "brefs", filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"BREF {bref_id} saved to: {local_path}")
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bref_documents 
                SET local_path = ?, last_updated = CURRENT_TIMESTAMP
                WHERE bref_id = ?
            ''', (local_path, bref_id))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error downloading BREF {bref_id}: {e}")
            return False
    
    def extract_bat_conclusions_from_bref(self, bref_id: str) -> List[BATConclusion]:
        """Extract BAT conclusions from a downloaded BREF document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get BREF local path
        cursor.execute('SELECT local_path FROM bref_documents WHERE bref_id = ?', (bref_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            print(f"BREF {bref_id} not found locally")
            return []
        
        local_path = result[0]
        
        try:
            # Extract text using existing PDF processor
            extracted_data = extract_text_and_metadata(local_path)
            
            if not extracted_data or 'full_text' in extracted_data:
                print(f"Failed to extract text from BREF {bref_id}")
                return []
            
            full_text = extracted_data['full_text']
            
            # Parse BAT conclusions from text
            bat_conclusions = self._parse_bat_conclusions(full_text, bref_id)
            
            # Store in database
            for bat in bat_conclusions:
                cursor.execute('''
                    INSERT OR REPLACE INTO bat_conclusions 
                    (bat_id, bref_source, title, description, applicability, 
                     emission_levels, monitoring_requirements, implementation_deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (bat.bat_id, bat.bref_source, bat.title, bat.description,
                      bat.applicability, bat.emission_levels, 
                      bat.monitoring_requirements, bat.implementation_deadline))
            
            conn.commit()
            print(f"Extracted {len(bat_conclusions)} BAT conclusions from BREF {bref_id}")
            return bat_conclusions
            
        except Exception as e:
            print(f"Error extracting BAT conclusions from BREF {bref_id}: {e}")
            return []
        finally:
            conn.close()
    
    def _parse_bat_conclusions(self, text: str, bref_id: str) -> List[BATConclusion]:
        """Parse BAT conclusions from BREF text"""
        # This is a simplified parser - would need more sophisticated NLP in practice
        bat_conclusions = []
        
        # Look for BAT conclusion patterns
        lines = text.split('\n')
        current_bat = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for BAT conclusion headers (e.g., "BAT 1", "BAT 2.1", etc.)
            if line.startswith('BAT ') and (line.endswith('.') or line.endswith(':')):
                if current_bat:
                    bat_conclusions.append(current_bat)
                
                bat_id = line.split()[1].rstrip('.').rstrip(':')
                current_bat = BATConclusion(
                    bat_id=f"{bref_id}_BAT_{bat_id}",
                    bref_source=bref_id,
                    title=line,
                    description="",
                    applicability=""
                )
            
            elif current_bat and line:
                # Accumulate description
                current_bat.description += line + " "
        
        if current_bat:
            bat_conclusions.append(current_bat)
        
        return bat_conclusions
    
    def initialize_bref_catalog(self):
        """Initialize BREF catalog with ALL official EU documents"""
        brefs = [
            # SECTOR-SPECIFIC BREFs
            BREFDocument("FDM", "Food, Drink and Milk Industries", "Food Processing", "2019-12-12"),
            BREFDocument("IRPP", "Intensive Rearing of Poultry or Pigs", "Livestock", "2017-02-15"), 
            BREFDocument("LCP", "Large Combustion Plants", "Energy", "2017-07-31"),
            BREFDocument("REF", "Refining of Mineral Oil and Gas", "Energy", "2014-10-09"),
            BREFDocument("ISP", "Iron and Steel Production", "Metals", "2012-02-28"),
            BREFDocument("NFM", "Non-ferrous Metals", "Metals", "2016-06-13"),
            BREFDocument("CLM", "Cement, Lime and Magnesium Oxide Production", "Building Materials", "2013-02-26"),
            BREFDocument("GLS", "Glass Manufacturing", "Building Materials", "2012-02-28"),
            BREFDocument("CAM", "Ceramic Manufacturing", "Building Materials", "2007-08-24"),
            BREFDocument("LVIC", "Large Volume Inorganic Chemicals", "Chemical", "2013-12-09"),
            BREFDocument("LVOC", "Large Volume Organic Chemicals", "Chemical", "2017-12-13"),
            BREFDocument("OFC", "Organic Fine Chemicals", "Chemical", "2006-11-09"),
            BREFDocument("POL", "Polymers Production", "Chemical", "2007-02-02"),
            BREFDocument("CAK", "Chlor-alkali Production", "Chemical", "2013-12-09"),
            BREFDocument("PPB", "Pulp, Paper and Board Production", "Paper", "2014-09-26"),
            BREFDocument("TXT", "Textiles Industry", "Textiles", "2003-10-14"),
            BREFDocument("SA", "Slaughterhouses and Animal By-products", "Food Processing", "2005-02-08"),
            BREFDocument("WBP", "Wood-based Panels Production", "Wood", "2007-01-25"),
            BREFDocument("MIN", "Mining", "Mining", "2009-05-13"),
            
            # WASTE BREFs
            BREFDocument("WT", "Waste Treatment", "Waste Management", "2018-08-10"),
            BREFDocument("WI", "Waste Incineration", "Waste Management", "2019-11-12"),
            
            # HORIZONTAL BREFs - CRITICAL FOR ALL SECTORS
            BREFDocument("ICS", "Industrial Cooling Systems", "HORIZONTAL", "2021-12-16"),
            BREFDocument("ENE", "Energy Efficiency", "HORIZONTAL", "2009-02-24"),
            BREFDocument("EMS", "Emissions Monitoring and Reporting", "HORIZONTAL", "2007-08-24"),
            BREFDocument("STM", "Surface Treatment of Metals", "HORIZONTAL", "2006-08-24"),
            BREFDocument("STP", "Surface Treatment using Plastics", "HORIZONTAL", "2007-02-09"),
            BREFDocument("STS", "Surface Treatment using Solvents", "HORIZONTAL", "2007-02-09"),
            BREFDocument("CWW", "Chemical Sector Waste Water and Gas Treatment", "HORIZONTAL", "2016-05-30"),
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for bref in brefs:
            cursor.execute('''
                INSERT OR REPLACE INTO bref_documents 
                (bref_id, title, sector, adoption_date, document_url, bat_conclusions_url, local_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bref.bref_id, bref.title, bref.sector, bref.adoption_date,
                  bref.document_url, bref.bat_conclusions_url, bref.local_path))
        
        conn.commit()
        conn.close()
        print(f"Initialized catalog with {len(brefs)} BREF documents")
    
    def get_dutch_bref_urls(self):
        """Complete Nederlandse BREF URLs voor download"""
        return {
            # SECTOR-SPECIFIC BREFs
            "FDM": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32019D2031",
            "IRPP": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D0302", 
            "LCP": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D1442",
            "REF": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32014D0738",
            "ISP": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32012D0135",
            "NFM": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32016D1032",
            "CLM": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32013D0163",
            "GLS": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32012D0134",
            "CAM": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0506",
            "LVIC": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32013D0732",
            "LVOC": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D2117",
            "OFC": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32006D0738",
            "POL": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0064",
            "CAK": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32013D0732",
            "PPB": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32014D0687",
            "TXT": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32003D0720",
            "SA": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32005D0079",
            "WBP": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0053",
            "MIN": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32009D0416",
            
            # WASTE BREFs
            "WT": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32018D1147",
            "WI": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32019D2010",
            
            # HORIZONTAL BREFs - KRITIEK VOOR ALLE SECTOREN
            "ICS": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32021D2285",
            "ENE": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32009D1357",
            "EMS": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0589",
            "STM": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32006D0061",
            "STP": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0084",
            "STS": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32007D0084",
            "CWW": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32016D0902",
        }
    
    def download_all_brefs(self):
        """Download alle BREFs in Nederlandse versie"""
        bref_urls = self.get_dutch_bref_urls()
        
        print(f"🚀 Downloading {len(bref_urls)} BREFs...")
        
        success_count = 0
        failed_brefs = []
        
        for bref_id, url in bref_urls.items():
            print(f"\n📥 Downloading {bref_id}...")
            try:
                if self.download_bref_document(bref_id, url):
                    success_count += 1
                    print(f"✅ {bref_id} downloaded successfully")
                    time.sleep(2)  # Respectful delay between downloads
                else:
                    failed_brefs.append(bref_id)
                    print(f"❌ {bref_id} download failed")
            except Exception as e:
                failed_brefs.append(bref_id)
                print(f"❌ {bref_id} failed with error: {e}")
        
        print(f"\n📊 === DOWNLOAD SAMENVATTING ===")
        print(f"✅ Successful: {success_count}/{len(bref_urls)}")
        print(f"❌ Failed: {len(failed_brefs)}")
        
        if failed_brefs:
            print(f"Failed BREFs: {', '.join(failed_brefs)}")
        
        return success_count, failed_brefs
    
    def is_horizontal_bref(self, bref_id: str) -> bool:
        """Check if BREF is horizontal (applicable to all sectors)"""
        horizontal_brefs = {"ICS", "ENE", "EMS", "STM", "STP", "STS", "CWW"}
        return bref_id in horizontal_brefs
    
    def get_horizontal_brefs(self) -> List[str]:
        """Get list of all horizontal BREFs"""
        return ["ICS", "ENE", "EMS", "STM", "STP", "STS", "CWW"]
    
    def get_applicable_rie_activities(self, permit_description: str) -> List[RIEActivity]:
        """Find RIE activities applicable to a permit description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword matching - could be enhanced with ML/NLP
        keywords = permit_description.lower().split()
        
        applicable = []
        cursor.execute('SELECT * FROM rie_activities')
        activities = cursor.fetchall()
        
        for activity in activities:
            activity_text = (activity[1] + " " + activity[2]).lower()
            if any(keyword in activity_text for keyword in keywords if len(keyword) > 3):
                applicable.append(RIEActivity(
                    category=activity[1],
                    activity_description=activity[2], 
                    threshold_values=activity[3],
                    notes=activity[4]
                ))
        
        conn.close()
        return applicable
    
    def get_applicable_brefs(self, sector: str = None, activity: str = None) -> List[BREFDocument]:
        """Get applicable BREF documents based on sector or activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if sector:
            cursor.execute('SELECT * FROM bref_documents WHERE sector LIKE ?', (f'%{sector}%',))
        elif activity:
            # Could enhance with better matching logic
            cursor.execute('SELECT * FROM bref_documents WHERE title LIKE ?', (f'%{activity}%',))
        else:
            cursor.execute('SELECT * FROM bref_documents')
        
        results = cursor.fetchall()
        brefs = []
        
        for result in results:
            brefs.append(BREFDocument(
                bref_id=result[0],
                title=result[1],
                sector=result[2],
                adoption_date=result[3],
                document_url=result[4],
                bat_conclusions_url=result[5],
                local_path=result[6],
                last_updated=result[7]
            ))
        
        conn.close()
        return brefs
    
    def get_bat_conclusions_for_bref(self, bref_id: str) -> List[BATConclusion]:
        """Get all BAT conclusions for a specific BREF"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bat_conclusions WHERE bref_source = ?', (bref_id,))
        results = cursor.fetchall()
        
        conclusions = []
        for result in results:
            conclusions.append(BATConclusion(
                bat_id=result[1],
                bref_source=result[2],
                title=result[3],
                description=result[4],
                applicability=result[5],
                emission_levels=result[6],
                monitoring_requirements=result[7],
                implementation_deadline=result[8]
            ))
        
        conn.close()
        return conclusions
    
    def setup_system(self):
        """Initialize the complete regulatory system"""
        print("Setting up regulatory data management system...")
        
        # Initialize BREF catalog
        self.initialize_bref_catalog()
        
        # Download RIE regulation
        self.download_rie_regulation()
        
        print("Regulatory system setup complete!")
        print(f"Database: {self.db_path}")
        print(f"Data directory: {self.data_dir}")

if __name__ == "__main__":
    manager = RegulatoryDataManager()
    manager.setup_system()