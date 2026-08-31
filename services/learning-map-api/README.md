# Learning Map API

PDFからブラウザで抽出・選択されたページ本文だけを受け取り、OpenAIの構造化出力で
概念依存候補と批判的レビューを生成するFastAPIサービスです。PDFバイナリ全体は
受信しません。

```bash
source .venv/bin/activate
uvicorn math_research_assistant.app:app --reload --host 127.0.0.1 --port 8000
```

`OPENAI_API_KEY`がない場合も`/health`は応答しますが、`aiAvailable`は`false`です。
キーは環境変数または秘密管理機構だけで渡し、ファイルへ保存しないでください。

未送信ページをAIが引用した場合、その引用は採用しません。非目標ノードは未採用の
PDF外前提候補へ降格し、エッジの根拠ページは除去して警告します。目標ノードが
根拠を失う場合やPDF範囲外ページはエラーとして拒否します。

```bash
source .venv/bin/activate
ruff check .
ruff format --check .
pytest
```
