# US WWII fiscal expansion & inflation aftermath

**Verdict:** SUPPORTED — 5-yr post-control mean CPI YoY +2.21%/yr <= 3.0%/yr threshold. WWII-peak federal deficit (1943-45 mean): -23.0%GDP (magnitude 23.0%). Immediate post-control 1947 YoY: +14.4%; 1947-48 mean: +11.0%; 1953-57 follow-on mean: +1.1%; pre-WWII (1923-40) baseline mean: -0.9%.

## Summary

- WWII-peak federal deficit (1943-1945 mean): **-23.0% of GDP** (magnitude 23.0%; the largest sustained US fiscal expansion of the 20th century).
- Pre-WWII baseline CPI inflation (1923-1940 mean): **-0.91%/yr** (deflationary tilt of the inter-war era).
- Immediate post-OPA-termination CPI YoY: 1947 = **+14.4%**; 1947-1948 mean = **+11.0%/yr**.
- **PRIMARY (dispositive):** mean CPI YoY 1949-1953 = **+2.21%/yr**.
  - SUPPORTED threshold: <= 3.0%/yr.
  - REFUTED threshold: > 5.0%/yr.
- 1953-1957 follow-on mean: **+1.14%/yr** (second sustainability check).

## Method

Window-mean test on annualised FRED CPIAUCNS YoY inflation, with
the dispositive PRIMARY window 1949-1953 chosen to start 2 full
years after the Nov-1946 OPA price-control termination so the
immediate 1947 de-control spike is excluded from the dispositive
test. The 1947 spike and the 1947-1948 window are reported as
INFORMATIVE so the reader can see what the MMT framing discounts.

METHOD_VALID gates: (i) FRED CPIAUCNS and FYFSGDA188S vintages
cover the full 1939-1957 window; (ii) WWII-peak (1943-1945 mean)
federal deficit magnitude must exceed 15% of GDP
(confirms we are testing the WWII-scale fiscal expansion case).

Caveat (per the spec's `disclosure` field): the verdict is
window-choice sensitive. The 8-year 1946-1953 window mean is
substantially higher (the 1946-1948 surge dominates), and the
Korean-War 1951 spike (separate fiscal-impulse event) is included
in the PRIMARY window. The Romer-counterfactual price-control
adjustment (reflate suppressed wartime CPI) is left to v2.

## Data

- fred:CPIAUCNS — US CPI all items, 1913+ monthly
- fred:FYFSGDA188S — US federal surplus/deficit % GDP, 1929+ annual
