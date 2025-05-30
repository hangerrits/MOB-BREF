#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/download_all_brefs.py

"""
Complete BREF Download System
Downloads alle 28 officiële EU BREFs in Nederlandse versie
"""

import os
import sys
from regulatory_data_manager import RegulatoryDataManager

def main():
    """Download alle BREFs en initialiseer volledig systeem"""
    
    print("🚀 === COMPLETE BREF DOWNLOAD SYSTEEM ===")
    print("Downloading alle 28 officiële EU BREFs in Nederlandse versie")
    print("Inclusief kritieke horizontale BREFs!\n")
    
    # Initialize manager
    manager = RegulatoryDataManager()
    
    # Setup database with complete catalog
    print("📋 Initializing complete BREF catalog...")
    manager.initialize_bref_catalog()
    
    # Download RIE regulation
    print("📜 Downloading RIE regulation...")
    manager.download_rie_regulation()
    
    # Download ALL BREFs
    print("\n🔥 === DOWNLOADING ALLE BREFs ===")
    success_count, failed_brefs = manager.download_all_brefs()
    
    # Summary
    print(f"\n📊 === COMPLETE DOWNLOAD SAMENVATTING ===")
    print(f"✅ Successfully downloaded: {success_count} BREFs")
    print(f"❌ Failed downloads: {len(failed_brefs)}")
    
    if failed_brefs:
        print(f"⚠️ Failed BREFs: {', '.join(failed_brefs)}")
        print("💡 Tip: Failed downloads kunnen handmatig worden herhaald")
    
    # Horizontal BREFs check
    horizontal_brefs = manager.get_horizontal_brefs()
    downloaded_horizontal = [b for b in horizontal_brefs if b not in failed_brefs]
    
    print(f"\n🔄 === HORIZONTALE BREFs STATUS ===")
    print(f"Totaal horizontale BREFs: {len(horizontal_brefs)}")
    print(f"✅ Downloaded: {len(downloaded_horizontal)}")
    print(f"❌ Failed: {len(horizontal_brefs) - len(downloaded_horizontal)}")
    
    if len(downloaded_horizontal) == len(horizontal_brefs):
        print("🎉 ALLE HORIZONTALE BREFs GEDOWNLOAD!")
        print("✅ Systeem is nu compleet voor alle sectoren")
    else:
        print("⚠️ Niet alle horizontale BREFs beschikbaar")
        print("🔧 Deze zijn kritiek voor volledige compliance")
    
    # Storage info
    storage_path = manager.data_dir
    db_path = manager.db_path
    
    print(f"\n📁 === OPSLAG INFORMATIE ===")
    print(f"Data directory: {storage_path}")
    print(f"Database: {db_path}")
    print(f"BREF PDFs: {os.path.join(storage_path, 'brefs')}")
    
    # Next steps
    print(f"\n🎯 === VOLGENDE STAPPEN ===")
    print("1. Extract BAT conclusions from downloaded BREFs")
    print("2. Test complete system with real permit")
    print("3. Verify horizontal BREF applicability logic")
    
    return success_count >= 20  # Success if most BREFs downloaded

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)