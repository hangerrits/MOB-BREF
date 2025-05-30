#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/enhanced_compliance_reporter.py

"""
Enhanced Compliance Reporter met Toepasselijkheidstabel
Genereert eerst analyse van welke BREFs/BATs en RIE van toepassing zijn
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from regulatory_data_manager import RegulatoryDataManager
import sqlite3

class EnhancedComplianceReporter:
    """Enhanced reporter met toepasselijkheidsanalyse"""
    
    def __init__(self):
        self.manager = RegulatoryDataManager()
        self.all_brefs = self._get_all_available_brefs()
        self.horizontal_brefs = self.manager.get_horizontal_brefs()
        
    def _get_all_available_brefs(self) -> Dict[str, Dict]:
        """Get alle beschikbare BREFs inclusief gedownloade"""
        brefs_dir = os.path.join(self.manager.data_dir, 'brefs')
        downloaded_brefs = []
        
        if os.path.exists(brefs_dir):
            downloaded_brefs = [f.replace('_bref.pdf', '') for f in os.listdir(brefs_dir) 
                              if f.endswith('_bref.pdf')]
        
        # Complete BREF catalog met toepasselijkheid
        return {
            # HORIZONTALE BREFs - Van toepassing op ALLE sectoren
            "ICS": {
                "title": "Industriële koelsystemen",
                "type": "HORIZONTAAL",
                "sectors": ["Alle industrieën met koeling > 2 MW"],
                "applicability": "Koelsystemen, airconditioning, warmtepompen",
                "downloaded": "ICS" in downloaded_brefs,
                "priority": "Hoog - geldt voor alle sectoren"
            },
            "ENE": {
                "title": "Energie-efficiëntie", 
                "type": "HORIZONTAAL",
                "sectors": ["Alle industrieën"],
                "applicability": "Energiegebruik, efficiency, warmteterugwinning",
                "downloaded": "ENE" in downloaded_brefs,
                "priority": "Hoog - geldt voor alle sectoren"
            },
            "EMS": {
                "title": "Emissiemonitoring",
                "type": "HORIZONTAAL", 
                "sectors": ["Alle industrieën met emissies"],
                "applicability": "Monitoring, rapportage, meetmethoden",
                "downloaded": "EMS" in downloaded_brefs,
                "priority": "Hoog - geldt voor alle sectoren"
            },
            "CWW": {
                "title": "Afvalwater en gasbehandeling",
                "type": "HORIZONTAAL",
                "sectors": ["Alle industrieën met afvalwater/gas"],
                "applicability": "Afvalwaterbehandeling, gasreiniging",
                "downloaded": "CWW" in downloaded_brefs,
                "priority": "Hoog - geldt voor alle sectoren"
            },
            "STM": {
                "title": "Oppervlaktebehandeling metalen",
                "type": "HORIZONTAAL",
                "sectors": ["Metaalbewerking, automotive, aerospace"],
                "applicability": "Galvaniseren, anodiseren, lakken van metaal",
                "downloaded": "STM" in downloaded_brefs,
                "priority": "Medium - sector-afhankelijk"
            },
            "STP": {
                "title": "Oppervlaktebehandeling kunststoffen", 
                "type": "HORIZONTAAL",
                "sectors": ["Kunststofverwerking, automotive"],
                "applicability": "Coating, lakken van kunststof",
                "downloaded": "STP" in downloaded_brefs,
                "priority": "Medium - sector-afhankelijk"
            },
            "STS": {
                "title": "Oppervlaktebehandeling oplosmiddelen",
                "type": "HORIZONTAAL",
                "sectors": ["Alle sectoren met oplosmiddelen"],
                "applicability": "Oplosmiddelgebruik > 150kg/h of 200t/jaar",
                "downloaded": "STS" in downloaded_brefs,
                "priority": "Medium - drempelwaarde-afhankelijk"
            },
            "ECM": {
                "title": "Economics and Cross-media Effects",
                "type": "HORIZONTAAL",
                "sectors": ["Alle sectoren - economische analyse"],
                "applicability": "Kosten-baten analyse, cross-media effecten",
                "downloaded": "ECM" in downloaded_brefs,
                "priority": "Laag - ondersteunend document"
            },
            
            # SECTOR-SPECIFIEKE BREFs
            "FDM": {
                "title": "Voedings-, dranken- en zuivelindustrie",
                "type": "SECTOR",
                "sectors": ["Voedingsmiddelen", "Zuivel", "Dranken"],
                "applicability": "Melkverwerking, voedselproductie",
                "downloaded": "FDM" in downloaded_brefs,
                "priority": "Hoog - bij voedselactiviteiten"
            },
            "IRPP": {
                "title": "Intensieve pluimvee- en varkenshouderij",
                "type": "SECTOR", 
                "sectors": ["Veehouderij"],
                "applicability": ">40.000 pluimvee, >2.000 varkens, >750 zeugen",
                "downloaded": "IRPP" in downloaded_brefs,
                "priority": "Hoog - bij intensieve veehouderij"
            },
            "LCP": {
                "title": "Grote stookinstallaties",
                "type": "SECTOR",
                "sectors": ["Energie", "Industrie met stoom"],
                "applicability": "Stookinstallaties > 50 MW thermisch",
                "downloaded": "LCP" in downloaded_brefs,
                "priority": "Hoog - bij grote ketels/turbines"
            },
            "WT": {
                "title": "Afvalbehandeling", 
                "type": "SECTOR",
                "sectors": ["Afvalbeheer"],
                "applicability": "Afvalverwerking, recycling, compostering",
                "downloaded": "WT" in downloaded_brefs,
                "priority": "Hoog - bij afvalactiviteiten"
            },
            "WI": {
                "title": "Afvalverbranding",
                "type": "SECTOR",
                "sectors": ["Afvalbeheer", "Energie"],
                "applicability": "Afvalverbranding > 3 ton/uur",
                "downloaded": "WI" in downloaded_brefs,
                "priority": "Hoog - bij afvalverbranding"
            },
            "REF": {
                "title": "Raffinage van minerale olie en gas",
                "type": "SECTOR",
                "sectors": ["Petrochemie", "Energie"],
                "applicability": "Olieraffinaderijen, gasverwerking",
                "downloaded": "REF" in downloaded_brefs,
                "priority": "Hoog - bij raffinageactiviteiten"
            },
            "ISP": {
                "title": "IJzer- en staalproductie",
                "type": "SECTOR",
                "sectors": ["Metaalindustrie"],
                "applicability": "Staalproductie > 2.5 ton/uur",
                "downloaded": "ISP" in downloaded_brefs,
                "priority": "Hoog - bij staalproductie"
            },
            "NFM": {
                "title": "Non-ferro metalen",
                "type": "SECTOR",
                "sectors": ["Metaalindustrie"],
                "applicability": "Aluminium, koper, zink productie",
                "downloaded": "NFM" in downloaded_brefs,
                "priority": "Hoog - bij non-ferro metalen"
            },
            "CLM": {
                "title": "Cement, kalk en magnesiumoxide",
                "type": "SECTOR", 
                "sectors": ["Bouwmaterialen"],
                "applicability": "Cement >500t/dag, kalk >50t/dag",
                "downloaded": "CLM" in downloaded_brefs,
                "priority": "Hoog - bij cement/kalkproductie"
            },
            "GLS": {
                "title": "Glasindustrie",
                "type": "SECTOR",
                "sectors": ["Bouwmaterialen", "Verpakking"],
                "applicability": "Glasproductie > 20 ton/dag",
                "downloaded": "GLS" in downloaded_brefs,
                "priority": "Hoog - bij glasproductie"
            },
            "CAM": {
                "title": "Keramische industrie",
                "type": "SECTOR",
                "sectors": ["Bouwmaterialen"],
                "applicability": "Keramiek > 75 ton/dag",
                "downloaded": "CAM" in downloaded_brefs,
                "priority": "Hoog - bij keramiekproductie"
            },
            "LVIC": {
                "title": "Anorganische chemicaliën (grote volumes)",
                "type": "SECTOR",
                "sectors": ["Chemische industrie"],
                "applicability": "Anorganische chemie op industriële schaal",
                "downloaded": "LVIC" in downloaded_brefs,
                "priority": "Hoog - bij anorganische chemie"
            },
            "LVOC": {
                "title": "Organische chemicaliën (grote volumes)",
                "type": "SECTOR",
                "sectors": ["Chemische industrie"],
                "applicability": "Organische chemie op industriële schaal", 
                "downloaded": "LVOC" in downloaded_brefs,
                "priority": "Hoog - bij organische chemie"
            },
            "CAK": {
                "title": "Chloor-alkali productie",
                "type": "SECTOR",
                "sectors": ["Chemische industrie"],
                "applicability": "Chloor, natronloog productie",
                "downloaded": "CAK" in downloaded_brefs,
                "priority": "Hoog - bij chloor-alkali"
            },
            "OFC": {
                "title": "Organische fijnchemicaliën",
                "type": "SECTOR",
                "sectors": ["Chemische industrie", "Farmaceutisch"],
                "applicability": "Fijnchemie, farmaceutische grondstoffen",
                "downloaded": "OFC" in downloaded_brefs,
                "priority": "Hoog - bij fijnchemie"
            },
            "POL": {
                "title": "Polymeren productie",
                "type": "SECTOR",
                "sectors": ["Chemische industrie", "Kunststof"],
                "applicability": "Kunststofproductie, polymeren",
                "downloaded": "POL" in downloaded_brefs,
                "priority": "Hoog - bij polymeerproductie"
            },
            "PPB": {
                "title": "Pulp, papier en karton",
                "type": "SECTOR",
                "sectors": ["Papierindustrie"],
                "applicability": "Papierproductie > 20 ton/dag",
                "downloaded": "PPB" in downloaded_brefs,
                "priority": "Hoog - bij papierproductie"
            },
            "TXT": {
                "title": "Textielindustrie",
                "type": "SECTOR",
                "sectors": ["Textiel"],
                "applicability": "Textielbehandeling > 10 ton/dag",
                "downloaded": "TXT" in downloaded_brefs,
                "priority": "Hoog - bij textielproductie"
            },
            "SA": {
                "title": "Slachthuizen",
                "type": "SECTOR",
                "sectors": ["Voedingsmiddelen"],
                "applicability": "Slachthuizen > 50 ton/dag geslacht gewicht",
                "downloaded": "SA" in downloaded_brefs,
                "priority": "Hoog - bij slachtactiviteiten"
            },
            "WBP": {
                "title": "Houtgebaseerde panelen",
                "type": "SECTOR",
                "sectors": ["Houtindustrie"],
                "applicability": "Spaanplaat, MDF, multiplex productie",
                "downloaded": "WBP" in downloaded_brefs,
                "priority": "Hoog - bij houtpaneelproductie"
            },
            "MIN": {
                "title": "Mijnbouw",
                "type": "SECTOR",
                "sectors": ["Mijnbouw", "Winning"],
                "applicability": "Mijnbouwactiviteiten, winning delfstoffen",
                "downloaded": "MIN" in downloaded_brefs,
                "priority": "Hoog - bij mijnbouwactiviteiten"
            }
        }
    
    def analyze_permit_applicability(self, permit_text: str, permit_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyseer welke BREFs/BATs en RIE van toepassing zijn"""
        
        print("🔍 === TOEPASSELIJKHEIDSANALYSE ===")
        
        analysis = {
            "applicable_brefs": [],
            "not_applicable_brefs": [],
            "potentially_applicable_brefs": [],
            "applicable_rie": [],
            "permit_classification": {},
            "analysis_summary": {}
        }
        
        permit_lower = permit_text.lower()
        
        # Keywords voor verschillende sectoren/activiteiten
        keywords = {
            "dairy": ["melk", "zuivel", "dairy", "melkvee", "rundvee"],
            "livestock": ["veehouderij", "pluimvee", "varkens", "runderen", "livestock"],
            "food": ["voedsel", "food", "levensmiddelen", "slachterij"],
            "energy": ["energie", "stoom", "ketel", "turbine", "warmte"],
            "cooling": ["koeling", "airco", "klimaat", "warmtepomp", "koelmachine"],
            "waste": ["afval", "waste", "verbranding", "recyclage"],
            "chemical": ["chemisch", "chemical", "reactie", "synthese"],
            "surface": ["oppervlakte", "galvani", "lak", "coating", "anodise"],
            "emissions": ["emissie", "uitstoot", "lozingen", "monitoring"],
            "wastewater": ["afvalwater", "rioolwater", "proceswater", "lozingen"]
        }
        
        # Detecteer activiteitscategorieën
        detected_categories = []
        for category, words in keywords.items():
            if any(word in permit_lower for word in words):
                detected_categories.append(category)
        
        # Analyseer elke BREF
        for bref_id, bref_info in self.all_brefs.items():
            applicability_score = 0
            reasons = []
            
            # Horizontale BREFs zijn bijna altijd van toepassing
            if bref_info["type"] == "HORIZONTAAL":
                if bref_id == "ICS" and "cooling" in detected_categories:
                    applicability_score = 3
                    reasons.append("Koelingsactiviteiten gedetecteerd")
                elif bref_id == "ENE":
                    applicability_score = 3
                    reasons.append("Energie-efficiëntie altijd relevant")
                elif bref_id == "EMS" and "emissions" in detected_categories:
                    applicability_score = 3
                    reasons.append("Emissies/monitoring gedetecteerd")
                elif bref_id == "CWW" and "wastewater" in detected_categories:
                    applicability_score = 3
                    reasons.append("Afvalwaterbehandeling gedetecteerd")
                elif bref_id in ["STM", "STP", "STS"] and "surface" in detected_categories:
                    applicability_score = 3
                    reasons.append("Oppervlaktebehandeling gedetecteerd")
                elif bref_id in ["ICS", "EMS", "CWW"]:
                    applicability_score = 2
                    reasons.append("Mogelijk van toepassing (horizontaal)")
                else:
                    applicability_score = 1
                    reasons.append("Laag relevant (horizontaal)")
            
            # Sector-specifieke BREFs
            else:
                if bref_id == "FDM" and ("dairy" in detected_categories or "food" in detected_categories):
                    applicability_score = 3
                    reasons.append("Voedsel/zuivelactiviteiten gedetecteerd")
                elif bref_id == "IRPP" and "livestock" in detected_categories:
                    applicability_score = 3
                    reasons.append("Veehouderijactiviteiten gedetecteerd")
                elif bref_id == "LCP" and "energy" in detected_categories:
                    applicability_score = 3
                    reasons.append("Grote energieactiviteiten gedetecteerd")
                elif bref_id in ["WT", "WI"] and "waste" in detected_categories:
                    applicability_score = 3
                    reasons.append("Afvalactiviteiten gedetecteerd")
                # Andere sector matches...
                else:
                    applicability_score = 0
                    reasons.append("Geen sectoractiviteiten gedetecteerd")
            
            # Categoriseer op basis van score
            bref_analysis = {
                "bref_id": bref_id,
                "title": bref_info["title"],
                "type": bref_info["type"],
                "applicability": bref_info["applicability"],
                "downloaded": bref_info["downloaded"],
                "score": applicability_score,
                "reasons": reasons,
                "priority": bref_info["priority"]
            }
            
            if applicability_score >= 3:
                analysis["applicable_brefs"].append(bref_analysis)
            elif applicability_score >= 2:
                analysis["potentially_applicable_brefs"].append(bref_analysis)
            else:
                analysis["not_applicable_brefs"].append(bref_analysis)
        
        # RIE analyse
        analysis["applicable_rie"] = self._analyze_rie_applicability(permit_text, detected_categories)
        
        # Permit classificatie
        analysis["permit_classification"] = {
            "detected_categories": detected_categories,
            "primary_sector": self._determine_primary_sector(detected_categories),
            "complexity": len(detected_categories),
            "industrial_scale": self._assess_industrial_scale(permit_text)
        }
        
        # Samenvatting
        analysis["analysis_summary"] = {
            "total_brefs": len(self.all_brefs),
            "applicable_count": len(analysis["applicable_brefs"]),
            "potentially_applicable_count": len(analysis["potentially_applicable_brefs"]),
            "not_applicable_count": len(analysis["not_applicable_brefs"]),
            "applicable_rie_count": len(analysis["applicable_rie"]),
            "coverage_percentage": round((len(analysis["applicable_brefs"]) / len(self.all_brefs)) * 100, 1)
        }
        
        return analysis
    
    def _analyze_rie_applicability(self, permit_text: str, categories: List[str]) -> List[Dict]:
        """Analyseer RIE Annex I toepasselijkheid"""
        applicable_rie = []
        
        # Get RIE activities from database
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rie_activities LIMIT 10')  # Sample
        activities = cursor.fetchall()
        conn.close()
        
        for activity in activities:
            category, description, threshold, notes = activity[1:5]
            
            rie_item = {
                "category": category,
                "description": description,
                "threshold": threshold,
                "applicable": False,
                "reason": "Geen match gevonden"
            }
            
            # Simple matching logic
            if "livestock" in categories and "intensive rearing" in description.lower():
                rie_item["applicable"] = True
                rie_item["reason"] = "Intensieve veehouderij gedetecteerd"
            elif "energy" in categories and "combustion" in description.lower():
                rie_item["applicable"] = True
                rie_item["reason"] = "Grote verbrandingsinstallatie mogelijk"
            elif "food" in categories and "food" in description.lower():
                rie_item["applicable"] = True
                rie_item["reason"] = "Voedselverwerking gedetecteerd"
            
            if rie_item["applicable"]:
                applicable_rie.append(rie_item)
        
        return applicable_rie
    
    def _determine_primary_sector(self, categories: List[str]) -> str:
        """Bepaal primaire sector"""
        if "dairy" in categories or "livestock" in categories:
            return "Veehouderij/Zuivel"
        elif "food" in categories:
            return "Voedingsmiddelen"
        elif "chemical" in categories:
            return "Chemische industrie"
        elif "energy" in categories:
            return "Energie"
        elif "waste" in categories:
            return "Afvalbeheer"
        else:
            return "Onbepaald"
    
    def _assess_industrial_scale(self, permit_text: str) -> str:
        """Beoordeel industriële schaal"""
        text_lower = permit_text.lower()
        
        # Look for scale indicators
        if any(indicator in text_lower for indicator in ["industriële schaal", "grote installatie", "> 50 mw", "industrial scale"]):
            return "Groot/Industrieel"
        elif any(indicator in text_lower for indicator in ["middelgroot", "medium", "beperkt"]):
            return "Middelgroot"
        else:
            return "Onbepaald"
    
    def generate_applicability_table_html(self, analysis: Dict[str, Any]) -> str:
        """Genereer HTML tabel voor toepasselijkheid"""
        
        html = """
        <div class="applicability-analysis">
            <h2>🔍 Toepasselijkheidsanalyse BREF/BAT en RIE</h2>
            
            <div class="summary-box">
                <h3>📊 Analyse Samenvatting</h3>
                <table class="summary-table">
                    <tr><td><strong>Primaire Sector:</strong></td><td>{primary_sector}</td></tr>
                    <tr><td><strong>Gedetecteerde Activiteiten:</strong></td><td>{detected_categories}</td></tr>
                    <tr><td><strong>Industriële Schaal:</strong></td><td>{industrial_scale}</td></tr>
                    <tr><td><strong>Totaal BREFs Beschikbaar:</strong></td><td>{total_brefs}</td></tr>
                    <tr><td><strong>Van Toepassing:</strong></td><td>{applicable_count} ({coverage_percentage}%)</td></tr>
                    <tr><td><strong>Mogelijk van Toepassing:</strong></td><td>{potentially_applicable_count}</td></tr>
                    <tr><td><strong>Niet van Toepassing:</strong></td><td>{not_applicable_count}</td></tr>
                </table>
            </div>
            
            <h3>✅ Van Toepassing - BREFs/BATs ({applicable_count})</h3>
            <table class="applicability-table applicable">
                <thead>
                    <tr>
                        <th>BREF</th>
                        <th>Titel</th>
                        <th>Type</th>
                        <th>Toepasselijkheid</th>
                        <th>Reden</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """.format(
            primary_sector=analysis["permit_classification"]["primary_sector"],
            detected_categories=", ".join(analysis["permit_classification"]["detected_categories"]),
            industrial_scale=analysis["permit_classification"]["industrial_scale"],
            total_brefs=analysis["analysis_summary"]["total_brefs"],
            applicable_count=analysis["analysis_summary"]["applicable_count"],
            coverage_percentage=analysis["analysis_summary"]["coverage_percentage"],
            potentially_applicable_count=analysis["analysis_summary"]["potentially_applicable_count"],
            not_applicable_count=analysis["analysis_summary"]["not_applicable_count"]
        )
        
        # Applicable BREFs
        for bref in analysis["applicable_brefs"]:
            status_icon = "📋" if bref["downloaded"] else "❌"
            type_icon = "🔄" if bref["type"] == "HORIZONTAAL" else "🏭"
            html += f"""
                    <tr class="applicable-row">
                        <td>{type_icon} <strong>{bref["bref_id"]}</strong></td>
                        <td>{bref["title"]}</td>
                        <td>{bref["type"]}</td>
                        <td>{bref["applicability"]}</td>
                        <td>{"; ".join(bref["reasons"])}</td>
                        <td>{status_icon} {"Beschikbaar" if bref["downloaded"] else "Niet gedownload"}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <h3>⚠️ Mogelijk van Toepassing - BREFs/BATs ({potentially_applicable_count})</h3>
            <table class="applicability-table potential">
                <thead>
                    <tr>
                        <th>BREF</th>
                        <th>Titel</th>
                        <th>Type</th>
                        <th>Toepasselijkheid</th>
                        <th>Reden</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """.format(potentially_applicable_count=analysis["analysis_summary"]["potentially_applicable_count"])
        
        # Potentially applicable BREFs
        for bref in analysis["potentially_applicable_brefs"]:
            status_icon = "📋" if bref["downloaded"] else "❌"
            type_icon = "🔄" if bref["type"] == "HORIZONTAAL" else "🏭"
            html += f"""
                    <tr class="potential-row">
                        <td>{type_icon} {bref["bref_id"]}</td>
                        <td>{bref["title"]}</td>
                        <td>{bref["type"]}</td>
                        <td>{bref["applicability"]}</td>
                        <td>{"; ".join(bref["reasons"])}</td>
                        <td>{status_icon} {"Beschikbaar" if bref["downloaded"] else "Niet gedownload"}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <h3>🏛️ Van Toepassing - RIE Annex I Activiteiten</h3>
            <table class="rie-table">
                <thead>
                    <tr>
                        <th>Categorie</th>
                        <th>Activiteit</th>
                        <th>Drempelwaarde</th>
                        <th>Reden</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # RIE activities
        for rie in analysis["applicable_rie"]:
            html += f"""
                    <tr>
                        <td>{rie["category"]}</td>
                        <td>{rie["description"]}</td>
                        <td>{rie["threshold"]}</td>
                        <td>{rie["reason"]}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <div class="next-steps">
                <h3>🎯 Vervolgstappen</h3>
                <ol>
                    <li><strong>Gedetailleerde BAT Controle:</strong> Voer volledige compliance controle uit voor van toepassing zijnde BREFs</li>
                    <li><strong>RIE Verificatie:</strong> Controleer of activiteiten boven drempelwaarden liggen</li>
                    <li><strong>Ontbrekende BREFs:</strong> Download ontbrekende BREF documenten indien nodig</li>
                    <li><strong>Monitoring:</strong> Implementeer continue monitoring conform EMS BREF</li>
                </ol>
            </div>
        </div>
        
        <style>
        .applicability-analysis { margin: 20px 0; }
        .summary-box { background: #f0f8ff; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .summary-table { width: 100%; border-collapse: collapse; }
        .summary-table td { padding: 5px 10px; border-bottom: 1px solid #ddd; }
        .applicability-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 12px; }
        .applicability-table th, .applicability-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .applicability-table th { background-color: #f2f2f2; font-weight: bold; }
        .applicable-row { background-color: #e8f5e8; }
        .potential-row { background-color: #fff3cd; }
        .rie-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .rie-table th, .rie-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .rie-table th { background-color: #f2f2f2; }
        .next-steps { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        </style>
        """
        
        return html

if __name__ == "__main__":
    # Test with sample permit
    reporter = EnhancedComplianceReporter()
    
    sample_permit = """
    Vergunning voor uitbreiding melkrundveehouderij
    Activiteit: melkveehouderij met 150 melkkoeien
    Installaties: melkstal, koeltanks, mestopslag
    Energiegebruik: stoomketel 30 MW
    Koeling: melkkoeling 50 kW
    """
    
    analysis = reporter.analyze_permit_applicability(sample_permit, {})
    print("✅ Toepasselijkheidsanalyse voltooid!")
    print(f"Van toepassing: {len(analysis['applicable_brefs'])} BREFs")
    print(f"Mogelijk van toepassing: {len(analysis['potentially_applicable_brefs'])} BREFs")