#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/download_missing_brefs.py

"""
Download Missing BREFs met alternatieve URLs
Probeert de laatste 3 ontbrekende BREFs te downloaden
"""

import requests
import os
import time
from regulatory_data_manager import RegulatoryDataManager

def get_alternative_bref_urls():
    """Alternatieve URLs voor ontbrekende BREFs"""
    return {
        # SA - Slachthuizen 
        "SA": [
            "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32005D0079",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32005D0079",
            "https://ec.europa.eu/environment/industry/stationary/ied/legislation.htm"
        ],
        
        # ICS - Industrial Cooling Systems (nieuwste BREF)
        "ICS": [
            "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32021D2285",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32021D2285",
            "https://eippcb.jrc.ec.europa.eu/reference/cooling-systems"
        ],
        
        # ENE - Energy Efficiency (oude BREF)
        "ENE": [
            "https://eur-lex.europa.eu/legal-content/NL/TXT/PDF/?uri=CELEX:32009D1357",
            "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32009D1357",
            "https://eippcb.jrc.ec.europa.eu/reference/energy-efficiency"
        ]
    }

def download_with_alternatives(bref_id: str, urls: list, manager: RegulatoryDataManager) -> bool:
    """Probeer download met meerdere URLs"""
    print(f"\n📥 Attempting download of {bref_id} with {len(urls)} alternative URLs...")
    
    for i, url in enumerate(urls, 1):
        print(f"  🔄 Attempt {i}/{len(urls)}: {url}")
        try:
            response = requests.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code == 200:
                # Check if we got a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or url.endswith('.pdf'):
                    # Save PDF
                    filename = f"{bref_id}_bref.pdf"
                    local_path = os.path.join(manager.data_dir, "brefs", filename)
                    
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"  ✅ {bref_id} downloaded successfully from attempt {i}")
                    print(f"     💾 Saved to: {local_path}")
                    print(f"     📊 Size: {len(response.content):,} bytes")
                    
                    # Update database
                    import sqlite3
                    conn = sqlite3.connect(manager.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE bref_documents 
                        SET local_path = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE bref_id = ?
                    ''', (local_path, bref_id))
                    conn.commit()
                    conn.close()
                    
                    return True
                else:
                    print(f"  ⚠️ Attempt {i}: Not a PDF (content-type: {content_type})")
            else:
                print(f"  ❌ Attempt {i}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Attempt {i}: Error - {e}")
        
        time.sleep(1)  # Brief delay between attempts
    
    print(f"  💥 All attempts failed for {bref_id}")
    return False

def download_missing_brefs():
    """Download alle ontbrekende BREFs"""
    
    print("🔍 === DOWNLOAD ONTBREKENDE BREFs ===")
    print("Attempting to download laatste 3 ontbrekende BREFs met alternatieve URLs\n")
    
    manager = RegulatoryDataManager()
    alternative_urls = get_alternative_bref_urls()
    
    results = {}
    
    for bref_id, urls in alternative_urls.items():
        print(f"🎯 === DOWNLOADING {bref_id} ===")
        success = download_with_alternatives(bref_id, urls, manager)
        results[bref_id] = success
        
        if success:
            print(f"✅ {bref_id}: SUCCESS")
        else:
            print(f"❌ {bref_id}: FAILED")
    
    # Summary
    print(f"\n📊 === DOWNLOAD RESULTATEN ===")
    successful = [bref for bref, success in results.items() if success]
    failed = [bref for bref, success in results.items() if not success]
    
    print(f"✅ Successful downloads: {len(successful)}")
    for bref in successful:
        print(f"  - {bref}")
    
    print(f"❌ Failed downloads: {len(failed)}")
    for bref in failed:
        print(f"  - {bref}")
    
    # Check final status
    brefs_dir = os.path.join(manager.data_dir, 'brefs')
    total_downloaded = len([f for f in os.listdir(brefs_dir) if f.endswith('_bref.pdf')])
    
    print(f"\n🎉 === FINALE STATUS ===")
    print(f"📚 Totaal BREFs gedownload: {total_downloaded}/28")
    print(f"🔄 Horizontale BREFs: {len([b for b in successful if b in ['ICS', 'ENE']])}/2 extra")
    
    if total_downloaded >= 27:
        print("🎉 BIJNA COMPLEET! Uitstekende dekking van EU BREFs")
    elif total_downloaded >= 25:
        print("✅ ZEER GOED! Meerderheid van BREFs beschikbaar")
    else:
        print("⚠️ Meer downloads nodig voor volledige dekking")
    
    return successful, failed

if __name__ == "__main__":
    successful, failed = download_missing_brefs()