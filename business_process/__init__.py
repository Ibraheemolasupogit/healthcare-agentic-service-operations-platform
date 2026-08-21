"""Platform-neutral business process domain (service taxonomy, case lifecycle)."""

from business_process.taxonomy import (
    CASE_LIFECYCLE_ORDER,
    CaseStage,
    ServiceCategory,
)

__all__ = [
    "CASE_LIFECYCLE_ORDER",
    "CaseStage",
    "ServiceCategory",
]
