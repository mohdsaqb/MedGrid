"""
Deliberately minimal, illustrative subsets of real FHIR resources - just
enough structure to demonstrate the mapping exercise honestly. This is
NOT a spec-complete implementation of HL7 FHIR (see Module 9's intro).
Deeply-nested sub-structures (name, telecom, references, coding, ...) are
left as plain dicts rather than fully modeled - fully typing FHIR's
recursive data types would mean re-implementing the spec, which is
explicitly out of scope here.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FHIRPatient(BaseModel):
    resourceType: Literal["Patient"] = "Patient"
    id: str
    identifier: list[dict]
    name: list[dict]
    gender: str
    birthDate: str
    telecom: list[dict] = []


class FHIREncounter(BaseModel):
    resourceType: Literal["Encounter"] = "Encounter"
    id: str
    status: str
    # "class" is a Python reserved word - a small, real taste of the kind
    # of friction cross-language interoperability code runs into. The
    # alias keeps our JSON output spec-correct while `class_` stays valid
    # Python on this side.
    class_: dict = Field(alias="class")
    subject: dict
    participant: list[dict]
    period: dict
    reasonCode: list[dict] = []

    model_config = ConfigDict(populate_by_name=True)


class FHIRObservation(BaseModel):
    resourceType: Literal["Observation"] = "Observation"
    id: str
    status: str
    code: dict
    subject: dict
    performer: list[dict] = []
    effectiveDateTime: str
    valueString: str | None = None
    valueQuantity: dict | None = None
    referenceRange: list[dict] = []
