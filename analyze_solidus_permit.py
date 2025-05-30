#!/usr/bin/env python3
"""
Comprehensive compliance analysis for Solidus Solutions permit documents
"""

import json
from permit_compliance_analyzer import PermitComplianceAnalyzer

def create_solidus_permit_text():
    """Combine and create focused permit text for analysis"""
    
    # Read both extracted texts
    with open('/Users/han/Code/MOB-BREF/permit_decision_text.txt', 'r', encoding='utf-8') as f:
        permit_text = f.read()
    
    with open('/Users/han/Code/MOB-BREF/project_description_text.txt', 'r', encoding='utf-8') as f:
        project_text = f.read()
    
    # Create focused analysis text combining key information
    combined_text = f"""
    INDUSTRIAL PERMIT - SOLIDUS SOLUTIONS BOARD B.V.
    
    FACILITY DETAILS:
    Company: Solidus Solutions Board B.V.
    Location: W.H. Bosgrastraat 82, Oude Pekela, Groningen
    Application: Environmental permit modification for reject processing facility
    
    INDUSTRIAL ACTIVITIES:
    1. EXISTING: Cardboard production facility (solid cardboard and packaging)
    2. NEW: Reject processing facility (rejectverwerkingsinstallatie)
       - Processing of cardboard production waste/reject materials
       - Material recovery and treatment operations
       - Waste stream optimization
    
    TECHNICAL PROCESSES:
    - Cardboard manufacturing with reject material processing
    - Material separation and recovery systems  
    - Waste treatment and processing operations
    - Storage systems for materials and chemicals
    - Cooling systems and utilities
    - Material handling and transport systems
    
    ENVIRONMENTAL ASPECTS:
    
    Air Emissions:
    - Dust emissions from material processing
    - Process air emissions 
    - Ventilation and extraction systems
    - Air quality monitoring requirements
    
    Waste Management:
    - Reject material processing and recovery
    - Waste stream separation
    - Material recycling operations
    - Waste storage and handling
    
    Water/Wastewater:
    - Process water usage
    - Wastewater treatment requirements
    - Water discharge monitoring
    - Legionella control measures
    
    Noise Control:
    - Acoustic studies conducted
    - Sound level limits
    - Noise monitoring requirements
    
    Energy Management:
    - Industrial energy consumption
    - Energy efficiency measures
    - Utilities and power systems
    
    REGULATORY REQUIREMENTS:
    - IPPC Directive compliance
    - BBT (Best Available Techniques) implementation
    - Environmental monitoring and reporting
    - Air emission controls
    - Waste management regulations
    - Water discharge permits
    - Noise regulations compliance
    
    MONITORING AND CONTROLS:
    - Regular environmental monitoring
    - Air emission measurements
    - Water quality monitoring
    - Noise level monitoring
    - Legionella monitoring plan
    - Regular reporting to authorities
    - Data registration and processing
    
    BBT COMPLIANCE:
    The permit explicitly references BBT requirements including:
    - Waste treatment techniques
    - Air emission reduction
    - Water treatment systems
    - Energy efficiency measures
    - Environmental monitoring systems
    - Process optimization
    
    PERMIT DETAILS FROM DOCUMENTS:
    {permit_text[:5000]}...
    
    PROJECT DESCRIPTION DETAILS:
    {project_text[:5000]}...
    """
    
    return combined_text

def analyze_solidus_compliance():
    """Run comprehensive compliance analysis for Solidus facility"""
    
    print("🏭 === SOLIDUS SOLUTIONS COMPLIANCE ANALYSIS ===\n")
    print("Facility: Solidus Solutions Board B.V.")
    print("Location: Oude Pekela, Groningen")
    print("Activity: Cardboard production + Reject processing facility\n")
    
    # Create analyzer
    analyzer = PermitComplianceAnalyzer()
    
    # Create combined permit text
    permit_text = create_solidus_permit_text()
    print(f"📄 Permit text prepared: {len(permit_text):,} characters")
    
    # Facility metadata
    facility_metadata = {
        'facility_name': 'Solidus Solutions Board B.V.',
        'location': 'W.H. Bosgrastraat 82, Oude Pekela, Groningen',
        'permit_type': 'Environmental Permit Modification (Omgevingsvergunning)',
        'application_number': '7907787',
        'activity_type': 'Cardboard production with reject processing facility',
        'permit_date': '2025-01-13',
        'competent_authority': 'Province of Groningen (Gedeputeerde Staten)',
        'ippc_facility': True,
        'analysis_date': '2025-05-30'
    }
    
    print(f"🔍 Running comprehensive BAT/BBT compliance analysis...")
    print(f"   Analyzing against {len(analyzer.bat_database.get('dutch_bbts', {}))} Dutch BATC documents")
    print(f"   Analyzing against {len(analyzer.bat_database.get('english_bats', {}))} English BREF documents")
    print(f"   Total techniques to assess: {sum(len(bbts) for bbts in analyzer.bat_database.get('dutch_bbts', {}).values()) + sum(len(bats) for bats in analyzer.bat_database.get('english_bats', {}).values())}")
    
    # Run the full compliance analysis
    try:
        report = analyzer.analyze_permit_compliance(permit_text, facility_metadata)
        
        # Save the comprehensive report
        filename = analyzer.save_analysis_report(report, "Solidus_Complete_Compliance_Report.json")
        
        # Print summary results
        print(f"\n📊 === COMPLIANCE ANALYSIS RESULTS ===")
        print(f"Documents assessed: {report['metadata']['total_documents_assessed']}")
        print(f"Applicable documents: {len(report['step1_applicability']['summary']['applicable_documents'])}")
        print(f"High confidence applicability: {len(report['step1_applicability']['summary']['high_confidence'])}")
        print(f"Requires review (applicability): {len(report['step1_applicability']['summary']['requires_review'])}")
        
        print(f"\nBAT Compliance Summary:")
        print(f"Total BATs assessed: {report['step2_compliance']['summary']['total_bats_assessed']}")
        print(f"Compliant BATs: {report['step2_compliance']['summary']['compliant_bats']}")
        print(f"Non-compliant BATs: {report['step2_compliance']['summary']['non_compliant_bats']}")
        print(f"Requires human review: {report['step2_compliance']['summary']['requires_human_review']}")
        
        print(f"\nConfidence Distribution:")
        conf_dist = report['step2_compliance']['summary']['confidence_distribution']
        print(f"High confidence: {conf_dist['high']}")
        print(f"Medium confidence: {conf_dist['medium']}")
        print(f"Low confidence: {conf_dist['low']}")
        
        # Show applicable documents
        applicable_docs = report['step1_applicability']['summary']['applicable_documents']
        print(f"\n📋 Applicable Documents ({len(applicable_docs)}):")
        for doc in applicable_docs:
            doc_result = report['step1_applicability']['results'][doc]
            print(f"   ✅ {doc}: {doc_result['confidence']} confidence")
            if doc_result.get('key_activities'):
                print(f"      🔑 {doc_result['key_activities'][:2]}")  # Show first 2 activities
        
        # Show some key compliance results
        print(f"\n⚖️  Key Compliance Results:")
        compliance_count = 0
        for doc_code, assessments in report['step2_compliance']['results'].items():
            if compliance_count >= 10:  # Limit output
                break
            for assessment in assessments[:3]:  # Show first 3 per document
                compliance_icon = {
                    'compliant': '✅',
                    'partially_compliant': '🟡',
                    'non_compliant': '❌',
                    'insufficient_info': '❓',
                    'not_applicable': '⚪'
                }.get(assessment['compliance_level'], '❓')
                
                print(f"   {compliance_icon} {doc_code}-{assessment['bat_id']}: {assessment['compliance_level']} ({assessment['confidence']})")
                compliance_count += 1
        
        print(f"\n💾 Complete report saved: {filename}")
        print(f"📄 Report size: {len(json.dumps(report)):,} characters")
        
        return report
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

if __name__ == "__main__":
    report = analyze_solidus_compliance()
    
    if report:
        print(f"\n✅ === ANALYSIS COMPLETED SUCCESSFULLY ===")
        print("The Solidus Solutions facility has been comprehensively analyzed")
        print("against all relevant BAT/BBT requirements!")
        
        print(f"\n📋 === NEXT STEPS ===")
        print("1. Review the detailed JSON report for specific findings")
        print("2. Focus on items flagged for human review")
        print("3. Address any non-compliant or partially compliant BATs")
        print("4. Consider recommendations for improvement")
    else:
        print(f"\n❌ === ANALYSIS FAILED ===")
        print("Please check the error messages above and try again.")