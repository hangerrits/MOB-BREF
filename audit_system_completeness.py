# /Users/han/Code/MOB-BREF/audit_system_completeness.py

import os
import json
import sqlite3
from typing import Dict, List, Any
from datetime import datetime

from regulatory_data_manager import RegulatoryDataManager

def audit_bref_completeness():
    """Audit of we alle BREFs en horizontale BREFs hebben"""
    
    print("🔍 === AUDIT: VOLLEDIGHEID BREF/BBT DATABASE ===\n")
    
    # Complete lijst van ALLE officiële EU BREFs (inclusief horizontale)
    complete_bref_catalog = {
        # SECTOR-SPECIFIEKE BREFs
        "FDM": {
            "nederlands": "Voedings-, dranken- en zuivelindustrie",
            "engels": "Food, Drink and Milk Industries",
            "type": "Sector-specifiek",
            "sectors": ["Voedingsmiddelen", "Zuivel", "Dranken"],
            "eu_besluit": "2019/2031/EU",
            "adoptie_datum": "2019-12-12"
        },
        "IRPP": {
            "nederlands": "Intensieve pluimvee- en varkenshouderij",
            "engels": "Intensive Rearing of Poultry or Pigs", 
            "type": "Sector-specifiek",
            "sectors": ["Veehouderij"],
            "eu_besluit": "2017/302/EU",
            "adoptie_datum": "2017-02-15"
        },
        "LCP": {
            "nederlands": "Grote stookinstallaties",
            "engels": "Large Combustion Plants",
            "type": "Sector-specifiek", 
            "sectors": ["Energie"],
            "eu_besluit": "2017/1442/EU",
            "adoptie_datum": "2017-07-31"
        },
        "REF": {
            "nederlands": "Raffinage van minerale olie en gas",
            "engels": "Refining of Mineral Oil and Gas",
            "type": "Sector-specifiek",
            "sectors": ["Petrochemie", "Energie"],
            "eu_besluit": "2014/738/EU", 
            "adoptie_datum": "2014-10-09"
        },
        "ISP": {
            "nederlands": "IJzer- en staalproductie",
            "engels": "Iron and Steel Production",
            "type": "Sector-specifiek",
            "sectors": ["Metaalindustrie"],
            "eu_besluit": "2012/135/EU",
            "adoptie_datum": "2012-02-28"
        },
        "NFM": {
            "nederlands": "Non-ferro metalen",
            "engels": "Non-ferrous Metals",
            "type": "Sector-specifiek", 
            "sectors": ["Metaalindustrie"],
            "eu_besluit": "2016/1032/EU",
            "adoptie_datum": "2016-06-13"
        },
        "CLM": {
            "nederlands": "Cement-, kalk- en magnesiumoxideproductie", 
            "engels": "Cement, Lime and Magnesium Oxide Production",
            "type": "Sector-specifiek",
            "sectors": ["Bouwmaterialen"],
            "eu_besluit": "2013/163/EU",
            "adoptie_datum": "2013-02-26"
        },
        "GLS": {
            "nederlands": "Glasindustrie",
            "engels": "Glass Manufacturing", 
            "type": "Sector-specifiek",
            "sectors": ["Bouwmaterialen"],
            "eu_besluit": "2012/134/EU",
            "adoptie_datum": "2012-02-28"
        },
        "CAM": {
            "nederlands": "Keramische industrie",
            "engels": "Ceramic Manufacturing",
            "type": "Sector-specifiek",
            "sectors": ["Bouwmaterialen"],
            "eu_besluit": "2007/506/EC",
            "adoptie_datum": "2007-08-24"
        },
        "LVIC": {
            "nederlands": "Anorganische chemicaliën in grote hoeveelheden",
            "engels": "Large Volume Inorganic Chemicals",
            "type": "Sector-specifiek",
            "sectors": ["Chemische industrie"],
            "eu_besluit": "2013/732/EU", 
            "adoptie_datum": "2013-12-09"
        },
        "LVOC": {
            "nederlands": "Organische chemicaliën in grote hoeveelheden",
            "engels": "Large Volume Organic Chemicals",
            "type": "Sector-specifiek",
            "sectors": ["Chemische industrie"], 
            "eu_besluit": "2017/2117/EU",
            "adoptie_datum": "2017-12-13"
        },
        "OFC": {
            "nederlands": "Organische fijnchemicaliën",
            "engels": "Organic Fine Chemicals",
            "type": "Sector-specifiek",
            "sectors": ["Chemische industrie"],
            "eu_besluit": "2006/738/EC",
            "adoptie_datum": "2006-11-09"
        },
        "POL": {
            "nederlands": "Polymeren productie",
            "engels": "Polymers Production", 
            "type": "Sector-specifiek",
            "sectors": ["Chemische industrie"],
            "eu_besluit": "2007/64/EC",
            "adoptie_datum": "2007-02-02"
        },
        "CAK": {
            "nederlands": "Chloor-alkali productie",
            "engels": "Chlor-alkali Production",
            "type": "Sector-specifiek",
            "sectors": ["Chemische industrie"],
            "eu_besluit": "2013/732/EU",
            "adoptie_datum": "2013-12-09"
        },
        "PPB": {
            "nederlands": "Pulp-, papier- en kartonproductie", 
            "engels": "Pulp, Paper and Board Production",
            "type": "Sector-specifiek",
            "sectors": ["Papierindustrie"],
            "eu_besluit": "2014/687/EU",
            "adoptie_datum": "2014-09-26"
        },
        "TXT": {
            "nederlands": "Textielindustrie",
            "engels": "Textiles Industry",
            "type": "Sector-specifiek",
            "sectors": ["Textiel"],
            "eu_besluit": "2003/720/EC",
            "adoptie_datum": "2003-10-14"
        },
        "SA": {
            "nederlands": "Slachthuizen en verwante industrie",
            "engels": "Slaughterhouses and Animal By-products",
            "type": "Sector-specifiek", 
            "sectors": ["Voedingsmiddelen"],
            "eu_besluit": "2005/79/EC",
            "adoptie_datum": "2005-02-08"
        },
        "WBP": {
            "nederlands": "Houtgebaseerde panelen productie",
            "engels": "Wood-based Panels Production",
            "type": "Sector-specifiek",
            "sectors": ["Houtindustrie"],
            "eu_besluit": "2007/53/EC", 
            "adoptie_datum": "2007-01-25"
        },
        "MIN": {
            "nederlands": "Mijnbouw",
            "engels": "Mining",
            "type": "Sector-specifiek",
            "sectors": ["Mijnbouw"],
            "eu_besluit": "2009/416/EC",
            "adoptie_datum": "2009-05-13"
        },
        
        # AFVAL BREFs
        "WT": {
            "nederlands": "Afvalbehandeling", 
            "engels": "Waste Treatment",
            "type": "Afval",
            "sectors": ["Afvalbeheer"],
            "eu_besluit": "2018/1147/EU",
            "adoptie_datum": "2018-08-10"
        },
        "WI": {
            "nederlands": "Afvalverbranding",
            "engels": "Waste Incineration", 
            "type": "Afval",
            "sectors": ["Afvalbeheer"],
            "eu_besluit": "2019/2010/EU",
            "adoptie_datum": "2019-11-12"
        },
        
        # ⚠️ HORIZONTALE BREFs - ESSENTIEEL VOOR ALLE SECTOREN! ⚠️
        "ICS": {
            "nederlands": "Industriële koelsystemen",
            "engels": "Industrial Cooling Systems",
            "type": "HORIZONTAAL",
            "sectors": ["ALLE SECTOREN - koeling"],
            "eu_besluit": "2021/2285/EU",
            "adoptie_datum": "2021-12-16",
            "toepassingsgebied": "Koelsystemen > 2 MW in alle industrieën"
        },
        "ENE": {
            "nederlands": "Energie-efficiëntie", 
            "engels": "Energy Efficiency",
            "type": "HORIZONTAAL",
            "sectors": ["ALLE SECTOREN - energie"],
            "eu_besluit": "2009/1357/EC",
            "adoptie_datum": "2009-02-24",
            "toepassingsgebied": "Energie-efficiëntie in alle industrieën"
        },
        "EMS": {
            "nederlands": "Emissiemonitoring",
            "engels": "Emissions Monitoring and Reporting", 
            "type": "HORIZONTAAL",
            "sectors": ["ALLE SECTOREN - monitoring"],
            "eu_besluit": "2007/589/EC",
            "adoptie_datum": "2007-08-24",
            "toepassingsgebied": "Emissie monitoring voor alle sectoren"
        },
        "STM": {
            "nederlands": "Oppervlaktebehandeling van metalen",
            "engels": "Surface Treatment of Metals",
            "type": "HORIZONTAAL",
            "sectors": ["Metaal", "Automotive", "Aerospace"],
            "eu_besluit": "2006/61/EC",
            "adoptie_datum": "2006-08-24",
            "toepassingsgebied": "Metaal oppervlaktebehandeling alle sectoren"
        },
        "STP": {
            "nederlands": "Oppervlaktebehandeling met kunststoffen",
            "engels": "Surface Treatment using Plastics",
            "type": "HORIZONTAAL", 
            "sectors": ["Kunststof", "Automotive", "Elektronica"],
            "eu_besluit": "2007/84/EC",
            "adoptie_datum": "2007-02-09",
            "toepassingsgebied": "Kunststof coating alle sectoren"
        },
        "STS": {
            "nederlands": "Oppervlaktebehandeling met oplosmiddelen",
            "engels": "Surface Treatment using Solvents",
            "type": "HORIZONTAAL",
            "sectors": ["ALLE SECTOREN - oplosmiddelen"],
            "eu_besluit": "2007/84/EC", 
            "adoptie_datum": "2007-02-09",
            "toepassingsgebied": "Oplosmiddel gebruik alle sectoren"
        },
        "CWW": {
            "nederlands": "Chemische sector afvalwater/gasbehandeling",
            "engels": "Chemical Sector Waste Water and Gas Treatment",
            "type": "HORIZONTAAL",
            "sectors": ["ALLE SECTOREN - afvalwater/gas"],
            "eu_besluit": "2016/902/EU",
            "adoptie_datum": "2016-05-30",
            "toepassingsgebied": "Afvalwater en gasbehandeling alle sectoren"
        }
    }
    
    print(f"📊 === COMPLETE BREF CATALOGUS ===")
    print(f"Totaal officiële EU BREFs: {len(complete_bref_catalog)}")
    
    # Categoriseren
    sector_specific = {k: v for k, v in complete_bref_catalog.items() if v['type'] == 'Sector-specifiek'}
    horizontal = {k: v for k, v in complete_bref_catalog.items() if v['type'] == 'HORIZONTAAL'}
    waste = {k: v for k, v in complete_bref_catalog.items() if v['type'] == 'Afval'}
    
    print(f"\n📋 BREF CATEGORIEËN:")
    print(f"  🏭 Sector-specifiek: {len(sector_specific)}")
    print(f"  🔄 Horizontaal (alle sectoren): {len(horizontal)}")
    print(f"  🗑️ Afval: {len(waste)}")
    
    print(f"\n⚠️ === KRITIEKE HORIZONTALE BREFs (VAAK GEMIST!) ===")
    for bref_id, info in horizontal.items():
        print(f"  {bref_id}: {info['nederlands']}")
        print(f"    └─ Toepasselijk voor: {info['toepassingsgebied']}")
    
    # Check wat we hebben in onze database
    reg_manager = RegulatoryDataManager()
    current_brefs = check_current_database(reg_manager)
    
    print(f"\n🔍 === HUIDIGE DATABASE STATUS ===")
    print(f"BREFs in onze database: {len(current_brefs)}")
    
    # Vergelijken
    missing_brefs = set(complete_bref_catalog.keys()) - set(current_brefs.keys())
    extra_brefs = set(current_brefs.keys()) - set(complete_bref_catalog.keys())
    
    print(f"\n❌ === ONTBREKENDE BREFs ({len(missing_brefs)}) ===")
    if missing_brefs:
        for bref_id in sorted(missing_brefs):
            info = complete_bref_catalog[bref_id]
            print(f"  {bref_id}: {info['nederlands']} ({info['type']})")
            if info['type'] == 'HORIZONTAAL':
                print(f"    ⚠️ KRITIEK: {info['toepassingsgebied']}")
    else:
        print("  ✅ Geen ontbrekende BREFs!")
    
    if extra_brefs:
        print(f"\n❓ === EXTRA BREFs IN DATABASE ({len(extra_brefs)}) ===")
        for bref_id in sorted(extra_brefs):
            print(f"  {bref_id}: {current_brefs.get(bref_id, 'Onbekend')}")
    
    # Horizontale BREF impact analyse
    print(f"\n🎯 === HORIZONTALE BREF IMPACT ANALYSE ===")
    print(f"Voor een typische industriële installatie zijn HORIZONTALE BREFs meestal:")
    print(f"  🔥 ICS (Koelsystemen): Van toepassing bij koeling > 2 MW")
    print(f"  ⚡ ENE (Energie-efficiëntie): Van toepassing bij alle energie gebruik")
    print(f"  📊 EMS (Emissiemonitoring): Van toepassing bij alle emissies")
    print(f"  🧪 CWW (Afvalwater/Gas): Van toepassing bij afvalwater/gasbehandeling")
    print(f"  🎨 STM/STP/STS: Van toepassing bij oppervlaktebehandeling")
    
    return {
        "complete_catalog": complete_bref_catalog,
        "current_database": current_brefs,
        "missing_brefs": missing_brefs,
        "horizontal_brefs": horizontal,
        "sector_brefs": sector_specific
    }

def check_current_database(reg_manager: RegulatoryDataManager) -> Dict[str, str]:
    """Check welke BREFs we momenteel in database hebben"""
    
    current_brefs = {}
    
    # Check BREF catalog in regulatory manager
    if hasattr(reg_manager, 'alle_nederlandse_brefs'):
        for bref_id, info in reg_manager.alle_nederlandse_brefs.items():
            current_brefs[bref_id] = info.get('nederlandse_titel', 'Onbekend')
    
    # Check database
    if os.path.exists(reg_manager.db_path):
        conn = sqlite3.connect(reg_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT DISTINCT bref_bron FROM alle_nederlandse_bbt_conclusies')
            db_brefs = cursor.fetchall()
            for (bref_id,) in db_brefs:
                if bref_id not in current_brefs:
                    current_brefs[bref_id] = "In database"
        except sqlite3.OperationalError:
            pass  # Table doesn't exist yet
        
        conn.close()
    
    return current_brefs

def audit_rie_completeness():
    """Audit RIE volledigheid"""
    
    print(f"\n🏛️ === AUDIT: RIE (INDUSTRIËLE EMISSIE RICHTLIJN) VOLLEDIGHEID ===")
    
    # Complete RIE Annex I activiteiten  
    complete_rie_activities = {
        "1_energy": {
            "categorie": "1. Energie-industrieën",
            "activiteiten": [
                "Verbrandingsinstallaties > 50 MW thermisch vermogen",
                "Raffinaderijen van minerale olie en gas", 
                "Cokesovens",
                "Vergassing- en vloeibaarstellingsinstallaties"
            ]
        },
        "2_metals": {
            "categorie": "2. Productie en verwerking van metalen",
            "activiteiten": [
                "Metaalerts roosten of sinteren",
                "IJzer- en staalproductie", 
                "Non-ferro metalen productie",
                "Metaal oppervlaktebehandeling"
            ]
        },
        "3_minerals": {
            "categorie": "3. Minerale industrie", 
            "activiteiten": [
                "Cement productie > 500 t/dag",
                "Kalk productie > 50 t/dag",
                "Glas productie > 20 t/dag",
                "Keramische producten"
            ]
        },
        "4_chemical": {
            "categorie": "4. Chemische industrie",
            "activiteiten": [
                "Organische chemicaliën op industriële schaal",
                "Anorganische chemicaliën op industriële schaal", 
                "Fosfaat, kalium of stikstof kunstmeststoffen",
                "Biociden en farmaceutische producten",
                "Explosieven"
            ]
        },
        "5_waste": {
            "categorie": "5. Afvalbeheer",
            "activiteiten": [
                "Gevaarlijk afval verwijdering/terugwinning > 10 t/dag",
                "Niet-gevaarlijk afval verbranding > 3 t/uur",
                "Niet-gevaarlijk afval verwijdering > 50 t/dag"
            ]
        },
        "6_other": {
            "categorie": "6. Andere activiteiten",
            "activiteiten": [
                "Pulp- en papierproductie > 20 t/dag",
                "Textielbehandeling > 10 t/dag",
                "Leerlooierijen > 12 t/dag eindproduct",
                "Slachthuizen > 50 t/dag geslacht gewicht",
                "Voedselbehandeling en drankenproductie",
                "Intensieve pluimvee- of varkenshouderij",
                "Oppervlaktebehandeling oplosmiddelen > 150 kg/h of 200 t/jaar",
                "Koolstofproductie",
                "Houtconservering"
            ]
        }
    }
    
    print(f"📋 RIE Annex I Categorieën: {len(complete_rie_activities)}")
    
    total_activities = sum(len(cat['activiteiten']) for cat in complete_rie_activities.values())
    print(f"📊 Totaal RIE activiteiten: {total_activities}")
    
    # Check wat we hebben
    reg_manager = RegulatoryDataManager()
    current_rie = check_current_rie_database(reg_manager)
    
    print(f"\n🔍 === HUIDIGE RIE DATABASE STATUS ===")
    print(f"RIE activiteiten in database: {len(current_rie)}")
    
    if len(current_rie) < total_activities:
        print(f"⚠️ ONVOLLEDIG: {total_activities - len(current_rie)} RIE activiteiten ontbreken")
        print(f"💡 Aanbeveling: Volledige RIE Annex I implementeren")
    else:
        print(f"✅ RIE database lijkt volledig")
    
    print(f"\n📋 === RIE CATEGORIEËN DETAIL ===")
    for cat_id, cat_info in complete_rie_activities.items():
        print(f"\n{cat_info['categorie']}:")
        for activiteit in cat_info['activiteiten']:
            print(f"  - {activiteit}")
    
    return {
        "complete_rie": complete_rie_activities, 
        "current_database": current_rie,
        "total_activities": total_activities
    }

def check_current_rie_database(reg_manager: RegulatoryDataManager) -> List[Dict]:
    """Check huidige RIE activiteiten in database"""
    
    if not os.path.exists(reg_manager.db_path):
        return []
    
    conn = sqlite3.connect(reg_manager.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM rie_activities')
        activities = cursor.fetchall()
        conn.close()
        return activities
    except sqlite3.OperationalError:
        conn.close()
        return []

def generate_completeness_upgrade_plan(audit_results: Dict[str, Any]):
    """Genereer upgrade plan voor volledigheid"""
    
    print(f"\n🚀 === UPGRADE PLAN VOOR VOLLEDIGE DEKKING ===")
    
    missing_brefs = audit_results.get('missing_brefs', set())
    horizontal_brefs = audit_results.get('horizontal_brefs', {})
    
    # Prioriteiten
    print(f"\n🔥 === HOGE PRIORITEIT: HORIZONTALE BREFs ===")
    missing_horizontal = {k: v for k, v in horizontal_brefs.items() if k in missing_brefs}
    
    if missing_horizontal:
        print(f"❌ Ontbrekende horizontale BREFs ({len(missing_horizontal)}):")
        for bref_id, info in missing_horizontal.items():
            print(f"  {bref_id}: {info['nederlands']}")
            print(f"    Impact: {info['toepassingsgebied']}")
            print(f"    EU Besluit: {info['eu_besluit']}")
    else:
        print(f"✅ Alle horizontale BREFs aanwezig!")
    
    print(f"\n⚠️ === MEDIUM PRIORITEIT: SECTOR BREFs ===")
    missing_sector = missing_brefs - set(horizontal_brefs.keys())
    if missing_sector:
        print(f"Ontbrekende sector BREFs: {len(missing_sector)}")
        for bref_id in sorted(missing_sector):
            complete_catalog = audit_results.get('complete_catalog', {})
            if bref_id in complete_catalog:
                info = complete_catalog[bref_id]
                print(f"  {bref_id}: {info['nederlands']} ({', '.join(info['sectors'])})")
    
    # Implementatie aanbevelingen
    print(f"\n💡 === IMPLEMENTATIE AANBEVELINGEN ===")
    print(f"1. **Direct implementeren:** Horizontale BREFs (allen toepasbaar)")
    print(f"2. **Gefaseerd implementeren:** Sector BREFs op basis van gebruik")
    print(f"3. **RIE completering:** Volledige Annex I activiteiten")
    print(f"4. **Systeem update:** URLs en download logic uitbreiden")
    
    # Code aanpassingen
    print(f"\n🔧 === BENODIGDE CODE AANPASSINGEN ===")
    print(f"1. Update `alle_nederlandse_brefs` dictionary met ontbrekende BREFs")
    print(f"2. Voeg horizontale BREF logic toe aan toepasselijkheidsbepaling")
    print(f"3. Uitbreiding RIE database met volledige Annex I")
    print(f"4. Update compliance engine voor horizontale BREF analyse")
    
    return {
        "priority_horizontal": missing_horizontal,
        "missing_sector": missing_sector,
        "total_missing": len(missing_brefs)
    }

def main():
    """Hoofdfunctie voor volledigheidsaudit"""
    
    print("🔍 === VOLLEDIGE SYSTEEM AUDIT: BREF/BBT & RIE DEKKING ===")
    print("Dit audit controleert of we ALLE officiële EU BREFs hebben,")
    print("inclusief HORIZONTALE BREFs die vaak worden vergeten!\n")
    
    # BREF audit
    bref_audit = audit_bref_completeness()
    
    # RIE audit  
    rie_audit = audit_rie_completeness()
    
    # Upgrade plan
    upgrade_plan = generate_completeness_upgrade_plan(bref_audit)
    
    # Samenvatting
    print(f"\n📊 === AUDIT SAMENVATTING ===")
    print(f"BREF Status:")
    print(f"  📚 Totaal officiële BREFs: {len(bref_audit['complete_catalog'])}")
    print(f"  ✅ In onze database: {len(bref_audit['current_database'])}")
    print(f"  ❌ Ontbrekend: {len(bref_audit['missing_brefs'])}")
    print(f"  🔄 Horizontale BREFs: {len(bref_audit['horizontal_brefs'])}")
    
    print(f"\nRIE Status:")
    print(f"  📚 Totaal RIE activiteiten: {rie_audit['total_activities']}")
    print(f"  ✅ In onze database: {len(rie_audit['current_database'])}")
    
    # Kritieke bevinding
    missing_horizontal = len([b for b in bref_audit['missing_brefs'] if b in bref_audit['horizontal_brefs']])
    if missing_horizontal > 0:
        print(f"\n🚨 === KRITIEKE BEVINDING ===")
        print(f"❌ {missing_horizontal} HORIZONTALE BREFs ontbreken!")
        print(f"💥 Dit betekent dat compliance controles ONVOLLEDIG zijn")
        print(f"🔧 Horizontale BREFs zijn toepasbaar op ALLE sectoren")
    else:
        print(f"\n✅ === HORIZONTALE BREFs COMPLEET ===")
    
    return {
        "bref_audit": bref_audit,
        "rie_audit": rie_audit, 
        "upgrade_plan": upgrade_plan
    }

if __name__ == "__main__":
    main()