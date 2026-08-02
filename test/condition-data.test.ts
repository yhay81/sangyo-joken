import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = process.cwd();
const index = JSON.parse(readFileSync(resolve(root, "public/data/index.json"), "utf8"));
const records = JSON.parse(readFileSync(resolve(root, "public/data/conditions.json"), "utf8"));
const find = (id: string) => records.find((record: { id: string }) => record.id === id);

describe("official industry condition tables", () => {
  it("retains verified source metadata and the current classification boundary", () => {
    expect(index).toMatchObject({
      asOf: "2026-08-02",
      edition: "2024〜2025年度（現行産業分類）",
      years: [2024, 2025],
      industryCount: 19,
      recordCount: 19,
      employment: "パートタイムを除く常用",
      sourceValueCount: 418,
      publishedValueCount: 380,
      conditionPairCount: 114,
    });
    expect(
      Object.fromEntries(
        index.sources.map((source: { metric: string; sha256: string }) => [
          source.metric,
          source.sha256,
        ]),
      ),
    ).toEqual({
      weekend: "29f327bdec9cdec90be27ef9a4dfee428df00aa2653c8ddd44f5b7c8cc16b730",
      bonus: "6733b6040ec11e0264715d70713f2ffaff9de48c8d07d3168c988c1bd3ad8027",
      commute: "df1ce802a1121d2932ca6946ea8af92861c7e74d3c8315b9bfdd0182c2f390bb",
    });
  });

  it("contains the total and 18 unique industries with two values per category", () => {
    expect(records).toHaveLength(19);
    expect(new Set(records.map((record: { id: string }) => record.id)).size).toBe(19);
    expect(records.map((record: { name: string }) => record.name)).toEqual([
      "産業計",
      "農業，林業",
      "漁業",
      "鉱業，採石業，砂利採取業",
      "建設業",
      "製造業",
      "電気・ガス・熱供給・水道業",
      "情報通信業",
      "運輸業，郵便業",
      "卸売業，小売業",
      "金融業，保険業",
      "不動産業，物品賃貸業",
      "学術研究，専門・技術サービス業",
      "宿泊業，飲食サービス業",
      "生活関連サービス業，娯楽業",
      "教育，学習支援業",
      "医療，福祉",
      "複合サービス事業",
      "サービス業（他に分類されないもの）",
    ]);
    for (const record of records)
      for (const values of [
        record.weekend.total,
        record.weekend.complete,
        record.weekend.other,
        record.weekend.none,
        record.bonus.yes,
        record.bonus.no,
        record.commute.upperLimit,
        record.commute.noLimit,
        record.commute.fixed,
        record.commute.none,
      ])
        expect(values).toHaveLength(2);
  });

  it("retains representative 2025 industry counts", () => {
    expect(find("H")).toMatchObject({
      weekend: { total: [expect.any(Number), 28942], complete: [expect.any(Number), 11632] },
      bonus: { yes: [expect.any(Number), 307250], no: [expect.any(Number), 103131] },
    });
    expect(find("Q")).toMatchObject({
      weekend: { total: [expect.any(Number), 3931], complete: [expect.any(Number), 2981] },
      bonus: { yes: [expect.any(Number), 28672], no: [expect.any(Number), 3099] },
    });
  });

  it("retains the published 2025 industry totals", () => {
    expect(find("ALL")).toMatchObject({
      weekend: { total: [487753, 467333], complete: [275831, 273456], none: [9302, 7915] },
      bonus: { yes: [4703629, 4557274], no: [1021829, 952076] },
      commute: {
        upperLimit: [3799692, 3647311],
        noLimit: [1321467, 1286082],
        fixed: [142464, 138168],
        none: [461835, 437789],
      },
    });
  });

  it("keeps weekend rows additive and benefit denominators identical", () => {
    for (const record of records)
      for (let year = 0; year < 2; year += 1) {
        expect(
          record.weekend.complete[year] + record.weekend.other[year] + record.weekend.none[year],
        ).toBe(record.weekend.total[year]);
        expect(record.bonus.yes[year] + record.bonus.no[year]).toBe(
          record.commute.upperLimit[year] +
            record.commute.noLimit[year] +
            record.commute.fixed[year] +
            record.commute.none[year],
        );
      }
  });

  it("keeps all 18 industries additive to the published total", () => {
    const total = find("ALL");
    const industries = records.filter((record: { id: string }) => record.id !== "ALL");
    for (const [group, key] of [
      ["weekend", "total"],
      ["weekend", "complete"],
      ["weekend", "other"],
      ["weekend", "none"],
      ["bonus", "yes"],
      ["bonus", "no"],
      ["commute", "upperLimit"],
      ["commute", "noLimit"],
      ["commute", "fixed"],
      ["commute", "none"],
    ] as const)
      for (let year = 0; year < 2; year += 1)
        expect(
          industries.reduce(
            (sum: number, record: Record<string, Record<string, number[]>>) =>
              sum + record[group][key][year],
            0,
          ),
        ).toBe(total[group][key][year]);
  });

  it("stays within the static delivery budget", () => {
    expect(statSync(resolve(root, "public/data/conditions.json")).size).toBeLessThan(20000);
  });
});
