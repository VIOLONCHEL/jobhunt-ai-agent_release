from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_resume_to_jobs(
    resume_text: str,
    job_texts: list[str],
    min_score: float = 0.03,     
    max_score: float = 0.30     
):
    if not resume_text or not job_texts:
        return []

    texts = [resume_text] + job_texts

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2)
    )

    tfidf = vectorizer.fit_transform(texts)

    resume_vec = tfidf[0]
    job_vecs = tfidf[1:]

    similarities = cosine_similarity(resume_vec, job_vecs)[0]

    results = []

    for i, score in enumerate(similarities):
        

        score = min(score, max_score)

        results.append({
            "job_index": i,
            "score": float(score)  
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results
