import numpy as np
from ai.matcher import match_resume_to_jobs
from ai.embedding_matcher import embedding_similarity


def hybrid_match(
    resume_text: str,
    job_texts: list[str],
    mode: str = "hybrid",
    alpha: float = 0.2
):
    # TF-IDF
    tfidf_results = match_resume_to_jobs(resume_text, job_texts)

    tfidf_scores = np.zeros(len(job_texts))
    for r in tfidf_results:
        tfidf_scores[r["job_index"]] = r["score"]

    # SBERT
    embedding_scores = embedding_similarity(resume_text, job_texts)

    #ablation study
    if mode == "tfidf":
        final_scores = tfidf_scores

    elif mode == "sbert":
        final_scores = embedding_scores

    elif mode == "hybrid":
        final_scores = alpha * tfidf_scores + (1 - alpha) * embedding_scores

    else:
        raise ValueError("Invalid mode")

    ranked = np.argsort(final_scores)[::-1]

    return [
        {
            "job_index": int(i),
            "score": float(final_scores[i])
        }
        for i in ranked
    ]