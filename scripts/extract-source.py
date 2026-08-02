"""Extract comparable 2024–2025 MHLW job-condition tables by industry."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import openpyxl

YEARS = [2024, 2025]
SOURCES = {
    "weekend": "https://www.mhlw.go.jp/toukei/list/xls/114-1d-11.xlsx",
    "bonus": "https://www.mhlw.go.jp/toukei/list/xls/114-1d-13.xlsx",
    "commute": "https://www.mhlw.go.jp/toukei/list/xls/114-1d-16.xlsx",
}
INDUSTRIES = [
    ("ALL", "産業計"),
    ("AB", "農業，林業"),
    ("C", "漁業"),
    ("D", "鉱業，採石業，砂利採取業"),
    ("E", "建設業"),
    ("F", "製造業"),
    ("G", "電気・ガス・熱供給・水道業"),
    ("H", "情報通信業"),
    ("I", "運輸業，郵便業"),
    ("J", "卸売業，小売業"),
    ("K", "金融業，保険業"),
    ("L", "不動産業，物品賃貸業"),
    ("M", "学術研究，専門・技術サービス業"),
    ("N", "宿泊業，飲食サービス業"),
    ("O", "生活関連サービス業，娯楽業"),
    ("P", "教育，学習支援業"),
    ("Q", "医療，福祉"),
    ("R", "複合サービス事業"),
    ("S", "サービス業（他に分類されないもの）"),
]


def value(cell: object) -> int:
    if isinstance(cell, bool) or not isinstance(cell, (int, float)):
        raise ValueError(f"expected numeric cell, got {cell!r}")
    number = int(cell)
    if number < 0 or number != cell:
        raise ValueError(f"expected non-negative integer, got {cell!r}")
    return number


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: extract-source.py WEEKEND.xlsx BONUS.xlsx COMMUTE.xlsx OUTPUT_DIR")

    paths = {
        "weekend": Path(sys.argv[1]),
        "bonus": Path(sys.argv[2]),
        "commute": Path(sys.argv[3]),
    }
    output_directory = Path(sys.argv[4])
    books = {
        key: openpyxl.load_workbook(path, data_only=True, read_only=False)
        for key, path in paths.items()
    }
    weekend_sheet = books["weekend"].worksheets[1]
    bonus_sheet = books["bonus"].worksheets[3]
    commute_sheet = books["commute"].worksheets[3]
    if weekend_sheet.max_row < 23 or weekend_sheet.max_column < 11:
        raise ValueError("unexpected weekend workbook layout")
    if bonus_sheet.max_row < 41 or bonus_sheet.max_column < 4:
        raise ValueError("unexpected bonus workbook layout")
    if commute_sheet.max_row < 79 or commute_sheet.max_column < 4:
        raise ValueError("unexpected commute workbook layout")

    records = []
    for offset, (industry_id, name) in enumerate(INDUSTRIES):
        row = 3 + offset
        weekend_values = {key: [] for key in ("total", "complete", "other", "none")}
        bonus_values = {key: [] for key in ("yes", "no")}
        commute_values = {key: [] for key in ("upperLimit", "noLimit", "fixed", "none")}
        for year_index, _year in enumerate(YEARS):
            base = 2 + year_index * 5
            total, complete, biweekly, other, none = [
                value(weekend_sheet.cell(row, column).value)
                for column in range(base, base + 5)
            ]
            if total != complete + biweekly + other + none:
                raise ValueError(f"weekend categories do not sum for {industry_id}")
            weekend_values["total"].append(total)
            weekend_values["complete"].append(complete)
            weekend_values["other"].append(biweekly + other)
            weekend_values["none"].append(none)

            column = 3 + year_index
            bonus_values["yes"].append(value(bonus_sheet.cell(row, column).value))
            bonus_values["no"].append(value(bonus_sheet.cell(row + 19, column).value))
            for block, key in enumerate(commute_values):
                commute_values[key].append(
                    value(commute_sheet.cell(row + 19 * block, column).value)
                )
            if sum(values[year_index] for values in bonus_values.values()) != sum(
                values[year_index] for values in commute_values.values()
            ):
                raise ValueError(f"bonus/commute denominator mismatch for {industry_id}")

        records.append(
            {
                "id": industry_id,
                "name": name,
                "weekend": weekend_values,
                "bonus": bonus_values,
                "commute": commute_values,
            }
        )

    for year_index, year in enumerate(YEARS):
        for metric, keys in (
            ("weekend", ("total", "complete", "other", "none")),
            ("bonus", ("yes", "no")),
            ("commute", ("upperLimit", "noLimit", "fixed", "none")),
        ):
            for key in keys:
                expected = sum(record[metric][key][year_index] for record in records[1:])
                if records[0][metric][key][year_index] != expected:
                    raise ValueError(f"industry total mismatch for {metric}.{key} {year}")

    hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}
    index = {
        "schemaVersion": 1,
        "asOf": "2026-08-02",
        "edition": "2024〜2025年度（現行産業分類）",
        "years": YEARS,
        "industryCount": len(INDUSTRIES),
        "recordCount": len(records),
        "employment": "パートタイムを除く常用",
        "sourceValueCount": len(INDUSTRIES) * len(YEARS) * 11,
        "publishedValueCount": len(INDUSTRIES) * len(YEARS) * 10,
        "conditionPairCount": len(INDUSTRIES) * len(YEARS) * 3,
        "weekendIdentityChecked": len(INDUSTRIES) * len(YEARS),
        "industryTotalChecked": len(YEARS) * 10,
        "sharedDenominatorChecked": len(INDUSTRIES) * len(YEARS),
        "sources": [
            {
                "metric": key,
                "url": SOURCES[key],
                "sha256": hashes[key],
                "bytes": paths[key].stat().st_size,
            }
            for key in ("weekend", "bonus", "commute")
        ],
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_directory / "conditions.json").write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"industries": len(records), "years": YEARS}, ensure_ascii=False))


if __name__ == "__main__":
    main()
