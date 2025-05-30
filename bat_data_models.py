"""
Enhanced BAT (Best Available Techniques) Data Models for EU BREF Compliance
Using Pydantic for robust data validation and serialization.
"""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, model_validator


class PollutantType(str, Enum):
    """Standard pollutant types in BREF documents"""
    AMMONIA = "NH3"
    NITROGEN_OXIDES = "NOx"
    PARTICULATE_MATTER = "PM"
    PARTICULATE_MATTER_10 = "PM10"
    PARTICULATE_MATTER_25 = "PM2.5"
    SULFUR_DIOXIDE = "SO2"
    CARBON_MONOXIDE = "CO"
    METHANE = "CH4"
    NITROUS_OXIDE = "N2O"
    ODOUR = "odour"
    NOISE = "noise"
    TOTAL_SUSPENDED_PARTICLES = "TSP"


class BATType(str, Enum):
    """Types of BAT conclusions"""
    TECHNIQUE = "technique"  # Specific technical solution
    PERFORMANCE_LEVEL = "performance_level"  # Emission/performance standards
    COMBINATION = "combination"  # Both technique and performance requirements


class BATCategory(str, Enum):
    """BAT categories for intensive livestock farming"""
    HOUSING = "housing"
    FEEDING = "feeding"
    MANURE_MANAGEMENT = "manure_management"
    AIR_TREATMENT = "air_treatment"
    WASTE_WATER_TREATMENT = "waste_water_treatment"
    ENERGY_EFFICIENCY = "energy_efficiency"
    MONITORING = "monitoring"
    MANAGEMENT = "management"


class AnimalSpecies(str, Enum):
    """Animal species covered by intensive rearing BREF"""
    PIGS = "pigs"
    POULTRY = "poultry"
    CATTLE = "cattle"
    LAYING_HENS = "laying_hens"
    BROILERS = "broilers"
    TURKEYS = "turkeys"
    DUCKS = "ducks"
    DAIRY_COWS = "dairy_cows"
    BEEF_CATTLE = "beef_cattle"


class MonitoringFrequency(str, Enum):
    """Monitoring frequency requirements"""
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    BIANNUAL = "biannual"
    ANNUAL = "annual"
    AS_NEEDED = "as_needed"


class ValidationStatus(str, Enum):
    """Status of BAT data validation"""
    VERIFIED = "verified"
    PENDING = "pending"
    FLAGGED = "flagged"
    NEEDS_REVIEW = "needs_review"


class ExtractionMethod(str, Enum):
    """Method used to extract BAT data"""
    MANUAL = "manual"
    SEMI_AUTOMATED = "semi_automated"
    FULLY_AUTOMATED = "fully_automated"
    EXPERT_VALIDATED = "expert_validated"


class SourceMetadata(BaseModel):
    """Detailed source information for traceability"""
    document_title: str = Field(..., description="Full title of source BREF document")
    document_version: str = Field(..., description="Version/revision of document")
    document_date: date = Field(..., description="Publication date")
    document_url: Optional[str] = Field(None, description="Official EU publication URL")
    
    chapter: str = Field(..., description="Chapter/section reference")
    page_range: List[int] = Field(..., description="Page numbers containing this BAT")
    paragraph_ids: List[str] = Field(default_factory=list, description="Specific paragraph references")
    table_references: List[str] = Field(default_factory=list, description="Referenced tables")
    figure_references: List[str] = Field(default_factory=list, description="Referenced figures")
    annex_references: List[str] = Field(default_factory=list, description="Referenced annexes")

    @validator('page_range')
    def validate_page_range(cls, v):
        if len(v) < 1:
            raise ValueError('At least one page number required')
        if len(v) == 2 and v[0] > v[1]:
            raise ValueError('Invalid page range: start page must be <= end page')
        return v


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process"""
    extraction_method: ExtractionMethod
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in extraction accuracy")
    validation_status: ValidationStatus
    extracted_by: str = Field(..., description="System or expert name")
    extracted_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    review_notes: Optional[str] = Field(None, description="Expert review comments")


class EmissionLimitValue(BaseModel):
    """Emission limit values and associated monitoring"""
    pollutant: PollutantType
    limit_value: float = Field(..., description="Numerical limit value")
    unit: str = Field(..., description="Unit of measurement")
    measurement_period: str = Field(..., description="Averaging period (daily, monthly, yearly)")
    measurement_conditions: Optional[str] = Field(None, description="Specific measurement conditions")
    monitoring_frequency: MonitoringFrequency
    monitoring_method: Optional[str] = Field(None, description="EN/ISO standard or method")
    
    # Performance ranges for different conditions
    minimum_performance: Optional[float] = Field(None, description="Minimum achievable performance")
    typical_performance: Optional[float] = Field(None, description="Typical performance range")
    maximum_performance: Optional[float] = Field(None, description="Maximum performance under optimal conditions")
    
    @validator('limit_value', 'minimum_performance', 'typical_performance', 'maximum_performance')
    def validate_positive_values(cls, v):
        if v is not None and v < 0:
            raise ValueError('Performance values must be non-negative')
        return v


class ApplicabilityCondition(BaseModel):
    """Conditions determining when BAT applies"""
    species: List[AnimalSpecies] = Field(default_factory=list)
    facility_types: List[str] = Field(default_factory=list, description="Types of facilities")
    size_thresholds: Optional[str] = Field(None, description="Minimum facility size requirements")
    
    # Economic and technical feasibility
    technical_feasibility: Optional[str] = Field(None, description="Technical feasibility conditions")
    economic_feasibility: Optional[str] = Field(None, description="Economic feasibility considerations")
    
    # Exclusions and special conditions
    exclusions: List[str] = Field(default_factory=list, description="When BAT does not apply")
    special_conditions: List[str] = Field(default_factory=list, description="Special circumstances")
    
    # Geographic or regulatory constraints
    geographic_constraints: Optional[str] = Field(None, description="Regional applicability limits")
    regulatory_constraints: Optional[str] = Field(None, description="Regulatory limitations")


class MonitoringRequirement(BaseModel):
    """Monitoring requirements associated with BAT"""
    monitoring_id: str = Field(..., description="Unique monitoring requirement ID")
    parameters: List[PollutantType] = Field(..., description="Parameters to monitor")
    monitoring_methods: List[str] = Field(..., description="Required monitoring methods/standards")
    frequency: MonitoringFrequency
    
    # Monitoring location and sampling
    monitoring_locations: List[str] = Field(default_factory=list, description="Where to monitor")
    sampling_requirements: Optional[str] = Field(None, description="Sampling methodology")
    
    # Quality assurance
    calibration_frequency: Optional[str] = Field(None, description="Equipment calibration requirements")
    qa_qc_requirements: Optional[str] = Field(None, description="Quality assurance/control procedures")
    
    # Reporting
    reporting_frequency: Optional[MonitoringFrequency] = Field(None, description="How often to report results")
    reporting_format: Optional[str] = Field(None, description="Required reporting format")


class BATRelationship(BaseModel):
    """Relationships between BAT conclusions"""
    related_bat_id: str = Field(..., description="ID of related BAT")
    relationship_type: str = Field(..., description="Type of relationship")
    description: str = Field(..., description="Description of relationship")
    
    class Config:
        schema_extra = {
            "example": {
                "related_bat_id": "BAT_HOUSING_02",
                "relationship_type": "prerequisite",
                "description": "BAT 2 (adequate ventilation) is required before implementing BAT 1"
            }
        }

# Define relationship types
class RelationshipType(str, Enum):
    PREREQUISITE = "prerequisite"  # Must implement related BAT first
    ALTERNATIVE = "alternative"    # Either this BAT or related BAT
    COMPLEMENTARY = "complementary"  # Works better when combined
    CONFLICTING = "conflicting"    # Cannot be used together
    SUPERSEDES = "supersedes"      # This BAT replaces the related BAT


class BATConclusion(BaseModel):
    """Enhanced BAT conclusion with comprehensive metadata"""
    
    # Core identification
    bat_id: str = Field(..., description="Unique BAT identifier within BREF")
    bat_uuid: UUID = Field(default_factory=uuid4, description="Universal unique identifier")
    
    # BAT classification
    bat_type: BATType
    bat_category: BATCategory
    bat_title: str = Field(..., description="Official BAT title from BREF")
    bat_description: str = Field(..., description="Full textual description")
    
    # Technical details
    technique_description: Optional[str] = Field(None, description="Detailed technique description")
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    
    # Applicability
    applicability: ApplicabilityCondition
    
    # Performance requirements
    emission_limit_values: List[EmissionLimitValue] = Field(default_factory=list)
    monitoring_requirements: List[MonitoringRequirement] = Field(default_factory=list)
    
    # Relationships with other BATs
    relationships: List[BATRelationship] = Field(default_factory=list)
    
    # Economic considerations
    investment_costs: Optional[str] = Field(None, description="Investment cost information")
    operating_costs: Optional[str] = Field(None, description="Operating cost information")
    cost_effectiveness: Optional[str] = Field(None, description="Cost-effectiveness analysis")
    
    # Environmental benefits
    environmental_benefits: List[str] = Field(default_factory=list, description="Environmental benefits achieved")
    side_effects: List[str] = Field(default_factory=list, description="Potential negative side effects")
    
    # Metadata
    source_metadata: SourceMetadata
    extraction_metadata: ExtractionMetadata
    
    # Validation
    is_active: bool = Field(True, description="Whether this BAT is currently valid")
    superseded_by: Optional[str] = Field(None, description="BAT ID that supersedes this one")
    
    @validator('bat_id')
    def validate_bat_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('BAT ID cannot be empty')
        return v.strip().upper()
    
    @model_validator(mode='after')
    def validate_performance_requirements(self):
        """Ensure performance-type BATs have emission limit values"""
        if self.bat_type in [BATType.PERFORMANCE_LEVEL, BATType.COMBINATION] and not self.emission_limit_values:
            raise ValueError(f'BAT type {self.bat_type} requires emission limit values')
        
        return self


class BREFDocument(BaseModel):
    """BREF document containing multiple BAT conclusions"""
    
    bref_id: str = Field(..., description="Unique BREF identifier")
    title: str = Field(..., description="Official BREF title")
    scope_description: str = Field(..., description="Scope and applicability of BREF")
    
    # Document metadata
    publication_date: date
    revision_date: Optional[date] = Field(None)
    document_version: str
    document_url: str
    
    # Content organization
    bat_conclusions: List[BATConclusion] = Field(default_factory=list)
    
    # Processing metadata
    total_pages: int = Field(..., gt=0)
    processing_status: ValidationStatus = Field(ValidationStatus.PENDING)
    last_processed: datetime = Field(default_factory=datetime.now)
    
    @validator('bat_conclusions')
    def validate_unique_bat_ids(cls, v):
        """Ensure all BAT IDs within a BREF are unique"""
        bat_ids = [bat.bat_id for bat in v]
        if len(bat_ids) != len(set(bat_ids)):
            raise ValueError('Duplicate BAT IDs found within BREF')
        return v


class ComplianceKnowledgeBase(BaseModel):
    """Complete knowledge base for BAT compliance verification"""
    
    knowledge_base_id: str = Field(..., description="Unique knowledge base identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field("1.0", description="Knowledge base version")
    
    # Content
    bref_documents: List[BREFDocument] = Field(default_factory=list)
    
    # Statistics
    total_bref_documents: int = Field(0, description="Total number of BREF documents")
    total_bat_conclusions: int = Field(0, description="Total number of BAT conclusions")
    
    # Validation status
    validation_summary: Dict[ValidationStatus, int] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def update_statistics(self):
        """Update statistics based on content"""
        self.total_bref_documents = len(self.bref_documents)
        self.total_bat_conclusions = sum(len(doc.bat_conclusions) for doc in self.bref_documents)
        
        # Count validation statuses
        validation_counts = {}
        for doc in self.bref_documents:
            for bat in doc.bat_conclusions:
                status = bat.extraction_metadata.validation_status
                validation_counts[status] = validation_counts.get(status, 0) + 1
        
        self.validation_summary = validation_counts
        return self


# Helper functions for data manipulation
def create_sample_bat() -> BATConclusion:
    """Create a sample BAT conclusion for testing"""
    return BATConclusion(
        bat_id="BAT_HOUSING_01",
        bat_type=BATType.COMBINATION,
        bat_category=BATCategory.HOUSING,
        bat_title="Use of low emission housing systems for pigs",
        bat_description="To reduce ammonia emissions from pig housing, BAT is to use one or more of the following low emission housing systems...",
        
        applicability=ApplicabilityCondition(
            species=[AnimalSpecies.PIGS],
            facility_types=["intensive_pig_rearing"],
            size_thresholds="2000+ pig places",
            technical_feasibility="Applicable to new installations and major retrofits"
        ),
        
        emission_limit_values=[
            EmissionLimitValue(
                pollutant=PollutantType.AMMONIA,
                limit_value=1.5,
                unit="kg NH3/animal place/year",
                measurement_period="yearly_average",
                monitoring_frequency=MonitoringFrequency.MONTHLY,
                monitoring_method="EN 14791"
            )
        ],
        
        source_metadata=SourceMetadata(
            document_title="Best Available Techniques Reference Document for the Intensive Rearing of Poultry or Pigs",
            document_version="2017",
            document_date=date(2017, 12, 21),
            chapter="4.1.1",
            page_range=[45, 47],
            paragraph_ids=["4.1.1.1", "4.1.1.2"]
        ),
        
        extraction_metadata=ExtractionMetadata(
            extraction_method=ExtractionMethod.EXPERT_VALIDATED,
            confidence_score=0.95,
            validation_status=ValidationStatus.VERIFIED,
            extracted_by="BAT Expert v1.0"
        )
    )


if __name__ == "__main__":
    # Example usage and validation
    sample_bat = create_sample_bat()
    print("Sample BAT created successfully!")
    print(f"BAT ID: {sample_bat.bat_id}")
    print(f"Title: {sample_bat.bat_title}")
    
    # Export to JSON
    import json
    sample_json = sample_bat.model_dump(indent=2)
    print("\nSample JSON structure:")
    print(json.dumps(sample_json, indent=2, default=str))