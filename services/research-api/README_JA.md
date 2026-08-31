# 再現可能な数学学習支援・研究基盤

既存の数学サンドボックスを残しつつ、複数PDFの版固定、ローカル検索、
引用検証、単一／複数エージェント構成の比較、再開可能な評価を追加した
オフライン優先の研究基盤です。Reactクライアント `my-app` の根拠付き質問機能から
同一オリジンBFFを介して接続します。ノードメモはブラウザ内に留まり、APIへ送りません。

## macOSでの再現

```zsh
cd /path/to/openai-sandbox
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python evaluation/datasets/demo-v1/generate_fixtures.py
python -m unittest discover -s tests -v
python research_api.py
```

APIは `127.0.0.1:8765` で待ち受け、リポジトリ内のCC0デモPDFだけを検索します。
外部モデルを呼ばず、取得済みチャンクを抽出的回答として返します。

オフライン実験と集計:

```zsh
mkdir -p evaluation/runs
for config in evaluation/configs/*.json; do
  name=${config:t:r}
  python evaluation/run_research.py --config "$config" --output "evaluation/runs/$name.jsonl" --no-resume
done
python evaluation/report_research.py evaluation/runs/*.jsonl \
  --csv evaluation/results.csv --markdown evaluation/RESULTS.md \
  --app-json /path/to/my-app/public/evaluation-results.json \
  --readme README_JA.md --readme /path/to/my-app/README.md
```

上記はOpenAI APIを呼びません。従来のAPI実験は、利用者が明示的に許可し、
`OPENAI_API_KEY` を実行環境だけに設定した場合に限ります。公開デモ・被験者
実験・OCR/VLM実測は未実施です。詳しくは `docs/reproducibility.md`、
`docs/security_privacy.md`、`docs/user_study_protocol.md` を参照してください。

<!-- RESEARCH_RESULTS_START -->
## Single／multi比較の実測結果

生成元: `evaluation` JSONL / 評価セット `demo-v1` / モデル `offline-extractive-v1`

| 方式 | 品質スコア | 引用精度 | 完了率 | 中央時間 | 平均API費用／問題 | 実行数 |
|---|---:|---:|---:|---:|---:|---:|
| 単一エージェント | 100% | 100% | 100% | 0.361 ms | $0.0000 | 4 |
| 複数役割エージェント | 100% | 100% | 100% | 0.370 ms | $0.0000 | 4 |

外部モデル呼び出しは0回です。品質は4問の抽出回答に対する決定論的採点であり、一般的な数学性能を示しません。OpenAIモデル、OCR、VLMは **Not run** です。
<!-- RESEARCH_RESULTS_END -->

生データは `evaluation/runs/integration-single.jsonl` と
`evaluation/runs/integration-multi.jsonl`、全集計は `evaluation/RESULTS.md` と
`evaluation/results.csv` に保存しています。
