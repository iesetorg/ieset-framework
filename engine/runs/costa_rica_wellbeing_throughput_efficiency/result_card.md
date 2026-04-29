# Costa Rica wellbeing-throughput v3 honesty correction

**Verdict:** refuted — homicide test fails: CRI homicide rate 10.9/100k vs USA 5.0/100k (ratio 2.19x > 1.5 threshold). v2 SUPPORTED was indicator-gamed; canonical wellbeing basket includes safety, and Costa Rica fails this leg. LE/CO2 legs still pass (LE ratio 1.019, CO2 ratio 0.096) but the canonical claim 'comparable wellbeing' is refuted on safety. Cantril ladder / WHR not on disk.

## Why v3 differs from v2

v2 graded SUPPORTED on LE + CO2 alone, reducing 'wellbeing' to life expectancy. Canonical wellbeing literature (OECD BLI, WHR, UNDP HDI extensions) defines wellbeing as multi-dimensional. Costa Rica is a documented regional outlier on homicide rate (~12/100k vs USA ~5/100k) — a wellbeing degradation excluded from v2.

## Canonical basket

| Dim | Source | Status |
|---|---|---|
| LE | WDI SP.DYN.LE00.IN | ✓ |
| Throughput (CO2) | OWID | ✓ |
| Safety (homicide) | WDI VC.IHR.PSRC.P5 | ✓ |
| UHC | WHO | ✓ |
| Cantril ladder | gallup_whr | **✗ missing** |

## Numbers

- LE ratio: 1.0186874982350118
- CO2 ratio: 0.09558283926003851
- Homicide ratio: 2.1912787633004944
- UHC ratio: 0.9620653319283456

## Archives

v2 (2-indicator subset, SUPPORTED) at ARCHIVED_v2/.
