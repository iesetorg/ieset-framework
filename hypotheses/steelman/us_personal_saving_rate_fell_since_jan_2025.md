# Steelman: us_personal_saving_rate_fell_since_jan_2025

Claim: Since January 2025 the US personal saving rate has fallen from about 5.7% to about 4.1%, the lowest since 2022, while real wages have been falling: households are drawing down savings to keep up with prices.

Strongest opposing case: Saving-rate levels are heavily revised at annual NIPA updates, and a falling saving rate can reflect rising asset wealth (wealth effect) rather than distress. Real average hourly earnings is a composition-sensitive series. The post attributes the fall to tariffs and war; this test checks only the facts, not the cause.

This test is descriptive, not causal.

Falsification (frozen): Let d = PSAVERT(latest) - PSAVERT(2025-01). Let low = PSAVERT(latest) < min(PSAVERT 2023-01..2024-12). Let rw = real AHE (CES0500000003/CPIAUCSL) latest common month vs 6 months earlier. SUPPORTED if d <= -1.0pp AND low AND rw < 0. REFUTED if d >= 0. PARTIAL otherwise. Current vintage as fetched on run date.

Source post(s): https://x.com/SteveRattner/status/2107916376459579534
