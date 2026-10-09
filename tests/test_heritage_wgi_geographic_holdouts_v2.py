"""Guard the country-disjoint, seven-test registration contract."""

import yaml

from scripts import run_heritage_wgi_geographic_holdouts_v2 as holdouts


def test_complete_cohort_and_original_country_exclusion() -> None:
    assert len(holdouts.COHORT) == 7
    assert holdouts.FAMILY_P_MAX == 0.10 / len(holdouts.COHORT)
    assert len(holdouts.OLD_COUNTRIES) == 53
    for hypothesis_id in holdouts.COHORT:
        old_id = hypothesis_id.removesuffix("_geographic_holdout_v2")
        matches = list((holdouts.ROOT / "hypotheses").glob(f"*/{old_id}.yaml"))
        assert len(matches) == 1
        old_spec = yaml.safe_load(matches[0].read_text())
        assert set(old_spec["sample"]["countries"]) == holdouts.OLD_COUNTRIES


def test_preflight_is_disjoint_and_does_not_estimate() -> None:
    for hypothesis_id in holdouts.COHORT:
        coverage, panel, sources = holdouts.preflight(hypothesis_id)
        assert coverage["passed"]
        assert coverage["coefficient_estimated"] is False
        assert coverage["overlap_with_old_countries"] == 0
        assert not (set(panel["country_iso3"]) & holdouts.OLD_COUNTRIES)
        assert len(sources) == 6


def test_family_adjusted_verdicts_are_sign_symmetric() -> None:
    threshold = holdouts.FAMILY_P_MAX
    assert holdouts.classify(0.1, threshold)[0] == "SUPPORTED"
    assert holdouts.classify(-0.1, threshold)[0] == "REFUTED"
    assert holdouts.classify(0.1, threshold + 1e-5)[0] == "PARTIAL"
    assert holdouts.classify(-0.1, threshold + 1e-5)[0] == "PARTIAL"
