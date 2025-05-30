# /Users/han/Code/MOB-BREF/dutch_compliance_system.py

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
from llm_handler import verify_permit_compliance_with_bat, llm_call

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

class Nederlandse_BREF_Processor:
    """Downloads en verwerkt Nederlandse BREF documenten met alle BBT conclusies"""
    
    def __init__(self, reg_manager: RegulatoryDataManager):
        self.reg_manager = reg_manager
        # Nederlandse EU-lex URLs voor BREF documenten
        self.nederlandse_bref_urls = {
            "FDM": {
                "titel": "Voedings-, dranken- en zuivelindustrie",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32019D2031",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/FDM_bref_2019.pdf"
            },
            "IRPP": {
                "titel": "Intensieve pluimvee- en varkenshouderij",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D0302",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC107189_IRPP_bref_2017.pdf"
            },
            "LCP": {
                "titel": "Grote stookinstallaties",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32017D1442",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC_107769_LCPBref_2017.pdf"
            },
            "WT": {
                "titel": "Afvalbehandeling",
                "bbt_conclusies_url": "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32018D1147",
                "volledige_bref_url": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC113018_WTBref_2018.pdf"
            }
        }
    
    def download_nederlandse_bbt_conclusies(self, bref_id: str) -> bool:
        """Download het officiële Nederlandse BBT conclusies document voor een BREF"""
        if bref_id not in self.nederlandse_bref_urls:
            print(f"BREF {bref_id} niet gevonden in bekende BREFs")
            return False
        
        bref_info = self.nederlandse_bref_urls[bref_id]
        url = bref_info["bbt_conclusies_url"]
        
        try:
            print(f"Downloaden van BBT conclusies voor {bref_id} van {url}")
            response = requests.get(url, timeout=60, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            # PDF opslaan
            filename = f"{bref_id}_BBT_conclusies_NL.pdf"
            local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Nederlandse BBT conclusies voor {bref_id} opgeslagen in: {local_path}")
            return True
            
        except Exception as e:
            print(f"Fout bij downloaden BBT conclusies voor {bref_id}: {e}")
            return False
    
    def extraheer_nederlandse_bbt_conclusies(self, bref_id: str) -> List[Nederlandse_BBT_Conclusie]:
        """Extraheer alle Nederlandse BBT conclusies uit gedownload document"""
        filename = f"{bref_id}_BBT_conclusies_NL.pdf"
        local_path = os.path.join(self.reg_manager.data_dir, "bat_conclusions", filename)
        
        if not os.path.exists(local_path):
            print(f"Nederlandse BBT conclusies document niet gevonden voor {bref_id}: {local_path}")
            return []
        
        try:
            # Tekst extraheren uit PDF
            extracted_data = extract_text_and_metadata(local_path)
            
            if not extracted_data or 'full_text' not in extracted_data:
                print(f"Kon geen tekst extraheren uit {local_path}")
                return []
            
            full_text = extracted_data['full_text']
            
            # Nederlandse BBT conclusies systematisch parsen
            bbt_conclusies = self._parseer_nederlandse_bbt_conclusies(full_text, bref_id)
            
            # Opslaan in database
            self._bewaar_nederlandse_bbt_conclusies(bbt_conclusies)
            
            print(f"Geëxtraheerd: {len(bbt_conclusies)} Nederlandse BBT conclusies uit {bref_id}")
            return bbt_conclusies
            
        except Exception as e:
            print(f"Fout bij extraheren Nederlandse BBT conclusies uit {bref_id}: {e}")
            return []
    
    def _parseer_nederlandse_bbt_conclusies(self, text: str, bref_id: str) -> List[Nederlandse_BBT_Conclusie]:
        """Uitgebreide parsing van Nederlandse BBT conclusies uit officiële documenten"""
        bbt_conclusies = []
        
        # Tekst splitsen in regels voor verwerking
        lines = text.split('\n')
        
        # Patronen voor Nederlandse BREF document structuren
        bbt_patronen = [
            r'^BBT\s+(\d+(?:\.\d+)?)\.\s*(.*?)$',  # BBT 1. Titel
            r'^(\d+(?:\.\d+)?)\.\s*BBT\s*(.*?)$',  # 1. BBT Titel
            r'^\*\*BBT\s+(\d+(?:\.\d+)?)\*\*\s*(.*?)$',  # **BBT 1** Titel
            r'^Om\s+.*?,\s*is\s+BBT\s*(.*?)$',  # Om ..., is BBT ...
            r'^Teneinde\s+.*?,\s*is\s+BBT\s*(.*?)$',  # Teneinde ..., is BBT ...
        ]
        
        current_bbt = None
        current_section = ""
        in_bbt_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Controleer of deze regel een nieuwe BBT conclusie start
            bbt_match = None
            for pattern in bbt_patronen:
                bbt_match = re.match(pattern, line, re.IGNORECASE)
                if bbt_match:
                    break
            
            if bbt_match:
                # Vorige BBT opslaan indien aanwezig
                if current_bbt:
                    bbt_conclusies.append(current_bbt)
                
                # Nieuwe BBT starten
                bbt_nummer = bbt_match.group(1) if bbt_match.groups() else str(len(bbt_conclusies) + 1)
                titel = bbt_match.group(2).strip() if len(bbt_match.groups()) > 1 else line
                
                current_bbt = Nederlandse_BBT_Conclusie(
                    bbt_id=f"{bref_id}_BBT_{bbt_nummer}",
                    bref_bron=bref_id,
                    bbt_nummer=bbt_nummer,
                    titel=titel,
                    beschrijving="",
                    toepasselijkheid="",
                    bron_sectie=current_section
                )
                in_bbt_section = True
                continue
            
            # Secties bijhouden
            if any(keyword in line.upper() for keyword in ['HOOFDSTUK', 'SECTIE', 'PARAGRAAF']):
                current_section = line
                in_bbt_section = False
                continue
            
            # BBT inhoud verzamelen
            if current_bbt and in_bbt_section and line:
                # Controleren op specifieke subsecties
                if any(keyword in line.lower() for keyword in ['toepasselijkheid', 'van toepassing']):
                    current_bbt.toepasselijkheid += line + " "
                elif any(keyword in line.lower() for keyword in ['emissie', 'grenswaarde', 'niveau']):
                    current_bbt.emissieniveaus = (current_bbt.emissieniveaus or "") + line + " "
                elif any(keyword in line.lower() for keyword in ['monitor', 'meting', 'controle']):
                    current_bbt.monitoringvereisten = (current_bbt.monitoringvereisten or "") + line + " "
                elif any(keyword in line.lower() for keyword in ['techniek', 'methode', 'procedure']):
                    current_bbt.technieken = (current_bbt.technieken or "") + line + " "
                else:
                    current_bbt.beschrijving += line + " "
        
        # Laatste BBT niet vergeten
        if current_bbt:
            bbt_conclusies.append(current_bbt)
        
        # Als geen BBT conclusies gevonden met patronen, probeer alternatieve extractie
        if not bbt_conclusies:
            bbt_conclusies = self._extraheer_bbt_conclusies_alternatief(text, bref_id)
        
        return bbt_conclusies
    
    def _extraheer_bbt_conclusies_alternatief(self, text: str, bref_id: str) -> List[Nederlandse_BBT_Conclusie]:
        """Alternatieve extractie methode voor verschillende document formaten"""
        bbt_conclusies = []
        
        # Zoek naar genummerde secties die BBT conclusies zouden kunnen zijn
        lines = text.split('\n')
        
        # Vind secties die eruitzien als BBT conclusies
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Zoek naar patronen zoals "Om te...", "Teneinde...", "Voor..."
            if (line.startswith('Om ') or line.startswith('Teneinde ') or 
                line.startswith('Voor ') or 'emissies te verminderen' in line.lower()):
                
                # Dit zou een BBT conclusie kunnen zijn - verzamel omringende context
                bbt_text = line
                
                # Kijk vooruit voor voortzetting
                j = i + 1
                while j < len(lines) and j < i + 10:  # Kijk tot 10 regels vooruit
                    next_line = lines[j].strip()
                    if (next_line and not any(start in next_line for start in ['Om ', 'Teneinde ', 'Voor ']) and 
                        len(next_line) > 10):
                        bbt_text += " " + next_line
                        j += 1
                    else:
                        break
                
                if len(bbt_text) > 50:  # Alleen als substantiële inhoud
                    bbt_nummer = str(len(bbt_conclusies) + 1)
                    
                    bbt_conclusie = Nederlandse_BBT_Conclusie(
                        bbt_id=f"{bref_id}_BBT_{bbt_nummer}",
                        bref_bron=bref_id,
                        bbt_nummer=bbt_nummer,
                        titel=f"BBT {bbt_nummer}",
                        beschrijving=bbt_text,
                        toepasselijkheid="Algemeen van toepassing"
                    )
                    bbt_conclusies.append(bbt_conclusie)
        
        return bbt_conclusies
    
    def _bewaar_nederlandse_bbt_conclusies(self, bbt_conclusies: List[Nederlandse_BBT_Conclusie]):
        """Bewaar gedetailleerde Nederlandse BBT conclusies in database"""
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        # Uitgebreide tabel aanmaken indien nodig
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nederlandse_bbt_conclusies (
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
        
        for bbt in bbt_conclusies:
            cursor.execute('''
                INSERT OR REPLACE INTO nederlandse_bbt_conclusies 
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
    
    def nederlandse_bbt_compliance_controle(self, vergunning_inhoud: str, bref_id: str) -> List[Dict[str, Any]]:
        """Systematische compliance controle tegen ALLE Nederlandse BBT conclusies voor een BREF"""
        print(f"\n=== UITGEBREIDE NEDERLANDSE BBT COMPLIANCE CONTROLE VOOR {bref_id} ===")
        
        # Haal alle Nederlandse BBT conclusies op voor deze BREF
        conn = sqlite3.connect(self.reg_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bbt_id, bref_bron, bbt_nummer, titel, beschrijving, toepasselijkheid,
                   emissieniveaus, monitoringvereisten, technieken, prestatieniveaus,
                   implementatienotities, bron_sectie
            FROM nederlandse_bbt_conclusies 
            WHERE bref_bron = ?
            ORDER BY bbt_nummer
        ''', (bref_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        bbt_conclusies = []
        for result in results:
            bbt_conclusies.append(Nederlandse_BBT_Conclusie(
                bbt_id=result[0], bref_bron=result[1], bbt_nummer=result[2],
                titel=result[3], beschrijving=result[4], toepasselijkheid=result[5],
                emissieniveaus=result[6], monitoringvereisten=result[7], technieken=result[8],
                prestatieniveaus=result[9], implementatienotities=result[10], bron_sectie=result[11]
            ))
        
        if not bbt_conclusies:
            print(f"Geen Nederlandse BBT conclusies gevonden voor {bref_id} - downloaden en extraheren...")
            if self.download_nederlandse_bbt_conclusies(bref_id):
                bbt_conclusies = self.extraheer_nederlandse_bbt_conclusies(bref_id)
        
        compliance_resultaten = []
        
        print(f"Controle van compliance tegen {len(bbt_conclusies)} Nederlandse BBT conclusies...")
        
        for i, bbt in enumerate(bbt_conclusies, 1):
            print(f"\nControleren BBT {bbt.bbt_nummer}: {bbt.titel[:50]}...")
            
            # Nederlandse BBT conclusie voorbereiden voor LLM analyse
            bbt_voor_llm = {
                "bat_id": bbt.bbt_id,
                "bat_text_description": f"{bbt.titel}. {bbt.beschrijving}",
                "source_metadata": {
                    "page_number": bbt.bron_sectie or "Onbekend",
                    "paragraph_id": bbt.bbt_nummer
                }
            }
            
            try:
                # Nederlandse prompt voor LLM
                nederlandse_prompt = f"""
                Je bent een expert in EU milieuregulering en industriële vergunningen. 
                Je moet de voorwaarden in een industriële vergunning nauwkeurig vergelijken met een specifieke Beste Beschikbare Techniek (BBT) conclusie.

                De BBT Conclusie (ID: {bbt.bbt_id}) is als volgt:
                {bbt.titel}. {bbt.beschrijving}
                (Bron: BREF Document, Sectie: {bbt.bron_sectie or 'N/A'}, Paragraaf: {bbt.bbt_nummer})

                De volledige tekst van de industriële vergunning wordt hieronder weergegeven:
                --- VERGUNNING START ---
                {vergunning_inhoud}
                --- VERGUNNING EINDE ---

                Analyseer de vergunningtekst en bepaal de compliance status met de gegeven BBT conclusie.
                Rapporteer over de volgende aspecten, met specifieke citaten uit de vergunning waar mogelijk:
                1. **Compliance:** Is de vergunning volledig conform deze BBT conclusie? Citeer vergunningtekst.
                2. **Gedeeltelijke Compliance/Afwijkingen:** Zijn er gedeeltelijke compliances of afwijkingen? Detail elk punt, citeer vergunningtekst en het relevante deel van de BBT.
                3. **Non-Compliance/Ontbrekende Elementen:** Zijn er duidelijke non-compliances of ontbrekende elementen in de vergunning betreffende deze BBT?
                4. **Onduidelijkheid/Onvoldoende Informatie:** Zijn er delen van de BBT die niet geverifieerd kunnen worden door onduidelijkheid of onvoldoende informatie in de vergunning?

                Bepaal op basis van je analyse een overall compliance status uit de volgende opties: 'Conform', 'Gedeeltelijk Conform', 'Niet-Conform', 'Onduidelijk/Onvoldoende Informatie'.

                Geef je antwoord in JSON formaat met de volgende keys: "bat_id", "compliance_status", "detailed_findings".
                De "detailed_findings" moet een tekstuele uitleg zijn die de bovenstaande punten dekt.
                
                Voorbeeld JSON response:
                {{
                  "bat_id": "{bbt.bbt_id}",
                  "compliance_status": "Gedeeltelijk Conform",
                  "detailed_findings": "De vergunning behandelt aspect X van de BBT conclusie (zie Vergunning Pagina Y, Para Z: '...tekst...'). Echter, aspect W wordt niet genoemd, en aspect V wordt slechts gedeeltelijk gedekt (Vergunning Pagina A, Para B: '...tekst...'). Daarom is aanvullende informatie of verduidelijking nodig voor aspect W."
                }}
                """
                
                print(f"--- Nederlandse prompt naar LLM voor BBT ID: {bbt.bbt_id} ---")
                llm_response_str = llm_call(nederlandse_prompt)
                print(f"LLM Nederlandse Response voor {bbt.bbt_id}: {llm_response_str}")
                
                if llm_response_str and not llm_response_str.startswith("Error:"):
                    try:
                        json_start = llm_response_str.find('{')
                        json_end = llm_response_str.rfind('}') + 1
                        if json_start != -1 and json_end != -1:
                            json_part = llm_response_str[json_start:json_end]
                            response_json = json.loads(json_part)
                            
                            # Uitbreiden met Nederlandse details
                            response_json.update({
                                "bbt_nummer": bbt.bbt_nummer,
                                "bbt_titel": bbt.titel,
                                "toepasselijkheid": bbt.toepasselijkheid,
                                "emissieniveaus": bbt.emissieniveaus,
                                "monitoringvereisten": bbt.monitoringvereisten,
                                "technieken": bbt.technieken,
                                "bref_bron": bref_id
                            })
                            
                            compliance_resultaten.append(response_json)
                            
                            # Samenvatting printen
                            status = response_json.get('compliance_status', 'Onbekend')
                            print(f"  → {status}")
                        else:
                            raise json.JSONDecodeError("Geen JSON object gevonden", llm_response_str, 0)
                    except json.JSONDecodeError as e:
                        print(f"Fout bij decoderen JSON van LLM response voor {bbt.bbt_id}: {e}")
                        compliance_resultaten.append({
                            "bat_id": bbt.bbt_id,
                            "bbt_nummer": bbt.bbt_nummer,
                            "bbt_titel": bbt.titel,
                            "compliance_status": "Fout",
                            "detailed_findings": f"Kon LLM response niet parsen: {llm_response_str}",
                            "bref_bron": bref_id
                        })
                else:
                    compliance_resultaten.append({
                        "bat_id": bbt.bbt_id,
                        "bbt_nummer": bbt.bbt_nummer,
                        "bbt_titel": bbt.titel,
                        "compliance_status": "Fout",
                        "detailed_findings": llm_response_str or "Geen response van LLM",
                        "bref_bron": bref_id
                    })
                
            except Exception as e:
                print(f"  → Fout: {e}")
                compliance_resultaten.append({
                    "bat_id": bbt.bbt_id,
                    "bbt_nummer": bbt.bbt_nummer,
                    "bbt_titel": bbt.titel,
                    "compliance_status": "Fout",
                    "detailed_findings": f"Analyse mislukt: {e}",
                    "bref_bron": bref_id
                })
        
        return compliance_resultaten
    
    def genereer_nederlands_pdf_rapport(self, compliance_resultaten: List[Dict[str, Any]], 
                                       bref_id: str, vergunning_id: str = "Test_Vergunning") -> str:
        """Genereer een uitgebreid Nederlands PDF rapport"""
        
        # Nederlandse markdown inhoud genereren
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        bref_titel = self.nederlandse_bref_urls.get(bref_id, {}).get("titel", bref_id)
        
        markdown_inhoud = f"""# BBT Compliance Rapport
        
**Vergunning ID:** {vergunning_id}  
**BREF:** {bref_id} - {bref_titel}  
**Gegenereerd op:** {timestamp}  

## Samenvatting

"""
        
        # Statistieken berekenen
        conform = len([r for r in compliance_resultaten if r.get('compliance_status') == 'Conform'])
        gedeeltelijk = len([r for r in compliance_resultaten if r.get('compliance_status') == 'Gedeeltelijk Conform'])
        niet_conform = len([r for r in compliance_resultaten if r.get('compliance_status') == 'Niet-Conform'])
        onduidelijk = len([r for r in compliance_resultaten if r.get('compliance_status') == 'Onduidelijk/Onvoldoende Informatie'])
        fouten = len([r for r in compliance_resultaten if r.get('compliance_status') == 'Fout'])
        
        markdown_inhoud += f"""
**Totaal aantal BBT conclusies gecontroleerd:** {len(compliance_resultaten)}

- **Conform:** {conform}
- **Gedeeltelijk Conform:** {gedeeltelijk}  
- **Niet-Conform:** {niet_conform}
- **Onduidelijk/Onvoldoende Informatie:** {onduidelijk}
- **Fouten bij analyse:** {fouten}

## Gedetailleerde Resultaten

"""
        
        # Gedetailleerde resultaten per BBT
        for result in compliance_resultaten:
            bbt_nummer = result.get('bbt_nummer', 'N/A')
            titel = result.get('bbt_titel', 'Geen titel')
            status = result.get('compliance_status', 'Onbekend')
            bevindingen = result.get('detailed_findings', 'Geen bevindingen beschikbaar')
            
            markdown_inhoud += f"""### BBT {bbt_nummer}

**Titel:** {titel}

**Compliance Status:** {status}

**Gedetailleerde Bevindingen:**
{bevindingen}

---

"""
        
        markdown_inhoud += """
## Aanbevelingen

Gebaseerd op deze analyse worden de volgende acties aanbevolen:

"""
        
        # Aanbevelingen genereren
        if niet_conform > 0:
            markdown_inhoud += f"1. **Prioriteit Hoog:** Behandel {niet_conform} niet-conforme BBT conclusies\n"
        
        if gedeeltelijk > 0:
            markdown_inhoud += f"2. **Prioriteit Medium:** Verbeter {gedeeltelijk} gedeeltelijk conforme BBT conclusies\n"
        
        if onduidelijk > 0:
            markdown_inhoud += f"3. **Prioriteit Medium:** Verkrijg aanvullende informatie voor {onduidelijk} onduidelijke BBT conclusies\n"
        
        markdown_inhoud += """
4. **Algemeen:** Zorg voor regelmatige monitoring en rapportage van BBT compliance
5. **Documentatie:** Verbeter documentatie van milieumaatregelen in vergunningsdossier

---
*Dit rapport is automatisch gegenereerd door het BBT Compliance Verificatie Systeem*
"""
        
        # Markdown opslaan
        md_filename = f"BBT_Compliance_Rapport_{bref_id}_{vergunning_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        md_path = os.path.join("/Users/han/Code/MOB-BREF/reports", md_filename)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_inhoud)
        
        # PDF genereren
        try:
            import markdown2
            from weasyprint import HTML as WeasyHTML
            from weasyprint.text.fonts import FontConfiguration
            
            html_content = markdown2.markdown(markdown_inhoud, extras=["tables", "fenced-code-blocks", "break-on-newline"])
            
            css_style = """
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: "Arial", "Helvetica", sans-serif;
                line-height: 1.6;
                font-size: 11pt;
            }
            h1, h2, h3 {
                color: #2c3e50;
                line-height: 1.2;
            }
            h1 {
                font-size: 24pt;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            h2 {
                font-size: 18pt;
                margin-top: 30px;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
            }
            h3 {
                font-size: 14pt;
                margin-top: 20px;
                color: #34495e;
            }
            strong {
                color: #2c3e50;
            }
            hr {
                border: none;
                border-top: 1px solid #bdc3c7;
                margin: 20px 0;
            }
            """
            
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>BBT Compliance Rapport - {bref_id}</title>
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            pdf_filename = f"BBT_Compliance_Rapport_{bref_id}_{vergunning_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join("/Users/han/Code/MOB-BREF/reports", pdf_filename)
            
            font_config = FontConfiguration()
            html_doc = WeasyHTML(string=full_html)
            html_doc.write_pdf(pdf_path, font_config=font_config)
            
            print(f"Nederlands PDF rapport gegenereerd: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Fout bij genereren PDF rapport: {e}")
            return md_path  # Return markdown path als fallback

# Test functie
def test_nederlands_systeem():
    """Test het Nederlandse compliance systeem"""
    print("=== TESTEN NEDERLANDS BBT COMPLIANCE SYSTEEM ===")
    
    reg_manager = RegulatoryDataManager()
    processor = Nederlandse_BREF_Processor(reg_manager)
    
    # Test met FDM (Voedings-, dranken- en zuivelindustrie)
    bref_id = "FDM"
    
    # Nederlandse BBT conclusies downloaden en extraheren
    print(f"\n=== VERWERKEN VAN NEDERLANDSE {bref_id} BREF ===")
    if processor.download_nederlandse_bbt_conclusies(bref_id):
        bbt_conclusies = processor.extraheer_nederlandse_bbt_conclusies(bref_id)
        
        if bbt_conclusies:
            print(f"\nNederlandse {bref_id} BBT CONCLUSIES SAMENVATTING:")
            print(f"Totaal geëxtraheerde BBT conclusies: {len(bbt_conclusies)}")
            
            # Test compliance controle
            sample_nederlandse_vergunning = """
            De zuivelfabriek verwerkt 1000 ton melk per jaar. De faciliteit omvat:
            - Melkontvangst en opslagtanks met koeling
            - Pasteurisatie-apparatuur met warmteterugwinning
            - Cleaning-in-place (CIP) systemen voor reiniging van apparatuur
            - Afvalwaterzuiveringsinstallatie voor zuivelafvalwater
            - Energiebeheersysteem voor monitoring van elektriciteit en stoom
            - Restwarmteterugwinning van pasteurisatie voor voorverwarming
            - Geautomatiseerde regelsystemen voor temperatuur en pH monitoring
            """
            
            print(f"\n=== NEDERLANDSE BBT COMPLIANCE CONTROLE ===")
            compliance_resultaten = processor.nederlandse_bbt_compliance_controle(
                sample_nederlandse_vergunning, bref_id
            )
            
            # Nederlands PDF rapport genereren
            pdf_path = processor.genereer_nederlands_pdf_rapport(
                compliance_resultaten, bref_id, "Test_Nederlandse_Vergunning"
            )
            
            print(f"\nNederlands rapport opgeslagen in: {pdf_path}")

if __name__ == "__main__":
    test_nederlands_systeem()