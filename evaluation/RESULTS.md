# Measured offline results

Only executed conditions appear below. API/OCR/VLM conditions are **Not run**.

| experiment_id | mode | retrieval | rerank | dataset_version | model | runs | successes | completion_rate | error_rate | answer_accuracy | citation_precision | citation_recall | latency_mean | latency_median | latency_stdev | latency_min | latency_max | tool_calls | input_tokens | output_tokens | cost_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1ae4f0acbbdec663 | single | hybrid | True | demo-v1 | offline-extractive-v1 | 4 | 4 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 0.0003875 | 0.000361 | 8.73999427917433e-05 | 0.000306 | 0.000522 | 4 | 0 | 0 | 0.0 |
| a7a052c8ba740612 | multi | hybrid | True | demo-v1 | offline-extractive-v1 | 4 | 4 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 0.0003815 | 0.00037 | 6.361407077054572e-05 | 0.00032 | 0.000466 | 8 | 0 | 0 | 0.0 |

## Not run

- OpenAI model single/multi comparison
- Neural embeddings and model reranking
- OCR enabled
- OCR + VLM
