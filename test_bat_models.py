"""
Test suite for BAT data models and validation workflows
Demonstrates the enhanced BAT system functionality
"""

import json
import pytest
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from bat_data_models import (
    BATConclusion, BREFDocument, ComplianceKnowledgeBase,
    EmissionLimitValue, ApplicabilityCondition, MonitoringRequirement,
    SourceMetadata, ExtractionMetadata, BATRelationship,
    PollutantType, BATType, BATCategory, AnimalSpecies,
    MonitoringFrequency, ValidationStatus, ExtractionMethod,
    create_sample_bat
)

from bat_validation_workflows import (
    BATValidator, ExpertValidationWorkflow, BATRelationshipMapper,
    ValidationRule, ValidationSeverity
)


class TestBATDataModels:
    """Test the Pydantic BAT data models"""
    
    def test_create_sample_bat(self):
        """Test that sample BAT creation works"""
        bat = create_sample_bat()
        assert bat.bat_id == "BAT_HOUSING_01"
        assert bat.bat_type == BATType.COMBINATION
        assert len(bat.emission_limit_values) > 0
        assert bat.extraction_metadata.validation_status == ValidationStatus.VERIFIED
    
    def test_emission_limit_value_validation(self):
        """Test emission limit value validation"""
        elv = EmissionLimitValue(
            pollutant=PollutantType.AMMONIA,
            limit_value=1.5,
            unit="kg NH3/animal place/year",
            measurement_period="yearly_average",
            monitoring_frequency=MonitoringFrequency.MONTHLY,
            monitoring_method="EN 14791"
        )
        assert elv.pollutant == PollutantType.AMMONIA
        assert elv.limit_value == 1.5
    
    def test_emission_limit_negative_value_fails(self):
        """Test that negative emission values are rejected"""
        with pytest.raises(ValueError):
            EmissionLimitValue(
                pollutant=PollutantType.AMMONIA,
                limit_value=-1.0,  # Invalid negative value
                unit="kg NH3/animal place/year",
                measurement_period="yearly_average",
                monitoring_frequency=MonitoringFrequency.MONTHLY
            )
    
    def test_applicability_condition_creation(self):
        """Test applicability condition model"""
        app = ApplicabilityCondition(
            species=[AnimalSpecies.PIGS, AnimalSpecies.POULTRY],
            facility_types=["intensive_rearing"],
            size_thresholds="2000+ animal places",
            technical_feasibility="Applicable to new installations",
            exclusions=["Small farms under 1000 places"]
        )
        assert AnimalSpecies.PIGS in app.species
        assert len(app.exclusions) == 1
    
    def test_source_metadata_validation(self):
        """Test source metadata validation"""
        # Valid page range
        metadata = SourceMetadata(
            document_title="Test BREF",
            document_version="2024",
            document_date=date(2024, 1, 1),
            chapter="4.1",
            page_range=[45, 47]
        )
        assert metadata.page_range == [45, 47]
        
        # Invalid page range should fail
        with pytest.raises(ValueError):
            SourceMetadata(
                document_title="Test BREF",
                document_version="2024",
                document_date=date(2024, 1, 1),
                chapter="4.1",
                page_range=[47, 45]  # Start > end
            )
    
    def test_bat_conclusion_performance_validation(self):
        """Test that performance BATs require emission limits"""
        with pytest.raises(ValueError):
            BATConclusion(
                bat_id="TEST_BAT",
                bat_type=BATType.PERFORMANCE_LEVEL,  # Requires emission limits
                bat_category=BATCategory.HOUSING,
                bat_title="Test BAT",
                bat_description="Test description",
                applicability=ApplicabilityCondition(),
                emission_limit_values=[],  # Empty - should fail
                source_metadata=SourceMetadata(
                    document_title="Test",
                    document_version="1.0",
                    document_date=date.today(),
                    chapter="1",
                    page_range=[1]
                ),
                extraction_metadata=ExtractionMetadata(
                    extraction_method=ExtractionMethod.MANUAL,
                    confidence_score=1.0,
                    validation_status=ValidationStatus.VERIFIED,
                    extracted_by="Test"
                )
            )
    
    def test_bref_document_unique_bat_ids(self):
        """Test that BREF documents enforce unique BAT IDs"""
        bat1 = create_sample_bat()
        bat2 = create_sample_bat()
        bat2.bat_title = "Different title"
        # Both have same bat_id - should fail
        
        with pytest.raises(ValueError):
            BREFDocument(
                bref_id="TEST_BREF",
                title="Test BREF",
                scope_description="Test scope",
                publication_date=date.today(),
                document_version="1.0",
                document_url="http://test.com",
                total_pages=100,
                bat_conclusions=[bat1, bat2]  # Duplicate IDs
            )


class TestBATValidator:
    """Test the BAT validation system"""
    
    def test_validator_creation(self):
        """Test validator can be created"""
        validator = BATValidator()
        assert len(validator.validation_rules) > 0
    
    def test_validate_sample_bat(self):
        """Test validation of a properly formed BAT"""
        validator = BATValidator()
        bat = create_sample_bat()
        issues = validator.validate_bat(bat)
        
        # Sample BAT should have minimal issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        assert len(critical_issues) == 0, f"Critical issues found: {[i.message for i in critical_issues]}"
    
    def test_validate_empty_bat_title(self):
        """Test validation catches empty BAT title"""
        validator = BATValidator()
        bat = create_sample_bat()
        bat.bat_title = ""  # Invalid empty title
        
        issues = validator.validate_bat(bat)
        title_issues = [i for i in issues if "title" in i.message.lower()]
        assert len(title_issues) > 0
    
    def test_validate_emission_limits_consistency(self):
        """Test emission limits validation"""
        validator = BATValidator()
        bat = create_sample_bat()
        
        # Add invalid emission limit
        bat.emission_limit_values[0].limit_value = 0  # Zero value should trigger warning
        
        issues = validator.validate_bat(bat)
        emission_issues = [i for i in issues if i.rule == ValidationRule.EMISSION_LIMITS_CONSISTENCY]
        assert len(emission_issues) > 0
    
    def test_validate_bref_document(self):
        """Test validation of entire BREF document"""
        validator = BATValidator()
        
        # Create BREF with multiple BATs
        bat1 = create_sample_bat()
        bat2 = create_sample_bat()
        bat2.bat_id = "BAT_HOUSING_02"
        bat2.bat_title = "Different housing technique"
        
        bref = BREFDocument(
            bref_id="TEST_BREF",
            title="Test BREF Document",
            scope_description="Test scope",
            publication_date=date.today(),
            document_version="1.0",
            document_url="http://test.com",
            total_pages=100,
            bat_conclusions=[bat1, bat2]
        )
        
        results = validator.validate_bref_document(bref)
        assert isinstance(results, dict)


class TestExpertValidationWorkflow:
    """Test expert validation workflow"""
    
    def test_create_validation_task(self, tmp_path):
        """Test creation of validation tasks"""
        workflow = ExpertValidationWorkflow(tmp_path)
        bat = create_sample_bat()
        
        task = workflow.create_validation_task(bat, priority="high", assigned_expert="Dr. Test")
        
        assert task["bat_id"] == bat.bat_id
        assert task["priority"] == "high"
        assert task["assigned_expert"] == "Dr. Test"
        assert "validation_checklist" in task
        
        # Check that task file was created
        task_file = tmp_path / "validation_logs" / f"{task['task_id']}.json"
        assert task_file.exists()
    
    def test_submit_expert_validation(self, tmp_path):
        """Test expert validation submission"""
        workflow = ExpertValidationWorkflow(tmp_path)
        bat = create_sample_bat()
        
        # Create task
        task = workflow.create_validation_task(bat)
        task_id = task["task_id"]
        
        # Submit validation
        success = workflow.submit_expert_validation(
            task_id=task_id,
            expert_name="Dr. Expert",
            validation_result=ValidationStatus.VERIFIED,
            notes="All checks passed",
            corrections={"bat_title": "Corrected title"}
        )
        
        assert success
        
        # Verify task was updated
        task_file = tmp_path / "validation_logs" / f"{task_id}.json"
        with open(task_file) as f:
            updated_task = json.load(f)
        
        assert updated_task["status"] == "completed"
        assert updated_task["expert_name"] == "Dr. Expert"
        assert updated_task["validation_result"] == "verified"


class TestBATRelationshipMapper:
    """Test BAT relationship detection and validation"""
    
    def test_detect_potential_relationships(self):
        """Test automatic relationship detection"""
        # Create related BATs
        bat1 = create_sample_bat()
        bat1.bat_category = BATCategory.MONITORING
        bat1.bat_description = "Monitoring system for emissions"
        
        bat2 = create_sample_bat()
        bat2.bat_id = "BAT_HOUSING_02"
        bat2.bat_category = BATCategory.HOUSING
        bat2.bat_description = "Housing system requiring monitoring"
        
        relationships = BATRelationshipMapper.detect_potential_relationships([bat1, bat2])
        
        # Should detect monitoring as prerequisite for housing
        assert len(relationships) > 0
        found_prerequisite = any(
            rel[2].value == "prerequisite" for rel in relationships
        )
        assert found_prerequisite
    
    def test_validate_relationship_consistency(self):
        """Test relationship consistency validation"""
        # Create BATs with valid relationships
        bat1 = create_sample_bat()
        bat2 = create_sample_bat()
        bat2.bat_id = "BAT_HOUSING_02"
        
        # Add valid relationship
        bat1.relationships = [
            BATRelationship(
                related_bat_id="BAT_HOUSING_02",
                relationship_type="complementary",
                description="Works together"
            )
        ]
        
        issues = BATRelationshipMapper.validate_relationship_consistency([bat1, bat2])
        assert len(issues) == 0  # No issues expected


class TestJSONSerialization:
    """Test JSON serialization and deserialization"""
    
    def test_bat_json_roundtrip(self):
        """Test BAT can be serialized to JSON and back"""
        original_bat = create_sample_bat()
        
        # Serialize to JSON
        json_data = original_bat.model_dump()
        json_str = json.dumps(json_data, default=str)
        
        # Deserialize back
        loaded_data = json.loads(json_str)
        restored_bat = BATConclusion.model_validate(loaded_data)
        
        assert restored_bat.bat_id == original_bat.bat_id
        assert restored_bat.bat_title == original_bat.bat_title
        assert len(restored_bat.emission_limit_values) == len(original_bat.emission_limit_values)
    
    def test_knowledge_base_json_export(self):
        """Test complete knowledge base JSON export"""
        bat = create_sample_bat()
        
        bref = BREFDocument(
            bref_id="TEST_BREF",
            title="Test BREF",
            scope_description="Test scope",
            publication_date=date.today(),
            document_version="1.0",
            document_url="http://test.com",
            total_pages=100,
            bat_conclusions=[bat]
        )
        
        kb = ComplianceKnowledgeBase(
            knowledge_base_id="TEST_KB",
            bref_documents=[bref]
        )
        
        json_data = kb.model_dump()
        json_str = json.dumps(json_data, indent=2, default=str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["knowledge_base_id"] == "TEST_KB"
        assert len(parsed["bref_documents"]) == 1


if __name__ == "__main__":
    # Run basic tests
    print("Running BAT model tests...")
    
    # Test model creation
    bat = create_sample_bat()
    print(f"✓ Created sample BAT: {bat.bat_id}")
    
    # Test validation
    validator = BATValidator()
    issues = validator.validate_bat(bat)
    print(f"✓ Validation completed: {len(issues)} issues found")
    
    # Test JSON serialization
    json_data = bat.model_dump()
    print(f"✓ JSON serialization successful: {len(json.dumps(json_data, default=str))} characters")
    
    # Load example JSON file
    try:
        with open("example_intensive_rearing_bats.json", "r") as f:
            kb_data = json.load(f)
        kb = ComplianceKnowledgeBase.model_validate(kb_data)
        print(f"✓ Loaded knowledge base: {kb.total_bat_conclusions} BATs")
    except FileNotFoundError:
        print("! Example JSON file not found - run from correct directory")
    
    print("\nAll basic tests passed! Run 'pytest test_bat_models.py' for full test suite.")