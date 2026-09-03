"""Drive the real generate_video_shot_list.py entrypoint on a real package."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generate_korea_shot_list(tmp_path: Path) -> None:
    out = tmp_path / "SHOT_LIST.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_video_shot_list.py"),
            "--hypothesis-id",
            "korean_institutional_divergence_gdp_gap",
            "--case-dir",
            "out/case_studies/20260710-korean-institutional-divergence-gdp-gap",
            "--education",
            "education/lesson_modules/korean_institutional_divergence_video_brief.md",
            "--social",
            "outreach/social_drafts/korean_institutional_divergence_video_wave_hooks.md",
            "--title",
            "Korean Institutional Divergence",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "SUPPORTED" in text.upper()
    assert "framework.ieset.org/h/korean_institutional_divergence_gdp_gap" in text
    assert "Publish checklist" in text
    assert "Scene board" in text


def test_wave_kit_has_vo_and_assets() -> None:
    wave = ROOT / "out" / "video_wave_20260710"
    for ep in ("01_chile", "02_korea", "03_volcker", "04_fiat"):
        assert (wave / ep / "VO_SCRIPT.md").is_file()
        assert (wave / ep / "SHOT_LIST.md").is_file()
        assert (wave / ep / "thread.md").is_file()
    assert list((wave / "02_korea" / "assets").glob("chart*.png")), "korea charts missing"
    assert (wave / "00_master" / "WAVE_PLAN.md").is_file()
