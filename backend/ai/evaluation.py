import numpy as np

from ai.matcher import match_resume_to_jobs
from ai.embedding_matcher import embedding_similarity
from ai.hybrid_matcher import hybrid_match
from api.adzuna import fetch_jobs


# METRICS
def precision_at_k(ranked, relevant, k=5):
    top_k = ranked[:k]
    hits = sum(1 for r in top_k if r["job_index"] in relevant)
    return hits / k


def mean_reciprocal_rank(ranked, relevant):
    for i, r in enumerate(ranked):
        if r["job_index"] in relevant:
            return 1 / (i + 1)
    return 0


# MATCHING
def get_ranked_results(resume_text, job_texts, mode="hybrid"):
    if mode == "tfidf":
        results = match_resume_to_jobs(resume_text, job_texts)
        return sorted(results, key=lambda x: x["score"], reverse=True)

    elif mode == "sbert":
        scores = embedding_similarity(resume_text, job_texts)

        ranked = [
            {"job_index": i, "score": float(score)}
            for i, score in enumerate(scores)
        ]
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    elif mode == "hybrid":
        return hybrid_match(resume_text, job_texts, mode="hybrid")

    else:
        raise ValueError("Invalid mode")


# SINGLE EVALUATION
def evaluate_single_query(resume_text, job_texts, relevant_jobs):
    modes = ["tfidf", "sbert", "hybrid"]
    results = {}

    for mode in modes:
        ranked = get_ranked_results(resume_text, job_texts, mode)

        p5 = precision_at_k(ranked, relevant_jobs, k=5)
        mrr = mean_reciprocal_rank(ranked, relevant_jobs)

        results[mode] = {
            "precision@5": round(p5, 4),
            "MRR": round(mrr, 4)
        }

    return results


# AGGREGATION
def aggregate_results(results_list):
    aggregated = {
        "tfidf": {"precision@5": [], "MRR": []},
        "sbert": {"precision@5": [], "MRR": []},
        "hybrid": {"precision@5": [], "MRR": []},
    }

    for res in results_list:
        for mode in res:
            aggregated[mode]["precision@5"].append(res[mode]["precision@5"])
            aggregated[mode]["MRR"].append(res[mode]["MRR"])

    final = {}

    for mode in aggregated:
        final[mode] = {
            "precision@5": round(np.mean(aggregated[mode]["precision@5"]), 4),
            "MRR": round(np.mean(aggregated[mode]["MRR"]), 4),
        }

    return final


# API EVALUATION
def evaluate_api(n_samples=3):
    all_results = []

    for i in range(n_samples):

        jobs = fetch_jobs("python data analyst", results=30)
        job_texts = [job["description"] for job in jobs]

        resume_text = (
            "Python developer with experience in machine learning and data analysis")

        if i == 0:
            print("\nSAMPLE JOBS:\n")
            for idx, job in enumerate(jobs[:10]):
                print(idx, job["title"])

        relevant = {0, 1, 2, 3, 5, 7} 
        res = evaluate_single_query(resume_text, job_texts, relevant)
        all_results.append(res)

    return aggregate_results(all_results)


if __name__ == "__main__":
    results = evaluate_api(n_samples=3)

    print("\nEVALUATION RESULTS (ADZUNA API)\n")

    for mode, metrics in results.items():
        print(f"{mode.upper()}:")
        print(f"  Precision@5: {metrics['precision@5']}")
        print(f"  MRR:         {metrics['MRR']}")
        print()