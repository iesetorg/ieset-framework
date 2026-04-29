# Korean institutional divergence and the GDP-per-capita gap
**Verdict:** SUPPORTED — Maddison MPD2020 KOR/PRK GDP-pc ratio at 2023 is 33.0x (log-gap +3.50, threshold ≥ 3.00 for SUPPORTED). At 1943 the ratio was 0.68x (log-gap -0.38). Cumulative log-growth: KOR +3.21, PRK -0.67; gap +3.88 log-points over 80 years.
## Headline numbers
- Endpoint (2023, Maddison): KOR $41,800 vs PRK $1,265; ratio **33.0x**; log-gap **+3.50**.
- Pre-window (1943, Maddison): KOR $1,686 vs PRK $2,462; ratio 0.68x; log-gap -0.38.
- Cumulative log-growth 1943→2023: KOR +3.21, PRK -0.67; gap +3.88 log-points over 80 years (annualised: KOR +4.01%/yr; PRK -0.83%/yr).
- Life expectancy at birth (WDI, 2024): KOR 83.6y vs PRK 73.7y; gap **+9.9 years**.
- Bank of Korea cross-check (DPRK GNI reconstruction, 2023): KOR/PRK ratio 40.3x.
## Threshold applied
- PRIMARY (dispositive): `log_gdppc(KOR, 2023) − log_gdppc(PRK, 2023)` determines the verdict. SUPPORTED if ≥ ln(20) ≈ 3.00 (i.e. ≥ 20× ratio, matching the claim's '~20x'); refuted if < ln(10) ≈ 2.30 (less than half the claimed gap, per the spec); partial otherwise.
- INFORMATIVE: pre-window |log-gap| at 1943 should be < 0.30 (realised 0.38; informative pass: **False**).
| Component | Threshold | Realised | Pass |
|---|---:|---:|:---:|
| Endpoint log-gap (SUPPORTED) | ≥ 3.00 | +3.50 | yes |
| Endpoint log-gap (not refuted) | ≥ 2.30 | +3.50 | yes |
| Pre-window |log-gap| (informative) | < 0.30 | 0.38 | no |
## Method
Bilateral KOR–PRK descriptive comparison. Primary GDP source is Maddison MPD2020 (Bolt & van Zanden 2020), the canonical long-run cross-country panel; values are in 2011 international $. The Maddison Korea-extension series (2020–2023) provides the endpoint year. Bank of Korea's DPRK GNI reconstruction (2020–2023) is reported as a cross-check. WDI is used for life expectancy (NY.GDP.PCAP.KD has no PRK observations and therefore cannot serve as the primary GDP series).
Verdict logic is dispositive on the endpoint ratio: < 10× → refuted (less than half the claimed ~20×); ≥ 20× → supported; between → partial. The pre-window gap at 1953 colours method validity (large pre-1953 gaps would weaken the natural-experiment framing) but does not gate the verdict.
## Caveats
- This is a descriptive bilateral comparison, not causal identification. The pre-1945 administrative division of Korea was not random with respect to industrial endowments — Japan-built heavy industry and most hydroelectric capacity sat in the north, favouring the DPRK at independence. The fact that the south overtook anyway *strengthens* the institutionalist read but does not establish causation.
- Pre-window choice: the spec's nominal baseline is 1953 (post-armistice). MPD2020 has no PRK observations 1944–1989, so the replication uses **1943** (latest_pre_division_1943) as the realised pre-window. This is the best published anchor for the 'matched starting conditions' premise; readers who want a 1953 baseline must rely on Bank of Korea's reconstruction, which only covers 2020–2023.
- DPRK GDP is hard to measure. Maddison's PRK series is itself a reconstruction (Lee, Bolt, others), so figures past 1990 have wider error bars than the KOR series.
- Post-1945 paths differ in foreign aid, security alignment, and 1960s policy choices, so divergence is the institutions × aid × alignment bundle. Claim authors who treat this as a clean natural experiment overstate identification (per the spec's disclosure block).
## Sources
- Maddison MPD2020 (`mpd2020`).
- Maddison Korea extension (`mpd2020_korea_extension`, 2020–2023).
- Bank of Korea DPRK GNI reconstruction (`dprk_gdp_reconstruction`, 2020–2023).
- World Bank WDI `NY.GDP.PCAP.KD` (KOR cross-check; PRK all-NaN).
- World Bank WDI `SP.DYN.LE00.IN` (life expectancy at birth).
