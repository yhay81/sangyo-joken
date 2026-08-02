# 産業別求人条件

厚生労働省「職業安定業務統計 雇用関係指標」の現行産業分類を使い、18産業の完全週休二日制・賞与・通勤手当を比較する日本語Webサービスです。

- 公開URL: <https://sangyo-joken.yhay81.com>
- 2024〜2025年度、産業計＋18産業
- パートタイムを除く常用
- 条件ごとに割合・元件数・前年差を表示
- 最大4産業の比較
- アカウント、Cookie、広告、外部解析なし

## 開発

Node.js 24 と npm 11 を使います。

```powershell
npm ci
npm run release:check
npm run check
npm test
npm run build
```

ローカル起動は `npm run dev`、公開は `npm run deploy` です。D1作成後に `wrangler.jsonc` の `database_id` を設定し、`npx wrangler d1 migrations apply sangyo-joken --remote` を実行します。

## データ再生成

厚生労働省の第11表、第13表、第16表を取得後、次を実行します。

```powershell
python scripts/extract-source.py 114-1d-11.xlsx 114-1d-13.xlsx 114-1d-16.xlsx public/data
npm run data:check
```

詳しい境界と照合内容は [SOURCE.md](SOURCE.md) を参照してください。

## License

コードは MIT License。出典データの利用は厚生労働省の利用条件に従います。
