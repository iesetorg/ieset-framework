#!/usr/bin/env python3
"""Build Colombia city rent/housing CPI panel from DANE IPC city tables."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location("ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load data/fetchers/_base.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FETCHER_BASE = load_fetcher_base()
FetchResult = _FETCHER_BASE.FetchResult
utc_now = _FETCHER_BASE.utc_now
utc_stamp = _FETCHER_BASE.utc_stamp

METHODOLOGY_URL = "https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc"
SOURCE_URL = (
    "https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/"
    "indice-de-precios-al-consumidor-ipc/ipc-historico"
)
LICENSE = "DANE public-use/citation terms; verify per downloaded table"
SOURCE_DATASET = "DANE IPC city rent and housing items"
HOUSING_DIVISION_CODE = "04"
HOUSING_DIVISION_NAME = "Alojamiento, Agua, Electricidad, Gas Y Otros Combustibles"

FIELD_ALIASES = {
    "city_name": ["ciudad", "dominio", "area", "geografia", "geography", "municipio", "city"],
    "date": ["fecha", "periodo", "period", "date"],
    "year": ["ano", "año", "year", "anio"],
    "month": ["mes", "month"],
    "item_code": ["codigo", "cod_item", "codigo_item", "coicop", "clase", "subclase", "gasto_basico_codigo"],
    "item_name": ["item", "producto", "nombre_item", "gasto_basico", "descripcion", "division", "subclase_nombre"],
    "index_value": ["indice", "index", "valor_indice", "ipc", "valor"],
    "monthly_variation_pct": ["variacion_mensual", "variacion mensual", "var_mensual", "monthly_variation"],
    "annual_variation_pct": ["variacion_anual", "variacion anual", "var_anual", "annual_variation"],
    "year_to_date_variation_pct": ["variacion_ano_corrido", "variacion año corrido", "ano_corrido", "year_to_date_variation"],
    "weight": ["ponderacion", "peso", "weight"],
}

FUZZY_TOKENS = {
    "city_name": [["ciudad"], ["dominio"], ["geograf"], ["municip"]],
    "date": [["fecha"], ["period"]],
    "year": [["ano"], ["anio"], ["year"]],
    "month": [["mes"], ["month"]],
    "item_code": [["codigo"], ["coicop"], ["subclase"], ["gasto", "codigo"]],
    "item_name": [["item"], ["producto"], ["gasto"], ["descripcion"], ["subclase"]],
    "index_value": [["indice"], ["ipc"], ["valor"]],
    "monthly_variation_pct": [["variacion", "mensual"], ["var", "mensual"]],
    "annual_variation_pct": [["variacion", "anual"], ["var", "anual"]],
    "year_to_date_variation_pct": [["corrido"], ["year", "date"]],
    "weight": [["ponder"], ["peso"], ["weight"]],
}

RENT_ITEM_PATTERNS = [
    re.compile(r"\bARRIEND"),
    re.compile(r"\bALQUIL"),
    re.compile(r"\bRENTA\b"),
    re.compile(r"\bALOJAMIENTO\b"),
]

CITY_ALIASES = {
    "BOGOTA D C": "BOGOTA",
    "BOGOTA": "BOGOTA",
    "MEDELLIN": "MEDELLIN",
    "CALI": "CALI",
    "BARRANQUILLA": "BARRANQUILLA",
    "CARTAGENA": "CARTAGENA",
    "CARTAGENA DE INDIAS": "CARTAGENA",
    "BUCARAMANGA": "BUCARAMANGA",
    "CUCUTA": "CUCUTA",
    "PEREIRA": "PEREIRA",
    "VALLEDUPAR": "VALLEDUPAR",
}

SPANISH_MONTHS = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "SETIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def normalise_token(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def normalise_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("\u00a0", "")
    if text in {".", "..", "-", "nan", "NaN"}:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    number = parse_number(value)
    return None if number is None else int(number)


def parse_month(value: object) -> int | None:
    number = parse_int(value)
    if number is not None and 1 <= number <= 12:
        return number
    text = normalise_name(value)
    for month_name, month_number in SPANISH_MONTHS.items():
        if month_name in text:
            return month_number
    return None


def parse_spanish_period_label(value: object) -> tuple[int, int] | None:
    text = normalise_name(value)
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    if not year_match:
        return None
    month = parse_month(text)
    if month is None:
        return None
    return int(year_match.group(1)), month


def parse_date_values(values: pd.Series) -> pd.Series:
    text = values.astype(str)
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    compact_parts = text.str.extract(r"^\s*(\d{4})(\d{2})(?:\d{2})?\s*$")
    compact_mask = compact_parts[0].notna()
    if compact_mask.any():
        compact_text = compact_parts.loc[compact_mask, 0] + "-" + compact_parts.loc[compact_mask, 1] + "-01"
        parsed.loc[compact_mask] = pd.to_datetime(compact_text, errors="coerce")
    iso_mask = text.str.match(r"^\s*\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?\s*$", na=False) & ~compact_mask
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(text.loc[iso_mask], errors="coerce", dayfirst=False)
    local_mask = parsed.isna()
    if local_mask.any():
        parsed.loc[local_mask] = pd.to_datetime(text.loc[local_mask], errors="coerce", dayfirst=True)
    return parsed


def pick_field(columns: list[str], logical_name: str, required: bool = True) -> str | None:
    normalised = {normalise_token(column): column for column in columns}
    for alias in FIELD_ALIASES[logical_name]:
        match = normalised.get(normalise_token(alias))
        if match:
            return match
    for column in columns:
        token = normalise_token(column)
        if logical_name in {"year", "month"} and ("variacion" in token or "variation" in token):
            continue
        for token_set in FUZZY_TOKENS[logical_name]:
            if all(part in token for part in token_set):
                return column
    if required:
        raise ValueError(f"could not identify field for {logical_name}; columns={columns}")
    return None


def is_dane_annex_workbook(path: Path) -> bool:
    try:
        workbook = pd.ExcelFile(path)
    except Exception:
        return False
    return {"4", "5", "6"}.issubset(set(workbook.sheet_names))


def find_annex_city_sheet(path: Path, variation_token: str, required: bool = True) -> str | None:
    workbook = pd.ExcelFile(path)
    for sheet_name in workbook.sheet_names:
        preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=6)
        text = " ".join(normalise_name(value) for value in preview.to_numpy().ravel())
        if (
            "SEGUN CIUDADES" in text
            and "DIVISIONES" in text
            and variation_token in text
            and "GRUPOS" not in text
        ):
            return sheet_name
    if required:
        raise ValueError(f"{path} is missing the DANE IPC city/division sheet for {variation_token}")
    return None


def parse_annex_sheet(path: Path, sheet_name: str, metric_name: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_candidates = raw.index[raw.iloc[:, 0].map(normalise_name).eq("CIUDADES")].tolist()
    if not header_candidates:
        raise ValueError(f"{path} sheet {sheet_name} is missing a city header row")
    header_row = header_candidates[0]
    period_candidates = [
        parse_spanish_period_label(value)
        for value in raw.iloc[:header_row, 0].tolist()
        if parse_spanish_period_label(value) is not None
    ]
    if not period_candidates:
        raise ValueError(f"{path} sheet {sheet_name} is missing a period label")
    year, month = period_candidates[-1]
    headers = raw.iloc[header_row].tolist()
    housing_cols = [
        idx
        for idx, value in enumerate(headers)
        if "ALOJAMIENTO" in normalise_name(value) and "COMBUSTIBLES" in normalise_name(value)
    ]
    if not housing_cols:
        raise ValueError(f"{path} sheet {sheet_name} is missing the housing IPC division column")
    city_col = 0
    value_col = housing_cols[0]
    rows = []
    for _, row in raw.iloc[header_row + 1 :].iterrows():
        city = row.iloc[city_col]
        city_norm = normalise_name(city)
        if not city_norm or city_norm in {"TOTAL IPC", "IPC TOTAL", "TOTAL NACIONAL", "NACIONAL", "FUENTE DANE"}:
            continue
        value = parse_number(row.iloc[value_col])
        if value is None:
            continue
        rows.append(
            {
                "Ciudad": str(city).strip(),
                "Periodo": f"{year}-{month:02d}-01",
                "Codigo": HOUSING_DIVISION_CODE,
                "Gasto Basico": HOUSING_DIVISION_NAME,
                metric_name: value,
            }
        )
    if not rows:
        raise ValueError(f"{path} sheet {sheet_name} produced no city rows")
    return pd.DataFrame(rows)


def parse_dane_annex_workbook(path: Path, workbook_url: str | None = None) -> list[dict[str, Any]]:
    key_cols = ["Ciudad", "Periodo", "Codigo", "Gasto Basico"]
    monthly = parse_annex_sheet(path, find_annex_city_sheet(path, "VARIACION MENSUAL"), "Variacion mensual")
    ytd = parse_annex_sheet(path, find_annex_city_sheet(path, "VARIACION ANO CORRIDO"), "Variacion año corrido")
    merged = monthly.merge(ytd, on=key_cols, how="outer")
    annual_sheet = find_annex_city_sheet(path, "VARIACION ANUAL", required=False)
    if annual_sheet:
        annual = parse_annex_sheet(path, annual_sheet, "Variacion anual")
        merged = merged.merge(annual, on=key_cols, how="outer")
    else:
        merged["Variacion anual"] = pd.NA
    merged["Indice"] = pd.NA
    merged["source_workbook"] = rel(path)
    merged["source_workbook_url"] = workbook_url or SOURCE_URL
    merged["source_workbook_sha256"] = sha256_path(path)
    return merged.to_dict("records")


def parse_dane_annex_directory(path: Path) -> list[dict[str, Any]]:
    manifest_path = path / "manifest_2026-06-29.json"
    url_by_path: dict[str, str] = {}
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text())
        url_by_path = {str(Path(record["path"]).resolve()): record["url"] for record in payload.get("records", [])}
    rows: list[dict[str, Any]] = []
    workbooks = sorted(p for p in path.glob("*.xlsx") if p.name != manifest_path.name)
    for workbook in workbooks:
        if not is_dane_annex_workbook(workbook):
            continue
        rows.extend(parse_dane_annex_workbook(workbook, url_by_path.get(str(workbook.resolve()))))
    return rows


def load_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"missing DANE IPC input: {path}. Export city/item IPC rows from {SOURCE_URL} into {rel(path)}."
        )
    if path.is_dir():
        return parse_dane_annex_directory(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", payload))
        if not isinstance(payload, list):
            raise ValueError(f"expected JSON list in {path}")
        return payload
    if suffix == ".csv":
        return pd.read_csv(path).to_dict("records")
    if suffix in {".xls", ".xlsx"}:
        if is_dane_annex_workbook(path):
            return parse_dane_annex_workbook(path)
        return pd.read_excel(path).to_dict("records")
    raise ValueError(f"unsupported input format: {path}")


def parse_period(frame: pd.DataFrame, fields: dict[str, str | None]) -> pd.DataFrame:
    if fields["year"] and fields["month"]:
        years = frame[fields["year"]].map(parse_int)
        months = frame[fields["month"]].map(parse_month)
        period = years.astype("Int64").astype(str) + "-" + months.astype("Int64").astype(str).str.zfill(2)
        return pd.DataFrame({"year": years, "month": months, "period": period})
    if fields["date"]:
        parsed = parse_date_values(frame[fields["date"]])
        return pd.DataFrame({"year": parsed.dt.year, "month": parsed.dt.month, "period": parsed.dt.strftime("%Y-%m")})
    raise ValueError("DANE IPC rows need either a date/period field or year+month fields")


def is_rent_item(item_name: object, item_code: object = None) -> bool:
    text = normalise_name(item_name)
    if any(pattern.search(text) for pattern in RENT_ITEM_PATTERNS):
        return True
    code = "" if pd.isna(item_code) else str(item_code)
    code_digits = re.sub(r"\D+", "", code)
    return code.strip() in {"04", "041", "0411", "0412", "04.1.1", "04.1.2"} or code_digits in {
        "04",
        "04000000",
        "041",
        "0411",
        "0412",
        "4000000",
        "411",
        "412",
    }


def build_colombia_alias_map(city_spine: pd.DataFrame) -> dict[str, dict[str, Any]]:
    colombia = city_spine[city_spine["country_name"].eq("Colombia")].copy()
    aliases: dict[str, list[dict[str, Any]]] = {}
    for row in colombia.to_dict("records"):
        name = normalise_name(row["city_name"])
        aliases.setdefault(name, []).append(
            {
                "ieset_city_id": row["ieset_city_id"],
                "ghsl_city_name": row["city_name"],
                "ghsl_city_rank_2025": row["city_rank_2025"],
                "match_type": "normalized_name",
                "manual_review_required": False,
            }
        )
    return {alias: records[0] for alias, records in aliases.items() if len({r["ieset_city_id"] for r in records}) == 1}


def attach_city_matches(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path) if city_spine_path.suffix.lower() == ".csv" else pd.read_parquet(city_spine_path)
    alias_map = build_colombia_alias_map(spine)
    rows = []
    for row in panel[["dane_city_name_norm"]].drop_duplicates().to_dict("records"):
        canonical = CITY_ALIASES.get(row["dane_city_name_norm"], row["dane_city_name_norm"])
        match = alias_map.get(canonical)
        if match:
            rows.append({"dane_city_name_norm": row["dane_city_name_norm"], **match})
        else:
            rows.append(
                {
                    "dane_city_name_norm": row["dane_city_name_norm"],
                    "ieset_city_id": None,
                    "ghsl_city_name": None,
                    "ghsl_city_rank_2025": pd.NA,
                    "match_type": "unmatched_or_ambiguous_name",
                    "manual_review_required": True,
                }
            )
    return panel.merge(pd.DataFrame(rows), on="dane_city_name_norm", how="left")


def build_panel(
    *,
    city_spine_path: Path,
    input_path: Path | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if rows is None:
        if input_path is None:
            raise ValueError("input_path is required when rows are not supplied")
        rows = load_input(input_path)
    if not rows:
        raise ValueError("DANE IPC input returned no rows")
    frame = pd.DataFrame(rows)
    columns = list(frame.columns)
    fields = {
        "city_name": pick_field(columns, "city_name"),
        "date": pick_field(columns, "date", required=False),
        "year": pick_field(columns, "year", required=False),
        "month": pick_field(columns, "month", required=False),
        "item_code": pick_field(columns, "item_code", required=False),
        "item_name": pick_field(columns, "item_name"),
        "index_value": pick_field(columns, "index_value", required=False),
        "monthly_variation_pct": pick_field(columns, "monthly_variation_pct", required=False),
        "annual_variation_pct": pick_field(columns, "annual_variation_pct", required=False),
        "year_to_date_variation_pct": pick_field(columns, "year_to_date_variation_pct", required=False),
        "weight": pick_field(columns, "weight", required=False),
    }
    period = parse_period(frame, fields)
    panel = pd.DataFrame(
        {
            "period": period["period"],
            "year": period["year"],
            "month": period["month"],
            "country_name": "Colombia",
            "country_iso3": "COL",
            "dane_city_name": frame[fields["city_name"]].astype(str).str.strip(),
            "item_code": frame[fields["item_code"]].astype(str).str.strip() if fields["item_code"] else pd.NA,
            "item_name": frame[fields["item_name"]].astype(str).str.strip(),
            "index_value": frame[fields["index_value"]].map(parse_number) if fields["index_value"] else pd.NA,
            "monthly_variation_pct": frame[fields["monthly_variation_pct"]].map(parse_number) if fields["monthly_variation_pct"] else pd.NA,
            "annual_variation_pct": frame[fields["annual_variation_pct"]].map(parse_number) if fields["annual_variation_pct"] else pd.NA,
            "year_to_date_variation_pct": frame[fields["year_to_date_variation_pct"]].map(parse_number) if fields["year_to_date_variation_pct"] else pd.NA,
            "weight": frame[fields["weight"]].map(parse_number) if fields["weight"] else pd.NA,
            "source_workbook": frame["source_workbook"] if "source_workbook" in frame.columns else pd.NA,
            "source_workbook_url": frame["source_workbook_url"] if "source_workbook_url" in frame.columns else pd.NA,
            "source_workbook_sha256": frame["source_workbook_sha256"] if "source_workbook_sha256" in frame.columns else pd.NA,
        }
    )
    panel["dane_city_name_norm"] = panel["dane_city_name"].map(normalise_name)
    panel["item_name_norm"] = panel["item_name"].map(normalise_name)
    panel = panel[panel.apply(lambda row: is_rent_item(row["item_name"], row["item_code"]), axis=1)].copy()
    panel = panel.dropna(subset=["period", "year", "month", "dane_city_name"]).copy()
    metric_cols = ["index_value", "monthly_variation_pct", "annual_variation_pct", "year_to_date_variation_pct"]
    panel = panel[panel[metric_cols].notna().any(axis=1)].copy()
    if panel.empty:
        raise ValueError("DANE IPC rows had no usable rent/housing city observations after filtering")
    panel["year"] = panel["year"].astype(int)
    panel["month"] = panel["month"].astype(int)
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = panel["source_workbook_url"].where(panel["source_workbook_url"].notna(), SOURCE_URL)
    panel["dane_item_filter_note"] = (
        "Rows retained when item names/codes indicate rent/arriendo/alquiler subitems or the DANE housing "
        "division Alojamiento, Agua, Electricidad, Gas Y Otros Combustibles."
    )
    panel = attach_city_matches(panel, city_spine_path)
    ordered = [
        "period",
        "year",
        "month",
        "country_name",
        "country_iso3",
        "dane_city_name",
        "dane_city_name_norm",
        "ieset_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "match_type",
        "manual_review_required",
        "item_code",
        "item_name",
        "item_name_norm",
        "index_value",
        "monthly_variation_pct",
        "annual_variation_pct",
        "year_to_date_variation_pct",
        "weight",
        "source_workbook",
        "source_workbook_url",
        "source_workbook_sha256",
        "source_dataset",
        "source_url",
        "dane_item_filter_note",
    ]
    panel = panel[ordered].sort_values(["period", "dane_city_name", "item_code"]).reset_index(drop=True)
    stats = {
        "panel_rows": int(len(panel)),
        "start_period": str(panel["period"].min()),
        "end_period": str(panel["period"].max()),
        "dane_city_count": int(panel["dane_city_name_norm"].nunique()),
        "matched_cities": int(panel[["dane_city_name_norm", "ieset_city_id"]].drop_duplicates()["ieset_city_id"].notna().sum()),
        "matched_observation_rows": int(panel["ieset_city_id"].notna().sum()),
        "unique_ieset_city_ids": int(panel["ieset_city_id"].nunique(dropna=True)),
        "item_count": int(panel["item_name_norm"].nunique()),
        "source_workbook_count": int(panel["source_workbook"].nunique(dropna=True)),
        "fields": fields,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_colombia_dane_ipc_city_rent.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "colombia_dane_ipc_city_rent_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="colombia_dane",
        series_id="colombia_dane_ipc_city_rent_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="monthly",
        units="IPC housing/rent item index and percentage variations",
        currency=None,
        start_date=stats["start_period"],
        end_date=stats["end_period"],
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Exported or annexed DANE IPC city rows filtered to rent-related CPI items or the housing "
                "division, normalized to city-month observations, and matched to the Colombia subset of the "
                "GHSL top-1000 city spine."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", default="data/raw/city_level/dane_ipc_city_rent_items.csv")
    parser.add_argument("--output", default="data/derived/colombia_dane_ipc_city_rent_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        input_path=path_arg(args.input).resolve(),
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK colombia_dane:colombia_dane_ipc_city_rent_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} matched_cities={stats['unique_ieset_city_ids']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
