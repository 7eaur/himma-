"""Governance boundary for machine speech decisions.

A provider adapter, confidence value or environment variable is never academic
approval by itself. Automatic acceptance is permitted only when Product/Speech
governance has explicitly registered an approved provider+model+calibration
contract here (or in a future persisted signed registry).

The production registry is intentionally empty today because Himma has no
approved Production ASR provider. Machine analyses therefore remain advisory
and require Human Supervisor Review.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovedASRCalibration:
    provider_name: str
    model: str
    calibration_version: str
    confidence_threshold: float


# Runtime audio transfer to an external provider is a separate governance gate
# from confidence calibration. The tuple stays empty until provider/privacy/
# cost/retention approval is recorded in an ADR and verified with representative
# recordings. Environment variables alone can never enable student-audio export.
APPROVED_ASR_RUNTIME_PROVIDERS: tuple[str, ...] = ()

# Automatic machine acceptance is an even stricter gate. It stays empty until a
# provider+model calibration artifact is approved. Lab evaluation never populates
# this registry and never changes academic state.
APPROVED_ASR_CALIBRATIONS: tuple[ApprovedASRCalibration, ...] = ()


def runtime_provider_is_approved(provider_name: str) -> bool:
    normalized = (provider_name or "").strip().lower()
    return normalized in {value.strip().lower() for value in APPROVED_ASR_RUNTIME_PROVIDERS}


def machine_review_decision(
    *,
    provider_name: str,
    model: str | None,
    confidence: float | None,
) -> tuple[str, str | None]:
    """Return a governed advisory decision for one ASR result.

    Unknown providers/models and the current unapproved state always require a
    human review. The calibration version is returned only for an actually
    approved registry entry, so arbitrary deployment strings cannot look like
    governed academic evidence.
    """
    if confidence is None or not 0.0 <= float(confidence) <= 1.0 or not model:
        return "review_required", None

    for calibration in APPROVED_ASR_CALIBRATIONS:
        if (
            calibration.provider_name == provider_name
            and calibration.model == model
        ):
            decision = (
                "auto_accepted"
                if float(confidence) >= calibration.confidence_threshold
                else "review_required"
            )
            return decision, calibration.calibration_version

    return "review_required", None
