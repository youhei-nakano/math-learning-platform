import json
import math
from pathlib import Path

from openai import OpenAI


INDEX_PATH = Path("data/rag_index.json")
QUESTIONS_PATH = Path("evaluation/questions.json")
UNANSWERABLE_PATH = Path(
    "evaluation/unanswerable_questions.json"
)
TOP_K = 3
QUESTION_FIELD = "question_ja"
TRANSLATION_MODEL = "gpt-4.1-mini"

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

with UNANSWERABLE_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    unanswerable_questions = json.load(file)

records = index_data["records"]

print(f"インデックスのチャンク数: {len(records)}")
print(f"評価質問数: {len(evaluation_questions)}")
print(
    f"資料外質問数: {len(unanswerable_questions)}"
)

client = OpenAI()

test_questions = [
    {
        "id": item["id"],
        "question_ja": item["question_ja"],
        "should_answer": True,
    }
    for item in evaluation_questions
] + [
    {
        "id": item["id"],
        "question_ja": item["question_ja"],
        "should_answer": False,
    }
    for item in unanswerable_questions
]

def translate_for_retrieval(question):
    response = client.responses.create(
        model=TRANSLATION_MODEL,
        instructions=(
            "Translate the Japanese mathematical question into English "
            "for searching an English mathematics textbook. "
            "Preserve mathematical terminology exactly. "
            "In this context, translate グロモフ面積 as Gromov area, "
            "not Gromov width. Translate 完全ラグランジュ as exact "
            "Lagrangian, not complete Lagrangian. "
            "Output only the English translation."
        ),
        input=question,
    )

    return response.output_text.strip()
question_texts = []

for item in test_questions:
    original_question = item[QUESTION_FIELD]
    translated_question = translate_for_retrieval(
        original_question
    )

    question_texts.append(translated_question)

    print()
    print(f"ID: {item['id']}")
    print(f"日本語: {original_question}")
    print(f"検索用英語: {translated_question}")

embedding_response = client.embeddings.create(
    model=index_data["embedding_model"],
    input=question_texts,
)

question_embeddings = [
    item.embedding
    for item in embedding_response.data
]

print(f"作成した質問Embedding数: {len(question_embeddings)}")

answerable_scores = []
unanswerable_scores = []

for question_item, question_embedding in zip(
    test_questions,
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

    top_score = similarities[top_indices[0]]
    retrieved_pages = [
        records[index]["pdf_page"]
        for index in top_indices
    ]

    if question_item["should_answer"]:
        answerable_scores.append(top_score)
        label = "資料内"
    else:
        unanswerable_scores.append(top_score)
        label = "資料外"

    print()
    print(f"ID: {question_item['id']}")
    print(f"区分: {label}")
    print(f"最高類似度: {top_score:.4f}")
    print(f"取得ページ: {retrieved_pages}")

print()
print(
    "資料内質問の最低類似度:",
    f"{min(answerable_scores):.4f}",
)
print(
    "資料外質問の最高類似度:",
    f"{max(unanswerable_scores):.4f}",
)