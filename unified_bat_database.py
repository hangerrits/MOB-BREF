#!/usr/bin/env python3
"""
Unified BAT/BBT Database Creator
Combines Dutch BBTs from BATCs with English BATs from BREFs
Creates comprehensive database for compliance verification
"""

import json
import os
from datetime import datetime
from typing import Dict, List

class UnifiedBATDatabase:
    """Creates unified database of Dutch BBTs and English BATs"""
    
    def __init__(self):
        self.dutch_bbts = {}
        self.english_bats = {}
        self.unified_database = {}
        self.statistics = {}
    
    def create_unified_database(self, output_file: str = "unified_bat_database.json") -> Dict:
        """Create comprehensive unified BAT/BBT database"""
        
        print("🌟 === UNIFIED BAT/BBT DATABASE CREATION ===\n")
        
        # Load Dutch BBTs from BATC extraction
        self.load_dutch_bbts()
        
        # Load English BATs from BREF extraction  
        self.load_english_bats()
        
        # Create unified structure
        self.create_unified_structure()
        
        # Generate statistics
        self.generate_statistics()
        
        # Save unified database
        self.save_unified_database(output_file)
        
        # Print summary
        self.print_summary()
        
        return self.unified_database
    
    def load_dutch_bbts(self):
        """Load Dutch BBTs from BATC extraction"""
        
        batc_file = "batc_extractions/dutch_only_bbts.json"
        
        if os.path.exists(batc_file):
            with open(batc_file, 'r', encoding='utf-8') as f:
                self.dutch_bbts = json.load(f)
            
            total_bbts = sum(len(bbts) for bbts in self.dutch_bbts.values())
            print(f"✅ Loaded {total_bbts} Dutch BBTs from {len(self.dutch_bbts)} BATC documents")
        else:
            print(f"❌ Dutch BBTs file not found: {batc_file}")
    
    def load_english_bats(self):
        """Load English BATs from BREF extraction"""
        
        bref_file = "bref_extractions/all_bref_final_complete.json"
        
        if os.path.exists(bref_file):
            with open(bref_file, 'r', encoding='utf-8') as f:
                self.english_bats = json.load(f)
            
            total_bats = sum(len(bats) for bats in self.english_bats.values())
            print(f"✅ Loaded {total_bats} English BATs from {len(self.english_bats)} BREF documents")
        else:
            print(f"❌ English BATs file not found: {bref_file}")
    
    def create_unified_structure(self):
        """Create unified database structure"""
        
        print(f"\n🔧 Creating unified database structure...")
        
        self.unified_database = {
            "metadata": {
                "creation_date": datetime.now().isoformat(),
                "description": "Unified EU BAT/BBT Database",
                "sources": {
                    "dutch_bbts": {
                        "source_type": "BATC HTML documents",
                        "language": "Dutch",
                        "legally_binding": True,
                        "document_count": len(self.dutch_bbts),
                        "total_bbts": sum(len(bbts) for bbts in self.dutch_bbts.values())
                    },
                    "english_bats": {
                        "source_type": "BREF PDF documents", 
                        "language": "English",
                        "legally_binding": False,
                        "document_count": len(self.english_bats),
                        "total_bats": sum(len(bats) for bats in self.english_bats.values())
                    }
                }
            },
            "dutch_bbts": self.dutch_bbts,
            "english_bats": self.english_bats,
            "document_mapping": self.create_document_mapping(),
            "sector_coverage": self.analyze_sector_coverage()
        }
    
    def create_document_mapping(self) -> Dict:
        """Create mapping between document codes and descriptions"""
        
        # Common document descriptions
        document_descriptions = {
            # BATC Documents (Dutch)
            'CAK': 'Chemical Alkali (CAK)',
            'CLM': 'Chlor-Alkali Manufacturing (CLM)', 
            'CWW': 'Common Waste Water and Waste Gas Treatment (CWW)',
            'FDM': 'Ferrous Metals Processing (FDM)',
            'FMP': 'Ferrous Metal Processing (FMP)',
            'IRPP': 'Iron and Steel Production and Processing (IRPP)',
            'IS': 'Iron and Steel (IS)',
            'LVOC': 'Large Volume Organic Chemicals (LVOC)',
            'NFM': 'Non-Ferrous Metals (NFM)',
            'PP': 'Pulp and Paper (PP)',
            'REF': 'Refineries (REF)',
            'SA': 'Slaughterhouses and Animal By-products (SA)',
            'SF': 'Smitheries and Foundries (SF)',
            'STS': 'Surface Treatment of metals and plastics (STS)',
            'TXT': 'Textiles (TXT)',
            'WBP': 'Waste and Biowaste Processing (WBP)',
            'WGC': 'Waste Gas Cleaning (WGC)',
            'WI': 'Waste Incineration (WI)',
            'WT': 'Waste Treatment (WT)',
            
            # BREF Documents (English)
            'CER': 'Ceramics Manufacturing (CER)',
            'ECM': 'Economics and Cross-Media Effects (ECM)',
            'EFS': 'Energy and Feed Systems (EFS)',
            'ENE': 'Energy Efficiency (ENE)',
            'ICS': 'Intensive Cooling Systems (ICS)',
            'LVIC-AAF': 'Large Volume Inorganic Chemicals - Ammonia, Acids and Fertilisers (LVIC-AAF)',
            'LVIC-S': 'Large Volume Inorganic Chemicals - Solids and Others (LVIC-S)',
            'OFC': 'Organic Fine Chemicals (OFC)',
            'POL': 'Polymers (POL)',
            'ROM': 'Reference Document on Monitoring (ROM)',
            'SIC': 'Smitheries and Foundries - Iron and Steel (SIC)',
            'STM': 'Surface Treatment of Metals and plastics (STM)'
        }
        
        mapping = {}
        
        # Map Dutch BBT documents
        for doc_code in self.dutch_bbts.keys():
            mapping[doc_code] = {
                'description': document_descriptions.get(doc_code, f'Unknown ({doc_code})'),
                'language': 'Dutch',
                'source_type': 'BATC',
                'legally_binding': True,
                'bbt_count': len(self.dutch_bbts[doc_code])
            }
        
        # Map English BAT documents
        for doc_code in self.english_bats.keys():
            mapping[doc_code] = {
                'description': document_descriptions.get(doc_code, f'Unknown ({doc_code})'),
                'language': 'English', 
                'source_type': 'BREF',
                'legally_binding': False,
                'bat_count': len(self.english_bats[doc_code])
            }
        
        return mapping
    
    def analyze_sector_coverage(self) -> Dict:
        """Analyze which industrial sectors are covered"""
        
        sectors = {
            'chemical': ['CAK', 'CLM', 'LVOC', 'LVIC-AAF', 'LVIC-S', 'OFC', 'POL'],
            'metals': ['FDM', 'FMP', 'IRPP', 'IS', 'NFM', 'SF', 'SIC'],
            'waste': ['CWW', 'WBP', 'WGC', 'WI', 'WT'],
            'energy': ['ENE'],
            'manufacturing': ['CER', 'TXT', 'PP'],
            'treatment': ['STS', 'STM'],
            'food': ['SA'],
            'oil': ['REF'],
            'monitoring': ['ROM'],
            'cooling': ['ICS'],
            'feed': ['EFS'],
            'economics': ['ECM']
        }
        
        coverage = {}
        
        for sector, doc_codes in sectors.items():
            dutch_docs = [code for code in doc_codes if code in self.dutch_bbts]
            english_docs = [code for code in doc_codes if code in self.english_bats]
            
            dutch_bbts = sum(len(self.dutch_bbts[code]) for code in dutch_docs)
            english_bats = sum(len(self.english_bats[code]) for code in english_docs)
            
            coverage[sector] = {
                'dutch_documents': dutch_docs,
                'english_documents': english_docs,
                'dutch_bbts': dutch_bbts,
                'english_bats': english_bats,
                'total_techniques': dutch_bbts + english_bats
            }
        
        return coverage
    
    def generate_statistics(self):
        """Generate comprehensive statistics"""
        
        # Basic counts
        total_dutch_bbts = sum(len(bbts) for bbts in self.dutch_bbts.values())
        total_english_bats = sum(len(bats) for bats in self.english_bats.values())
        
        # Documents with tables
        dutch_with_tables = 0
        english_with_tables = 0
        
        for bbts in self.dutch_bbts.values():
            dutch_with_tables += sum(1 for bbt in bbts if bbt.get('has_tables', False))
        
        for bats in self.english_bats.values():
            english_with_tables += sum(1 for bat in bats if bat.get('has_tables', False))
        
        self.statistics = {
            "total_documents": len(self.dutch_bbts) + len(self.english_bats),
            "total_techniques": total_dutch_bbts + total_english_bats,
            "dutch_bbts": {
                "documents": len(self.dutch_bbts),
                "total_bbts": total_dutch_bbts,
                "with_tables": dutch_with_tables
            },
            "english_bats": {
                "documents": len(self.english_bats),
                "total_bats": total_english_bats,
                "with_tables": english_with_tables
            },
            "coverage_analysis": self.unified_database["sector_coverage"]
        }
    
    def save_unified_database(self, output_file: str):
        """Save unified database to JSON file"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.unified_database, f, indent=2, ensure_ascii=False)
        
        # Also save just the statistics
        stats_file = output_file.replace('.json', '_statistics.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Unified database saved:")
        print(f"   📄 Complete database: {output_file}")
        print(f"   📊 Statistics: {stats_file}")
    
    def print_summary(self):
        """Print comprehensive summary"""
        
        print(f"\n🎯 === UNIFIED DATABASE SUMMARY ===")
        
        print(f"\n📚 Total Coverage:")
        print(f"   Documents: {self.statistics['total_documents']}")
        print(f"   Techniques: {self.statistics['total_techniques']}")
        
        print(f"\n🇳🇱 Dutch BBTs (Legally Binding):")
        print(f"   Documents: {self.statistics['dutch_bbts']['documents']}")
        print(f"   BBTs: {self.statistics['dutch_bbts']['total_bbts']}")
        print(f"   With tables: {self.statistics['dutch_bbts']['with_tables']}")
        
        print(f"\n🇬🇧 English BATs (Technical Reference):")
        print(f"   Documents: {self.statistics['english_bats']['documents']}")
        print(f"   BATs: {self.statistics['english_bats']['total_bats']}")
        print(f"   With tables: {self.statistics['english_bats']['with_tables']}")
        
        print(f"\n🏭 Sector Coverage:")
        for sector, data in self.statistics['coverage_analysis'].items():
            if data['total_techniques'] > 0:
                print(f"   {sector.capitalize():12s}: {data['total_techniques']:3d} techniques ({data['dutch_bbts']} Dutch + {data['english_bats']} English)")
        
        print(f"\n✅ Database ready for compliance verification system!")


def main():
    """Create unified BAT/BBT database"""
    
    creator = UnifiedBATDatabase()
    database = creator.create_unified_database()
    
    return database


if __name__ == "__main__":
    main()