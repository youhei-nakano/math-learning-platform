# Math Learning Platform

数学学習マップのWebアプリと、根拠付き検索・評価を行うPythonサービスをまとめた
モノレポです。元の2リポジトリは履歴を保持したまま`git subtree`で統合しています。

```text
apps/web/                       React / Vite / Node BFF
services/research-api/          Python検索API・評価基盤
docs/                           統合設計とセキュリティ
scripts/                        ルート操作コマンド
```

## セットアップと起動

```zsh
./scripts/setup.sh
./scripts/dev.sh
```

画面は`http://127.0.0.1:5173`、検索APIは`http://127.0.0.1:8765`です。
Webは同一オリジン`/api/research/query`を経由し、ノードメモやPDF全体を検索APIへ
暗黙送信しません。

## 検査と評価

```zsh
./scripts/check.sh
./scripts/evaluate-deterministic.sh
```

実LLM評価は通常テスト・CIから分離されています。APIキーを環境だけに設定し、
`--live`を明示した場合に限り動作します。最初は必ず1問で確認してください。

```zsh
export OPENAI_API_KEY='your key in this shell only'
./scripts/evaluate-live.sh --live --mode live-multi \
  --case-id arith-percent-001 --limit 1 --max-total-cost-usd 0.20 \
  --output evaluation/runs/pipeline-smoke.jsonl
```

`live-single`は`single-v1`、旧実測データの固定5 call方式は`multi-fixed-v1`、
新方式は`multi-pipeline-v2`として分離します。新方式はCoordinatorの計画を
Retrieverへ渡し、生成クエリで実際に再検索した後、Solver、Verifier、Tutorへ
構造化データを渡します。正解とrubricは全モデル処理終了後の採点だけで使います。

詳細は[アーキテクチャ](docs/architecture.md)、
[評価手順](docs/evaluation.md)、[セキュリティ](docs/security.md)を参照してください。

## ライセンス

アプリケーションコードの再配布ライセンスは明示されていません。評価fixtureは各
データセットに記載されたCC0条件に従います。詳しくは[LICENSE](LICENSE)を確認して
ください。
