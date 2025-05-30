# /Users/han/Code/MOB-BREF/compliance_engine_standalone.py

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from regulatory_data_manager import RegulatoryDataManager, RIEActivity, BREFDocument, BATConclusion
from pdf_processor import extract_text_and_metadata

@dataclass
class PermitDocument:
    """Represents a permit document with metadata"""
    doc_id: str
    file_path: str
    document_type: str  # 'decision', 'application', 'advice', 'mer', 'other'
    title: Optional[str] = None
    date: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class PermitActivity:
    """Represents an activity described in a permit"""
    activity_description: str
    capacity: Optional[str] = None
    location: Optional[str] = None
    emissions: Optional[Dict] = None
    sector: Optional[str] = None

@dataclass
class ComplianceResult:
    """Results of compliance checking"""
    permit_id: str
    rie_compliance: Dict[str, Any]
    bref_applicability: List[Dict[str, Any]]
    bat_compliance: List[Dict[str, Any]]
    overall_assessment: str
    recommendations: List[str]
    legal_issues: List[str]
    timestamp: str

class PermitClassifier:
    """Classifies permits and extracts key information"""
    
    def __init__(self):
        self.sector_keywords = {
            'livestock': ['veehouderij', 'melkrundvee', 'varkens', 'pluimvee', 'kippen', 'runderen', 'dairy', 'cattle', 'pigs', 'poultry'],
            'chemical': ['chemisch', 'chemie', 'reactie', 'destillatie', 'chemical', 'reaction', 'distillation'],
            'energy': ['energie', 'verbranding', 'biomassa', 'warmte', 'stoom', 'energy', 'combustion', 'power'],
            'food': ['voedsel', 'melk', 'zuivel', 'slachterij', 'food', 'dairy', 'slaughter'],
            'waste': ['afval', 'waste', 'recycling', 'incineration', 'verbranding'],
            'metals': ['metaal', 'staal', 'ijzer', 'metal', 'steel', 'iron', 'aluminum'],
            'manufacturing': ['productie', 'fabricage', 'manufacturing', 'production']
        }
    
    def classify_documents(self, permit_folder: str) -> List[PermitDocument]:
        """Classify documents in a permit folder"""
        documents = []
        
        if not os.path.exists(permit_folder):
            raise ValueError(f"Permit folder not found: {permit_folder}")
        
        for filename in os.listdir(permit_folder):
            if not filename.lower().endswith('.pdf'):
                continue
                
            file_path = os.path.join(permit_folder, filename)
            doc_type = self._classify_document_type(filename)
            
            # Extract content (simplified for testing)
            try:
                extracted = extract_text_and_metadata(file_path)
                content = extracted.get('full_text', '') if extracted else ''
                title = extracted.get('title', '') if extracted else filename
            except Exception as e:
                print(f"Error extracting content from {filename}: {e}")
                content = ''
                title = filename
            
            document = PermitDocument(
                doc_id=filename,
                file_path=file_path,
                document_type=doc_type,
                title=title,
                content=content,
                date=self._extract_date_from_filename(filename)
            )
            documents.append(document)
        
        return documents
    
    def _classify_document_type(self, filename: str) -> str:
        """Classify document type based on filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['besluit', 'beschikking', 'decision']):
            return 'decision'
        elif any(word in filename_lower for word in ['aanvraag', 'application']):
            return 'application'
        elif any(word in filename_lower for word in ['advies', 'advice', 'rapport', 'report']):
            return 'advice'
        elif any(word in filename_lower for word in ['mer', 'eia']):
            return 'mer'
        else:
            return 'other'
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from filename if present"""
        date_patterns = [
            r'(\d{8})',  # YYYYMMDD
            r'(\d{6})',  # YYMMDD  
            r'(\d{2}-\d{2}-\d{2})',  # YY-MM-DD
            r'(\d{4}-\d{2}-\d{2})'   # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        
        return None
    
    def extract_activities(self, documents: List[PermitDocument]) -> List[PermitActivity]:
        """Extract activities from permit documents"""
        activities = []
        
        # Focus on application and decision documents
        relevant_docs = [doc for doc in documents if doc.document_type in ['application', 'decision']]
        
        for doc in relevant_docs:
            if not doc.content:
                continue
            
            # Extract activity information using pattern matching
            activity_text = self._extract_activity_description(doc.content)
            sector = self._classify_sector(doc.content)
            capacity = self._extract_capacity_info(doc.content)
            
            if activity_text:
                activity = PermitActivity(
                    activity_description=activity_text,
                    capacity=capacity,
                    sector=sector
                )
                activities.append(activity)
        
        return activities
    
    def _extract_activity_description(self, content: str) -> str:
        """Extract main activity description from content"""
        lines = content.split('\n')
        activity_lines = []
        
        in_activity_section = False
        for line in lines:
            line = line.strip()
            
            # Look for activity description headers
            if any(keyword in line.lower() for keyword in ['activiteit', 'inrichting', 'bedrijf', 'project', 'uitbreiden', 'melkrundvee']):
                in_activity_section = True
                activity_lines.append(line)
                continue
            
            if in_activity_section and line:
                activity_lines.append(line)
                if len(activity_lines) > 3:  # Limit description length
                    break
        
        return ' '.join(activity_lines) if activity_lines else 'Activity description not clearly identified'
    
    def _classify_sector(self, content: str) -> Optional[str]:
        """Classify the sector based on content"""
        content_lower = content.lower()
        
        for sector, keywords in self.sector_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return sector
        
        return None
    
    def _extract_capacity_info(self, content: str) -> Optional[str]:
        """Extract capacity/threshold information"""
        # Look for numerical values with units
        patterns = [
            r'(\d+(?:,\d+)?)\s*(MW|kW|ton|m3|m²|places|plaatsen|stuks)',
            r'(\d+(?:,\d+)?)\s*(aantal|capacity|melkkoeien|runderen)'
        ]
        
        capacities = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                capacities.extend([f"{match[0]} {match[1]}" for match in matches[:3]])
        
        return '; '.join(capacities) if capacities else None

class SimpleComplianceEngine:
    """Simplified compliance checking engine for testing without LLM"""
    
    def __init__(self, regulatory_manager: RegulatoryDataManager):
        self.reg_manager = regulatory_manager
        self.classifier = PermitClassifier()
    
    def check_permit_compliance(self, permit_folder: str, permit_id: str = None) -> ComplianceResult:
        """Perform compliance check on a permit"""
        if not permit_id:
            permit_id = os.path.basename(permit_folder)
        
        print(f"Starting compliance check for permit: {permit_id}")
        
        # Step 1: Classify and extract documents
        documents = self.classifier.classify_documents(permit_folder)
        print(f"Classified {len(documents)} documents")
        
        # Step 2: Extract activities
        activities = self.classifier.extract_activities(documents)
        print(f"Extracted {len(activities)} activities")
        
        # Step 3: Check RIE applicability
        rie_compliance = self._check_rie_compliance(activities)
        
        # Step 4: Determine applicable BREFs
        bref_applicability = self._determine_applicable_brefs(activities)
        
        # Step 5: Check BAT compliance (simplified)
        bat_compliance = self._check_bat_compliance_simple(documents, bref_applicability)
        
        # Step 6: Check procedural compliance
        legal_issues = self._check_procedural_compliance(documents)
        
        # Step 7: Generate assessment
        overall_assessment, recommendations = self._generate_assessment(
            rie_compliance, bref_applicability, bat_compliance, legal_issues
        )
        
        result = ComplianceResult(
            permit_id=permit_id,
            rie_compliance=rie_compliance,
            bref_applicability=bref_applicability,
            bat_compliance=bat_compliance,
            overall_assessment=overall_assessment,
            recommendations=recommendations,
            legal_issues=legal_issues,
            timestamp=datetime.now().isoformat()
        )
        
        print(f"Compliance check completed for permit: {permit_id}")
        return result
    
    def _check_rie_compliance(self, activities: List[PermitActivity]) -> Dict[str, Any]:
        """Check if activities fall under RIE regulation"""
        applicable_activities = []
        
        for activity in activities:
            rie_activities = self.reg_manager.get_applicable_rie_activities(activity.activity_description)
            
            for rie_activity in rie_activities:
                applicable_activities.append({
                    'permit_activity': activity.activity_description,
                    'rie_category': rie_activity.category,
                    'rie_description': rie_activity.activity_description,
                    'threshold_values': rie_activity.threshold_values,
                    'capacity_check_needed': True,
                    'capacity_info': activity.capacity
                })
        
        return {
            'applicable_activities': applicable_activities,
            'requires_rie_compliance': len(applicable_activities) > 0,
            'total_activities_checked': len(activities)
        }
    
    def _determine_applicable_brefs(self, activities: List[PermitActivity]) -> List[Dict[str, Any]]:
        """Determine which BREFs are applicable (simplified)"""
        applicable_brefs = []
        
        for activity in activities:
            if activity.sector:
                brefs = self.reg_manager.get_applicable_brefs(sector=activity.sector)
                
                for bref in brefs:
                    # Simple keyword-based applicability assessment
                    applicability = "Potentially Applicable" if activity.sector == "livestock" and "IRPP" in bref.bref_id else "Requires Review"
                    
                    applicable_brefs.append({
                        'bref_id': bref.bref_id,
                        'bref_title': bref.title,
                        'applicability': applicability,
                        'justification': f'Sector match: {activity.sector}',
                        'confidence': 'Medium',
                        'activity_description': activity.activity_description
                    })
        
        return applicable_brefs
    
    def _check_bat_compliance_simple(self, documents: List[PermitDocument], applicable_brefs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simplified BAT compliance check"""
        bat_compliance_results = []
        
        # Get permit content
        permit_content = ''
        for doc in documents:
            if doc.document_type in ['application', 'decision'] and doc.content:
                permit_content += doc.content + '\n'
        
        for bref_info in applicable_brefs:
            if bref_info.get('applicability') in ['Likely Applicable', 'Potentially Applicable']:
                bref_id = bref_info.get('bref_id')
                
                # Get BAT conclusions for this BREF
                bat_conclusions = self.reg_manager.get_bat_conclusions_for_bref(bref_id)
                
                # If no BAT conclusions in DB, create sample ones for livestock
                if not bat_conclusions and bref_id == 'IRPP':
                    bat_conclusions = [
                        BATConclusion(
                            bat_id="IRPP_BAT_1",
                            bref_source="IRPP",
                            title="BAT 1: Nutritional management",
                            description="To reduce nitrogen and phosphorus excretion and ammonia emissions, BAT is to use nutritional management",
                            applicability="Applicable to all livestock installations"
                        ),
                        BATConclusion(
                            bat_id="IRPP_BAT_2", 
                            bref_source="IRPP",
                            title="BAT 2: Housing and management",
                            description="To reduce ammonia emissions from housing, BAT is to use appropriate housing and management techniques",
                            applicability="Applicable to all livestock installations"
                        )
                    ]
                
                for bat_conclusion in bat_conclusions:
                    # Simple text-based compliance check
                    compliance_status = self._simple_bat_check(permit_content, bat_conclusion)
                    
                    bat_compliance_results.append({
                        'bat_id': bat_conclusion.bat_id,
                        'bat_title': bat_conclusion.title,
                        'compliance_status': compliance_status,
                        'detailed_findings': f'Simple text analysis for {bat_conclusion.title}',
                        'source_bref_id': bref_id,
                        'bat_description': bat_conclusion.description[:200] + "..." if len(bat_conclusion.description) > 200 else bat_conclusion.description
                    })
        
        return bat_compliance_results
    
    def _simple_bat_check(self, permit_content: str, bat_conclusion: BATConclusion) -> str:
        """Simple BAT compliance check based on keyword matching"""
        content_lower = permit_content.lower()
        
        # Look for relevant keywords in permit content
        if 'nutritional' in bat_conclusion.title.lower():
            if any(word in content_lower for word in ['voer', 'voeding', 'nutrition', 'feed']):
                return "Potentially Compliant"
            else:
                return "Requires Review"
        
        elif 'housing' in bat_conclusion.title.lower():
            if any(word in content_lower for word in ['huisvesting', 'stal', 'housing', 'barn']):
                return "Potentially Compliant"
            else:
                return "Requires Review"
        
        elif 'emission' in bat_conclusion.description.lower():
            if any(word in content_lower for word in ['emissie', 'uitstoot', 'emission']):
                return "Potentially Compliant"
            else:
                return "Non-Compliant"
        
        return "Requires Review"
    
    def _check_procedural_compliance(self, documents: List[PermitDocument]) -> List[str]:
        """Check procedural compliance"""
        issues = []
        
        # Check for MER documents
        mer_docs = [doc for doc in documents if doc.document_type == 'mer']
        mer_assessment = any('beoordelingsbesluit' in doc.title.lower() for doc in mer_docs if doc.title)
        mer_notification = any('aanmeldnotitie' in doc.title.lower() for doc in mer_docs if doc.title)
        
        if mer_assessment and not mer_notification:
            issues.append("MER assessment decision present but no MER notification found - consultation rights may be violated")
        
        # Check for decision document
        decision_docs = [doc for doc in documents if doc.document_type == 'decision']
        if not decision_docs:
            issues.append("No decision document found in permit file")
        
        # Check for application documents
        application_docs = [doc for doc in documents if doc.document_type == 'application']
        if not application_docs:
            issues.append("No application document found in permit file")
        
        return issues
    
    def _generate_assessment(self, rie_compliance: Dict, bref_applicability: List, 
                           bat_compliance: List, legal_issues: List) -> Tuple[str, List[str]]:
        """Generate overall assessment and recommendations"""
        
        recommendations = []
        
        # Check RIE compliance
        if rie_compliance.get('requires_rie_compliance', False):
            recommendations.append("Verify that installation meets RIE threshold values and has appropriate permit")
        
        # Check BAT compliance issues
        non_compliant_bats = [bat for bat in bat_compliance if bat.get('compliance_status') == 'Non-Compliant']
        review_needed_bats = [bat for bat in bat_compliance if bat.get('compliance_status') == 'Requires Review']
        
        if non_compliant_bats:
            recommendations.append(f"Address {len(non_compliant_bats)} non-compliant BAT conclusions")
        
        if review_needed_bats:
            recommendations.append(f"Review {len(review_needed_bats)} BAT conclusions that require detailed analysis")
        
        # Check legal issues
        if legal_issues:
            recommendations.extend([f"Legal issue: {issue}" for issue in legal_issues])
        
        # Generate overall assessment
        total_issues = len(non_compliant_bats) + len(legal_issues)
        
        if total_issues == 0:
            assessment = "Permit appears to be compliant with applicable regulations"
        elif total_issues <= 2:
            assessment = f"Permit has {total_issues} compliance issue(s) that should be addressed"
        else:
            assessment = f"Permit has significant compliance issues ({total_issues} issues identified)"
        
        return assessment, recommendations
    
    def save_compliance_report(self, result: ComplianceResult, output_path: str):
        """Save compliance report to JSON file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        print(f"Compliance report saved to: {output_path}")

# Testing function
def test_system():
    """Test the compliance system with the livestock example"""
    print("Testing compliance system...")
    
    # Initialize system
    reg_manager = RegulatoryDataManager()
    if not os.path.exists(reg_manager.db_path):
        reg_manager.setup_system()
    
    engine = SimpleComplianceEngine(reg_manager)
    
    # Test with livestock permit example
    livestock_folder = "/Users/han/Code/MOB-BREF/documents/Voorbeeld documenten Veehouderij"
    
    if os.path.exists(livestock_folder):
        result = engine.check_permit_compliance(livestock_folder, "Livestock_Permit_Example")
        
        # Save report
        report_path = "/Users/han/Code/MOB-BREF/reports/compliance_report_livestock.json"
        engine.save_compliance_report(result, report_path)
        
        print("\n=== COMPLIANCE SUMMARY ===")
        print(f"Overall Assessment: {result.overall_assessment}")
        print(f"RIE Compliance Required: {result.rie_compliance.get('requires_rie_compliance', False)}")
        print(f"Applicable BREFs: {len(result.bref_applicability)}")
        print(f"BAT Compliance Issues: {len([b for b in result.bat_compliance if b.get('compliance_status') == 'Non-Compliant'])}")
        print(f"Legal Issues: {len(result.legal_issues)}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"- {rec}")
                
        print(f"\nDetailed report saved to: {report_path}")
    else:
        print(f"Livestock folder not found: {livestock_folder}")

if __name__ == "__main__":
    test_system()