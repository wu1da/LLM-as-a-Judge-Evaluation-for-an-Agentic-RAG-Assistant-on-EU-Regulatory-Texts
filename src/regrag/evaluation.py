import json
from pathlib import Path


def load_qa(data_dir):
    """The 137 AI Act benchmark questions (English)."""
    path = Path(data_dir) / "ai-act-benchmark" / "qa_pairs.json"
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def is_gold(chunk, item):
    """True if this chunk comes from the article that answers the question."""
    return (chunk["kind"] == "article"
            and chunk["act"] == "ai-act"
            and chunk["number"] == item["relevant_article"])


def recall_at_k(index, qa, k):
    """Share of questions whose gold article appears in the top-k chunks."""
    hits = 0
    for item in qa:
        results = index.search(item["question"], k)
        if any(is_gold(chunk, item) for _, chunk in results):
            hits += 1
    return hits / len(qa)




def results_row(name, index, qa, ks=(1, 3, 5, 10)):
    """Recall@k for several k, formatted as one row of the results.md table."""
    scores = [f"{recall_at_k(index, qa, k):.3f}" for k in ks]
    return "| " + name + " | " + " | ".join(scores) + " |"