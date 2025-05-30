# /Users/han/Code/MOB-BREF/comprehensive_all_bref_system.py

import os
import json
import requests
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from regulatory_data_manager import RegulatoryDataManager
from pdf_processor import extract_text_and_metadata
from llm_handler import llm_call

@dataclass
class Nederlandse_BBT_Conclusie:
    """Nederlandse BBT conclusie met alle details"""
    bbt_id: str
    bref_bron: str
    bbt_nummer: str
    titel: str
    beschrijving: str
    toepasselijkheid: str
    emissieniveaus: Optional[str] = None
    monitoringvereisten: Optional[str] = None
    technieken: Optional[str] = None
    prestatieniveaus: Optional[str] = None
    implementatienotities: Optional[str] = None
    bron_sectie: Optional[str] = None

@dataclass
class BREF_Overzicht:
    """Overzicht van een complete BREF met alle informatie"""
    bref_id: str
    nederlandse_titel: str
    engelse_titel: str
    sector: str
    toepassingsgebied: str
    totaal_bbt_conclusies: int
    compliance_samenvatting: Dict[str, int]
    belangrijkste_bevindingen: List[str]

class Uitgebreide_BREF_Processor:
    """Uitgebreide processor voor alle Nederlandse BREF documenten"""
    
    def __init__(self, reg_manager: RegulatoryDataManager):
        self.reg_manager = reg_manager
        
        # Uitgebreide lijst van alle Nederlandse BREF URLs
        self.alle_nederlandse_brefs = {
            "FDM": {
                "nederlandse_titel": "Voedings-, dranken- en zuivelindustrie",
                "engelse_titel": "Food, Drink and Milk Industries",
                "sector": "Voedingsmiddelenindustrie",
                "toepassingsgebied": "Verwerking van dierlijke en plantaardige producten tot voedsel, dranken en melkproducten",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32019D2031",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/FDM_bref_2019.pdf"
            },
            "IRPP": {
                "nederlandse_titel": "Intensieve pluimvee- en varkenshouderij", 
                "engelse_titel": "Intensive Rearing of Poultry or Pigs",
                "sector": "Veehouderij",
                "toepassingsgebied": "Intensieve houderij van pluimvee of varkens boven bepaalde drempelwaarden",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D0302",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC107189_IRPP_bref_2017.pdf"
            },
            "LCP": {
                "nederlandse_titel": "Grote stookinstallaties",
                "engelse_titel": "Large Combustion Plants", 
                "sector": "Energie",
                "toepassingsgebied": "Verbrandingsinstallaties met thermisch vermogen > 50 MW",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D1442",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107769_LCPBref_2017.pdf"
            },
            "WT": {
                "nederlandse_titel": "Afvalbehandeling",
                "engelse_titel": "Waste Treatment",
                "sector": "Afvalbeheer", 
                "toepassingsgebied": "Behandeling van gevaarlijk en niet-gevaarlijk afval",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32018D1147",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC113018_WTBref_2018.pdf"
            },
            "WI": {
                "nederlandse_titel": "Afvalverbranding",
                "engelse_titel": "Waste Incineration",
                "sector": "Afvalbeheer",
                "toepassingsgebied": "Verbranding of meeverbanding van afval",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32019D2010",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_113018_WI_Bref_2019.pdf"
            },
            "REF": {
                "nederlandse_titel": "Raffinage van minerale olie en gas",
                "engelse_titel": "Refining of Mineral Oil and Gas",
                "sector": "Energie en petrochemie",
                "toepassingsgebied": "Raffinage van ruwe olie, natuurlijke gascondensaten en feedstocks",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32014D0738",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107705_REFBref_2015.pdf"
            },
            "ISP": {
                "nederlandse_titel": "IJzer- en staalproductie",
                "engelse_titel": "Iron and Steel Production",
                "sector": "Metaalindustrie",
                "toepassingsgebied": "Productie van ruwijzer, staal en ferrolegeringen",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32012D0135",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_69967_IS_Bref_2012.pdf"
            },
            "NFM": {
                "nederlandse_titel": "Non-ferro metalen",
                "engelse_titel": "Non-ferrous Metals",
                "sector": "Metaalindustrie", 
                "toepassingsgebied": "Productie van non-ferro metalen uit ertsen, concentraten en secundaire materialen",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32016D1032",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107041_NFM_bref_2017.pdf"
            },
            "CLM": {
                "nederlandse_titel": "Cement-, kalk- en magnesiumoxideproductie",
                "engelse_titel": "Cement, Lime and Magnesium Oxide Production",
                "sector": "Bouwmaterialen",
                "toepassingsgebied": "Productie van cement, kalk, magnesiumoxide en daaraan gerelateerde producten",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32013D0163",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107018_CLM_bref_2013.pdf"
            },
            "GLS": {
                "nederlandse_titel": "Glasindustrie",
                "engelse_titel": "Glass Manufacturing",
                "sector": "Bouwmaterialen",
                "toepassingsgebied": "Vervaardiging van glas en glasproducten",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32012D0134",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_68698_GLS_bref_2012.pdf"
            },
            "LVIC": {
                "nederlandse_titel": "Anorganische chemicaliën in grote hoeveelheden",
                "engelse_titel": "Large Volume Inorganic Chemicals",
                "sector": "Chemische industrie",
                "toepassingsgebied": "Productie van anorganische chemicaliën op industriële schaal",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32013D0732",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_87923_LVIC_bref_2017.pdf"
            },
            "LVOC": {
                "nederlandse_titel": "Organische chemicaliën in grote hoeveelheden",
                "engelse_titel": "Large Volume Organic Chemicals", 
                "sector": "Chemische industrie",
                "toepassingsgebied": "Productie van organische chemicaliën op industriële schaal",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D2117",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_109279_LVOC_bref_2017.pdf"
            }
        }
    
    def download_alle_nederlandse_brefs(self, bref_ids: List[str] = None) -> Dict[str, bool]:
        """Download alle Nederlandse BREF documenten parallel"""
        if bref_ids is None:
            bref_ids = list(self.alle_nederlandse_brefs.keys())
        
        resultaten = {}
        
        print(f"=== DOWNLOADEN VAN {len(bref_ids)} NEDERLANDSE BREF DOCUMENTEN ===")
        
        # Parallel downloaden voor snelheid
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for bref_id in bref_ids:
                if bref_id in self.alle_nederlandse_brefs:
                    future = executor.submit(self._download_enkele_bref, bref_id)
                    futures[future] = bref_id
            
            for future in as_completed(futures):
                bref_id = futures[future]
                try:
                    resultaat = future.result()
                    resultaten[bref_id] = resultaat
                    status = "✅ Succesvol" if resultaat else "❌ Mislukt"
                    print(f"{bref_id}: {status}")
                except Exception as e:
                    print(f"{bref_id}: ❌ Fout - {e}")
                    resultaten[bref_id] = False
        
        return resultaten
    
    def _download_enkele_bref(self, bref_id: str) -> bool:
        """Download een enkel BREF document"""
        if bref_id not in self.alle_nederlandse_brefs:
            return False
        
        bref_info = self.alle_nederlandse_brefs[bref_id]
        url = bref_info["bbt_conclusies_url"]
        
        try:
            response = requests.get(url, timeout=60, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            filename = f"{bref_id}_BBT_conclusies_NL.pdf"
            local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"Fout bij downloaden {bref_id}: {e}")
            return False
    
    def extraheer_alle_bbt_conclusies(self, bref_ids: List[str] = None) -> Dict[str, List[Nederlandse_BBT_Conclusie]]:
        """Extraheer BBT conclusies uit alle BREF documenten"""
        if bref_ids is None:
            bref_ids = list(self.alle_nederlandse_brefs.keys())
        
        alle_bbt_conclusies = {}
        
        print(f"=== EXTRAHEREN BBT CONCLUSIES UIT {len(bref_ids)} BREF DOCUMENTEN ===")
        
        for bref_id in bref_ids:
            print(f"\nVerwerken {bref_id}...")
            
            filename = f"{bref_id}_BBT_conclusies_NL.pdf"
            local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
            
            if not os.path.exists(local_path):
                print(f"⚠️ Document niet gevonden: {local_path}")
                continue
            
            try:
                # Tekst extraheren
                extracted_data = extract_text_and_metadata(local_path)
                
                if not extracted_data or 'full_text' not in extracted_data:
                    print(f"❌ Kon geen tekst extraheren uit {bref_id}")
                    continue
                
                full_text = extracted_data['full_text']
                
                # BBT conclusies parsen
                bbt_conclusies = self._parseer_nederlandse_bbt_conclusies(full_text, bref_id)
                
                if bbt_conclusies:
                    # Opslaan in database
                    self._bewaar_nederlandse_bbt_conclusies(bbt_conclusies)
                    alle_bbt_conclusies[bref_id] = bbt_conclusies
                    print(f"✅ {len(bbt_conclusies)} BBT conclusies geëxtraheerd uit {bref_id}")
                else:
                    print(f"⚠️ Geen BBT conclusies gevonden in {bref_id}")
                
            except Exception as e:
                print(f"❌ Fout bij verwerken {bref_id}: {e}")
                continue
        
        return alle_bbt_conclusies
    
    def _parseer_nederlandse_bbt_conclusies(self, text: str, bref_id: str) -> List[Nederlandse_BBT_Conclusie]:
        """Geavanceerde parsing van Nederlandse BBT conclusies"""
        bbt_conclusies = []
        
        # Verschillende patronen voor verschillende BREF structuren
        bbt_patronen = [
            r'^BBT\s+(\d+(?:\.\d+)?)\s*[\.:]?\s*(.*?)$',  # BBT 1. Titel
            r'^(\d+(?:\.\d+)?)\.\s*BBT\s+(.*?)$',  # 1. BBT Titel  
            r'^\*\*BBT\s+(\d+(?:\.\d+)?)\*\*\s*(.*?)$',  # **BBT 1** Titel
            r'^Om\s+.*?,\s*is\s+de\s+BBT\s*(.*?)$',  # Om ..., is de BBT ...
            r'^Teneinde\s+.*?,\s*is\s+de\s+BBT\s*(.*?)$',  # Teneinde ..., is de BBT ...
            r'Voor\s+.*?,\s*is\s+de\s+BBT\s*(.*?)$',  # Voor ..., is de BBT ...
        ]
        
        lines = text.split('\n')
        current_bbt = None
        current_section = ""
        bbt_counter = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Controleer BBT patronen
            bbt_match = None
            for pattern in bbt_patronen:
                bbt_match = re.match(pattern, line, re.IGNORECASE)
                if bbt_match:
                    break
            
            if bbt_match:
                # Vorige BBT opslaan
                if current_bbt:
                    bbt_conclusies.append(current_bbt)
                
                # Nieuwe BBT starten
                bbt_counter += 1
                if bbt_match.groups():
                    bbt_nummer = bbt_match.group(1) if len(bbt_match.groups()) >= 1 else str(bbt_counter)
                    titel = bbt_match.group(2) if len(bbt_match.groups()) >= 2 else line
                else:
                    bbt_nummer = str(bbt_counter)
                    titel = line
                
                current_bbt = Nederlandse_BBT_Conclusie(
                    bbt_id=f"{bref_id}_BBT_{bbt_nummer}",
                    bref_bron=bref_id,
                    bbt_nummer=str(bbt_nummer),
                    titel=titel.strip(),
                    beschrijving="",
                    toepasselijkheid="",
                    bron_sectie=current_section
                )
                continue
            
            # Sectie headers bijhouden
            if any(keyword in line.upper() for keyword in ['HOOFDSTUK', 'SECTIE', 'PARAGRAAF', 'BIJLAGE']):
                current_section = line
                continue
            
            # BBT inhoud verzamelen
            if current_bbt and line:
                # Specifieke subsecties identificeren
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['toepasselijkheid', 'van toepassing', 'geldt voor']):
                    current_bbt.toepasselijkheid += line + " "
                elif any(keyword in line_lower for keyword in ['emissie', 'grenswaarde', 'niveau', 'mg/m³', 'μg/m³']):
                    current_bbt.emissieniveaus = (current_bbt.emissieniveaus or "") + line + " "
                elif any(keyword in line_lower for keyword in ['monitor', 'meting', 'controle', 'frequentie']):
                    current_bbt.monitoringvereisten = (current_bbt.monitoringvereisten or "") + line + " "
                elif any(keyword in line_lower for keyword in ['techniek', 'methode', 'procedure', 'apparatuur']):
                    current_bbt.technieken = (current_bbt.technieken or "") + line + " "
                else:
                    current_bbt.beschrijving += line + " "
        
        # Laatste BBT niet vergeten
        if current_bbt:
            bbt_conclusies.append(current_bbt)
        
        # Alternatieve extractie als weinig conclusies gevonden
        if len(bbt_conclusies) < 5:
            extra_conclusies = self._alternatieve_bbt_extractie(text, bref_id, len(bbt_conclusies))
            bbt_conclusies.extend(extra_conclusies)
        
        return bbt_conclusies
    
    def _alternatieve_bbt_extractie(self, text: str, bref_id: str, start_counter: int) -> List[Nederlandse_BBT_Conclusie]:
        """Alternatieve extractie voor moeilijk parseerbare documenten"""
        alternatieve_conclusies = []
        lines = text.split('\n')
        
        # Zoek naar zinnen die BBT conclusies zouden kunnen zijn
        bbt_zinnen = []
        for line in lines:
            line = line.strip()
            if (len(line) > 50 and 
                any(start in line for start in ['Om ', 'Teneinde ', 'Voor ', 'Met het doel']) and
                any(keyword in line.lower() for keyword in ['emissie', 'energie', 'water', 'afval', 'milieu'])):
                bbt_zinnen.append(line)
        
        # Converteer naar BBT conclusies
        for i, zin in enumerate(bbt_zinnen[:20], start_counter + 1):  # Max 20 extra
            alternatieve_conclusies.append(Nederlandse_BBT_Conclusie(
                bbt_id=f"{bref_id}_BBT_{i}",
                bref_bron=bref_id,
                bbt_nummer=str(i),
                titel=f"BBT {i}",
                beschrijving=zin,
                toepasselijkheid="Algemeen van toepassing"
            ))
        
        return alternatieve_conclusies
    
    def _bewaar_nederlandse_bbt_conclusies(self, bbt_conclusies: List[Nederlandse_BBT_Conclusie]):
        """Bewaar Nederlandse BBT conclusies in database"""
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        # Database tabel aanmaken
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alle_nederlandse_bbt_conclusies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bbt_id TEXT UNIQUE NOT NULL,
                bref_bron TEXT NOT NULL,
                bbt_nummer TEXT NOT NULL,
                titel TEXT NOT NULL,
                beschrijving TEXT,
                toepasselijkheid TEXT,
                emissieniveaus TEXT,
                monitoringvereisten TEXT,
                technieken TEXT,
                prestatieniveaus TEXT,
                implementatienotities TEXT,
                bron_sectie TEXT,
                aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # BBT conclusies opslaan
        for bbt in bbt_conclusies:
            cursor.execute('''
                INSERT OR REPLACE INTO alle_nederlandse_bbt_conclusies 
                (bbt_id, bref_bron, bbt_nummer, titel, beschrijving, toepasselijkheid,
                 emissieniveaus, monitoringvereisten, technieken, prestatieniveaus,
                 implementatienotities, bron_sectie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bbt.bbt_id, bbt.bref_bron, bbt.bbt_nummer, bbt.titel,
                bbt.beschrijving, bbt.toepasselijkheid, bbt.emissieniveaus,
                bbt.monitoringvereisten, bbt.technieken, bbt.prestatieniveaus,
                bbt.implementatienotities, bbt.bron_sectie
            ))
        
        conn.commit()
        conn.close()
    
    def krijg_alle_bbt_conclusies_voor_bref(self, bref_id: str) -> List[Nederlandse_BBT_Conclusie]:
        """Krijg alle BBT conclusies voor een specifieke BREF"""
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bbt_id, bref_bron, bbt_nummer, titel, beschrijving, toepasselijkheid,
                   emissieniveaus, monitoringvereisten, technieken, prestatieniveaus,
                   implementatienotities, bron_sectie
            FROM alle_nederlandse_bbt_conclusies 
            WHERE bref_bron = ?
            ORDER BY CAST(bbt_nummer AS REAL)
        ''', (bref_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Nederlandse_BBT_Conclusie(
            bbt_id=r[0], bref_bron=r[1], bbt_nummer=r[2], titel=r[3],
            beschrijving=r[4], toepasselijkheid=r[5], emissieniveaus=r[6],
            monitoringvereisten=r[7], technieken=r[8], prestatieniveaus=r[9],
            implementatienotities=r[10], bron_sectie=r[11]
        ) for r in results]
    
    def voer_volledige_compliance_controle_uit(self, vergunning_inhoud: str, 
                                              toepasselijke_brefs: List[str],
                                              vergunning_id: str = "Test_Vergunning") -> Dict[str, Any]:
        """Voer volledige compliance controle uit tegen alle toepasselijke BREFs"""
        
        print(f"\n=== VOLLEDIGE COMPLIANCE CONTROLE VOOR {len(toepasselijke_brefs)} BREFs ===")
        
        alle_resultaten = {}
        totaal_statistieken = {
            "totaal_brefs": len(toepasselijke_brefs),
            "totaal_bbt_conclusies": 0,
            "conform": 0,
            "gedeeltelijk_conform": 0,
            "niet_conform": 0,
            "onduidelijk": 0,
            "fouten": 0
        }
        
        for bref_id in toepasselijke_brefs:
            if bref_id not in self.alle_nederlandse_brefs:
                print(f"⚠️ Onbekende BREF: {bref_id}")
                continue
            
            print(f"\n--- Controleren {bref_id}: {self.alle_nederlandse_brefs[bref_id]['nederlandse_titel']} ---")
            
            # Krijg BBT conclusies voor deze BREF
            bbt_conclusies = self.krijg_alle_bbt_conclusies_voor_bref(bref_id)
            
            if not bbt_conclusies:
                print(f"⚠️ Geen BBT conclusies gevonden voor {bref_id}")
                continue
            
            print(f"Controleren van {len(bbt_conclusies)} BBT conclusies...")
            
            # Voer compliance controle uit
            bref_resultaten = self._controleer_bref_compliance(
                vergunning_inhoud, bref_id, bbt_conclusies
            )
            
            # Statistieken bijwerken
            bref_stats = self._bereken_bref_statistieken(bref_resultaten)
            
            alle_resultaten[bref_id] = {
                "bref_info": self.alle_nederlandse_brefs[bref_id],
                "bbt_conclusies": len(bbt_conclusies),
                "compliance_resultaten": bref_resultaten,
                "statistieken": bref_stats
            }
            
            # Totaal statistieken bijwerken
            totaal_statistieken["totaal_bbt_conclusies"] += len(bbt_conclusies)
            totaal_statistieken["conform"] += bref_stats["conform"]
            totaal_statistieken["gedeeltelijk_conform"] += bref_stats["gedeeltelijk_conform"]
            totaal_statistieken["niet_conform"] += bref_stats["niet_conform"]
            totaal_statistieken["onduidelijk"] += bref_stats["onduidelijk"]
            totaal_statistieken["fouten"] += bref_stats["fouten"]
            
            print(f"✅ {bref_id} voltooid: {bref_stats}")
        
        return {
            "vergunning_id": vergunning_id,
            "timestamp": datetime.now().isoformat(),
            "totaal_statistieken": totaal_statistieken,
            "bref_resultaten": alle_resultaten
        }
    
    def _controleer_bref_compliance(self, vergunning_inhoud: str, bref_id: str, 
                                   bbt_conclusies: List[Nederlandse_BBT_Conclusie]) -> List[Dict[str, Any]]:
        """Controleer compliance voor alle BBT conclusies van een BREF"""
        resultaten = []
        
        for i, bbt in enumerate(bbt_conclusies, 1):
            print(f"  {i}/{len(bbt_conclusies)}: BBT {bbt.bbt_nummer}")
            
            try:
                # Nederlandse LLM prompt
                prompt = self._maak_nederlandse_compliance_prompt(vergunning_inhoud, bbt)
                
                # LLM aanroepen
                llm_response = llm_call(prompt)
                
                if llm_response and not llm_response.startswith("Error:"):
                    try:
                        # JSON uit response extraheren
                        json_start = llm_response.find('{')
                        json_end = llm_response.rfind('}') + 1
                        
                        if json_start != -1 and json_end != -1:
                            json_part = llm_response[json_start:json_end]
                            response_json = json.loads(json_part)
                            
                            # Aanvullen met metadata
                            response_json.update({
                                "bbt_nummer": bbt.bbt_nummer,
                                "bbt_titel": bbt.titel,
                                "toepasselijkheid": bbt.toepasselijkheid,
                                "emissieniveaus": bbt.emissieniveaus,
                                "monitoringvereisten": bbt.monitoringvereisten,
                                "technieken": bbt.technieken,
                                "bref_bron": bref_id
                            })
                            
                            resultaten.append(response_json)
                        else:
                            raise json.JSONDecodeError("Geen JSON gevonden", llm_response, 0)
                    
                    except json.JSONDecodeError:
                        resultaten.append(self._maak_fout_resultaat(bbt, "JSON parse fout", llm_response))
                else:
                    resultaten.append(self._maak_fout_resultaat(bbt, "LLM fout", llm_response))
            
            except Exception as e:
                resultaten.append(self._maak_fout_resultaat(bbt, f"Algemene fout: {e}", ""))
        
        return resultaten
    
    def _maak_nederlandse_compliance_prompt(self, vergunning_inhoud: str, 
                                          bbt: Nederlandse_BBT_Conclusie) -> str:
        """Maak Nederlandse compliance prompt voor LLM"""
        return f"""
Je bent een expert in EU milieuregulering en industriële vergunningen. 
Je moet de voorwaarden in een industriële vergunning nauwkeurig vergelijken met een specifieke Beste Beschikbare Techniek (BBT) conclusie.

De BBT Conclusie (ID: {bbt.bbt_id}) is als volgt:
**Titel:** {bbt.titel}
**Beschrijving:** {bbt.beschrijving}
**Toepasselijkheid:** {bbt.toepasselijkheid}
**Emissieniveaus:** {bbt.emissieniveaus or 'Niet gespecificeerd'}
**Monitoringvereisten:** {bbt.monitoringvereisten or 'Niet gespecificeerd'}
**Technieken:** {bbt.technieken or 'Niet gespecificeerd'}

De volledige tekst van de industriële vergunning:
--- VERGUNNING START ---
{vergunning_inhoud}
--- VERGUNNING EINDE ---

Analyseer de vergunning systematisch tegen deze BBT conclusie:

1. **Volledige Compliance:** Voldoet de vergunning volledig aan alle aspecten van deze BBT conclusie? Citeer specifieke delen.

2. **Gedeeltelijke Compliance:** Welke aspecten zijn gedeeltelijk gedekt? Wat ontbreekt er precies?

3. **Non-Compliance:** Welke vereiste BBT elementen ontbreken volledig in de vergunning?

4. **Onduidelijkheden:** Welke BBT aspecten kunnen niet worden geverifieerd door gebrek aan informatie?

5. **Aanbevelingen:** Welke specifieke verbeteringen zijn nodig voor volledige compliance?

Bepaal de overall compliance status: 'Conform', 'Gedeeltelijk Conform', 'Niet-Conform', of 'Onduidelijk/Onvoldoende Informatie'.

Geef je antwoord in JSON formaat:
{{
  "bat_id": "{bbt.bbt_id}",
  "compliance_status": "[status]",
  "detailed_findings": "[gedetailleerde bevindingen in het Nederlands]",
  "specific_gaps": "[specifieke tekortkomingen]",
  "recommendations": "[concrete aanbevelingen]"
}}
"""
    
    def _maak_fout_resultaat(self, bbt: Nederlandse_BBT_Conclusie, fout_type: str, details: str) -> Dict[str, Any]:
        """Maak foutresultaat voor mislukte analyse"""
        return {
            "bat_id": bbt.bbt_id,
            "bbt_nummer": bbt.bbt_nummer,
            "bbt_titel": bbt.titel,
            "compliance_status": "Fout",
            "detailed_findings": f"Analyse mislukt: {fout_type}",
            "specific_gaps": "Kon niet worden bepaald",
            "recommendations": "Handmatige review vereist",
            "error_details": details[:200] if details else "Geen details beschikbaar"
        }
    
    def _bereken_bref_statistieken(self, bref_resultaten: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bereken statistieken voor een BREF"""
        stats = {
            "conform": 0,
            "gedeeltelijk_conform": 0, 
            "niet_conform": 0,
            "onduidelijk": 0,
            "fouten": 0
        }
        
        for resultaat in bref_resultaten:
            status = resultaat.get('compliance_status', 'Fout')
            if status == 'Conform':
                stats["conform"] += 1
            elif status == 'Gedeeltelijk Conform':
                stats["gedeeltelijk_conform"] += 1
            elif status == 'Niet-Conform':
                stats["niet_conform"] += 1
            elif status == 'Onduidelijk/Onvoldoende Informatie':
                stats["onduidelijk"] += 1
            else:
                stats["fouten"] += 1
        
        return stats
    
    def genereer_uitgebreid_nederlands_rapport(self, volledige_resultaten: Dict[str, Any]) -> str:
        """Genereer uitgebreid Nederlands rapport met hoofdstukken per BREF"""
        
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        vergunning_id = volledige_resultaten.get("vergunning_id", "Onbekend")
        totaal_stats = volledige_resultaten.get("totaal_statistieken", {})
        
        # Start markdown rapport
        markdown = f"""# Uitgebreide BBT Compliance Rapport

**Vergunning ID:** {vergunning_id}  
**Gegenereerd op:** {timestamp}  
**Systeem:** Geautomatiseerde BBT Compliance Verificatie  

## Executive Samenvatting

Dit rapport bevat een volledige analyse van de vergunning tegen alle toepasselijke BBT conclusies uit de relevante BREF documenten.

### Totaal Overzicht
- **Aantal onderzochte BREFs:** {totaal_stats.get('totaal_brefs', 0)}
- **Totaal BBT conclusies gecontroleerd:** {totaal_stats.get('totaal_bbt_conclusies', 0)}

### Compliance Resultaten
- ✅ **Conform:** {totaal_stats.get('conform', 0)} ({self._bereken_percentage(totaal_stats.get('conform', 0), totaal_stats.get('totaal_bbt_conclusies', 1))}%)
- ⚠️ **Gedeeltelijk Conform:** {totaal_stats.get('gedeeltelijk_conform', 0)} ({self._bereken_percentage(totaal_stats.get('gedeeltelijk_conform', 0), totaal_stats.get('totaal_bbt_conclusies', 1))}%)
- ❌ **Niet-Conform:** {totaal_stats.get('niet_conform', 0)} ({self._bereken_percentage(totaal_stats.get('niet_conform', 0), totaal_stats.get('totaal_bbt_conclusies', 1))}%)
- ❓ **Onduidelijk:** {totaal_stats.get('onduidelijk', 0)} ({self._bereken_percentage(totaal_stats.get('onduidelijk', 0), totaal_stats.get('totaal_bbt_conclusies', 1))}%)
- ⚡ **Analyse Fouten:** {totaal_stats.get('fouten', 0)}

### Prioriteit Acties
"""
        
        # Prioriteit acties
        niet_conform = totaal_stats.get('niet_conform', 0)
        gedeeltelijk = totaal_stats.get('gedeeltelijk_conform', 0)
        
        if niet_conform > 0:
            markdown += f"1. **HOGE PRIORITEIT:** {niet_conform} niet-conforme BBT conclusies vereisen directe actie\n"
        if gedeeltelijk > 0:
            markdown += f"2. **MEDIUM PRIORITEIT:** {gedeeltelijk} gedeeltelijk conforme BBT conclusies vereisen verbetering\n"
        
        markdown += "\n---\n"
        
        # Hoofdstukken per BREF
        bref_resultaten = volledige_resultaten.get("bref_resultaten", {})
        
        for bref_id, bref_data in bref_resultaten.items():
            bref_info = bref_data.get("bref_info", {})
            bref_stats = bref_data.get("statistieken", {})
            compliance_resultaten = bref_data.get("compliance_resultaten", [])
            
            markdown += f"""
## {bref_id}: {bref_info.get('nederlandse_titel', 'Onbekende BREF')}

**Engelse titel:** {bref_info.get('engelse_titel', 'N/A')}  
**Sector:** {bref_info.get('sector', 'N/A')}  
**Toepassingsgebied:** {bref_info.get('toepassingsgebied', 'N/A')}  

### Samenvatting {bref_id}
- **Totaal BBT conclusies:** {len(compliance_resultaten)}
- **Conform:** {bref_stats.get('conform', 0)}
- **Gedeeltelijk Conform:** {bref_stats.get('gedeeltelijk_conform', 0)}
- **Niet-Conform:** {bref_stats.get('niet_conform', 0)}
- **Onduidelijk:** {bref_stats.get('onduidelijk', 0)}

### Alle BBT Conclusies voor {bref_id}

"""
            
            # Alle BBT conclusies opsommen om er geen te missen
            for i, resultaat in enumerate(compliance_resultaten, 1):
                bbt_nummer = resultaat.get('bbt_nummer', 'N/A')
                titel = resultaat.get('bbt_titel', 'Geen titel')
                status = resultaat.get('compliance_status', 'Onbekend')
                bevindingen = resultaat.get('detailed_findings', 'Geen bevindingen')
                gaps = resultaat.get('specific_gaps', '')
                aanbevelingen = resultaat.get('recommendations', '')
                
                # Status icoon
                status_icoon = {
                    'Conform': '✅',
                    'Gedeeltelijk Conform': '⚠️', 
                    'Niet-Conform': '❌',
                    'Onduidelijk/Onvoldoende Informatie': '❓',
                    'Fout': '⚡'
                }.get(status, '❓')
                
                markdown += f"""#### {status_icoon} BBT {bbt_nummer}: {titel[:100]}{"..." if len(titel) > 100 else ""}

**Status:** {status}

**Bevindingen:**  
{bevindingen}

"""
                
                if gaps and gaps != "Kon niet worden bepaald":
                    markdown += f"**Specifieke Tekortkomingen:**  \n{gaps}\n\n"
                
                if aanbevelingen and aanbevelingen != "Handmatige review vereist":
                    markdown += f"**Aanbevelingen:**  \n{aanbevelingen}\n\n"
                
                markdown += "---\n\n"
        
        # Algemene aanbevelingen
        markdown += f"""
## Algemene Aanbevelingen

### Directe Acties (Hoge Prioriteit)
"""
        
        # Verzamel alle niet-conforme BBTs
        niet_conforme_bbts = []
        for bref_id, bref_data in bref_resultaten.items():
            for resultaat in bref_data.get("compliance_resultaten", []):
                if resultaat.get('compliance_status') == 'Niet-Conform':
                    niet_conforme_bbts.append(f"{bref_id} BBT {resultaat.get('bbt_nummer')}")
        
        if niet_conforme_bbts:
            markdown += f"1. **Niet-conforme BBT conclusies aanpakken:** {', '.join(niet_conforme_bbts[:10])}"
            if len(niet_conforme_bbts) > 10:
                markdown += f" (en {len(niet_conforme_bbts) - 10} andere)"
            markdown += "\n"
        
        markdown += f"""
2. **Verbeter documentatie** voor gedeeltelijk conforme BBT conclusies
3. **Implementeer ontbrekende monitoring** systemen waar vereist
4. **Update vergunningsvoorwaarden** om volledige BBT compliance te waarborgen

### Monitoring en Follow-up
1. **Kwartaal reviews** van BBT compliance status
2. **Jaarlijkse update** van dit compliance rapport  
3. **Training** van operationeel personeel over BBT vereisten
4. **Documentatie verbetering** voor onduidelijke gebieden

### Technische Verbeteringen
1. **Emissie monitoring** systemen waar tekortkomingen geïdentificeerd
2. **Energie efficiency** maatregelen volgens relevante BBT conclusies
3. **Afvalwater behandeling** optimalisatie indien van toepassing
4. **Geluid en geur management** plannen waar vereist

---

## Bijlagen

### A. Methodologie
Dit rapport is gegenereerd door een geautomatiseerd systeem dat:
- Alle relevante Nederlandse BBT conclusies analyseert
- AI-gestuurde compliance beoordeling uitvoert
- Systematische gap analyse voert uit
- Concrete aanbevelingen genereert

### B. BREF Referenties
"""
        
        for bref_id, bref_data in bref_resultaten.items():
            bref_info = bref_data.get("bref_info", {})
            markdown += f"- **{bref_id}:** {bref_info.get('nederlandse_titel', '')} ({bref_info.get('engelse_titel', '')})\n"
        
        markdown += f"""

### C. Contact
Voor vragen over dit rapport of de BBT compliance beoordeling, neem contact op met de milieucoördinator.

---
*Rapport gegenereerd op {timestamp} door het Geautomatiseerde BBT Compliance Verificatie Systeem*
"""
        
        return markdown
    
    def _bereken_percentage(self, aantal: int, totaal: int) -> int:
        """Bereken percentage veilig"""
        if totaal == 0:
            return 0
        return round((aantal / totaal) * 100)
    
    def genereer_pdf_van_markdown(self, markdown_inhoud: str, vergunning_id: str) -> str:
        """Genereer PDF van markdown inhoud"""
        try:
            import markdown2
            from weasyprint import HTML as WeasyHTML
            from weasyprint.text.fonts import FontConfiguration
            
            # Converteer naar HTML
            html_content = markdown2.markdown(
                markdown_inhoud, 
                extras=["tables", "fenced-code-blocks", "break-on-newline", "header-ids"]
            )
            
            # Nederlandse PDF styling
            css_style = """
            @page {
                size: A4;
                margin: 2.5cm 2cm;
                @bottom-center {
                    content: "Pagina " counter(page) " van " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }
            }
            body {
                font-family: "Arial", "Helvetica", "DejaVu Sans", sans-serif;
                line-height: 1.5;
                font-size: 10pt;
                color: #333;
            }
            h1 {
                font-size: 20pt;
                color: #1a365d;
                border-bottom: 3px solid #3182ce;
                padding-bottom: 10px;
                margin-bottom: 25px;
                page-break-before: auto;
            }
            h2 {
                font-size: 16pt;
                color: #2d3748;
                margin-top: 30px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 8px;
                page-break-before: auto;
            }
            h3 {
                font-size: 13pt;
                color: #4a5568;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            h4 {
                font-size: 11pt;
                color: #2d3748;
                margin-top: 15px;
                margin-bottom: 8px;
            }
            strong {
                color: #2d3748;
                font-weight: bold;
            }
            ul, ol {
                margin-left: 20px;
                margin-bottom: 10px;
            }
            li {
                margin-bottom: 5px;
            }
            hr {
                border: none;
                border-top: 1px solid #e2e8f0;
                margin: 20px 0;
            }
            .executive-summary {
                background-color: #f7fafc;
                padding: 15px;
                border-left: 4px solid #3182ce;
                margin-bottom: 25px;
            }
            """
            
            full_html = f"""
            <!DOCTYPE html>
            <html lang="nl">
            <head>
                <meta charset="UTF-8">
                <title>BBT Compliance Rapport - {vergunning_id}</title>
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # PDF genereren
            pdf_filename = f"Uitgebreid_BBT_Rapport_{vergunning_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join("/Users/han/Code/MOB-BREF/reports", pdf_filename)
            
            font_config = FontConfiguration()
            html_doc = WeasyHTML(string=full_html)
            html_doc.write_pdf(pdf_path, font_config=font_config)
            
            print(f"📄 Uitgebreid Nederlands PDF rapport gegenereerd: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"❌ Fout bij PDF generatie: {e}")
            # Fallback: sla markdown op
            md_filename = f"Uitgebreid_BBT_Rapport_{vergunning_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            md_path = os.path.join("/Users/han/Code/MOB-BREF/reports", md_filename)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_inhoud)
            
            return md_path

# Test functie voor het volledige systeem
def test_volledig_nederlands_systeem():
    """Test het volledige Nederlandse BBT compliance systeem"""
    print("🚀 === TESTEN VOLLEDIG NEDERLANDS BBT SYSTEEM ===")
    
    reg_manager = RegulatoryDataManager()
    processor = Uitgebreide_BREF_Processor(reg_manager)
    
    # Test met selectie van BREFs (start klein)
    test_brefs = ["FDM", "IRPP", "LCP"]  # Voeg meer toe: "WT", "WI", "REF"
    
    print(f"\n📥 === STAP 1: DOWNLOADEN VAN {len(test_brefs)} BREFs ===")
    download_resultaten = processor.download_alle_nederlandse_brefs(test_brefs)
    
    print(f"\n🔍 === STAP 2: EXTRAHEREN BBT CONCLUSIES ===")  
    alle_bbt_conclusies = processor.extraheer_alle_bbt_conclusies(test_brefs)
    
    # Overzicht van geëxtraheerde conclusies
    print(f"\n📊 === EXTRACTIE OVERZICHT ===")
    totaal_conclusies = 0
    for bref_id, conclusies in alle_bbt_conclusies.items():
        print(f"{bref_id}: {len(conclusies)} BBT conclusies")
        totaal_conclusies += len(conclusies)
    print(f"Totaal: {totaal_conclusies} BBT conclusies geëxtraheerd")
    
    # Test vergunning (uitgebreider)
    test_vergunning = """
    De industriële installatie betreft een geïntegreerd zuivel- en voedingsbedrijf met de volgende activiteiten:
    
    ZUIVELVERWERKING:
    - Ontvangst en opslag van 50.000 ton rauwe melk per jaar
    - Pasteurisatie-installaties met warmteterugwinning (85% efficiency)
    - Productie van kaas, boter, yoghurt en melkpoeder
    - Cleaning-in-place (CIP) systemen met chemicaliën recycling
    
    ENERGIESYSTEMEN:
    - 2 biomassa ketels van 25 MW elk (totaal 50 MW thermisch vermogen)
    - Warmte-kracht koppeling (WKK) installatie 
    - Energiebeheersysteem met continue monitoring
    - Zonnepanelen 500 kWp op dakoppervlak
    
    AFVALWATERBEHANDELING:
    - Fysisch-chemische voorbehandeling
    - Biologische zuivering (aerobe en anaerobe behandeling)
    - Tertiaire behandeling met membraanfiltratie
    - Slibverwerking en biogas productie
    
    EMISSIEBEHEERSING:
    - Continue emissie monitoring systemen
    - Stofafscheiders op drooginstallaties
    - VOC-reductie systemen
    - Geurbeheersing met biofilters
    
    GELUID EN TRILLINGEN:
    - Geluidsisolatie van compressoren en pompen
    - Geluidswallen rond buiteninstallaties
    - Onderhoudsschema's voor geluidsniveau beheersing
    - 24-uurs geluidsmeting op omgevingsgrens
    
    AFVALBEHEER:
    - Gescheiden inzameling van afvalstromen
    - Hergebruik van verpakkingsmaterialen
    - Compostering van organisch afval
    - Recycling van metalen en kunststoffen
    """
    
    print(f"\n🎯 === STAP 3: VOLLEDIGE COMPLIANCE CONTROLE ===")
    volledige_resultaten = processor.voer_volledige_compliance_controle_uit(
        test_vergunning, 
        list(alle_bbt_conclusies.keys()),
        "Geïntegreerd_Zuivel_Voedingsbedrijf"
    )
    
    print(f"\n📋 === STAP 4: RAPPORT GENERATIE ===")
    markdown_rapport = processor.genereer_uitgebreid_nederlands_rapport(volledige_resultaten)
    
    # Markdown opslaan
    md_path = os.path.join("/Users/han/Code/MOB-BREF/reports", 
                          f"Volledig_BBT_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_rapport)
    
    # PDF genereren  
    pdf_path = processor.genereer_pdf_van_markdown(
        markdown_rapport, 
        "Geïntegreerd_Zuivel_Voedingsbedrijf"
    )
    
    # Eindresultaten
    stats = volledige_resultaten.get("totaal_statistieken", {})
    print(f"\n🎉 === VOLTOOIING VOLLEDIG SYSTEEM ===")
    print(f"✅ BREFs geanalyseerd: {stats.get('totaal_brefs', 0)}")
    print(f"✅ BBT conclusies gecontroleerd: {stats.get('totaal_bbt_conclusies', 0)}")
    print(f"✅ Conform: {stats.get('conform', 0)}")
    print(f"⚠️ Gedeeltelijk conform: {stats.get('gedeeltelijk_conform', 0)}")
    print(f"❌ Niet-conform: {stats.get('niet_conform', 0)}")
    print(f"📄 Markdown rapport: {md_path}")
    print(f"📄 PDF rapport: {pdf_path}")

if __name__ == "__main__":
    test_volledig_nederlands_systeem()