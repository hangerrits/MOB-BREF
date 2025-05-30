#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/bat_extraction_summary.py

"""
BAT Extraction Summary
Create a concise summary of extracted BATs for review
"""

import json
import os
from datetime import datetime

def create_bat_summary():
    """Create a summary of extracted BATs for review"""
    
    print("📊 === BAT EXTRACTION SUMMARY ===\n")
    
    # Load the enhanced database
    db_file = "/Users/han/Code/MOB-BREF/enhanced_bat_database.json"
    
    if not os.path.exists(db_file):
        print("❌ Enhanced database not found. Run enhanced extraction first.")
        return
    
    with open(db_file, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    metadata = database['metadata']
    bats_by_bref = database['bats_by_bref']
    
    print(f"🎯 **EXTRACTION RESULTS**")
    print(f"📅 Extracted on: {metadata['extraction_date'][:19]}")
    print(f"📊 Total BATs: **{metadata['total_bats']}**")
    print(f"📋 BREFs processed: **{len(metadata['brefs_processed'])}**")
    print(f"⚙️ Extractor: {metadata['extractor_version']}")
    
    print(f"\n📋 **BATs PER BREF:**")
    for bref_id, count in metadata['bats_per_bref'].items():
        print(f"   ✓ **{bref_id}**: {count} BATs")
    
    print(f"\n🔍 **SAMPLE BATs FOR REVIEW:**")
    
    # Show samples from each BREF
    for bref_id, bats in bats_by_bref.items():
        print(f"\n📋 **{bref_id} BREF ({len(bats)} BATs):**")
        
        # Show first 3 BATs as samples
        for i, bat in enumerate(bats[:3]):
            title = bat['title'][:80] + "..." if len(bat['title']) > 80 else bat['title']
            print(f"   {i+1}. {bat['bat_id']}: {title}")
            print(f"      Page: {bat['page']} | Method: {bat['extraction_method'][:40]}...")
        
        if len(bats) > 3:
            print(f"   ... and {len(bats) - 3} more BATs")
    
    # Create validation checklist
    print(f"\n✅ **VALIDATION CHECKLIST:**")
    print(f"Please review each BREF section:")
    
    for bref_id, bats in bats_by_bref.items():
        print(f"\n□ **{bref_id} BREF ({len(bats)} BATs):**")
        print(f"  □ Check if all expected BATs are captured")
        print(f"  □ Verify BAT numbers are sequential and correct")
        print(f"  □ Confirm descriptions are complete and accurate")
        print(f"  □ Validate page references are correct")
        print(f"  □ Assess if referenced sections need inclusion")
    
    # Create detailed review file
    create_detailed_review_file(bats_by_bref)
    
    print(f"\n📄 **FILES GENERATED:**")
    print(f"📊 Database: enhanced_bat_database.json")
    print(f"📋 Review Report: enhanced_bat_review_report.html")
    print(f"📝 Summary: bat_detailed_review.txt")
    
    print(f"\n🎯 **NEXT STEPS:**")
    print(f"1. Review the HTML report: enhanced_bat_review_report.html")
    print(f"2. Validate BAT accuracy against source documents")
    print(f"3. Note any corrections needed in bat_detailed_review.txt")
    print(f"4. Confirm referenced sections are properly included")
    print(f"5. Once validated, integrate into compliance system")

def create_detailed_review_file(bats_by_bref):
    """Create detailed text file for BAT review"""
    
    content = f"""BAT EXTRACTION DETAILED REVIEW
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INSTRUCTIONS:
- Review each BAT entry below
- Mark ✓ for correct extractions
- Mark ✗ for incorrect extractions
- Add comments for any needed corrections

=================================================================
"""
    
    for bref_id, bats in bats_by_bref.items():
        content += f"""
BREF: {bref_id} ({len(bats)} BATs)
=================================

"""
        
        for bat in bats:
            content += f"""
□ {bat['bat_id']}: {bat['title']}
   Page: {bat['page']}
   Extraction: {bat['extraction_method']}
   
   Raw Text (first 200 chars):
   {bat['raw_text'][:200]}...
   
   VALIDATION:
   □ BAT number correct
   □ Title accurate
   □ Text complete
   □ Page reference correct
   □ References resolved (if any)
   
   Comments: ________________________________
   
   Quality: ⭐⭐⭐⭐⭐ (1-5 stars)
   
---------------------------------------------------
"""
    
    content += f"""

SUMMARY VALIDATION:
==================

Total BATs reviewed: {sum(len(bats) for bats in bats_by_bref.values())}

BREF COMPLETION STATUS:
"""
    
    for bref_id, bats in bats_by_bref.items():
        content += f"□ {bref_id}: {len(bats)} BATs - Complete/Incomplete/Needs Review\n"
    
    content += f"""

OVERALL ASSESSMENT:
□ Extraction quality is acceptable
□ Ready for integration into compliance system
□ Needs corrections (specify below)

CORRECTIONS NEEDED:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

NEXT STEPS:
□ Validate against source BREF documents
□ Correct any extraction errors
□ Include missing referenced sections
□ Integrate validated BATs into compliance system

Reviewer: _____________________ Date: ______________
"""
    
    with open("bat_detailed_review.txt", 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📝 Detailed review file created: bat_detailed_review.txt")

def show_database_structure():
    """Show the database structure for integration"""
    
    print(f"\n🏗️ **DATABASE STRUCTURE:**")
    print(f"""
The extracted BATs are stored in JSON format with this structure:

{{
  "metadata": {{
    "extraction_date": "2025-05-30T07:45:30",
    "total_bats": 177,
    "brefs_processed": ["ICS", "ENE", "CVS", "OFC", "NEW", "SA", "WI"],
    "bats_per_bref": {{"ENE": 29, "WT": 0, ...}},
    "extractor_version": "EnhancedMultiBREFExtractor v1.0"
  }},
  "bats_by_bref": {{
    "ENE": [
      {{
        "bref_id": "ENE",
        "bat_number": 1,
        "bat_id": "ENE-BAT-1",
        "title": "ENEMS",
        "raw_text": "Complete BAT text including context...",
        "page": 303,
        "extraction_method": "Enhanced pattern: BAT...",
        "extraction_date": "2025-05-30T07:45:21"
      }}
    ]
  }},
  "all_bats": [...]
}}

This structure allows:
✓ Individual BAT lookup by BREF-id and BAT number
✓ Complete BAT text for permit comparison
✓ Traceability to source document pages
✓ Easy integration into compliance checking
""")

def integration_proposal():
    """Show how to integrate BATs into existing system"""
    
    print(f"\n🔗 **INTEGRATION WITH EXISTING SYSTEM:**")
    print(f"""
To replace the mock BAT system with real extracted BATs:

1. MODIFY generate_full_conclusions_report.py:
   - Replace mock BAT generation (lines 116-318)
   - Load real BATs from enhanced_bat_database.json
   - Use actual BAT text for compliance checking

2. UPDATE compliance assessment logic:
   - Compare permit text against real BAT requirements
   - Use actual BAT titles and descriptions
   - Reference source document pages in reports

3. ENHANCE reporting:
   - Include official BREF citations
   - Show real BAT text in assessments
   - Provide legally defensible compliance determinations

EXAMPLE CODE:
```python
def load_real_bats():
    with open('enhanced_bat_database.json', 'r') as f:
        return json.load(f)

def create_ene_real_conclusions(permit_text):
    db = load_real_bats()
    ene_bats = db['bats_by_bref']['ENE']
    
    conclusions = []
    for bat in ene_bats:
        # Use real BAT text for compliance checking
        compliance = assess_real_bat_compliance(
            bat['raw_text'], 
            permit_text,
            bat['bat_id']
        )
        conclusions.append({{
            'bat_id': bat['bat_id'],
            'title': bat['title'],
            'compliance_status': compliance['status'],
            'source_page': bat['page'],
            'bref_citation': f"ENE BREF page {{bat['page']}}"
        }})
    
    return conclusions
```
""")

if __name__ == "__main__":
    create_bat_summary()
    show_database_structure()
    integration_proposal()