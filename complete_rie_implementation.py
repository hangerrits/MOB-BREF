#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/complete_rie_implementation.py

"""
Complete RIE Annex I Implementation
Implementeert alle 29 officiële RIE activiteiten in database
"""

import sqlite3
from regulatory_data_manager import RegulatoryDataManager, RIEActivity

def get_complete_rie_activities():
    """Complete lijst van alle RIE Annex I activiteiten"""
    return [
        # 1. ENERGIE-INDUSTRIEËN
        RIEActivity(
            category="1. Energie-industrieën",
            activity_description="Verbrandingsinstallaties met een nominaal thermisch vermogen van meer dan 50 MW",
            threshold_values="> 50 MW thermisch vermogen"
        ),
        RIEActivity(
            category="1. Energie-industrieën", 
            activity_description="Raffinaderijen van minerale olie en gas",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="1. Energie-industrieën",
            activity_description="Cokesovens",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="1. Energie-industrieën",
            activity_description="Installaties voor vergassing en vloeibaarstelling van kool",
            threshold_values="Alle capaciteiten"
        ),
        
        # 2. PRODUCTIE EN VERWERKING VAN METALEN
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Installaties voor roosten of sinteren van metaalerts",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Installaties voor de productie van ruwijzer of staal (primaire of secundaire smelting) inclusief continugieten",
            threshold_values="> 2,5 ton per uur"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen", 
            activity_description="Installaties voor de verwerking van ferro-metalen",
            threshold_values="> 20 ton ruimtaal per dag"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Gieterijen van ferro-metalen",
            threshold_values="> 20 ton per dag productiecapaciteit"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Installaties voor de productie van non-ferro ruwe metalen uit erts, concentraten of secundaire grondstoffen door metallurgische, chemische of elektrolytische processen",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Installaties voor het smelten van non-ferro metalen, inclusief legeringen",
            threshold_values="> 4 ton per dag voor lood en cadmium of > 20 ton per dag voor andere metalen"
        ),
        RIEActivity(
            category="2. Productie en verwerking van metalen",
            activity_description="Installaties voor oppervlaktebehandeling van metalen en kunststoffen door een elektrolytisch of chemisch procédé",
            threshold_values="Volume van de behandelingsbakken > 30 m³"
        ),
        
        # 3. MINERALE INDUSTRIE
        RIEActivity(
            category="3. Minerale industrie",
            activity_description="Installaties voor de productie van cement, kalk en magnesiumoxide",
            threshold_values="Cement > 500 ton/dag, Kalk > 50 ton/dag, MgO alle capaciteiten"
        ),
        RIEActivity(
            category="3. Minerale industrie",
            activity_description="Installaties voor de productie van asbest en asbestproducten",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="3. Minerale industrie",
            activity_description="Installaties voor de vervaardiging van glas, inclusief glasvezels",
            threshold_values="> 20 ton per dag smeltcapaciteit"
        ),
        RIEActivity(
            category="3. Minerale industrie",
            activity_description="Installaties voor het smelten van minerale stoffen, inclusief de productie van mineraalvezels",
            threshold_values="> 20 ton per dag smeltcapaciteit"
        ),
        RIEActivity(
            category="3. Minerale industrie", 
            activity_description="Installaties voor de vervaardiging van keramische producten door verhitting",
            threshold_values="> 75 ton per dag productiecapaciteit en/of > 4 m³ ovencapaciteit en > 300 kg/m³ laaddichtheid per oven"
        ),
        
        # 4. CHEMISCHE INDUSTRIE
        RIEActivity(
            category="4. Chemische industrie",
            activity_description="Chemische installaties voor de productie op industriële schaal van organische basischemicaliën",
            threshold_values="Industriële schaal productie"
        ),
        RIEActivity(
            category="4. Chemische industrie",
            activity_description="Chemische installaties voor de productie op industriële schaal van anorganische basischemicaliën",
            threshold_values="Industriële schaal productie"
        ),
        RIEActivity(
            category="4. Chemische industrie",
            activity_description="Chemische installaties voor de productie op industriële schaal van fosfaat-, kalium- of stikstofkunstmeststoffen",
            threshold_values="Industriële schaal productie"
        ),
        RIEActivity(
            category="4. Chemische industrie",
            activity_description="Chemische installaties voor de productie op industriële schaal van biociden en farmaceutische producten",
            threshold_values="Industriële schaal productie"
        ),
        RIEActivity(
            category="4. Chemische industrie",
            activity_description="Chemische installaties die gebruikmaken van een chemisch of biologisch procédé voor de productie op industriële schaal van explosieven",
            threshold_values="Industriële schaal productie"
        ),
        
        # 5. AFVALBEHEER
        RIEActivity(
            category="5. Afvalbeheer",
            activity_description="Installaties voor de verwijdering of benutting van gevaarlijk afval",
            threshold_values="> 10 ton per dag capaciteit"
        ),
        RIEActivity(
            category="5. Afvalbeheer",
            activity_description="Installaties voor de verbranding van gemeentelijk afval",
            threshold_values="> 3 ton per uur capaciteit"
        ),
        RIEActivity(
            category="5. Afvalbeheer",
            activity_description="Installaties voor de verwijdering van niet-gevaarlijk afval",
            threshold_values="> 50 ton per dag capaciteit"
        ),
        RIEActivity(
            category="5. Afvalbeheer",
            activity_description="Stortplaatsen die meer dan 10 ton afval per dag ontvangen of een totale capaciteit van meer dan 25 000 ton hebben",
            threshold_values="> 10 ton/dag of > 25.000 ton totaal"
        ),
        
        # 6. ANDERE ACTIVITEITEN
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Industriële installaties voor de productie van pulp uit hout of andere vezelhoudende materialen",
            threshold_values="> 20 ton per dag productiecapaciteit"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Industriële installaties voor de productie van papier en karton",
            threshold_values="> 20 ton per dag productiecapaciteit"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de voorbehandeling of het verven van vezels of textiel",
            threshold_values="> 10 ton per dag verwerkingscapaciteit"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor het looien van huiden",
            threshold_values="> 12 ton per dag capaciteit van afgewerkte producten"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Slachthuizen",
            threshold_values="> 50 ton per dag geslacht gewicht"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de behandeling en verwerking van voedingsmiddelen",
            threshold_values="Afgewerkte producten > 300 ton/dag (gemiddeld op kwartaalbasis)"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de behandeling en verwerking van melk",
            threshold_values="Ontvangen melk > 200 ton per dag (gemiddeld op jaarbasis)"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de intensieve pluimveehouderij of varkenshouderij",
            threshold_values="> 40.000 plaatsen pluimvee, > 2.000 plaatsen varkens (>30kg), > 750 plaatsen zeugen"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor oppervlaktebehandeling van stoffen, voorwerpen of producten met organische oplosmiddelen",
            threshold_values="> 150 kg/h of > 200 ton/jaar oplosmiddelverbruik"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de productie van koolstof (hard gebakken kool) of elektrografiet door verbranding of grafitisering",
            threshold_values="Alle capaciteiten"
        ),
        RIEActivity(
            category="6. Andere activiteiten",
            activity_description="Installaties voor de bouw van, en het verven of verwijderen van verf van schepen",
            threshold_values="> 100 m scheepslengte"
        )
    ]

def implement_complete_rie():
    """Implementeer alle RIE activiteiten in database"""
    
    print("🏛️ === COMPLETE RIE IMPLEMENTATIE ===")
    print("Implementatie van alle 35 RIE Annex I activiteiten\n")
    
    manager = RegulatoryDataManager()
    activities = get_complete_rie_activities()
    
    print(f"📋 Totaal activiteiten te implementeren: {len(activities)}")
    
    # Clear existing and insert all
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    
    # Clear existing RIE activities
    cursor.execute('DELETE FROM rie_activities')
    print("🗑️ Existing RIE activities cleared")
    
    # Insert all activities
    for i, activity in enumerate(activities, 1):
        cursor.execute('''
            INSERT INTO rie_activities 
            (category, activity_description, threshold_values, notes)
            VALUES (?, ?, ?, ?)
        ''', (activity.category, activity.activity_description, 
              activity.threshold_values, activity.notes))
        print(f"✅ {i:2d}. {activity.category}: {activity.activity_description[:50]}...")
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM rie_activities')
    count = cursor.fetchone()[0]
    
    print(f"\n📊 === IMPLEMENTATIE RESULTAAT ===")
    print(f"✅ RIE activiteiten in database: {count}")
    print(f"🎯 Expected: {len(activities)}")
    
    if count == len(activities):
        print("🎉 VOLLEDIGE RIE IMPLEMENTATIE SUCCESVOL!")
    else:
        print("⚠️ Niet alle activiteiten geïmplementeerd")
    
    # Show categories
    cursor.execute('''
        SELECT category, COUNT(*) 
        FROM rie_activities 
        GROUP BY category 
        ORDER BY category
    ''')
    categories = cursor.fetchall()
    
    print(f"\n📋 === RIE CATEGORIEËN ===")
    for category, count in categories:
        print(f"  {category}: {count} activiteiten")
    
    conn.close()
    return count == len(activities)

if __name__ == "__main__":
    success = implement_complete_rie()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")