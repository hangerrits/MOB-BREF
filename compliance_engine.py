# /Users/han/Code/MOB-BREF/compliance_engine.py

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from regulatory_data_manager import RegulatoryDataManager, RIEActivity, BREFDocument, BATConclusion
from pdf_processor import extract_text_and_metadata
from llm_handler import determine_applicable_brefs, verify_permit_compliance_with_bat

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
            
            # Extract content
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
        # Look for date patterns like YYYYMMDD, YY-MM-DD, etc.
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
        # Look for key sections that describe the activity
        lines = content.split('\n')
        activity_lines = []
        
        in_activity_section = False
        for line in lines:
            line = line.strip()
            
            # Look for activity description headers
            if any(keyword in line.lower() for keyword in ['activiteit', 'inrichting', 'bedrijf', 'project']):
                in_activity_section = True
                continue
            
            if in_activity_section and line:
                activity_lines.append(line)
                if len(activity_lines) > 5:  # Limit description length
                    break
        
        return ' '.join(activity_lines) if activity_lines else ''
    
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
            r'(\d+(?:,\d+)?)\s*(MW|kW|ton|m3|m²|places|plaatsen)',
            r'(\d+(?:,\d+)?)\s*(stuks|aantal|capacity)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return '; '.join([f"{match[0]} {match[1]}" for match in matches[:3]])
        
        return None

class ComplianceEngine:
    """Main compliance checking engine"""
    
    def __init__(self, regulatory_manager: RegulatoryDataManager):
        self.reg_manager = regulatory_manager
        self.classifier = PermitClassifier()
    
    def check_permit_compliance(self, permit_folder: str, permit_id: str = None) -> ComplianceResult:
        """Perform comprehensive compliance check on a permit"""
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
        
        # Step 5: Check BAT compliance
        bat_compliance = self._check_bat_compliance(documents, bref_applicability)
        
        # Step 6: Check procedural compliance (MER, etc.)
        legal_issues = self._check_procedural_compliance(documents)
        
        # Step 7: Generate overall assessment
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
            # Get potentially applicable RIE activities
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
        """Determine which BREFs are applicable"""
        applicable_brefs = []
        
        for activity in activities:
            if activity.sector:
                brefs = self.reg_manager.get_applicable_brefs(sector=activity.sector)
                
                for bref in brefs:
                    # Use LLM to determine detailed applicability
                    try:
                        llm_analysis = determine_applicable_brefs(
                            activity.activity_description,
                            [{'bref_id': bref.bref_id, 'scope_description': bref.title}]
                        )
                        
                        if llm_analysis:
                            applicable_brefs.extend(llm_analysis)
                    except Exception as e:
                        # Fallback to simple keyword matching
                        applicable_brefs.append({
                            'bref_id': bref.bref_id,
                            'bref_title': bref.title,
                            'applicability': 'Potentially Applicable',
                            'justification': f'Sector match: {activity.sector}',
                            'confidence': 'Medium'
                        })
        
        return applicable_brefs
    
    def _check_bat_compliance(self, documents: List[PermitDocument], applicable_brefs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check compliance with BAT conclusions"""
        bat_compliance_results = []
        
        # Get permit content for analysis
        permit_content = ''
        for doc in documents:
            if doc.document_type in ['application', 'decision'] and doc.content:
                permit_content += doc.content + '\n'
        
        for bref_info in applicable_brefs:
            if bref_info.get('applicability') in ['Likely Applicable', 'Potentially Applicable']:
                bref_id = bref_info.get('bref_id')
                
                # Get BAT conclusions for this BREF
                bat_conclusions = self.reg_manager.get_bat_conclusions_for_bref(bref_id)
                
                for bat_conclusion in bat_conclusions:
                    try:
                        # Use LLM to verify compliance
                        compliance_result = verify_permit_compliance_with_bat(permit_content, {
                            'bat_id': bat_conclusion.bat_id,
                            'title': bat_conclusion.title,
                            'description': bat_conclusion.description,
                            'applicability': bat_conclusion.applicability
                        })
                        
                        bat_compliance_results.append(compliance_result)
                        
                    except Exception as e:
                        # Fallback to simple text matching
                        bat_compliance_results.append({
                            'bat_id': bat_conclusion.bat_id,
                            'compliance_status': 'Unable to Determine',
                            'detailed_findings': f'Error in analysis: {e}',
                            'source_bref_id': bref_id
                        })
        
        return bat_compliance_results
    
    def _check_procedural_compliance(self, documents: List[PermitDocument]) -> List[str]:
        """Check procedural compliance (MER, consultation, etc.)"""
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
        if non_compliant_bats:
            recommendations.append(f"Address {len(non_compliant_bats)} non-compliant BAT conclusions")
        
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
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
        print(f"Compliance report saved to: {output_path}")

# Testing function
def test_system():
    """Test the compliance system with the livestock example"""
    print("Testing compliance system...")
    
    # Initialize system
    reg_manager = RegulatoryDataManager()
    reg_manager.setup_system()
    
    engine = ComplianceEngine(reg_manager)
    
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
    else:
        print(f"Livestock folder not found: {livestock_folder}")

if __name__ == "__main__":
    test_system()