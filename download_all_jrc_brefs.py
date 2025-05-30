#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/download_all_jrc_brefs.py

"""
Download ALLE BREFs van JRC EIPPCB
Comprehensive download van alle beschikbare EU BREFs
"""

import requests
import os
import time
from regulatory_data_manager import RegulatoryDataManager

def get_additional_jrc_brefs():
    """Extra BREFs gevonden op JRC EIPPCB site"""
    return {
        # Horizontal BREFs
        "ECM": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/ecm_bref_0706.pdf",
        "EFS": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/efs_bref_0706_0.pdf", 
        "ROM": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/rom_bref_2018.pdf",
        
        # Sector BREFs - nieuwere versies
        "FMP": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2022-11/FMP%20BREF_Final%20Version.pdf",
        "IS": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/is_bref_0312.pdf",
        "TXT_NEW": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2023-01/TXT_BREF_final.pdf",
        
        # Ontbrekende sector BREFs  
        "CER": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/cer_bref_0807.pdf",
        "SF": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/sf_bref_0807.pdf",
        "TAN": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/tan_bref_0208.pdf",
        "WGC": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/wgc_bref_0801.pdf",
        
        # BAT Conclusions (nieuwere versies)
        "FDM_BATC": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/JRC118627_FDM_Bref_2019_published.pdf",
        "CWW_NEW": "https://eippcb.jrc.ec.europa.eu/sites/default/files/2019-11/CWW_Bref_2016_published.pdf",
    }

def download_additional_brefs():
    """Download alle extra JRC BREFs"""
    
    print("🚀 === DOWNLOAD ALLE JRC BREFs ===")
    print("Downloading alle extra BREFs van JRC EIPPCB site\n")
    
    manager = RegulatoryDataManager()
    additional_brefs = get_additional_jrc_brefs()
    
    results = {"success": [], "failed": []}
    
    for bref_id, url in additional_brefs.items():
        print(f"📥 Downloading {bref_id}...")
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Save PDF
            filename = f"{bref_id}_bref.pdf"
            local_path = os.path.join(manager.data_dir, "brefs", filename)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✅ Downloaded: {len(response.content):,} bytes")
            results["success"].append(bref_id)
            
            time.sleep(1)  # Respectful delay
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            results["failed"].append(bref_id)
    
    # Summary
    print(f"\n📊 === DOWNLOAD RESULTATEN ===")
    print(f"✅ Successful: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    if results["success"]:
        print(f"\n✅ Successfully downloaded:")
        for bref in results["success"]:
            print(f"  - {bref}")
    
    if results["failed"]:
        print(f"\n❌ Failed downloads:")
        for bref in results["failed"]:
            print(f"  - {bref}")
    
    # Final count
    brefs_dir = os.path.join(manager.data_dir, 'brefs')
    total_pdfs = len([f for f in os.listdir(brefs_dir) if f.endswith('.pdf')])
    
    print(f"\n🎉 === FINALE TELLING ===")
    print(f"📚 Totaal BREF PDFs: {total_pdfs}")
    print(f"🏭 Originele 28 BREFs + Extra JRC BREFs")
    print(f"🔄 Inclusief horizontale en sector-specifieke BREFs")
    
    if total_pdfs >= 35:
        print("🚀 SUPER COMPLEET! Uitgebreide EU BREF collectie!")
    elif total_pdfs >= 30:
        print("🎯 ZEER COMPLEET! Excellente dekking!")
    else:
        print("✅ GOEDE dekking van EU BREFs")
    
    return results

if __name__ == "__main__":
    results = download_additional_brefs()