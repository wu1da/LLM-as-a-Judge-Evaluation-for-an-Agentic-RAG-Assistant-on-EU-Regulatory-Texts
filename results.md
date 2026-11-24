# Retrieval results

Setup: 137 AI Act benchmark questions (English). Index = all English chunks
(AI Act + GDPR, articles + annexes, paragraph-level chunks of max 200 words).
Hit = the gold AI Act article appears in the top-k results.

| Retriever | R@1 | R@3 | R@5 | R@10 |
|---|---|---|---|---|
| BM25 (chunks) | 0.577 | 0.745 | 0.839 | 0.905 |
| BM25, one result per article | 0.577 | 0.810 | 0.905 | 0.927 |