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

    def search(self, query, k=5):
        """Return the k best chunks as a list of (score, chunk)."""
        terms = set(tokenize(query))
        scored = [(self.score(terms, i), c) for i, c in enumerate(self.chunks)]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(key=lambda x: -x[0])
        return scored[:k]