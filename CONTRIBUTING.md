# Contributing

Thank you for helping improve Math Learning Platform.

## Before opening a change

- Use an Issue for bugs, proposals, evaluation changes, or architecture decisions.
- Keep changes focused; avoid unrelated rewrites.
- Never commit API keys, `.env` files, user PDFs, participant data, local indexes, raw private traces, or copyrighted source material.
- Use only original or clearly redistributable evaluation fixtures and document their provenance and license.

## Development setup

Requirements are Python 3.11+, Node.js 22, npm, and `curl` on macOS or Linux.

```bash
git clone https://github.com/youhei-nakano/math-learning-platform.git
cd math-learning-platform
./scripts/setup.sh
./scripts/dev.sh
```

## Branches and commits

- Create a short-lived branch from `main`.
- Use descriptive, imperative commit subjects.
- Keep generated files, dependency caches, and private run outputs out of commits.
- Do not rewrite shared history or force-push another contributor's work.

## Required checks

Run the repository-level check before opening a pull request:

```bash
./scripts/check.sh
./scripts/evaluate-deterministic.sh
```

This covers Python lint/format/tests, dataset validation, Web lint/tests/build, and the three-service integration smoke.

## Evaluation data

New cases must include stable IDs, domain, difficulty, answerability, expected answer, grading rubric, source document/page, citation expectations, dataset version, and license/provenance. Regenerate deterministic PDFs through the checked-in generator and run the dataset validator. Do not copy problem text or PDF pages whose redistribution rights are unclear.

Keep ground truth and rubrics out of model inputs. A changed result must identify its dataset, configuration, model, pipeline version, code commit, trial count, and limitations.

## Live LLM tests

Do not run paid live evaluation in a normal pull request or CI workflow. The default test suite must remain deterministic and secret-free. Live runs require maintainer authorization, a protected GitHub Environment, an environment secret, an explicit `--live` flag, and a small cost limit. Raw live traces are not committed.

## Pull requests

Describe:

- the user or research problem;
- the implementation and security/privacy impact;
- commands and results used for verification;
- evaluation changes and their limitations;
- screenshots only when they contain no keys, local paths, user documents, or personal data.

By contributing, you agree that your contribution is licensed under the repository's MIT License, except for files that explicitly declare another compatible license.
