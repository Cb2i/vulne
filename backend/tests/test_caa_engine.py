from app.models.rules import CAAConfig
from app.rules.caa.engine import compute_caa_score

CONFIG = CAAConfig(
    weight_exposition_internet=1.5,
    weight_exposition_dmz=0.5,
    weight_exposition_internal=-0.5,
    weight_exposition_airgapped=-2.0,
    weight_criticite_critical=2.5,
    weight_criticite_high=1.5,
    weight_criticite_medium=0.0,
    weight_criticite_low=-1.0,
    weight_exploitable=2.0,
    normalization_divisor=1.0,
)


def test_internet_exposed_critical_exploitable_scores_high():
    result = compute_caa_score(
        cvss=7.0, exposition="Internet", criticite="Critical", exploitable=True, config=CONFIG
    )
    # 7.0 + 1.5 (internet) + 2.5 (critical) + 2.0 (exploitable) = 13.0, clamped to 10
    assert result.caa_score == 10.0
    assert len(result.adjustments) == 3


def test_internal_low_criticality_not_exploitable_scores_lower_than_cvss():
    result = compute_caa_score(
        cvss=6.0, exposition="Internal", criticite="Low", exploitable=False, config=CONFIG
    )
    # 6.0 - 0.5 (internal) - 1.0 (low) = 4.5
    assert result.caa_score == 4.5


def test_score_never_negative():
    result = compute_caa_score(cvss=0.0, exposition="Airgapped", criticite="Low", exploitable=False, config=CONFIG)
    assert result.caa_score == 0.0


def test_french_labels_are_normalized():
    result_fr = compute_caa_score(cvss=5.0, exposition="Interne", criticite="Critique", exploitable=False, config=CONFIG)
    result_en = compute_caa_score(cvss=5.0, exposition="Internal", criticite="Critical", exploitable=False, config=CONFIG)
    assert result_fr.caa_score == result_en.caa_score
