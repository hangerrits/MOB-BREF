# /Users/han/Code/MOB-BREF/run_focused_livestock_analysis.py

import os
import json
from datetime import datetime

from regulatory_data_manager import RegulatoryDataManager
from dutch_compliance_system import Nederlandse_BREF_Processor

def run_focused_dairy_analysis():
    """Run focused analysis on the real dairy farm permit"""
    
    print("🐄 === GERICHTE ANALYSE MELKRUNDVEEHOUDERIJ ZOETERWOUDE ===")
    
    # Real permit info extracted
    permit_info = {
        "vergunning_id": "Melkrundveehouderij_Laan_van_Oud_Raadwijk_Zoeterwoude",
        "zaaknummer": "00618806",
        "kenmerk": "ODH673696", 
        "datum": "04-07-2023",
        "type": "Wet natuurbescherming - Natura 2000-gebieden",
        "activiteit": "Uitbreiden van een bestaande melkrundveehouderij",
        "locatie": "Laan van Oud Raadwijk 6 - 8 te Zoeterwoude"
    }
    
    print(f"📋 Vergunning Details:")
    for key, value in permit_info.items():
        print(f"  {key}: {value}")
    
    # Load the extracted permit content
    permit_content_path = "/Users/han/Code/MOB-BREF/reports/quick_livestock_extract.txt"
    
    with open(permit_content_path, 'r', encoding='utf-8') as f:
        permit_content = f.read()
    
    print(f"✅ Vergunning inhoud geladen: {len(permit_content)} karakters")
    
    # Determine applicable BREFs for dairy farming
    print(f"\n🎯 === BEPALEN TOEPASSELIJKE BREFs VOOR MELKVEEHOUDERIJ ===")
    
    applicable_brefs = {
        "FDM": {
            "reden": "Melkverwerking en zuivelproductie (indien op locatie)",
            "prioriteit": "Medium",
            "toepasselijk": "Mogelijk - afhankelijk van verwerkingsactiviteiten"
        },
        "IRPP": {
            "reden": "Intensieve veehouderij - controleren tegen drempelwaarden",
            "prioriteit": "Hoog", 
            "toepasselijk": "Waarschijnlijk niet - IRPP betreft pluimvee/varkens, niet rundvee"
        },
        "WT": {
            "reden": "Mestverwerking en afvalwaterbehandeling", 
            "prioriteit": "Medium",
            "toepasselijk": "Mogelijk - afhankelijk van mestverwerking"
        },
        "LCP": {
            "reden": "Biomassa ketels of stookinstallaties > 50 MW",
            "prioriteit": "Laag",
            "toepasselijk": "Onwaarschijnlijk - melkveebedrijven hebben meestal kleinere installaties"
        }
    }
    
    for bref_id, info in applicable_brefs.items():
        print(f"  {bref_id}: {info['toepasselijk']} - {info['reden']}")
    
    # Initialize system  
    reg_manager = RegulatoryDataManager()
    processor = Nederlandse_BREF_Processor(reg_manager)
    
    # Focus on most relevant BREF: FDM (if dairy processing) and check IRPP relevance
    print(f"\n📥 === DOWNLOADEN RELEVANTE BBT CONCLUSIES ===")
    
    primary_brefs = ["FDM", "IRPP"]  # Start with these two
    
    download_results = {}
    for bref_id in primary_brefs:
        try:
            success = processor.download_nederlandse_bbt_conclusies(bref_id)
            download_results[bref_id] = success
            print(f"  {bref_id}: {'✅ Succesvol' if success else '❌ Mislukt'}")
        except Exception as e:
            print(f"  {bref_id}: ❌ Fout - {e}")
            download_results[bref_id] = False
    
    # Extract BBT conclusions
    print(f"\n🔍 === EXTRAHEREN BBT CONCLUSIES ===")
    
    extracted_bbts = {}
    for bref_id in primary_brefs:
        if download_results.get(bref_id, False):
            try:
                bbts = processor.extraheer_nederlandse_bbt_conclusies(bref_id)
                extracted_bbts[bref_id] = bbts
                print(f"  {bref_id}: {len(bbts)} BBT conclusies geëxtraheerd")
            except Exception as e:
                print(f"  {bref_id}: ❌ Extractie fout - {e}")
                extracted_bbts[bref_id] = []
    
    # Run compliance analysis for the most relevant BREF
    print(f"\n🎯 === COMPLIANCE ANALYSE ===")
    
    all_results = {}
    
    for bref_id, bbts in extracted_bbts.items():
        if not bbts:
            continue
            
        print(f"\nAnalyseren {bref_id} ({len(bbts)} BBT conclusies)...")
        
        # Run compliance check
        try:
            compliance_results = processor.nederlandse_bbt_compliance_controle(permit_content, bref_id)
            all_results[bref_id] = {
                "bref_info": processor.nederlandse_bref_urls.get(bref_id, {}),
                "bbt_count": len(bbts),
                "compliance_results": compliance_results
            }
            
            # Quick stats
            conform = len([r for r in compliance_results if r.get('compliance_status') == 'Conform'])
            gedeeltelijk = len([r for r in compliance_results if r.get('compliance_status') == 'Gedeeltelijk Conform'])
            niet_conform = len([r for r in compliance_results if r.get('compliance_status') == 'Niet-Conform'])
            
            print(f"  ✅ Conform: {conform}")
            print(f"  ⚠️ Gedeeltelijk: {gedeeltelijk}")
            print(f"  ❌ Niet-conform: {niet_conform}")
            
        except Exception as e:
            print(f"  ❌ Analyse fout voor {bref_id}: {e}")
    
    # Generate focused report
    print(f"\n📋 === RAPPORT GENERATIE ===")
    
    focused_report = generate_focused_dairy_report(permit_info, all_results)
    
    # Save report
    report_filename = f"Echte_Melkveehouderij_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join("/Users/han/Code/MOB-BREF/reports", report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(focused_report)
    
    # Generate PDF
    try:
        pdf_path = generate_pdf_from_markdown(focused_report, report_filename.replace('.md', '.pdf'))
        print(f"📄 PDF rapport: {pdf_path}")
    except Exception as e:
        print(f"⚠️ PDF generatie fout: {e}")
        pdf_path = None
    
    print(f"📄 Markdown rapport: {report_path}")
    
    # Summary
    total_bbts = sum(len(result.get('compliance_results', [])) for result in all_results.values())
    
    print(f"\n🎉 === SAMENVATTING ECHTE MELKVEEBEDRIJF ===")
    print(f"🐄 Bedrijf: Melkrundveehouderij Zoeterwoude")
    print(f"📋 Vergunning: {permit_info['zaaknummer']}")
    print(f"✅ BREFs geanalyseerd: {len(all_results)}")
    print(f"✅ BBT conclusies gecontroleerd: {total_bbts}")
    print(f"📄 Rapport gegenereerd: {report_path}")
    
    return {
        "permit_info": permit_info,
        "results": all_results,
        "report_path": report_path,
        "pdf_path": pdf_path
    }

def generate_focused_dairy_report(permit_info: dict, analysis_results: dict) -> str:
    """Generate focused report for dairy farm"""
    
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    report = f"""# 🐄 BBT Compliance Rapport - Melkrundveehouderij Zoeterwoude

**Vergunning ID:** {permit_info['vergunning_id']}  
**Zaaknummer:** {permit_info['zaaknummer']}  
**Kenmerk:** {permit_info['kenmerk']}  
**Datum Besluit:** {permit_info['datum']}  
**Type Vergunning:** {permit_info['type']}  
**Gegenereerd op:** {timestamp}  

## 📋 Project Beschrijving

**Activiteit:** {permit_info['activiteit']}  
**Locatie:** {permit_info['locatie']}  

Dit betreft een **Wet natuurbescherming** vergunning voor de uitbreiding van een bestaande melkrundveehouderij. De analyse richt zich op de toepasselijke BBT conclusies voor deze specifieke activiteit.

## 🎯 BREF Toepasselijkheid

### Voor Melkrundveehouderij Relevante BREFs:

**FDM (Voedings-, dranken- en zuivelindustrie):**
- ✅ Mogelijk van toepassing indien melkverwerking op locatie plaatsvindt
- 🔍 Relevant voor zuivelproductie en voedselverwerking

**IRPP (Intensieve pluimvee- en varkenshouderij):**
- ❌ Waarschijnlijk niet van toepassing - betreft specifiek pluimvee en varkens
- 📋 Rundveehouderij valt buiten de scope van IRPP BREF

**WT (Afvalbehandeling):**
- ⚠️ Mogelijk relevant voor mestverwerking en afvalwaterbehandeling

**LCP (Grote stookinstallaties):**
- ❓ Alleen van toepassing bij stookinstallaties > 50 MW thermisch vermogen

---

"""
    
    # Add detailed results for each analyzed BREF
    total_conform = 0
    total_gedeeltelijk = 0
    total_niet_conform = 0
    total_bbts = 0
    
    for bref_id, result in analysis_results.items():
        bref_info = result.get('bref_info', {})
        compliance_results = result.get('compliance_results', [])
        
        # Calculate stats
        conform = len([r for r in compliance_results if r.get('compliance_status') == 'Conform'])
        gedeeltelijk = len([r for r in compliance_results if r.get('compliance_status') == 'Gedeeltelijk Conform'])
        niet_conform = len([r for r in compliance_results if r.get('compliance_status') == 'Niet-Conform'])
        
        total_conform += conform
        total_gedeeltelijk += gedeeltelijk
        total_niet_conform += niet_conform
        total_bbts += len(compliance_results)
        
        report += f"""## 🏗️ {bref_id}: {bref_info.get('titel', 'Onbekende BREF')}

**Sector:** {bref_info.get('sector', 'N/A')}  
**BBT Conclusies Geanalyseerd:** {len(compliance_results)}  

### Compliance Samenvatting {bref_id}:
- ✅ **Conform:** {conform}
- ⚠️ **Gedeeltelijk Conform:** {gedeeltelijk}
- ❌ **Niet-Conform:** {niet_conform}

"""
        
        # Show key findings
        if compliance_results:
            report += f"### Belangrijkste Bevindingen {bref_id}:\n\n"
            
            # Show first few results as examples
            for i, result_item in enumerate(compliance_results[:5], 1):
                bbt_nummer = result_item.get('bbt_nummer', 'N/A')
                titel = result_item.get('bbt_titel', 'Geen titel')
                status = result_item.get('compliance_status', 'Onbekend')
                bevindingen = result_item.get('detailed_findings', 'Geen bevindingen')
                
                status_icon = {
                    'Conform': '✅',
                    'Gedeeltelijk Conform': '⚠️',
                    'Niet-Conform': '❌'
                }.get(status, '❓')
                
                report += f"""#### {status_icon} BBT {bbt_nummer}: {titel[:60]}{"..." if len(titel) > 60 else ""}

**Status:** {status}  
**Bevindingen:** {bevindingen[:200]}{"..." if len(bevindingen) > 200 else ""}

"""
            
            if len(compliance_results) > 5:
                report += f"*... en {len(compliance_results) - 5} andere BBT conclusies*\n\n"
        
        report += "---\n\n"
    
    # Overall summary
    report += f"""## 📊 Totaal Samenvatting

**Alle Geanalyseerde BBT Conclusies:** {total_bbts}  
- ✅ **Conform:** {total_conform} ({round(total_conform/max(total_bbts,1)*100)}%)  
- ⚠️ **Gedeeltelijk Conform:** {total_gedeeltelijk} ({round(total_gedeeltelijk/max(total_bbts,1)*100)}%)  
- ❌ **Niet-Conform:** {total_niet_conform} ({round(total_niet_conform/max(total_bbts,1)*100)}%)  

## 🎯 Aanbevelingen voor Melkrundveehouderij

### Prioriteit Acties:
"""
    
    if total_niet_conform > 0:
        report += f"1. **HOGE PRIORITEIT:** {total_niet_conform} niet-conforme BBT conclusies vereisen directe aandacht\n"
    
    if total_gedeeltelijk > 0:
        report += f"2. **MEDIUM PRIORITEIT:** {total_gedeeltelijk} gedeeltelijk conforme BBT conclusies kunnen worden verbeterd\n"
    
    report += f"""
### Melkveehouderij Specifieke Aanbevelingen:
1. **Mestmanagement:** Zorg voor adequate mestopslag en -behandeling conform BBT
2. **Ammoniakemissies:** Implementeer emissiearme technieken voor stallen
3. **Energiegebruik:** Overweeg energie-efficiënte systemen voor melkwinning en koeling
4. **Afvalwater:** Behandel melkstal afvalwater conform BBT vereisten
5. **Monitoring:** Implementeer continue monitoring van relevante parameters

### Vervolgstappen:
1. **Gedetailleerde review** van niet-conforme BBT conclusies
2. **Implementatieplan** voor verbeteringen
3. **Monitoring programma** voor compliance tracking
4. **Jaarlijkse hervalidatie** van BBT compliance

---

## 📞 Projectinformatie

**Melkrundveehouderij:** Laan van Oud Raadwijk 6-8, Zoeterwoude  
**Omgevingsdienst:** Haaglanden  
**Contact:** ing. L. Hopman, Hoofd Toetsing & Vergunningverlening Milieu  

---

*Rapport gegenereerd op {timestamp} voor echte melkrundveehouderij vergunning {permit_info['zaaknummer']}*
"""
    
    return report

def generate_pdf_from_markdown(markdown_content: str, pdf_filename: str) -> str:
    """Generate PDF from markdown content"""
    try:
        import markdown2
        from weasyprint import HTML as WeasyHTML
        from weasyprint.text.fonts import FontConfiguration
        
        html_content = markdown2.markdown(markdown_content, extras=["tables", "fenced-code-blocks"])
        
        css_style = """
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial, sans-serif; line-height: 1.5; font-size: 10pt; }
        h1 { font-size: 18pt; color: #1a365d; border-bottom: 2px solid #3182ce; }
        h2 { font-size: 14pt; color: #2d3748; margin-top: 20px; }
        h3 { font-size: 12pt; color: #4a5568; }
        """
        
        full_html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><style>{css_style}</style></head>
        <body>{html_content}</body></html>
        """
        
        pdf_path = os.path.join("/Users/han/Code/MOB-BREF/reports", pdf_filename)
        font_config = FontConfiguration()
        html_doc = WeasyHTML(string=full_html)
        html_doc.write_pdf(pdf_path, font_config=font_config)
        
        return pdf_path
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None

if __name__ == "__main__":
    run_focused_dairy_analysis()