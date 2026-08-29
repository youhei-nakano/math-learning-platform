import json
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader


PDF_PATH = Path("data/source.pdf")
INDEX_PATH = Path("data/rag_index.json")
EMBEDDING_MODEL = "text-embedding-3-small"
START_PAGE = 30
END_PAGE = 41
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def split_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


reader = PdfReader(PDF_PATH)

page_texts = []
for page_index in range(START_PAGE, END_PAGE):
    text = reader.pages[page_index].extract_text() or ""
    page_texts.append(text)

section_text = "\n".join(page_texts)
chunks = split_text(section_text)

client = OpenAI()
embedding_response = client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=chunks,
)

records = [
    {
        "chunk_id": index,
        "text": chunk,
        "embedding": item.embedding,
    }
    for index, (chunk, item) in enumerate(
        zip(chunks, embedding_response.data)
    )
]

index_data = {
    "embedding_model": EMBEDDING_MODEL,
    "source_pdf": PDF_PATH.name,
    "start_page_index": START_PAGE,
    "end_page_index_exclusive": END_PAGE,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
    "records": records,
}

INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
with INDEX_PATH.open("w", encoding="utf-8") as file:
    json.dump(index_data, file, ensure_ascii=False)

print(f"保存先: {INDEX_PATH}")
print(f"保存したチャンク数: {len(records)}")
