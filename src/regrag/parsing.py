import re
from pathlib import Path
from lxml import html

# act name -> (regulation number, expected number of articles)
ACTS = {"ai-act": ("2024/1689", 113), "gdpr": ("2016/679", 99)}
LANG_CODES = {"en": "eng", "fr": "fra"}   # EUR-Lex uses 3-letter codes in URLs


def load_articles(data_dir):
    """Parse the 4 EUR-Lex HTML files and return one dict per article."""
    data_dir = Path(data_dir)
    articles = []
    for act, (regulation, expected) in ACTS.items():
        for lang in ("en", "fr"):
            # build the file path and parse it
            path = data_dir / "eur-lex" / f"{act}-{lang}-oj.html"
            root = html.fromstring(path.read_bytes())
            # find the article blocks (art_1, art_2, ...)
            nodes = [n for n in root.xpath("//div[@id]")
                        if re.fullmatch(r"art_\d+", n.get("id"))]
            #  check that all articles are there
            assert {n.get("id") for n in nodes} == {f"art_{i}" for i in range(1, expected + 1)}, \
                f"{act}-{lang}: wrong set of articles"
            # for each block, build the dict and append it
            for node in nodes:
                number = int(node.get("id")[4:])
                title = " ".join(node.xpath('.//*[contains(@class, "sti-art")]//text()')).strip()
                body = " ".join(" ".join(node.itertext()).split())
                url = f"https://eur-lex.europa.eu/eli/reg/{regulation}/oj/{LANG_CODES[lang]}#art_{number}"
                content = list(node)[2:]   # skip the "Article 20" line and the title
                para_nodes = [c for c in content
                              if re.fullmatch(r"\d{3}\.\d{3}", c.get("id") or "")]
                if para_nodes:
                    paragraphs = [(int(p.get("id")[4:]), clean_text(p)) for p in para_nodes]
                else:
                    paragraphs = [(None, " ".join(clean_text(c) for c in content))]
                articles.append(dict(kind="article", act=act, lang=lang, number=number,
                                     title=title, body=body, url=url, paragraphs=paragraphs))      
    return articles



def clean_text(element):
    """All the text inside an HTML element, with spaces and line breaks cleaned."""
    return " ".join(" ".join(element.itertext()).split())


def split_words(text, size=200, overlap=50):
    """Cut a long text into overlapping windows of `size` words."""
    words = text.split()
    if len(words) <= size:
        return [text]
    step = size - overlap
    windows = []
    for start in range(0, len(words), step):
        windows.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return windows


def make_chunks(docs, size=200, overlap=50):
    """Turn articles/annexes into chunks: one per paragraph, long ones split into windows."""
    chunks = []
    for doc in docs:
        for para, text in doc["paragraphs"]:
            windows = split_words(text, size, overlap)
            for part, window in enumerate(windows):
                if doc["kind"] == "article":
                    ref = f"Article {doc['number']}" + (f"({para})" if para else "")
                else:
                    ref = f"Annex {doc['number']}"
                chunk_id = (f"{doc['act']}-{doc['lang']}-"
                            + ref.lower().replace(" ", "").replace("(", "-p").replace(")", ""))
                if len(windows) > 1:
                    chunk_id += f"-w{part}"
                chunks.append(dict(chunk_id=chunk_id, kind=doc["kind"], act=doc["act"],
                                   lang=doc["lang"], number=doc["number"], paragraph=para,
                                   ref=ref, title=doc["title"], url=doc["url"], text=window))
    return chunks



ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]


def load_annexes(data_dir):
    """Parse the 13 AI Act annexes (EN and FR). The GDPR has no annexes."""
    data_dir = Path(data_dir)
    annexes = []
    for lang in ("en", "fr"):
        path = data_dir / "eur-lex" / f"ai-act-{lang}-oj.html"
        root = html.fromstring(path.read_bytes())

        nodes = root.xpath('//div[starts-with(@id, "anx_")]')
        assert [n.get("id") for n in nodes] == [f"anx_{r}" for r in ROMAN], \
            f"ai-act-{lang}: wrong set of annexes"

        for node in nodes:
            number = node.get("id")[4:]                     # "anx_III" -> "III"
            headings = node.xpath('./p[contains(@class, "oj-doc-ti")]')
            title = clean_text(headings[1])
            body = clean_text(node)
            url = f"https://eur-lex.europa.eu/eli/reg/2024/1689/oj/{LANG_CODES[lang]}#anx_{number}"
            content = list(node)[2:]   # skip "ANNEX III" and the title
            paragraphs = [(None, " ".join(clean_text(c) for c in content))]
            annexes.append(dict(kind="annex", act="ai-act", lang=lang, number=number,
                                title=title, body=body, url=url, paragraphs=paragraphs))
    return annexes