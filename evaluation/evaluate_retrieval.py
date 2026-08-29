import json
import math
from pathlib import Path

from openai import OpenAI


INDEX_PATH = Path("data/rag_index.json")
QUESTIONS_PATH = Path("evaluation/questions.json")
TOP_K = 3

def cosine_similarity(vector_a, vector_b):
    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    return dot_product / (norm_a * norm_b)

with INDEX_PATH.open("r", encoding="utf-8") as file:
    index_data = json.load(file)

with QUESTIONS_PATH.open("r", encoding="utf-8") as file:
    evaluation_questions = json.load(file)

records = index_data["records"]

print(f"インデックスのチャンク数: {len(records)}")
print(f"評価質問数: {len(evaluation_questions)}")

client = OpenAI()

question_texts = [
    item["question"]
    for item in evaluation_questions
]

embedding_response = client.embeddings.create(
    model=index_data["embedding_model"],
    input=question_texts,
)

question_embeddings = [
    item.embedding
    for item in embedding_response.data
]

print(f"作成した質問Embedding数: {len(question_embeddings)}")

hit_count = 0

for question_item, question_embedding in zip(
    evaluation_questions,
    question_embeddings,
):
    similarities = [
        cosine_similarity(
            question_embedding,
            record["embedding"],
        )
        for record in records
    ]

    top_indices = sorted(
        range(len(similarities)),
        key=lambda index: similarities[index],
        reverse=True,
    )[:TOP_K]

    retrieved_pages = [
        records[index]["pdf_page"]
        for index in top_indices
    ]

    expected_pages = set(
        question_item["expected_pdf_pages"]
    )
    matched_pages = expected_pages.intersection(
        retrieved_pages
    )
    is_hit = bool(matched_pages)

    if is_hit:
        hit_count += 1

    print()
    print(f"ID: {question_item['id']}")
    print(f"取得ページ: {retrieved_pages}")
    print(f"正解ページ: {sorted(expected_pages)}")
    print(f"判定: {'成功' if is_hit else '失敗'}")

hit_rate = hit_count / len(evaluation_questions)

print()
print(
    f"Hit@{TOP_K}: "
    f"{hit_count}/{len(evaluation_questions)} "
    f"({hit_rate:.1%})"
)