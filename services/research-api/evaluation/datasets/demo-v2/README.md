# demo-v2

`generate_fixtures.py`だけから再生成できる、オリジナルCC0数学コーパスです。
6文書・12ページ、answerable 24問とunanswerable 3問の合計27問を含みます。

- easy: 9問
- medium: 8問
- hard: 10問
- 分野: arithmetic, algebra, functions, sequences, differentiation, integration,
  linear algebra, probability, statistics, geometry, word problems、および
  unanswerable確認用3分野

難易度は、`easy`を公式への単純代入、`medium`を1～2段階の適用、`hard`を
複数段階・条件判断・説明が必要な問題として付与しています。テスト用正解・rubricは
runnerがLLMへ渡すcase viewから除外します。

再生成:

```zsh
python evaluation/datasets/demo-v2/generate_fixtures.py
python evaluation/validate_dataset.py evaluation/datasets/demo-v2/dataset.json
```
