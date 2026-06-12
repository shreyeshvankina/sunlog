from dataclasses import dataclass

COVERAGE_FRACTIONS = {
    "minimal": 0.06,
    "arms":    0.18,
    "legs":    0.36,
    "full":    0.55,
}

SKIN_TONE_MULTIPLIERS = {
    "fair":   1.0,
    "medium": 0.6,
    "dark":   0.3,
}

BASE_IU_PER_MIN_FULL_FAIR_UV3 = 333.0


@dataclass
class ExposureParams:
    duration_minutes: float
    uv_index: float
    coverage: str
    skin_tone: str


def estimate_vitamin_d(params: ExposureParams) -> float:
    if params.uv_index < 2:
        return 0.0

    uv_factor = params.uv_index / 3.0
    coverage_fraction = COVERAGE_FRACTIONS[params.coverage]
    skin_multiplier = SKIN_TONE_MULTIPLIERS[params.skin_tone]

    effective_minutes = params.duration_minutes * (
        1 - 0.5 * (params.duration_minutes / (params.duration_minutes + 20))
    )

    iu = (
        BASE_IU_PER_MIN_FULL_FAIR_UV3
        * effective_minutes
        * uv_factor
        * coverage_fraction
        * skin_multiplier
    )

    return round(iu, 1)


def coverage_options() -> list[str]:
    return list(COVERAGE_FRACTIONS.keys())


def skin_tone_options() -> list[str]:
    return list(SKIN_TONE_MULTIPLIERS.keys())