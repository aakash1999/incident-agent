from typing import Literal

from pydantic import BaseModel, Field

SeverityLevel = Literal["P1", "P2", "P3", "P4"]


class SeverityResult(BaseModel):
    severity: SeverityLevel = Field(
        ...,
        description="Incident severity. P1 is most critical, P4 is lowest.",
    )
    summary: str = Field(
        ...,
        description="One-sentence summary of the customer-reported issue.",
    )
    rationale: str = Field(
        ...,
        description="Short reasoning referencing impact, scope, and urgency.",
    )
