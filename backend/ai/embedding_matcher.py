from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def embedding_similarity(resume_text: str, job_texts: list[str]):
    embeddings = model.encode([resume_text] + job_texts)

    resume_vec = embeddings[0].reshape(1, -1)
    job_vecs = embeddings[1:]

    scores = cosine_similarity(resume_vec, job_vecs)[0]
    return scores
