"""Regression check for index.html: run `python3 tests/check_index.py`."""
from html.parser import HTMLParser
from pathlib import Path

VOID = {"meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.hrefs, self.meta, self.text, self.labels = [], [], {}, [], []
        self.in_a = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.hrefs.append(a.get("href"))
            self.in_a = True
            self.labels.append("")
        if tag == "meta":
            self.meta[a.get("property") or a.get("name")] = a.get("content")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        assert self.stack and self.stack[-1] == tag, f"unbalanced </{tag}>, open: {self.stack}"
        self.stack.pop()
        if tag == "a":
            self.in_a = False

    def handle_data(self, data):
        self.text.append(data)
        if self.in_a:
            self.labels[-1] += data.strip()


html = (Path(__file__).parent.parent / "index.html").read_text()
p = Page()
p.feed(html)
p.close()
text = "".join(p.text)

assert not p.stack, f"unclosed tags: {p.stack}"
assert html.count("<!--") == html.count("-->"), "malformed HTML comment"
assert "#" not in p.hrefs and 'href="#"' not in html, "placeholder href=\"#\" present"
assert "-->" not in text and "<!--" not in text, "comment debris in rendered text"
assert p.meta.get("description") and "littlelink.io" not in p.meta["description"], "template meta description"
for key in ("og:title", "og:description", "og:image"):
    assert p.meta.get(key), f"missing {key}"
assert p.meta.get("og:type") == "website"
assert p.meta.get("og:url") == "https://littlelink-omega.vercel.app/"
assert p.meta["og:image"].startswith("https://"), "og:image must be absolute"
assert p.meta.get("twitter:card") == "summary"
assert p.labels.count("Website") == 1, f"Website buttons: {p.labels.count('Website')}"
assert "RSS Subscribe" in p.labels
print("index.html OK:", len(p.hrefs), "links")
