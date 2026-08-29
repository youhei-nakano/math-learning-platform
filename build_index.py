import json
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader


PDF_PATH = Path("data/source.pdf")
INDEX_PATH = Path("data/rag_index.json")
EMBEDDING_MODEL = "text-embedding-3-small"
START_PAGE = 0
END_PAGE = None
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
BATCH_SIZE = 100


def split_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


reader = PdfReader(PDF_PATH)
end_page = (
    END_PAGE
    if END_PAGE is not None
    else len(reader.pages)
)

page_texts = []
for page_index in range(START_PAGE, end_page):
    text = reader.pages[page_index].extract_text() or ""
    page_texts.append(text)

section_text = "\n".join(page_texts)
chunks = split_text(section_text)

client = OpenAI()

chunk_embeddings = []

for batch_start in range(0, len(chunks), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(chunks))
    batch_chunks = chunks[batch_start:batch_end]

    embedding_response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=batch_chunks,
    )

    chunk_embeddings.extend(
        item.embedding for item in embedding_response.data
    )

    print(f"Embedding作成済み: {batch_end}/{len(chunks)}")

records = [
    {
        "chunk_id": index,
        "text": chunk,
        "embedding": embedding,
    }
    for index, (chunk, embedding) in enumerate(
        zip(chunks, chunk_embeddings)
    )
]

index_data = {
    "embedding_model": EMBEDDING_MODEL,
    "source_pdf": PDF_PATH.name,
    "start_page_index": START_PAGE,
    "end_page_index_exclusive": end_page,
    "chunk_size": CHUNK_SIZE,
    "chunk_overlap": CHUNK_OVERLAP,
    "records": records,
}

INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
with INDEX_PATH.open("w", encoding="utf-8") as file:
    json.dump(index_data, file, ensure_ascii=False)

print(f"保存先: {INDEX_PATH}")
print(f"保存したチャンク数: {len(records)}")


