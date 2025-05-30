#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/demo_complete_system.py

"""
Demo Complete Compliance System
Met sample melkveevergunning text voor demonstratie
"""

import os
from complete_compliance_system import CompleteComplianceSystem

def demo_with_sample_text():
    """Demo met sample melkveevergunning tekst"""
    
    # Sample melkveevergunning tekst (gebaseerd op Zoeterwoude case)
    sample_permit_text = """
    OMGEVINGSDIENST HAAGLANDEN
    
    BESCHIKKING
    Wet natuurbescherming - Natura 2000-gebieden
    
    Zaaknummer: 00618806
    Kenmerk: ODH673696
    Datum besluit: 04-07-2023
    
    BESCHIKKING UITBREIDING MELKRUNDVEEHOUDERIJ
    
    Aanvrager: [Naam]
    Locatie: Laan van Oud Raadwijk 6-8 te Zoeterwoude
    
    BESCHRIJVING ACTIVITEIT:
    
    Het betreft een uitbreiding van een bestaande melkrundveehouderij met de volgende kenmerken:
    
    - Huisvesting van maximaal 150 melkkoeien
    - Melkstal met moderne melkrobot systemen
    - Koeltanks voor melkopslag met een capaciteit van 20.000 liter
    - Mestopslag in dichte mestkelder onder de stal
    - Energievoorziening via stoomketel van 25 MW thermisch vermogen
    - Koelsysteem voor melkkoeling met vermogen van 75 kW
    - Afvalwaterbehandeling van melkstal afvalwater
    - Dieseltank van 5.000 liter voor noodaggregaat
    
    VOORSCHRIFTEN:
    
    1. GELUIDSBEHEER
    - Het opstellen van een geluidsbeheerplan zoals vereist
    - Geluidsarme apparatuur voor melkwinning en voerbehandeling
    - Onderhoudswerkzaamheden alleen tussen 07:00-19:00 uur
    
    2. MILIEUBELEID
    - Opstellen van milieubeleid inclusief structuur en verantwoordelijkheid
    - Registratie van milieugegevens conform voorschriften
    - Jaarlijkse evaluatie van milieuprestaties
    
    3. MESTBEHEER
    - Maximaal 2.800 m³ drijfmest opslag in mestkelder
    - Afdekken van mestopslagplaats ter voorkoming van geuremissies
    - Locatie mestopslag rekening houdend met windrichting
    
    4. AFVALWATERBEHANDELING
    - Passende bufferopslagcapaciteit voor afvalwater
    - Gescheiden afvoer van melkstal afvalwater
    - Voorkoming van verontreiniging oppervlaktewater
    
    5. DIERAANTALLEN
    - Maximaal 150 melkkoeien (grootvee-eenheden)
    - Registratie van dieraantallen conform I&R regelgeving
    - Meldingsplicht bij overschrijding toegestane aantallen
    
    6. ENERGIE EN KOELING
    - Energieregistratie van stoomketel en koelsystemen
    - Onderhoud koelinstallaties conform onderhoudsschema
    - Lekdetectie voor koelvloeistoffen
    
    7. EMISSIEBEPERKING
    - Toepassing van emissiearme technieken voor stallen
    - Monitoring van ammoniakemissies
    - Registratie van emissiegegevens
    
    8. MONITORING EN RAPPORTAGE
    - Continue monitoring van relevante parameters
    - Jaarrapportage over milieuprestaties aan bevoegd gezag
    - Registratie van incidenten en maatregelen
    
    OVERIGE BEPALINGEN:
    
    - De vergunning is geldig voor onbepaalde tijd
    - Voorschriften treden in werking vanaf datum beschikking
    - Controle en handhaving door Omgevingsdienst Haaglanden
    
    Deze beschikking bevat een beoordeling van:
    - Natura 2000 effecten (stikstofdepositie)
    - Milieueffecten (emissies naar lucht, water, bodem)
    - Dierenwelzijn en huisvesting
    - Energiegebruik en -efficiëntie
    
    TECHNISCHE SPECIFICATIES:
    
    Melkwinning:
    - 2x12 melkrobot DeLaval VMS V300
    - Melkleiding roestvrijstaal met automatische reiniging
    - Koeltanks geïsoleerd met glycol koeling
    
    Ventilatie:
    - Natuurlijke ventilatie met windbreken
    - Mechanische ventilatie voor melkstal
    - Emissiearme technieken voor stalventilatie
    
    Voerbehandeling:
    - Voermengwagen voor ruwvoer distributie
    - Krachtvoerautomaten gekoppeld aan melkrobots
    - Opslagloods voor voer en strooisel
    
    Utilities:
    - Elektriciteitsaansluiting 3x400V
    - Wateraansluiting via gemeentelijke leiding
    - Telefoon/internet voor monitoring systemen
    """
    
    print("🎯 === DEMO COMPLETE COMPLIANCE SYSTEM ===")
    print("Testing met sample melkveevergunning tekst\n")
    
    # Create temporary file with sample text
    temp_file = "/tmp/sample_permit.txt"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(sample_permit_text)
    
    # Initialize system
    system = CompleteComplianceSystem()
    
    # Mock the PDF extraction to use our sample text
    def mock_extract_text_and_metadata(pdf_path):
        return {
            'full_text': sample_permit_text,
            'title': 'Melkveevergunning Zoeterwoude',
            'pages': [{'page_number': 1, 'text': sample_permit_text}]
        }
    
    # Replace the extraction function temporarily
    original_extract = system.analyze_complete_permit.__globals__['extract_text_and_metadata']
    system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = mock_extract_text_and_metadata
    
    try:
        # Run analysis
        results = system.analyze_complete_permit(temp_file, output_dir="demo_reports")
        
        print(f"\n🎉 === DEMO RESULTATEN ===")
        
        if "applicability_analysis" in results:
            analysis = results["applicability_analysis"]
            print(f"📊 Toepasselijkheidsanalyse:")
            print(f"  - Primaire sector: {analysis['permit_classification']['primary_sector']}")
            print(f"  - Van toepassing: {len(analysis['applicable_brefs'])} BREFs")
            print(f"  - Mogelijk toepassing: {len(analysis['potentially_applicable_brefs'])} BREFs")
            print(f"  - RIE activiteiten: {len(analysis['applicable_rie'])}")
            
            print(f"\n✅ Van toepassing zijnde BREFs:")
            for bref in analysis['applicable_brefs']:
                status = "📋 Beschikbaar" if bref['downloaded'] else "❌ Niet gedownload"
                print(f"  🔄 {bref['bref_id']}: {bref['title']} ({status})")
        
        if "detailed_bat_results" in results:
            detailed = results["detailed_bat_results"]
            print(f"\n🔬 Gedetailleerde BAT Analyse:")
            for bref_id, result in detailed.items():
                if isinstance(result, dict) and "total_conclusions" in result:
                    print(f"  📋 {bref_id}: {result['total_conclusions']} BBT conclusies gecontroleerd")
        
        if "report_files" in results:
            files = results["report_files"]
            print(f"\n📄 Gegenereerde rapporten:")
            if files.get("html_path"):
                print(f"  📝 HTML: {files['html_path']}")
            if files.get("pdf_path"):
                print(f"  📄 PDF: {files['pdf_path']}")
        
        return results
        
    finally:
        # Restore original function
        system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = original_extract
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    demo_with_sample_text()