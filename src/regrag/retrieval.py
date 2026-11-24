import math
import re
from collections import Counter


def tokenize(text):
    """Lowercase the text and split it into words."""
    return re.findall(r"\w+", text.casefold())


class BM25Index:
    """Keyword search over the chunks of one language."""

    def __init__(self, chunks, lang, k1=1.2, b=0.75):
        self.k1, self.b = k1, b
        self.chunks = [c for c in chunks if c["lang"] == lang]
        # word counts for each chunk (title included: it often contains the key term)
        self.counts = [Counter(tokenize(c["title"] + " " + c["text"])) for c in self.chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.avg_length = sum(self.lengths) / len(self.lengths)
        # df = in how many chunks each word appears; idf = how rare it is
        df = Counter()
        for counts in self.counts:
            df.update(counts.keys())
        n = len(self.chunks)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def score(self, terms, i):
        """BM25 score of chunk number i for a set of query words."""
        counts, length = self.counts[i], self.lengths[i]
        s = 0.0
        for t in terms:
            tf = counts.get(t, 0)
            if tf:
                norm = 1 - self.b + self.b * length / self.avg_length
                s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * norm)
        return s

    def search(self, query, k=5, one_per_source=True):
        """Return the k best chunks as a list of (score, chunk)."""
        terms = set(tokenize(query))
        scored = [(self.score(terms, i), c) for i, c in enumerate(self.chunks)]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(key=lambda x: -x[0])
        if one_per_source:
            return best_per_source(scored, k)
        return scored[:k]



def source_key(chunk):
    """Which article or annex a chunk comes from, e.g. ('article', 'gdpr', 20)."""
    return (chunk["kind"], chunk["act"], chunk["number"])


def best_per_source(scored, k):
    """From (score, chunk) pairs sorted best-first, keep the first chunk of each source, up to k."""
    seen = set()
    results = []
    for score, chunk in scored:
        key = source_key(chunk)
        if key not in seen:
            seen.add(key)
            results.append((score, chunk))
            if len(results) == k:
                break
    return results




class DenseIndex:
    """Embedding (meaning-based) search over the chunks of one language."""

    def __init__(self, chunks, lang, model, batch_size=32):
        import numpy as np   # imported here so BM25 still works without numpy installed
        self.np = np
        self.model = model
        self.chunks = [c for c in chunks if c["lang"] == lang]
        texts = [c["title"] + " " + c["text"] for c in self.chunks]
        # one vector per chunk, normalized to length 1
        self.embeddings = model.encode(texts, batch_size=batch_size,
                                       normalize_embeddings=True, show_progress_bar=True)

    def search(self, query, k=5, one_per_source=True):
        """Return the k most similar chunks as a list of (score, chunk)."""
        q = self.model.encode([query], normalize_embeddings=True)[0]
        sims = self.embeddings @ q            # cosine similarity with every chunk
        order = self.np.argsort(-sims)        # indices, best first
        scored = [(float(sims[i]), self.chunks[i]) for i in order]
        if one_per_source:
            return best_per_source(scored, k)
        return scored[:k]