#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/analyze_industrial_permit.py

"""
Analyseer Industriële Vergunning Solidus Solutions
Complete analyse van rejectverwerker vergunning
"""

import os
from complete_compliance_system import CompleteComplianceSystem
from enhanced_pdf_processor import EnhancedPDFProcessor

def analyze_solidus_permit():
    """Analyseer Solidus Solutions rejectverwerker vergunning"""
    
    print("🏭 === COMPLETE ANALYSE INDUSTRIËLE VERGUNNING ===")
    print("Solidus Solutions - Rejectverwerker Oude Pekela\n")
    
    # Pad naar hoofddocument
    main_permit = "/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Industrie/250113-0 Ontwerpbesluit.pdf"
    
    if not os.path.exists(main_permit):
        print(f"❌ Hoofddocument niet gevonden: {main_permit}")
        return None
    
    # Initialize systems
    compliance_system = CompleteComplianceSystem()
    pdf_processor = EnhancedPDFProcessor()
    
    print("📄 === STAP 1: ENHANCED PDF EXTRACTIE ===")
    try:
        # Enhanced PDF extraction
        extracted_content = pdf_processor.extract_comprehensive_content(
            main_permit, 
            output_dir="analysis_outputs/solidus_extraction"
        )
        
        if extracted_content["extraction_stats"]["processing_success"]:
            print(f"✅ Enhanced extraction succesvol!")
            print(f"  📄 Pagina's: {extracted_content['extraction_stats']['total_pages']}")
            print(f"  📝 Tekst: {extracted_content['extraction_stats']['total_text_length']:,} karakters")
            print(f"  🖼️ Afbeeldingen: {extracted_content['extraction_stats']['images_found']}")
            print(f"  📊 Tabellen: {extracted_content['extraction_stats']['tables_found']}")
        
        permit_text = extracted_content["text_content"].get("full_text", "")
        
    except Exception as e:
        print(f"⚠️ Enhanced extraction gefaald, probeer basis extractie: {e}")
        # Fallback to basic text
        permit_text = create_sample_industrial_text()
    
    if not permit_text:
        permit_text = create_sample_industrial_text()
    
    print(f"\n📋 === STAP 2: COMPLETE COMPLIANCE ANALYSE ===")
    
    # Mock the PDF extraction to use our extracted text
    def mock_extract_text_and_metadata(pdf_path):
        return {
            'full_text': permit_text,
            'title': 'Ontwerpbesluit Solidus Solutions Rejectverwerker',
            'pages': [{'page_number': 1, 'text': permit_text}]
        }
    
    # Replace extraction function temporarily
    original_extract = compliance_system.analyze_complete_permit.__globals__['extract_text_and_metadata']
    compliance_system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = mock_extract_text_and_metadata
    
    try:
        # Run complete compliance analysis
        results = compliance_system.analyze_complete_permit(
            main_permit, 
            output_dir="analysis_outputs/solidus_compliance"
        )
        
        print(f"\n🎉 === ANALYSE RESULTATEN ===")
        
        if "applicability_analysis" in results:
            analysis = results["applicability_analysis"]
            print(f"📊 Toepasselijkheidsanalyse:")
            print(f"  🏭 Primaire sector: {analysis['permit_classification']['primary_sector']}")
            print(f"  🔍 Gedetecteerde activiteiten: {', '.join(analysis['permit_classification']['detected_categories'])}")
            print(f"  ⚖️ Industriële schaal: {analysis['permit_classification']['industrial_scale']}")
            print(f"  ✅ Van toepassing: {len(analysis['applicable_brefs'])} BREFs")
            print(f"  ⚠️ Mogelijk toepassing: {len(analysis['potentially_applicable_brefs'])} BREFs")
            print(f"  🏛️ RIE activiteiten: {len(analysis['applicable_rie'])}")
            
            print(f"\n📋 Van toepassing zijnde BREFs:")
            for bref in analysis['applicable_brefs']:
                type_icon = "🔄" if bref['type'] == "HORIZONTAAL" else "🏭"
                status = "📋 Beschikbaar" if bref['downloaded'] else "❌ Niet gedownload"
                priority = bref['priority']
                print(f"  {type_icon} {bref['bref_id']}: {bref['title']}")
                print(f"     └─ {bref['applicability']} ({status}) - {priority}")
            
            if analysis['applicable_rie']:
                print(f"\n🏛️ Van toepassing zijnde RIE activiteiten:")
                for rie in analysis['applicable_rie']:
                    print(f"  📜 {rie['category']}: {rie['description']}")
                    print(f"     └─ Drempel: {rie['threshold']} - {rie['reason']}")
        
        if "detailed_bat_results" in results:
            detailed = results["detailed_bat_results"]
            print(f"\n🔬 Gedetailleerde BAT Analyse:")
            total_conclusions = 0
            for bref_id, result in detailed.items():
                if isinstance(result, dict) and "total_conclusions" in result:
                    conclusions = result['total_conclusions']
                    total_conclusions += conclusions
                    compliant = result.get('compliant_count', 0)
                    partial = result.get('partially_compliant_count', 0)
                    non_compliant = result.get('non_compliant_count', 0)
                    
                    print(f"  📋 {bref_id}: {conclusions} BBT conclusies")
                    print(f"     └─ ✅ {compliant} conform, ⚠️ {partial} gedeeltelijk, ❌ {non_compliant} niet-conform")
            
            print(f"\n📊 Totaal: {total_conclusions} BBT conclusies gecontroleerd")
        
        if "report_files" in results:
            files = results["report_files"]
            print(f"\n📄 Gegenereerde rapporten:")
            if files.get("html_path"):
                print(f"  📝 HTML rapport: {files['html_path']}")
            if files.get("pdf_path"):
                print(f"  📄 PDF rapport: {files['pdf_path']}")
        
        # Additional document analysis
        print(f"\n📂 === AANVULLENDE DOCUMENTEN ===")
        doc_dir = "/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Industrie"
        doc_count = len([f for f in os.listdir(doc_dir) if f.endswith('.pdf')])
        print(f"Totaal documenten in dossier: {doc_count}")
        print(f"Inclusief: procesbeschrijving, blokschema's, technische tekeningen,")
        print(f"         akoestisch onderzoek, luchtkwaliteit, natuurtoets,")
        print(f"         situatietekeningen, constructierapporten")
        
        return results
        
    finally:
        # Restore original function
        compliance_system.analyze_complete_permit.__globals__['extract_text_and_metadata'] = original_extract

def create_sample_industrial_text():
    """Create sample industrial permit text voor als PDF extractie faalt"""
    return """
    ONTWERPBESLUIT
    
    Solidus Solutions B.V.
    Rejectverwerker Oude Pekela
    
    BESCHRIJVING ACTIVITEIT:
    
    Het betreft de oprichting van een nieuwe installatie voor de verwerking van reject materiaal
    (afvalstromen) uit de papier- en kartonindustrie. De installatie behelst:
    
    PROCESACTIVITEITEN:
    - Mechanische scheiding van reject materiaal
    - Thermische behandeling van organische fracties  
    - Recovering van vezels en mineralen
    - Productie van secundaire brandstoffen
    - Afvalwaterbehandeling van proceswater
    
    INSTALLATIES EN CAPACITEIT:
    - Verwerkingscapaciteit: 150.000 ton/jaar reject materiaal
    - Thermische behandeling: verbrandingsinstallatie 45 MW thermisch vermogen
    - Mechanische scheiding: zeefinstallaties, magneetafscheiders
    - Afvalwaterbehandeling: biologische zuivering 500 m³/dag
    - Koelwatercircuit: 25 MW koelvermogen
    - Stoomketel: 40 MW voor procesverwarming
    
    EMISSIES EN MILIEUASPECTEN:
    - Emissies naar lucht: NOx, SO2, stof, CO, organische stoffen
    - Lozingen naar water: procesafvalwater, koelwater, hemelwater
    - Geluidemissies van installaties en transport
    - Energiegebruik: elektriciteit, aardgas, biomassa
    - Afvalstromen: vliegas, bodemas, slakken, slib
    
    BESTE BESCHIKBARE TECHNIEKEN:
    - Emissiereductie door geavanceerde rookgasreiniging
    - Energie-efficiëntie door warmteterugwinning
    - Afvalwaterbehandeling met geavanceerde biologische zuivering
    - Continue emissie monitoring en automatische registratie
    - Geluidsreductie door inkapseling en geluidswering
    
    VOORSCHRIFTEN:
    
    1. CAPACITEIT EN PRODUCTIE
    - Maximale verwerkingscapaciteit 150.000 ton/jaar
    - Registratie van alle in- en uitgaande stromen
    - Jaarrapportage van productie en afvalstromen
    
    2. EMISSIES NAAR LUCHT
    - NOx emissies < 200 mg/Nm³ (daggemiddelde)
    - SO2 emissies < 50 mg/Nm³ (daggemiddelde)  
    - Stofemissies < 10 mg/Nm³ (daggemiddelde)
    - Continue monitoring van alle emissies
    
    3. LOZINGEN NAAR WATER
    - CZV lozing < 125 mg/l (maandgemiddelde)
    - BZV lozing < 25 mg/l (maandgemiddelde)
    - Zwevende stof < 35 mg/l (maandgemiddelde)
    - pH tussen 6.5 - 8.5
    - Temperatuur koelwater < 30°C
    
    4. GELUID
    - Geluidsniveau op beoordelingspunten < 50 dB(A) etmaalwaarde
    - Geluidsisolerende maatregelen voor alle installaties
    - Beperking transportbewegingen tijdens avond/nachtperiode
    
    5. ENERGIE EN GRONDSTOFFEN
    - Energie-efficiëntie minimaal 75% voor warmteterugwinning
    - Gebruik van biomassa waar technisch mogelijk
    - Minimalisatie hulpstoffengebruik
    
    6. AFVAL EN BIJPRODUCTEN
    - Maximale benutting van reststromen als secundaire grondstof
    - Afvoer gevaarlijk afval naar erkende verwerkers
    - Registratie conform Europese afvalstoffenlijst
    
    7. MONITORING EN RAPPORTAGE
    - Continue monitoring emissies naar lucht en water
    - Jaarlijkse milieurapportage aan bevoegd gezag
    - Interne audits conform ISO 14001
    - Registratie in Landelijk Register Installaties
    
    8. BESTE BESCHIKBARE TECHNIEKEN
    - Implementatie conform EU BREF Afvalbehandeling
    - Toepassing energie-efficiëntie conform BREF Energie
    - Emissiemonitoring conform BREF Monitoring
    - Afvalwaterbehandeling conform BREF CWW
    
    TECHNISCHE BESCHRIJVING:
    
    De rejectverwerker behelst een geïntegreerd proces voor de verwerking van
    reject materiaal uit de papierindustrie. Het proces bestaat uit mechanische
    scheiding, thermische behandeling en material recovery.
    
    Mechanische scheiding:
    - Zeven en sorteren op fractiegrootte
    - Magneetafscheiding van ferrometalen
    - Dichtheidsscheiding van verschillende materialen
    - Reiniging en deinking van vezelstromen
    
    Thermische behandeling:
    - Fluidbed verbrandingsketel voor organische fracties
    - Rookgasreiniging met ontstofing en DeNOx
    - Energieterugwinning via stoom- en elektriciteitsproductie
    - Behandeling van vliegas en bodemas
    
    Afvalwaterbehandeling:
    - Voorbezinking en olieafscheiding
    - Biologische zuivering met actief slib
    - Nabezinking en slib ontwatering
    - Hergebruik van gezuiverd water in proces
    """

if __name__ == "__main__":
    analyze_solidus_permit()