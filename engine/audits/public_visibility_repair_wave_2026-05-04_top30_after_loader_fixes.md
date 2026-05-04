# Public Visibility Repair Wave

Generated: 2026-05-05
- Queue: `engine/audits/public_visibility_repair_queue_2026-05-04_after_partial_score_fix.json`
- Reason: `needs_successful_rerun`
- Limit: `30`

## Counts

- blocked: 1
- crashed: 1
- inconclusive_persisted: 28

## Unresolved Templates

- `gdpr_digital_sector_firm_scale_effect` (panel_fe): Traceback (most recent call last):
  File "./engine/runs/gdpr_digital_sector_firm_scale_effect/replication.py", line 282, in <module>
    sys.exit(main())
  File "./engine/runs/gdpr_digital_sector_firm_scale_effect/replication.py", line 149, in main
    df, manifest = assemble()
  File "./engine/runs/gdpr_digital_sector_firm_scale_effect/replication.py", line 84, in assemble
    j_lp, vp1, hp1 = load_pdb_sector("GVAHRS", "J", "LR")
  File "./engine/runs/gdpr_digital_sector_firm_scale_effect/replication.py", line 69, in load_pdb_sector
    p = latest("oecd", "OECD.SDD.TPS_DSD_PDB_DF_PDB_2.0@*.parquet")
  File "./engine/runs/gdpr_digital_sector_firm_scale_effect/replication.py", line 53, in latest
    raise FileNotFoundError(f"{pub}:{pattern}")
FileNotFoundError: oecd:OECD.SDD.TPS_DSD_PDB_DF_PDB_2.0@*.parquet
