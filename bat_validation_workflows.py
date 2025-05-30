"""
BAT Validation Workflows and Relationship Management
Handles expert validation, relationship mapping, and data quality assurance.
"""

from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import json
from pathlib import Path

from bat_data_models import (
    BATConclusion, BREFDocument, ComplianceKnowledgeBase,
    RelationshipType, BATRelationship, ValidationStatus,
    ExtractionMethod, ExtractionMetadata
)


class ValidationRule(str, Enum):
    """Types of validation rules for BAT data"""
    MANDATORY_FIELDS = "mandatory_fields"
    EMISSION_LIMITS_CONSISTENCY = "emission_limits_consistency"
    MONITORING_ALIGNMENT = "monitoring_alignment"
    RELATIONSHIP_VALIDITY = "relationship_validity"
    APPLICABILITY_LOGIC = "applicability_logic"
    CROSS_REFERENCE_INTEGRITY = "cross_reference_integrity"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"  # Blocks usage
    WARNING = "warning"    # Should be reviewed
    INFO = "info"         # Informational


class ValidationIssue:
    """Represents a validation issue found in BAT data"""
    
    def __init__(
        self,
        rule: ValidationRule,
        severity: ValidationSeverity,
        message: str,
        bat_id: str,
        field_path: Optional[str] = None,
        suggested_fix: Optional[str] = None
    ):
        self.rule = rule
        self.severity = severity
        self.message = message
        self.bat_id = bat_id
        self.field_path = field_path
        self.suggested_fix = suggested_fix
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "rule": self.rule.value,
            "severity": self.severity.value,
            "message": self.message,
            "bat_id": self.bat_id,
            "field_path": self.field_path,
            "suggested_fix": self.suggested_fix,
            "timestamp": self.timestamp.isoformat()
        }


class BATValidator:
    """Comprehensive BAT data validator with expert workflow support"""
    
    def __init__(self):
        self.validation_rules = {
            ValidationRule.MANDATORY_FIELDS: self._validate_mandatory_fields,
            ValidationRule.EMISSION_LIMITS_CONSISTENCY: self._validate_emission_limits,
            ValidationRule.MONITORING_ALIGNMENT: self._validate_monitoring_alignment,
            ValidationRule.RELATIONSHIP_VALIDITY: self._validate_relationships,
            ValidationRule.APPLICABILITY_LOGIC: self._validate_applicability,
            ValidationRule.CROSS_REFERENCE_INTEGRITY: self._validate_cross_references
        }
    
    def validate_bat(self, bat: BATConclusion, context: Optional[List[BATConclusion]] = None) -> List[ValidationIssue]:
        """Validate a single BAT conclusion"""
        issues = []
        
        for rule, validator_func in self.validation_rules.items():
            try:
                rule_issues = validator_func(bat, context or [])
                issues.extend(rule_issues)
            except Exception as e:
                issues.append(ValidationIssue(
                    rule=rule,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation rule {rule.value} failed: {str(e)}",
                    bat_id=bat.bat_id
                ))
        
        return issues
    
    def validate_bref_document(self, bref: BREFDocument) -> Dict[str, List[ValidationIssue]]:
        """Validate entire BREF document with cross-BAT validation"""
        results = {}
        all_bats = bref.bat_conclusions
        
        for bat in all_bats:
            issues = self.validate_bat(bat, all_bats)
            if issues:
                results[bat.bat_id] = issues
        
        # Cross-document validation
        cross_issues = self._validate_cross_document_integrity(bref)
        if cross_issues:
            results["_cross_document"] = cross_issues
        
        return results
    
    def _validate_mandatory_fields(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate that mandatory fields are present and valid"""
        issues = []
        
        # Check critical fields
        if not bat.bat_title.strip():
            issues.append(ValidationIssue(
                rule=ValidationRule.MANDATORY_FIELDS,
                severity=ValidationSeverity.CRITICAL,
                message="BAT title is missing or empty",
                bat_id=bat.bat_id,
                field_path="bat_title"
            ))
        
        if not bat.bat_description.strip():
            issues.append(ValidationIssue(
                rule=ValidationRule.MANDATORY_FIELDS,
                severity=ValidationSeverity.CRITICAL,
                message="BAT description is missing or empty",
                bat_id=bat.bat_id,
                field_path="bat_description"
            ))
        
        # Check source metadata completeness
        if not bat.source_metadata.document_title:
            issues.append(ValidationIssue(
                rule=ValidationRule.MANDATORY_FIELDS,
                severity=ValidationSeverity.CRITICAL,
                message="Source document title is missing",
                bat_id=bat.bat_id,
                field_path="source_metadata.document_title"
            ))
        
        return issues
    
    def _validate_emission_limits(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate emission limit values for consistency"""
        issues = []
        
        for i, elv in enumerate(bat.emission_limit_values):
            # Check for reasonable values
            if elv.limit_value <= 0:
                issues.append(ValidationIssue(
                    rule=ValidationRule.EMISSION_LIMITS_CONSISTENCY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Emission limit value {elv.limit_value} seems unrealistic (non-positive)",
                    bat_id=bat.bat_id,
                    field_path=f"emission_limit_values[{i}].limit_value"
                ))
            
            # Check unit consistency
            if not elv.unit.strip():
                issues.append(ValidationIssue(
                    rule=ValidationRule.EMISSION_LIMITS_CONSISTENCY,
                    severity=ValidationSeverity.CRITICAL,
                    message="Emission limit unit is missing",
                    bat_id=bat.bat_id,
                    field_path=f"emission_limit_values[{i}].unit"
                ))
            
            # Validate performance ranges
            if elv.minimum_performance and elv.maximum_performance:
                if elv.minimum_performance > elv.maximum_performance:
                    issues.append(ValidationIssue(
                        rule=ValidationRule.EMISSION_LIMITS_CONSISTENCY,
                        severity=ValidationSeverity.WARNING,
                        message="Minimum performance exceeds maximum performance",
                        bat_id=bat.bat_id,
                        field_path=f"emission_limit_values[{i}]"
                    ))
        
        return issues
    
    def _validate_monitoring_alignment(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate that monitoring requirements align with emission limits"""
        issues = []
        
        # Get pollutants from emission limits
        elv_pollutants = {elv.pollutant for elv in bat.emission_limit_values}
        
        # Check if monitoring covers all emission limit pollutants
        for req in bat.monitoring_requirements:
            monitored_pollutants = set(req.parameters)
            
            missing_pollutants = elv_pollutants - monitored_pollutants
            if missing_pollutants:
                issues.append(ValidationIssue(
                    rule=ValidationRule.MONITORING_ALIGNMENT,
                    severity=ValidationSeverity.WARNING,
                    message=f"Missing monitoring for pollutants with emission limits: {missing_pollutants}",
                    bat_id=bat.bat_id,
                    suggested_fix=f"Add monitoring for: {', '.join(str(p.value) for p in missing_pollutants)}"
                ))
        
        return issues
    
    def _validate_relationships(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate BAT relationships"""
        issues = []
        
        # Create context lookup
        context_ids = {b.bat_id for b in context}
        
        for rel in bat.relationships:
            # Check if related BAT exists in context
            if rel.related_bat_id not in context_ids:
                issues.append(ValidationIssue(
                    rule=ValidationRule.RELATIONSHIP_VALIDITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Related BAT '{rel.related_bat_id}' not found in document",
                    bat_id=bat.bat_id,
                    suggested_fix="Verify BAT ID or add missing BAT to document"
                ))
            
            # Check for circular relationships
            if rel.related_bat_id == bat.bat_id:
                issues.append(ValidationIssue(
                    rule=ValidationRule.RELATIONSHIP_VALIDITY,
                    severity=ValidationSeverity.CRITICAL,
                    message="BAT cannot have relationship with itself",
                    bat_id=bat.bat_id
                ))
        
        return issues
    
    def _validate_applicability(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate applicability conditions logic"""
        issues = []
        
        app = bat.applicability
        
        # Check for contradictory conditions
        if app.technical_feasibility and "not feasible" in app.technical_feasibility.lower():
            if not app.exclusions:
                issues.append(ValidationIssue(
                    rule=ValidationRule.APPLICABILITY_LOGIC,
                    severity=ValidationSeverity.WARNING,
                    message="Technical feasibility issues mentioned but no exclusions specified",
                    bat_id=bat.bat_id,
                    suggested_fix="Add specific exclusion conditions"
                ))
        
        # Check species and facility type alignment
        if app.species and app.facility_types:
            # This would require domain knowledge to validate properly
            # For now, just check basic consistency
            pass
        
        return issues
    
    def _validate_cross_references(self, bat: BATConclusion, context: List[BATConclusion]) -> List[ValidationIssue]:
        """Validate cross-references in text descriptions"""
        issues = []
        
        # Look for BAT references in text
        text_fields = [bat.bat_description, bat.technique_description or "", bat.implementation_guidance or ""]
        full_text = " ".join(text_fields).upper()
        
        # Find potential BAT references (BAT followed by numbers)
        import re
        bat_refs = re.findall(r'BAT\s*(\d+)', full_text)
        
        context_nums = set()
        for context_bat in context:
            # Extract number from BAT ID if follows pattern
            match = re.search(r'(\d+)$', context_bat.bat_id)
            if match:
                context_nums.add(match.group(1))
        
        for ref_num in bat_refs:
            if ref_num not in context_nums:
                issues.append(ValidationIssue(
                    rule=ValidationRule.CROSS_REFERENCE_INTEGRITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Reference to BAT {ref_num} found in text but BAT not in document",
                    bat_id=bat.bat_id,
                    suggested_fix=f"Verify reference or add BAT {ref_num} to document"
                ))
        
        return issues
    
    def _validate_cross_document_integrity(self, bref: BREFDocument) -> List[ValidationIssue]:
        """Validate integrity across entire BREF document"""
        issues = []
        
        # Check for duplicate BAT IDs (should be caught by Pydantic but double-check)
        bat_ids = [bat.bat_id for bat in bref.bat_conclusions]
        if len(bat_ids) != len(set(bat_ids)):
            duplicates = [bat_id for bat_id in bat_ids if bat_ids.count(bat_id) > 1]
            issues.append(ValidationIssue(
                rule=ValidationRule.CROSS_REFERENCE_INTEGRITY,
                severity=ValidationSeverity.CRITICAL,
                message=f"Duplicate BAT IDs found: {set(duplicates)}",
                bat_id="_document",
                suggested_fix="Ensure all BAT IDs within document are unique"
            ))
        
        return issues


class ExpertValidationWorkflow:
    """Workflow for expert validation of extracted BAT data"""
    
    def __init__(self, knowledge_base_path: Path):
        self.kb_path = knowledge_base_path
        self.validator = BATValidator()
        self.validation_log_path = knowledge_base_path / "validation_logs"
        self.validation_log_path.mkdir(exist_ok=True)
    
    def create_validation_task(
        self,
        bat: BATConclusion,
        priority: str = "normal",
        assigned_expert: Optional[str] = None
    ) -> Dict:
        """Create a validation task for expert review"""
        
        # Run automated validation first
        issues = self.validator.validate_bat(bat)
        
        task = {
            "task_id": f"VAL_{bat.bat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "bat_id": bat.bat_id,
            "priority": priority,
            "assigned_expert": assigned_expert,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "automated_issues": [issue.to_dict() for issue in issues],
            "expert_notes": [],
            "validation_checklist": self._generate_validation_checklist(bat),
            "bat_data": bat.model_dump()
        }
        
        # Save task to file
        task_file = self.validation_log_path / f"{task['task_id']}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2, default=str)
        
        return task
    
    def _generate_validation_checklist(self, bat: BATConclusion) -> List[Dict]:
        """Generate expert validation checklist"""
        checklist = [
            {
                "item": "Verify BAT title matches BREF document exactly",
                "status": "pending",
                "notes": ""
            },
            {
                "item": "Confirm BAT description captures all key technical details",
                "status": "pending",
                "notes": ""
            },
            {
                "item": "Validate emission limit values and units",
                "status": "pending",
                "notes": ""
            },
            {
                "item": "Check applicability conditions for completeness",
                "status": "pending",
                "notes": ""
            },
            {
                "item": "Verify monitoring requirements align with limits",
                "status": "pending",
                "notes": ""
            },
            {
                "item": "Confirm source metadata accuracy (pages, sections)",
                "status": "pending",
                "notes": ""
            }
        ]
        
        # Add specific checks based on BAT type
        if bat.emission_limit_values:
            checklist.append({
                "item": "Cross-check emission values with BREF tables",
                "status": "pending",
                "notes": ""
            })
        
        if bat.relationships:
            checklist.append({
                "item": "Validate relationships with other BATs",
                "status": "pending",
                "notes": ""
            })
        
        return checklist
    
    def submit_expert_validation(
        self,
        task_id: str,
        expert_name: str,
        validation_result: ValidationStatus,
        notes: str,
        corrections: Optional[Dict] = None
    ) -> bool:
        """Submit expert validation results"""
        
        task_file = self.validation_log_path / f"{task_id}.json"
        if not task_file.exists():
            return False
        
        # Load existing task
        with open(task_file, 'r') as f:
            task = json.load(f)
        
        # Update with expert validation
        task.update({
            "status": "completed",
            "expert_name": expert_name,
            "validation_result": validation_result.value,
            "expert_notes": notes,
            "corrections": corrections or {},
            "completed_at": datetime.now().isoformat()
        })
        
        # Save updated task
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2, default=str)
        
        return True
    
    def generate_validation_report(self, bref_id: str) -> Dict:
        """Generate validation report for a BREF document"""
        
        # Find all validation tasks for this BREF
        tasks = []
        for task_file in self.validation_log_path.glob("*.json"):
            with open(task_file, 'r') as f:
                task = json.load(f)
                # Check if BAT belongs to this BREF (would need proper mapping)
                tasks.append(task)
        
        # Generate summary
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t["status"] == "completed"])
        pending_tasks = total_tasks - completed_tasks
        
        # Count validation results
        validation_results = {}
        for task in tasks:
            if task["status"] == "completed":
                result = task.get("validation_result", "unknown")
                validation_results[result] = validation_results.get(result, 0) + 1
        
        return {
            "bref_id": bref_id,
            "report_generated": datetime.now().isoformat(),
            "summary": {
                "total_bats": total_tasks,
                "validated": completed_tasks,
                "pending": pending_tasks,
                "validation_results": validation_results
            },
            "tasks": tasks
        }


# Relationship management utilities
class BATRelationshipMapper:
    """Manages relationships between BAT conclusions"""
    
    @staticmethod
    def detect_potential_relationships(bats: List[BATConclusion]) -> List[Tuple[str, str, RelationshipType, str]]:
        """Detect potential relationships between BATs using heuristics"""
        potential_relationships = []
        
        for i, bat1 in enumerate(bats):
            for bat2 in bats[i+1:]:
                # Check for complementary techniques
                if bat1.bat_category == bat2.bat_category:
                    # Same category might be complementary or alternative
                    if "combination" in bat1.bat_description.lower() or "together" in bat1.bat_description.lower():
                        potential_relationships.append((
                            bat1.bat_id,
                            bat2.bat_id,
                            RelationshipType.COMPLEMENTARY,
                            "Both BATs in same category with combination mentions"
                        ))
                
                # Check for prerequisites (monitoring before implementation)
                if bat1.bat_category.value == "monitoring" and bat2.bat_category.value != "monitoring":
                    potential_relationships.append((
                        bat2.bat_id,
                        bat1.bat_id,
                        RelationshipType.PREREQUISITE,
                        "Monitoring typically required before technique implementation"
                    ))
        
        return potential_relationships
    
    @staticmethod
    def validate_relationship_consistency(bats: List[BATConclusion]) -> List[str]:
        """Validate that BAT relationships are logically consistent"""
        issues = []
        
        # Build relationship graph
        relationships = {}
        for bat in bats:
            relationships[bat.bat_id] = bat.relationships
        
        # Check for circular dependencies
        def has_circular_dependency(start_id: str, current_id: str, visited: Set[str]) -> bool:
            if current_id in visited:
                return current_id == start_id
            
            visited.add(current_id)
            for rel in relationships.get(current_id, []):
                if rel.relationship_type == RelationshipType.PREREQUISITE.value:
                    if has_circular_dependency(start_id, rel.related_bat_id, visited.copy()):
                        return True
            return False
        
        for bat_id in relationships:
            if has_circular_dependency(bat_id, bat_id, set()):
                issues.append(f"Circular dependency detected involving BAT {bat_id}")
        
        return issues


if __name__ == "__main__":
    # Example usage
    from bat_data_models import create_sample_bat
    
    # Create validator and test
    validator = BATValidator()
    sample_bat = create_sample_bat()
    
    issues = validator.validate_bat(sample_bat)
    print(f"Found {len(issues)} validation issues:")
    for issue in issues:
        print(f"  {issue.severity.value.upper()}: {issue.message}")
    
    # Create validation workflow
    workflow = ExpertValidationWorkflow(Path("./validation_workspace"))
    task = workflow.create_validation_task(sample_bat, priority="high")
    print(f"\nCreated validation task: {task['task_id']}")