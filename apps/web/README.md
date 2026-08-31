# 数学学習マップ

学習目標までの概念依存関係と、各ノード専用の学習メモを管理するReactアプリです。
旧「疑問・メモ」画面は廃止しました。旧画面が使用していた
`math-reading-todos` / `math-reading-folders` のlocalStorageデータは、移行不能な
内容を勝手に破棄しないため削除しません。

ノードメモは学習マップの各ノードの `notes` に保存されます。古いマップに
`notes` がない場合は空文字として読み込みます。マップ画面からJSON形式で
書き出し・読み込みができ、ノード複製時はメモも複製、削除時はノードと一緒に
除去されます。ノードメモはAI候補生成APIへ送信されません。

## macOSで成果物を確認する

既存機能、PDF解析、検索・引用統合を確認する場合はTerminalを2つ使います。

Terminal 1（固定済みCC0資料を検索するsandbox API）:

```zsh
cd /path/to/openai-sandbox
source .venv/bin/activate
python research_api.py
```

Terminal 2（開発用BFFを含むReactアプリ）:

```zsh
cd /path/to/my-app
npm install
npm run dev
```

Terminalに表示された `http://localhost:5173` をブラウザで開きます。
「学習マップ」→「PDFから作成」で、ブラウザ内PDF解析、レビュー済み
線形代数マップ、文書構造マップを利用できます。

AI候補生成も確認する場合は、別のTerminalで
`math-research-assistant-portfolio` バックエンドを起動します:

```bash
cd /path/to/math-research-assistant-portfolio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
export OPENAI_MODEL='gpt-5-mini'
uvicorn math_research_assistant.app:app --reload --port 8000
```

ヘルスチェックは `curl http://127.0.0.1:8000/health` です。APIキーがない場合も
Math Notes、Floerデモ、保存済みマップ、PDF基本解析、文書構造フォールバックは
動作します。

`/path/to/openai-sandbox` の検索APIとは、ブラウザから直接ではなく
`/api/research/query` の同一オリジンBFF経由で接続します。開発時はVite proxy、
ビルド後は `npm start` のNodeサーバーがBFFを担当します。質問と処理方式だけを送り、
ノードメモやPDF全体をsandboxへ暗黙に送信しません。接続境界は
[docs/research_integration.md](docs/research_integration.md) に記録しています。

PDF全体は外部送信されません。AIによる章節選定の前に、書名・著者・目次・学習目標
の送信について同意を求めます。その後、利用者がAI選定章節とページ範囲を確認し、
別の同意欄をオンにした場合だけ、ブラウザで抽出したページ番号付き本文が
バックエンド経由でOpenAI APIへ送信されます。APIキーはフロントエンドへ渡しません。

## 検査

```bash
npm test
npm run lint
npm run build
npm start
```

AIが返したノード・依存関係は未確認候補として保存されます。根拠ページは、実際に
APIへ送信されたページ集合に含まれるかバックエンドで検証されます。ノードと
依存関係は別々に確認し、両方の確認が終わるまで学習マップとして確定できません。

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.

<!-- RESEARCH_RESULTS_START -->
## Single／multi比較の実測結果

生成元: `evaluation` JSONL / 評価セット `demo-v1` / モデル `offline-extractive-v1`

| 方式 | 品質スコア | 引用精度 | 完了率 | 中央時間 | 平均API費用／問題 | 実行数 |
|---|---:|---:|---:|---:|---:|---:|
| 単一エージェント | 100% | 100% | 100% | 0.361 ms | $0.0000 | 4 |
| 複数役割エージェント | 100% | 100% | 100% | 0.370 ms | $0.0000 | 4 |

外部モデル呼び出しは0回です。品質は4問の抽出回答に対する決定論的採点であり、一般的な数学性能を示しません。OpenAIモデル、OCR、VLMは **Not run** です。
<!-- RESEARCH_RESULTS_END -->

画面は `public/evaluation-results.json` を読み込みます。このJSON、README管理区間、
CSV、Markdownは、sandboxの同じJSONL生データから生成されます。
