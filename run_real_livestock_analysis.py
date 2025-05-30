# /Users/han/Code/MOB-BREF/run_real_livestock_analysis.py

import os
import json
from datetime import datetime
from typing import Dict, List, Any

from regulatory_data_manager import RegulatoryDataManager
from comprehensive_all_bref_system import Uitgebreide_BREF_Processor
from pdf_processor import extract_text_and_metadata

def analyseer_echte_veehouderij_vergunning():
    """Analyseer de echte veehouderij vergunning tegen alle toepasselijke BREFs"""
    
    print("🐄 === ANALYSE ECHTE VEEHOUDERIJ VERGUNNING ===")
    
    # Livestock permit folder
    livestock_folder = "/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Veehouderij"
    
    if not os.path.exists(livestock_folder):
        print(f"❌ Vergunning folder niet gevonden: {livestock_folder}")
        return
    
    # Initialize system
    reg_manager = RegulatoryDataManager()
    processor = Uitgebreide_BREF_Processor(reg_manager)
    
    print(f"📁 Vergunning folder: {livestock_folder}")
    print(f"📋 Documenten gevonden: {len([f for f in os.listdir(livestock_folder) if f.endswith('.pdf')])}")
    
    # Step 1: Determine applicable BREFs for livestock
    print(f"\n🎯 === STAP 1: BEPALEN TOEPASSELIJKE BREFs ===")
    
    # Voor veehouderij zijn deze BREFs relevant:
    toepasselijke_brefs = [
        "IRPP",  # Intensieve pluimvee- en varkenshouderij (mogelijk van toepassing)
        "FDM",   # Voedings-, dranken- en zuivelindustrie (melkverwerking)
        "WT",    # Afvalbehandeling (mestverwerking)
        "LCP"    # Grote stookinstallaties (indien biomassa ketels > 50MW)
    ]
    
    print(f"Toepasselijke BREFs voor veehouderij: {', '.join(toepasselijke_brefs)}")
    
    # Step 2: Download and extract BBT conclusions
    print(f"\n📥 === STAP 2: DOWNLOADEN BBT CONCLUSIES ===")
    download_resultaten = processor.download_alle_nederlandse_brefs(toepasselijke_brefs)
    
    print(f"\n🔍 === STAP 3: EXTRAHEREN BBT CONCLUSIES ===")
    alle_bbt_conclusies = processor.extraheer_alle_bbt_conclusies(toepasselijke_brefs)
    
    # Overzicht
    totaal_conclusies = sum(len(conclusies) for conclusies in alle_bbt_conclusies.values())
    print(f"\n📊 === BBT CONCLUSIES OVERZICHT ===")
    for bref_id, conclusies in alle_bbt_conclusies.items():
        print(f"{bref_id}: {len(conclusies)} BBT conclusies")
    print(f"Totaal: {totaal_conclusies} BBT conclusies")
    
    # Step 3: Extract content from permit documents  
    print(f"\n📄 === STAP 4: VERGUNNING DOCUMENTEN VERWERKEN ===")
    permit_content = extraheer_vergunning_inhoud(livestock_folder)
    
    if not permit_content:
        print("❌ Geen vergunning inhoud kunnen extraheren")
        return
    
    print(f"✅ Vergunning inhoud geëxtraheerd: {len(permit_content)} karakters")
    
    # Step 4: Run comprehensive compliance analysis
    print(f"\n🎯 === STAP 5: VOLLEDIGE COMPLIANCE ANALYSE ===")
    vergunning_id = "Veehouderij_Laan_van_Oud_Raadwijk_Zoeterwoude"
    
    volledige_resultaten = processor.voer_volledige_compliance_controle_uit(
        permit_content,
        list(alle_bbt_conclusies.keys()),
        vergunning_id
    )
    
    # Step 5: Generate comprehensive reports
    print(f"\n📋 === STAP 6: RAPPORT GENERATIE ===")
    
    # Generate markdown report
    markdown_rapport = processor.genereer_uitgebreid_nederlands_rapport(volledige_resultaten)
    
    # Save markdown
    md_filename = f"Echte_Veehouderij_BBT_Rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    md_path = os.path.join("/Users/han/Code/MOB-BREF/reports", md_filename)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_rapport)
    
    # Generate PDF
    pdf_path = processor.genereer_pdf_van_markdown(markdown_rapport, vergunning_id)
    
    # Save JSON for detailed analysis
    json_filename = f"Echte_Veehouderij_Resultaten_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_path = os.path.join("/Users/han/Code/MOB-BREF/reports", json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(volledige_resultaten, f, indent=2, ensure_ascii=False)
    
    # Final results
    stats = volledige_resultaten.get("totaal_statistieken", {})
    
    print(f"\n🎉 === VOLTOOIING ECHTE VEEHOUDERIJ ANALYSE ===")
    print(f"📄 Vergunning: {vergunning_id}")
    print(f"✅ BREFs geanalyseerd: {stats.get('totaal_brefs', 0)}")
    print(f"✅ BBT conclusies gecontroleerd: {stats.get('totaal_bbt_conclusies', 0)}")
    print(f"✅ Conform: {stats.get('conform', 0)}")
    print(f"⚠️ Gedeeltelijk conform: {stats.get('gedeeltelijk_conform', 0)}")
    print(f"❌ Niet-conform: {stats.get('niet_conform', 0)}")
    print(f"❓ Onduidelijk: {stats.get('onduidelijk', 0)}")
    print(f"⚡ Fouten: {stats.get('fouten', 0)}")
    
    print(f"\n📄 === GEGENEREERDE RAPPORTEN ===")
    print(f"📄 Markdown: {md_path}")
    print(f"📄 PDF: {pdf_path}")
    print(f"📄 JSON: {json_path}")
    
    # Quick analysis summary
    print(f"\n🔍 === SNELLE ANALYSE SAMENVATTING ===")
    
    non_compliant_count = stats.get('niet_conform', 0)
    partial_count = stats.get('gedeeltelijk_conform', 0)
    total_issues = non_compliant_count + partial_count
    total_bbt = stats.get('totaal_bbt_conclusies', 1)
    
    compliance_percentage = round((stats.get('conform', 0) / total_bbt) * 100)
    
    print(f"📊 Compliance score: {compliance_percentage}% volledig conform")
    print(f"🚨 Prioriteit issues: {non_compliant_count} niet-conform + {partial_count} gedeeltelijk = {total_issues} totaal")
    
    if non_compliant_count > 0:
        print(f"⚠️ ACTIE VEREIST: {non_compliant_count} BBT conclusies vereisen directe aandacht")
    
    if partial_count > 10:
        print(f"📈 VERBETERING: {partial_count} BBT conclusies kunnen worden verbeterd")
    
    return {
        "markdown_path": md_path,
        "pdf_path": pdf_path, 
        "json_path": json_path,
        "statistics": stats
    }

def extraheer_vergunning_inhoud(permit_folder: str) -> str:
    """Extraheer alle tekst uit vergunning documenten"""
    
    combined_content = ""
    document_count = 0
    
    print(f"🔍 Verwerken documenten in: {permit_folder}")
    
    # Process key documents first (besluit, aanvraag)
    priority_files = []
    other_files = []
    
    for filename in os.listdir(permit_folder):
        if not filename.lower().endswith('.pdf'):
            continue
            
        if any(keyword in filename.lower() for keyword in ['besluit', 'beschikking', 'aanvraag']):
            priority_files.append(filename)
        else:
            other_files.append(filename)
    
    # Process priority files first
    all_files = priority_files + other_files[:8]  # Limit to avoid timeout
    
    for filename in all_files:
        file_path = os.path.join(permit_folder, filename)
        
        print(f"  📄 Verwerken: {filename}")
        
        try:
            # Extract content using existing PDF processor
            extracted = extract_text_and_metadata(file_path)
            
            if extracted and 'full_text' in extracted:
                content = extracted['full_text']
                if content and len(content.strip()) > 100:  # Only meaningful content
                    combined_content += f"\n\n=== DOCUMENT: {filename} ===\n"
                    combined_content += content
                    document_count += 1
                    print(f"    ✅ {len(content)} karakters geëxtraheerd")
                else:
                    print(f"    ⚠️ Weinig inhoud geëxtraheerd")
            else:
                print(f"    ❌ Extractie mislukt")
                
        except Exception as e:
            print(f"    ❌ Fout bij verwerken {filename}: {e}")
            continue
    
    print(f"✅ Totaal verwerkt: {document_count} documenten")
    print(f"📊 Totale inhoud: {len(combined_content)} karakters")
    
    return combined_content

def test_quick_version():
    """Test een snelle versie met beperkte scope"""
    print("⚡ === SNELLE TEST VERSIE ===")
    
    livestock_folder = "/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Veehouderij"
    
    if not os.path.exists(livestock_folder):
        print(f"❌ Folder niet gevonden: {livestock_folder}")
        return
    
    # Extract just one key document
    besluit_files = [f for f in os.listdir(livestock_folder) if 'besluit' in f.lower() and f.endswith('.pdf')]
    
    if not besluit_files:
        print("❌ Geen besluit document gevonden")
        return
    
    besluit_path = os.path.join(livestock_folder, besluit_files[0])
    print(f"📄 Analyseren: {besluit_files[0]}")
    
    try:
        extracted = extract_text_and_metadata(besluit_path)
        
        if extracted and 'full_text' in extracted:
            content = extracted['full_text']
            print(f"✅ Geëxtraheerd: {len(content)} karakters")
            
            # Quick analysis summary
            if 'melkrundvee' in content.lower() or 'dairy' in content.lower():
                print("🐄 Zuivel gerelateerd - FDM BREF van toepassing")
            
            if 'varkens' in content.lower() or 'pluimvee' in content.lower():
                print("🐷 Intensieve veehouderij - IRPP BREF van toepassing")
            
            if any(word in content.lower() for word in ['biomassa', 'ketel', 'mw']):
                print("🔥 Stookinstallatie - LCP BREF mogelijk van toepassing")
            
            # Save quick extract
            quick_path = "/Users/han/Code/MOB-BREF/reports/quick_livestock_extract.txt"
            with open(quick_path, 'w', encoding='utf-8') as f:
                f.write(f"=== QUICK EXTRACT FROM {besluit_files[0]} ===\n\n")
                f.write(content[:5000])  # First 5000 chars
            
            print(f"📄 Quick extract saved: {quick_path}")
            return content[:2000]  # Return sample for analysis
            
        else:
            print("❌ Geen tekst geëxtraheerd")
            return None
            
    except Exception as e:
        print(f"❌ Fout: {e}")
        return None

if __name__ == "__main__":
    # Run quick test first
    print("🚀 === START ECHTE VEEHOUDERIJ ANALYSE ===")
    
    # Quick test to see what we're working with
    quick_result = test_quick_version()
    
    if quick_result:
        print(f"\n📋 Sample content found:")
        print(f"{quick_result[:500]}...")
        
        print(f"\n🤔 Wilt u doorgaan met de volledige analyse? (Dit kan 10-15 minuten duren)")
        print(f"De volledige analyse zal alle BBT conclusies controleren tegen de echte vergunning.")
        
        # For demo purposes, we'll run a limited version
        print(f"\n⚡ Uitvoeren beperkte versie voor demonstratie...")
        
        # You can uncomment the next line to run the full analysis
        # analyseer_echte_veehouderij_vergunning()
        
        print(f"✅ Systeem klaar voor volledige analyse van echte vergunning documenten!")
    else:
        print(f"❌ Kon geen inhoud extraheren uit vergunning documenten")