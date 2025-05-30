# /Users/han/Code/MOB-BREF/demo_compliance_system.py

import os
import json
from regulatory_data_manager import RegulatoryDataManager

def demo_system():
    """Demonstrate the regulatory compliance system"""
    print("=== REGULATORY COMPLIANCE SYSTEM DEMO ===\n")
    
    # Initialize the regulatory data manager
    reg_manager = RegulatoryDataManager()
    
    # Show what's in the database
    print("1. RIE ACTIVITIES IN DATABASE:")
    activities = reg_manager.get_applicable_rie_activities("livestock dairy cattle")
    for activity in activities:
        print(f"   - Category: {activity.category}")
        print(f"     Description: {activity.activity_description}")
        print(f"     Thresholds: {activity.threshold_values}")
        print()
    
    print("2. BREF DOCUMENTS IN CATALOG:")
    brefs = reg_manager.get_applicable_brefs()
    for bref in brefs[:5]:  # Show first 5
        print(f"   - {bref.bref_id}: {bref.title} ({bref.sector})")
    print(f"   ... and {len(brefs)-5} more BREFs")
    print()
    
    print("3. LIVESTOCK-SPECIFIC ANALYSIS:")
    livestock_brefs = reg_manager.get_applicable_brefs(sector="Livestock")
    if livestock_brefs:
        for bref in livestock_brefs:
            print(f"   - Applicable BREF: {bref.bref_id} - {bref.title}")
            
            # Show sample BAT conclusions for livestock
            bat_conclusions = reg_manager.get_bat_conclusions_for_bref(bref.bref_id)
            if bat_conclusions:
                for bat in bat_conclusions[:2]:  # Show first 2
                    print(f"     BAT {bat.bat_id}: {bat.title}")
            else:
                print("     (No BAT conclusions loaded yet - would need to download BREF documents)")
    else:
        print("   - No livestock BREFs found in catalog")
    print()
    
    print("4. SAMPLE PERMIT ANALYSIS:")
    # Simulate a livestock permit analysis
    sample_permit_description = "expansion of existing dairy cattle farm with 150 dairy cows"
    
    print(f"   Permit Description: {sample_permit_description}")
    
    # Check RIE applicability
    applicable_rie = reg_manager.get_applicable_rie_activities(sample_permit_description)
    if applicable_rie:
        print("   RIE Applicability: YES")
        for rie in applicable_rie:
            print(f"     - {rie.category}: {rie.threshold_values}")
    else:
        print("   RIE Applicability: NO direct matches found")
    
    # Check applicable BREFs
    applicable_brefs = reg_manager.get_applicable_brefs(activity="livestock")
    if applicable_brefs:
        print("   Applicable BREFs:")
        for bref in applicable_brefs:
            print(f"     - {bref.bref_id}: {bref.title}")
    
    print()
    print("5. SYSTEM CAPABILITIES:")
    print("   ✓ RIE regulation database with activity categories and thresholds")
    print("   ✓ BREF document catalog with sector classifications")
    print("   ✓ BAT conclusions database (ready for BREF document processing)")
    print("   ✓ Permit document classification system")
    print("   ✓ Compliance checking engine")
    print("   ✓ Report generation system")
    print()
    
    print("6. NEXT STEPS TO COMPLETE THE SYSTEM:")
    print("   - Download actual BREF documents and extract BAT conclusions")
    print("   - Integrate with LLM for sophisticated compliance analysis")
    print("   - Add more RIE activities from the complete regulation")
    print("   - Enhance permit document parsing and classification")
    print("   - Add legal compliance checking (MER procedures, etc.)")
    print()
    
    # Show database statistics
    import sqlite3
    conn = sqlite3.connect(reg_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM rie_activities")
    rie_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bref_documents")
    bref_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bat_conclusions")
    bat_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("7. DATABASE STATISTICS:")
    print(f"   - RIE Activities: {rie_count}")
    print(f"   - BREF Documents: {bref_count}")
    print(f"   - BAT Conclusions: {bat_count}")
    print(f"   - Database location: {reg_manager.db_path}")

if __name__ == "__main__":
    demo_system()