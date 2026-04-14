import chromadb
import os
from sentence_transformers import SentenceTransformer

# ── Config ──
CHUNK_SIZE = 300   # characters per chunk (≈ 60-80 tokens)
CHUNK_OVERLAP = 50

client = chromadb.PersistentClient(path='./chroma_db')

# Delete old collection if exists, then recreate
try:
    client.delete_collection('day09_docs')
    print("🗑️  Deleted old collection")
except Exception:
    pass

col = client.get_or_create_collection(
    'day09_docs',
    metadata={"hnsw:space": "cosine"}
)

model = SentenceTransformer('all-MiniLM-L6-v2')

docs_dir = './data/docs'
doc_id = 0

for fname in sorted(os.listdir(docs_dir)):
    fpath = os.path.join(docs_dir, fname)
    with open(fpath, encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Simple chunking with overlap
    chunks = []
    start = 0
    while start < len(content):
        end = start + CHUNK_SIZE
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    # Embed all chunks for this file
    embeddings = model.encode(chunks).tolist()

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        doc_id += 1
        col.add(
            documents=[chunk],
            embeddings=[emb],
            metadatas=[{"source": fname, "chunk_index": i}],
            ids=[f"{fname}_chunk_{i}"]
        )

    print(f'✅ Indexed: {fname} → {len(chunks)} chunks')

print(f'\n📦 Total documents in collection: {col.count()}')
print('Index ready.')