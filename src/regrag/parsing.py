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
                articles.append(dict(act=act, lang=lang, number=number,
                                     title=title, body=body, url=url))
          
    return articles