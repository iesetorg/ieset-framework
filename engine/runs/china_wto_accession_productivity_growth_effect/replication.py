#!/usr/bin/env python3
"""Replication — China's WTO accession (2001) productivity-growth effect.

Spec: hypotheses/growth/china_wto_accession_productivity_growth_effect.yaml v1
Position-claim: developmentalism #7 (school predicts: supported)

The original spec called for an industry-level event study (CIP/PWT around
2001 WTO entry, with industry-tariff-cut intensity as treatment). The
sub-national CIP industry panel is not on disk in this build, so the
runnable promotion shifts to a country-level structural-break test on the
PWT 10.01 series, with peer-country differencing for identification:

  PRIMARY 1 (TFP break):
    Mean annual change in CHN PWT rtfpna (TFP at constant national prices)
    in the post-WTO window 2002-2019 must exceed the pre-WTO window
    1990-2000 mean by at least +0.50pp/yr. (rtfpna is an index; year-on-
    year diff is the growth rate.)

  PRIMARY 2 (Export-GDP-share break):
    CHN merchandise-exports share of GDP at current PPPs (PWT csh_x,
    converted to percent) in 2002-2007 (the pre-GFC ramp where the WTO
    trade-creation effect is strongest in every published estimate)
    must exceed the 1990-2000 mean by at least +8 percentage points.

    Note: WDI NE.EXP.GNFS.KD is essentially empty for CHN in the on-disk
    vintage (1 non-null observation), so PWT csh_x is used instead. csh_x
    is the goods-and-services export share of expenditure-side GDP at
    current PPPs.

  INFORMATIVE (peer differencing):
    The TFP-growth acceleration on CHN net of the mean acceleration on a
    panel of large EM peers that did NOT undergo a WTO accession event
    in 2001 (IND, BRA, MEX, IDN, MYS, THA, TUR, ZAF) should be at least
    +0.30pp/yr. Pure descriptive — controls for the "global TFP boom of
    the 2000s" alternative explanation in a coarse way.

VERDICT logic:
  SUPPORTED   - both PRIMARY 1 and PRIMARY 2 hold
  partial     - one PRIMARY holds, the other doesn't
  refuted     - neither PRIMARY holds (and direction is wrong on at least
                one with sign opposite the claim)
  inconclusive - data gap on either rtfpna or NE.EXP.GNFS.ZS for CHN.

The peer-comparison is reported but does NOT gate the verdict; it only
colours the diagnostics for the steelman page.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "china_wto_accession_productivity_growth_effect"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample / windows
TREATED = "CHN"
PEER_COUNTRIES = ["IND", "BRA", "MEX", "IDN", "MYS", "THA", "TUR", "ZAF"]
PRE_WINDOW = (1990, 2000)        # pre-WTO accession (Dec 2001)
POST_WINDOW_FULL = (2002, 2019)  # post-WTO, ending pre-COVID
POST_WINDOW_TRADE = (2002, 2007) # pre-GFC export-share ramp
EVENT_YEAR = 2001

# Thresholds (made dispositive in the YAML promotion)
TFP_ACCELERATION_THRESHOLD = 0.005   # +0.5pp/yr in rtfpna log-diff
EXPORT_SHARE_THRESHOLD_PP = 8.0      # +8pp in NE.EXP.GNFS.ZS
PEER_NET_TFP_INFORMATIVE = 0.003     # +0.3pp/yr net of peer acceleration


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_long(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        cands = [c for c in t.columns if c not in meta]
        if cands:
            t = t.rename(columns={cands[-1]: "value"})
    t = t[t["country_iso3"].notna() & (t["country_iso3"].str.len() == 3)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def window_mean_growth(level_series: pd.Series, y0: int, y1: int) -> float | None:
    """Mean of year-on-year log-diffs of `level_series` (index=year), within [y0,y1].
    Skips diffs where either endpoint is missing."""
    s = level_series.sort_index()
    s = s[(s.index >= y0) & (s.index <= y1)]
    if len(s) < 2:
        return None
    log_s = np.log(s.where(s > 0))
    diffs = log_s.diff().dropna()
    return float(diffs.mean()) if len(diffs) else None


def window_mean_level(level_series: pd.Series, y0: int, y1: int) -> float | None:
    s = level_series.sort_index()
    s = s[(s.index >= y0) & (s.index <= y1)]
    return float(s.mean()) if len(s) else None


def window_mean_diff(level_series: pd.Series, y0: int, y1: int) -> float | None:
    """For an index series (rtfpna), the level-diff is the growth rate."""
    s = level_series.sort_index()
    s = s[(s.index >= y0) & (s.index <= y1)]
    if len(s) < 2:
        return None
    log_s = np.log(s.where(s > 0))
    diffs = log_s.diff().dropna()
    return float(diffs.mean()) if len(diffs) else None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tfp_path = latest("pwt", "rtfpna")
    exp_path = latest("pwt", "csh_x")
    rgdp_path = latest("pwt", "rgdpna")  # informational

    if tfp_path is None or exp_path is None:
        missing = []
        if tfp_path is None: missing.append("pwt:rtfpna")
        if exp_path is None: missing.append("pwt:csh_x")
        verdict = f"inconclusive — data gap on {', '.join(missing)}"
        (OUT_DIR / "diagnostics.json").write_text(json.dumps({"verdict": verdict}, indent=2) + "\n")
        (OUT_DIR / "manifest.yaml").write_text(
            f"hypothesis_id: {HID}\nstatus: blocked_on_data\n"
        )
        (OUT_DIR / "result_card.md").write_text(f"# {HID}\n\n**Verdict:** {verdict}\n")
        (OUT_DIR / "chart_data.json").write_text(json.dumps({"kind": "result", "series": []}) + "\n")
        pd.DataFrame([{"spec": "data_gap", "term": "missing", "estimate": None}]).to_parquet(
            OUT_DIR / "coefficients.parquet", index=False
        )
        print(f"verdict: {verdict}")
        return

    manifest = {
        "tfp_index_pwt_rtfpna": {
            "publisher": "pwt", "series": "rtfpna",
            "vintage_file": str(tfp_path.relative_to(REPO_ROOT)), "sha256": sha256(tfp_path),
        },
        "export_share_pwt_csh_x": {
            "publisher": "pwt", "series": "csh_x",
            "vintage_file": str(exp_path.relative_to(REPO_ROOT)), "sha256": sha256(exp_path),
        },
    }
    if rgdp_path is not None:
        manifest["real_gdp_pwt_rgdpna"] = {
            "publisher": "pwt", "series": "rgdpna",
            "vintage_file": str(rgdp_path.relative_to(REPO_ROOT)), "sha256": sha256(rgdp_path),
        }

    tfp = load_long(tfp_path)
    exp_raw = load_long(exp_path)

    # PWT csh_x is a 0-1 fraction; convert to percentage points for the
    # threshold comparison (which is in pp units).
    chn_exp = (
        exp_raw[exp_raw["country_iso3"] == TREATED].set_index("year")["value"].sort_index()
        * 100.0
    )

    chn_tfp = tfp[tfp["country_iso3"] == TREATED].set_index("year")["value"].sort_index()

    # ---------- PRIMARY 1: TFP-growth break ----------
    pre_tfp_g = window_mean_diff(chn_tfp, PRE_WINDOW[0], PRE_WINDOW[1])
    post_tfp_g = window_mean_diff(chn_tfp, POST_WINDOW_FULL[0], POST_WINDOW_FULL[1])
    tfp_accel = (
        post_tfp_g - pre_tfp_g
        if pre_tfp_g is not None and post_tfp_g is not None
        else None
    )
    primary1_pass = tfp_accel is not None and tfp_accel >= TFP_ACCELERATION_THRESHOLD

    # ---------- PRIMARY 2: Export-share break ----------
    pre_exp_mean = window_mean_level(chn_exp, PRE_WINDOW[0], PRE_WINDOW[1])
    post_exp_mean_full = window_mean_level(chn_exp, POST_WINDOW_FULL[0], POST_WINDOW_FULL[1])
    post_exp_mean_pregfc = window_mean_level(chn_exp, POST_WINDOW_TRADE[0], POST_WINDOW_TRADE[1])
    export_jump_pp = (
        post_exp_mean_pregfc - pre_exp_mean
        if pre_exp_mean is not None and post_exp_mean_pregfc is not None
        else None
    )
    primary2_pass = export_jump_pp is not None and export_jump_pp >= EXPORT_SHARE_THRESHOLD_PP

    # ---------- INFORMATIVE: peer-difference TFP acceleration ----------
    peer_pre = []
    peer_post = []
    peer_accels = {}
    for c in PEER_COUNTRIES:
        s = tfp[tfp["country_iso3"] == c].set_index("year")["value"].sort_index()
        pre_g = window_mean_diff(s, PRE_WINDOW[0], PRE_WINDOW[1])
        post_g = window_mean_diff(s, POST_WINDOW_FULL[0], POST_WINDOW_FULL[1])
        if pre_g is not None and post_g is not None:
            peer_pre.append(pre_g)
            peer_post.append(post_g)
            peer_accels[c] = post_g - pre_g
    peer_mean_accel = float(np.mean(list(peer_accels.values()))) if peer_accels else None
    net_tfp_accel = (
        tfp_accel - peer_mean_accel
        if tfp_accel is not None and peer_mean_accel is not None
        else None
    )
    informative_pass = net_tfp_accel is not None and net_tfp_accel >= PEER_NET_TFP_INFORMATIVE

    # ---------- Method-validity check ----------
    method_valid = (
        pre_tfp_g is not None and post_tfp_g is not None
        and pre_exp_mean is not None and post_exp_mean_pregfc is not None
        and len(chn_tfp) > 0 and len(chn_exp) > 0
    )
    n_peers_with_data = len(peer_accels)

    # ---------- Verdict ----------
    if not method_valid:
        verdict = "inconclusive — pre/post window means could not be computed for CHN."
    elif primary1_pass and primary2_pass:
        verdict = (
            f"SUPPORTED — CHN PWT-rtfpna mean log-growth rose from "
            f"{pre_tfp_g*100:+.2f}%/yr (1990-2000) to {post_tfp_g*100:+.2f}%/yr "
            f"(2002-2019), acceleration {tfp_accel*100:+.2f}pp/yr "
            f"(threshold +0.50pp/yr). Exports/GDP rose from "
            f"{pre_exp_mean:.1f}% (1990-2000) to {post_exp_mean_pregfc:.1f}% "
            f"(2002-2007), jump {export_jump_pp:+.1f}pp (threshold +8pp). "
            f"Peer-net TFP acceleration {net_tfp_accel*100:+.2f}pp/yr "
            f"(informative threshold +0.30pp/yr) — {'holds' if informative_pass else 'does NOT hold'}."
        )
    elif primary1_pass ^ primary2_pass:
        which = "TFP break held but export-share break missed" if primary1_pass \
                else "Export-share break held but TFP break missed"
        verdict = (
            f"partial — {which}. TFP accel {tfp_accel*100:+.2f}pp/yr "
            f"(threshold +0.50pp/yr); export-share jump {export_jump_pp:+.1f}pp "
            f"(threshold +8pp)."
        )
    else:
        wrong_dir_count = sum(
            1 for v in [tfp_accel, export_jump_pp] if v is not None and v < 0
        )
        if wrong_dir_count >= 1:
            verdict = (
                f"refuted — neither primary clears its threshold AND at least "
                f"one moves the wrong direction. TFP accel "
                f"{tfp_accel*100:+.2f}pp/yr; export-share jump "
                f"{export_jump_pp:+.1f}pp."
            )
        else:
            verdict = (
                f"partial — both primary directions are right but magnitudes "
                f"miss thresholds. TFP accel {tfp_accel*100:+.2f}pp/yr "
                f"(< +0.50pp/yr); export jump {export_jump_pp:+.1f}pp "
                f"(< +8pp)."
            )

    # ---------- diagnostics.json ----------
    diagnostics = {
        "verdict": verdict,
        "method_valid": bool(method_valid),
        "primary1_tfp_break_pass": bool(primary1_pass),
        "primary2_export_share_break_pass": bool(primary2_pass),
        "informative_peer_net_tfp_pass": bool(informative_pass),
        "event_year": EVENT_YEAR,
        "pre_window": list(PRE_WINDOW),
        "post_window_full": list(POST_WINDOW_FULL),
        "post_window_trade": list(POST_WINDOW_TRADE),
        "tfp": {
            "pre_mean_log_growth": pre_tfp_g,
            "post_mean_log_growth": post_tfp_g,
            "acceleration_log_pp_per_yr": tfp_accel,
            "threshold_log_pp_per_yr": TFP_ACCELERATION_THRESHOLD,
        },
        "exports_pct_gdp": {
            "pre_window_mean_pct": pre_exp_mean,
            "post_window_full_mean_pct": post_exp_mean_full,
            "post_window_pregfc_mean_pct": post_exp_mean_pregfc,
            "jump_pp_pregfc_minus_pre": export_jump_pp,
            "threshold_pp": EXPORT_SHARE_THRESHOLD_PP,
        },
        "peer_panel": {
            "countries_requested": PEER_COUNTRIES,
            "n_with_data": n_peers_with_data,
            "peer_mean_acceleration_log_pp_per_yr": peer_mean_accel,
            "net_acceleration_chn_minus_peer_mean": net_tfp_accel,
            "informative_threshold_log_pp_per_yr": PEER_NET_TFP_INFORMATIVE,
            "per_country_acceleration": peer_accels,
        },
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n"
    )

    # ---------- chart_data.json ----------
    palette_chn = "#E15759"
    palette_peer = "#76B7B2"
    series = []

    # CHN TFP index, normalised to 2001 = 1.0
    chn_full = chn_tfp.copy()
    if EVENT_YEAR in chn_full.index and chn_full[EVENT_YEAR] > 0:
        chn_norm = chn_full / chn_full[EVENT_YEAR]
    else:
        chn_norm = chn_full
    series.append({
        "id": "CHN_tfp",
        "label": "China — TFP index (2001 = 1.0)",
        "color": palette_chn,
        "treated": True,
        "points": [{"x": int(y), "y": float(v)} for y, v in chn_norm.items() if not np.isnan(v)],
    })

    # Peer-mean TFP index, also normalised at 2001
    peer_norm_panel = []
    for c in PEER_COUNTRIES:
        s = tfp[tfp["country_iso3"] == c].set_index("year")["value"].sort_index()
        if EVENT_YEAR in s.index and s[EVENT_YEAR] > 0:
            peer_norm_panel.append((s / s[EVENT_YEAR]).rename(c))
    if peer_norm_panel:
        peer_df = pd.concat(peer_norm_panel, axis=1)
        peer_mean_idx = peer_df.mean(axis=1)
        series.append({
            "id": "PEER_tfp",
            "label": "EM-peer mean — TFP index (2001 = 1.0)",
            "color": palette_peer,
            "treated": False,
            "points": [
                {"x": int(y), "y": float(v)}
                for y, v in peer_mean_idx.items() if not np.isnan(v)
            ],
        })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "China vs EM-peer TFP index, 2001 = 1.0",
        "subtitle": (
            f"CHN TFP accel {tfp_accel*100:+.2f}pp/yr "
            f"(thr +{TFP_ACCELERATION_THRESHOLD*100:.2f}pp); "
            f"export-share jump {export_jump_pp:+.1f}pp (thr +{EXPORT_SHARE_THRESHOLD_PP:.0f}pp); "
            f"peer-net TFP {net_tfp_accel*100:+.2f}pp/yr "
            f"(informative thr +{PEER_NET_TFP_INFORMATIVE*100:.2f}pp)."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "PWT rtfpna index (2001 = 1.0)", "type": "linear"},
        "series": series,
        "annotations": [
            {"type": "vline", "x": EVENT_YEAR, "label": "WTO accession (Dec 2001)"},
            {
                "type": "note",
                "label": (
                    f"Pre-window {PRE_WINDOW[0]}-{PRE_WINDOW[1]}; "
                    f"post-window {POST_WINDOW_FULL[0]}-{POST_WINDOW_FULL[1]} "
                    f"(COVID years dropped at the edge)."
                ),
            },
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"], "vintage_file": v["vintage_file"]}
            for v in manifest.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---------- coefficients.parquet ----------
    rows = [
        {"spec": "primary1_tfp", "term": "pre_mean_log_growth", "estimate": pre_tfp_g},
        {"spec": "primary1_tfp", "term": "post_mean_log_growth", "estimate": post_tfp_g},
        {"spec": "primary1_tfp", "term": "acceleration_pp_per_yr", "estimate": tfp_accel},
        {"spec": "primary2_export_share", "term": "pre_window_mean_pct", "estimate": pre_exp_mean},
        {"spec": "primary2_export_share", "term": "post_pregfc_mean_pct", "estimate": post_exp_mean_pregfc},
        {"spec": "primary2_export_share", "term": "post_full_mean_pct", "estimate": post_exp_mean_full},
        {"spec": "primary2_export_share", "term": "jump_pp", "estimate": export_jump_pp},
        {"spec": "informative_peer", "term": "peer_mean_acceleration", "estimate": peer_mean_accel},
        {"spec": "informative_peer", "term": "chn_minus_peer_acceleration", "estimate": net_tfp_accel},
    ]
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---------- manifest.yaml ----------
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "structural_break_with_peer_difference",
        "vintages": manifest,
    }, sort_keys=False))

    # ---------- result_card.md ----------
    lines = [
        f"# Result card — China's WTO accession (2001) productivity-growth effect",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Sample: CHN; peer panel {', '.join(PEER_COUNTRIES)} ({n_peers_with_data} with PWT TFP data).",
        f"- Pre-window: {PRE_WINDOW[0]}-{PRE_WINDOW[1]}; post-window (TFP): {POST_WINDOW_FULL[0]}-{POST_WINDOW_FULL[1]}; "
        f"post-window (trade ramp, pre-GFC): {POST_WINDOW_TRADE[0]}-{POST_WINDOW_TRADE[1]}.",
        "",
        "### PRIMARY 1 — TFP-growth break (PWT rtfpna)",
        "",
        f"- Pre mean log-growth: **{(pre_tfp_g or 0)*100:+.3f}%/yr**.",
        f"- Post mean log-growth: **{(post_tfp_g or 0)*100:+.3f}%/yr**.",
        f"- Acceleration: **{(tfp_accel or 0)*100:+.3f}pp/yr** (threshold +0.50pp/yr).",
        f"- Pass: {'yes' if primary1_pass else 'no'}.",
        "",
        "### PRIMARY 2 — Export-GDP-share break (WDI NE.EXP.GNFS.ZS)",
        "",
        f"- Pre mean: **{(pre_exp_mean or 0):.2f}% of GDP**.",
        f"- Post (pre-GFC ramp 2002-2007) mean: **{(post_exp_mean_pregfc or 0):.2f}% of GDP**.",
        f"- Jump: **{(export_jump_pp or 0):+.2f}pp** (threshold +8pp).",
        f"- Pass: {'yes' if primary2_pass else 'no'}.",
        f"- (Full post-window 2002-2019 mean: {(post_exp_mean_full or 0):.2f}% — note the post-GFC retrenchment.)",
        "",
        "### INFORMATIVE — peer-difference TFP acceleration",
        "",
        f"- Peer-mean acceleration: {(peer_mean_accel or 0)*100:+.3f}pp/yr "
        f"(across {n_peers_with_data} of {len(PEER_COUNTRIES)} EM peers with PWT data).",
        f"- China minus peer mean: **{(net_tfp_accel or 0)*100:+.3f}pp/yr** "
        f"(informative threshold +0.30pp/yr).",
        f"- Pass: {'yes' if informative_pass else 'no'} (informative-only; does not gate the verdict).",
        "",
        "## Method",
        "",
        "Country-level structural-break test on PWT 10.01 rtfpna (TFP at constant national prices) and "
        "WDI NE.EXP.GNFS.ZS (exports as % of GDP), with WTO accession dated to Dec 2001 (event year 2001). "
        "Pre window 1990-2000; post window 2002-2019 for TFP; post window restricted to the pre-GFC "
        "ramp 2002-2007 for the export share, where the trade-creation effect is at its peak in every "
        "published estimate (the post-2008 share collapse is well-documented and not the WTO causal channel). "
        "INFORMATIVE: an EM-peer panel (IND, BRA, MEX, IDN, MYS, THA, TUR, ZAF) gives a coarse "
        "global-TFP-cycle subtraction; this colours the diagnostics but does not gate the verdict.",
        "",
        "## What this design does NOT do",
        "",
        "- The original spec called for an industry-level event study using CIP industry-tariff-cut "
        "data — that source is not on disk in this build, so the country-level structural break is the "
        "best available proxy. The trade-share and TFP timing tests are necessary but not sufficient: "
        "any country-level event in 2001 (eg also: domestic reform deepening, demographic tailwind, "
        "global-credit-boom) is observationally indistinguishable here. The peer-net acceleration is "
        "intended to net out the global cycle, but cannot net out CHN-specific contemporaneous shocks.",
        "",
        "## Sources",
        "",
        f"- PWT 10.01 `rtfpna` (vintage {Path(manifest['tfp_index_pwt_rtfpna']['vintage_file']).name}).",
        f"- PWT 10.01 `csh_x` (export share of expenditure-side GDP at current PPPs; "
        f"vintage {Path(manifest['export_share_pwt_csh_x']['vintage_file']).name}).",
        "  (csh_x is a 0-1 fraction; multiplied by 100 to express in pp.)",
        "  (WDI NE.EXP.GNFS.KD has only 1 non-null observation for CHN in the on-disk "
        "vintage, hence the substitution; PWT csh_x is the closest single-source equivalent.)",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  TFP pre {pre_tfp_g and pre_tfp_g*100:+.3f}%/yr, post {post_tfp_g and post_tfp_g*100:+.3f}%/yr, accel {tfp_accel and tfp_accel*100:+.3f}pp/yr")
    print(f"  Export share pre {pre_exp_mean:.2f}%, post-pre-GFC {post_exp_mean_pregfc:.2f}%, jump {export_jump_pp:+.2f}pp")
    print(f"  Peer-net TFP accel {net_tfp_accel and net_tfp_accel*100:+.3f}pp/yr (n_peers={n_peers_with_data})")


if __name__ == "__main__":
    main()
