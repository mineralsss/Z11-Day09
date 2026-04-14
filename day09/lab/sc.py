import chromadb
import os
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path='./chroma_db')
col = client.get_or_create_collection('day09_docs')
model = SentenceTransformer('all-MiniLM-L6-v2')

docs_dir = './data/docs'
for fname in os.listdir(docs_dir):
    with open(os.path.join(docs_dir, fname), encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(f'Indexed: {fname}')
print('Index ready.')