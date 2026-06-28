# Second-order Data Acquisition

This directory is the operating surface for acquiring the data needed before
IESET can safely turn on strict second-order policy scoring.

The live scoreboard should not rely on the strict gate as public ranking-grade
evidence until the datasets here are landed, normalized, and joined to policy
treatment contracts. The gate currently holds almost all public claim links
because the corpus has policies and hypotheses, but not enough treatment-unit
and mechanism-layer data.

## Core Files

- `source_inventory.yaml`: source-first catalog of high-leverage datasets.
- `ingestion_queue.yaml`: bounded waves for agent swarms and recurring loops.
- `HUNT_LOOP.md`: operating contract for agents and automations.

Generated outputs:

- `engine/second_order_data_source_index.json`
- `engine/second_order_data_source_index.md`

## Current Program Shape

The initial swarms are:

1. Treatment contracts: event dates, treated units, comparison units,
   exemptions, thresholds, and phase-ins.
2. Household distribution: EUROMOD, EU-SILC/HBS, LIS, CEQ, LSMS, IPUMS,
   CEX, IRS SOI, WID.
3. Labor/payroll: BLS QCEW, Census LEHD/QWI/J2J, ILOSTAT, OECD/Eurostat.
4. Welfare ledger: net-welfare accounting from fiscal, distributional, labor,
   price, quality, supply, and externality panels.
5. Trade/procurement/firms: WITS, Comtrade, UNCTAD, OCDS, TED, Enterprise
   Surveys, EU KLEMS.
6. Energy reliability: EIA, ENTSO-E, IEA, regulator portals, fuel inventory and
   outage proxies.
7. City housing controls: regulated/exempt treatment plus rent, permits,
   quality, listings, evictions, mobility, and conversion layers.
8. Retail scarcity: price schedules, scanner access targets, stockouts,
   complaints, queues, and parallel-market prices.

## Minimum Source Record

Each source record must include:

- `source_id`
- `source_name`
- `source_family_id`
- `publisher`
- `domain`
- `geography`
- `unit_of_observation`
- `time_coverage`
- `policy_or_outcome_fields`
- `access_format`
- `source_url`
- `license_or_terms`
- `update_frequency`
- `second_order_layers`
- `gate_unlocks`
- `acquisition_status`
- `ingestion_difficulty`
- `immediate_payoff_rank`
- `verification_status`
- `notes`

## Validation And Indexing

Run after edits:

```bash
python3 scripts/validate_second_order_data_program.py
python3 scripts/generate_second_order_data_index.py
python3 -m pytest tests/test_second_order_data_program.py
```

If changing source families or gate artifacts, also run the relevant
second-order generators:

```bash
python3 scripts/generate_policy_event_treatment_registry.py
python3 scripts/generate_second_order_test_backlog.py
python3 scripts/generate_scoreboard_second_order_gates.py
```
