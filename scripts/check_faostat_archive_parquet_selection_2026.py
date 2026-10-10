#!/usr/bin/env python3
"""Compare every FAOSTAT family selector row in official ZIP CSV vs derived Parquet."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_faostat_relative_price_supply_2026.py"
SPEC = importlib.util.spec_from_file_location("faostat_family", RUNNER_PATH)
FAMILY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FAMILY)
OUTPUT = ROOT / "engine/audits/faostat_archive_parquet_selection_check_2026-10-10.json"


def canon_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def canon_number(value: object) -> str:
    if value is None or canon_text(value) == "":
        return ""
    number = float(value)
    if math.isnan(number):
        return ""
    if not math.isfinite(number):
        raise RuntimeError(f"nonfinite source value {value!r}")
    return number.hex()


def collect_archive(archive: Path, selected: set[int], price: bool) -> dict:
    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"not a ZIP archive: {archive}")
    result = {}
    with zipfile.ZipFile(archive) as z:
        names = [name for name in z.namelist() if name.endswith("All_Data_(Normalized).csv")]
        if len(names) != 1:
            raise RuntimeError(f"unexpected CSV archive contents: {names}")
        with z.open(names[0]) as binary:
            reader = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            for row in reader:
                item, element = int(row["Item Code"]), int(row["Element Code"])
                if item not in selected or element != (FAMILY.INDEX_ELEMENT if price else -1) and price:
                    continue
                if price and int(row["Months Code"]) != FAMILY.ANNUAL_MONTH_CODE:
                    continue
                if not price and element not in {v["code"] for v in FAMILY.MARGINS.values()}:
                    continue
                key = (canon_text(row["Area Code (M49)"]), item, element, int(row["Year"]))
                if price:
                    key += (int(row["Months Code"]),)
                if key in result:
                    raise RuntimeError(f"duplicate archive key: {key}")
                result[key] = (canon_number(row["Value"]), canon_text(row["Flag"]), canon_text(row["Unit"]))
    return result


def collect_parquet(path: Path, selected: set[int], price: bool) -> dict:
    cols = ["Area Code (M49)", "Item Code", "Element Code", "Year", "Unit", "Value", "Flag"]
    if price:
        cols.append("Months Code")
    frame = pd.read_parquet(path, columns=cols)
    frame = frame.loc[frame["Item Code"].isin(selected)]
    frame = frame.loc[frame["Element Code"].eq(FAMILY.INDEX_ELEMENT)] if price else frame.loc[
        frame["Element Code"].isin([v["code"] for v in FAMILY.MARGINS.values()])]
    if price:
        frame = frame.loc[frame["Months Code"].eq(FAMILY.ANNUAL_MONTH_CODE)]
    result = {}
    for r in frame.to_dict("records"):
        key = (canon_text(r["Area Code (M49)"]), int(r["Item Code"]), int(r["Element Code"]), int(r["Year"]))
        if price:
            key += (int(r["Months Code"]),)
        if key in result:
            raise RuntimeError(f"duplicate derived key: {key}")
        result[key] = (canon_number(r["Value"]), canon_text(r["Flag"]), canon_text(r["Unit"]))
    return result


def digest(mapping: dict) -> str:
    sha = hashlib.sha256()
    for key, fields in sorted(mapping.items()):
        sha.update(json.dumps([key, fields], ensure_ascii=False, separators=(",", ":")).encode())
        sha.update(b"\n")
    return sha.hexdigest()


def compare(label: str, archive: Path, parquet: Path, items: set[int], price: bool) -> dict:
    original = collect_archive(archive, items, price)
    derived = collect_parquet(parquet, items, price)
    if original != derived:
        missing = sorted(original.keys() - derived.keys())[:5]
        extra = sorted(derived.keys() - original.keys())[:5]
        changed = [(key, original[key], derived[key]) for key in original.keys() & derived.keys()
                   if original[key] != derived[key]][:5]
        raise RuntimeError(f"{label} archive/parquet mismatch: missing={missing}; extra={extra}; changed={changed}")
    return {"selected_rows": len(original), "row_and_measurement_sha256": digest(original),
            "archive_path": str(archive.relative_to(archive.parents[3])),
            "parquet_path": str(parquet.relative_to(parquet.parents[3])),
            "exact_selected_key_value_flag_unit_match": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    reg, roster_hash, _ = FAMILY.registration_commit()
    lock = FAMILY.source_lock_commit(args.source_root, reg, roster_hash)
    price_items = {FAMILY.AGRICULTURE_INDEX_CODE} | {v["code"] for v in FAMILY.GROUPS.values()}
    crop_items = {v["code"] for v in FAMILY.GROUPS.values()}
    checks = {
        "price": compare("price", FAMILY.raw(args.source_root, "price_archive"),
                         FAMILY.raw(args.source_root, "price_panel"), price_items, True),
        "crop": compare("crop", FAMILY.raw(args.source_root, "crop_archive"),
                        FAMILY.raw(args.source_root, "crop_panel"), crop_items, False),
    }
    report = {"family_id": FAMILY.FAMILY, "registration_commit": reg, "source_lock_commit": lock,
              "source_lock": FAMILY.LOCK, "checks": checks,
              "scope": "all selected item/element/month rows, including non-ISO3 keys and excluded flags; exact key, binary64 numeric value, flag and unit",
              "limit": "This verifies selected archive-to-Parquet equality, not the upstream FAOSTAT collection process or future source availability."}
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.verify:
        if not OUTPUT.is_file() or OUTPUT.read_text() != output:
            raise RuntimeError("archive/parquet audit exact replay mismatch")
        print("exact archive/parquet audit replay passed", {k: v["selected_rows"] for k, v in checks.items()})
    else:
        if OUTPUT.exists():
            raise RuntimeError("audit output already exists")
        OUTPUT.write_text(output)
        print("exact archive/parquet match", {k: v["selected_rows"] for k, v in checks.items()})


if __name__ == "__main__":
    main()
