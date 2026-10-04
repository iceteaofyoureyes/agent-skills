"""Finding vocabulary; execution routing remains the existing contract."""
from enum import Enum


class FindingKind(str, Enum):
    DEFECT = 'DEFECT'
    SPEC_GAP = 'SPEC_GAP'
    BUSINESS_DECISION_REQUIRED = 'BUSINESS_DECISION_REQUIRED'
    TEST_ISSUE = 'TEST_ISSUE'
    ENVIRONMENT_ISSUE = 'ENVIRONMENT_ISSUE'
