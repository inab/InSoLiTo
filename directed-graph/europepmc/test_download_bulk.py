"""Tests for download_europepmc_bulk.py, offline. Run: pytest test_download_bulk.py"""

import csv
import gzip

import download_europepmc as dl
import download_europepmc_bulk as bulk
from parse_jats import parse_file

ARTICLE = """<article article-type="{atype}" xmlns:xlink="http://www.w3.org/1999/xlink">
<front><journal-meta><journal-title-group><journal-title>J Test</journal-title></journal-title-group></journal-meta>
<article-meta>
  <article-id pub-id-type="pmcid">{pmcid}</article-id>
  <article-id pub-id-type="pmid">{pmid}</article-id>
  <article-id pub-id-type="doi">10.1/{pmid}</article-id>
  <pub-date pub-type="epub"><year>2020</year></pub-date>
</article-meta></front>
<body><sec><title>Introduction</title><p>Cited [<xref ref-type="bibr" rid="R1">1</xref>].</p></sec></body>
{back}
</article>"""
REFLIST = '<back><ref-list><ref id="R1"><element-citation><pub-id pub-id-type="pmid">9</pub-id></element-citation></ref></ref-list></back>'


def make_bundle(path, articles):
    body = "<articles>" + "".join(
        ARTICLE.format(pmcid=p, pmid=p[3:], atype=t, back=REFLIST if ref else "") for p, t, ref in articles
    ) + "</articles>"
    with gzip.open(path, "wt") as fh:
        fh.write(body)


def split(tmp_path, bundle, overwrite=False):
    return bulk.split_bundle(str(bundle), str(tmp_path / "xml"), str(tmp_path / "parts" / "b.tsv"),
                             overwrite, require_reflist=True)


def test_split_writes_articles_in_topic_layout(tmp_path):
    bundle = tmp_path / "PMC1_PMC3.xml.gz"
    make_bundle(bundle, [("PMC1234567", "research-article", True),
                         ("PMC1234568", "review-article", True),
                         ("PMC1234569", "editorial", False)])
    counts = split(tmp_path, bundle)
    assert counts == dict(n_articles=3, n_written=2, n_existing=0, n_no_reflist=1, n_no_pmcid=0)

    dest = dl.xml_path(tmp_path / "xml", "PMC1234567")
    assert dest == tmp_path / "xml" / "PMC123" / "PMC1234567.xml.gz"
    assert not dl.xml_path(tmp_path / "xml", "PMC1234569").exists()

    # Each file is a standalone JATS article the parser can read.
    art, refs, ments = parse_file(dest)
    assert art["pmcid"] == "PMC1234567" and art["status"] == "ok"
    assert [r["pmid"] for r in refs] == ["9"] and len(ments) == 1

    rows = list(csv.reader((tmp_path / "parts" / "b.tsv").open(), delimiter="\t"))
    assert [dict(zip(dl.MANIFEST_COLUMNS, r)) for r in rows][0] == {
        "pmcid": "PMC1234567", "pmid": "1234567", "doi": "10.1/1234567", "topics": "oa_bulk",
        "pub_type": "research-article", "pub_year": "2020", "journal": "J Test", "status": "ok",
        "xml_path": "xml/PMC123/PMC1234567.xml.gz",
    }
    assert len(rows) == 2


def test_split_skips_existing_unless_overwrite(tmp_path):
    bundle = tmp_path / "b.xml.gz"
    make_bundle(bundle, [("PMC1234567", "research-article", True)])
    split(tmp_path, bundle)
    dest = dl.xml_path(tmp_path / "xml", "PMC1234567")
    dest.write_bytes(gzip.compress(b"<article>old</article>"))

    assert split(tmp_path, bundle)["n_existing"] == 1
    assert b"old" in gzip.decompress(dest.read_bytes())
    assert split(tmp_path, bundle, overwrite=True)["n_written"] == 1
    assert b"old" not in gzip.decompress(dest.read_bytes())
    # Existing files are still listed in the manifest.
    assert len((tmp_path / "parts" / "b.tsv").read_text().splitlines()) == 1


def test_state_roundtrip_and_order(tmp_path):
    state = {n: bulk.Bundle(n, size=s) for n, s in
             [("PMC100001_PMC200000.xml.gz", 5), ("PMC13900_PMC17829.xml.gz", 7)]}
    state["PMC13900_PMC17829.xml.gz"].split_size = 7
    path = tmp_path / "bundles.tsv"
    bulk.save_state(path, state)
    loaded = bulk.load_state(path)
    assert loaded == state
    assert list(loaded) == ["PMC13900_PMC17829.xml.gz", "PMC100001_PMC200000.xml.gz"]  # by PMCID
    assert not loaded["PMC13900_PMC17829.xml.gz"].needs_split
    assert loaded["PMC100001_PMC200000.xml.gz"].needs_split


class FakeResponse:
    def __init__(self, status, data, headers):
        self.status_code, self._data, self.headers = status, data, headers

    def iter_content(self, _size):
        yield self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    """Serves ``data``, honouring Range + If-Range like the EBI server."""

    def __init__(self, data, etag):
        self.data, self.etag, self.calls = data, etag, []

    def get(self, url, headers=None, **kw):
        headers = headers or {}
        self.calls.append(headers)
        if "Range" in headers and headers.get("If-Range") == self.etag:
            start = int(headers["Range"][6:-1])
            return FakeResponse(206, self.data[start:],
                                {"Content-Range": f"bytes {start}-{len(self.data) - 1}/{len(self.data)}"})
        return FakeResponse(200, self.data, {"Content-Length": str(len(self.data))})


def test_download_resumes_from_part(tmp_path, monkeypatch):
    data = b"0123456789" * 100
    session = FakeSession(data, '"v1"')
    monkeypatch.setattr(dl, "get_session", lambda ua: session)
    dest = tmp_path / "b.xml.gz"
    (tmp_path / "b.xml.gz.part").write_bytes(data[:300])

    status, size = bulk.download_bundle(bulk.Bundle("b.xml.gz", size=len(data), etag='"v1"'), dest, "ua")
    assert (status, size) == ("ok", len(data))
    assert dest.read_bytes() == data
    assert session.calls[0]["Range"] == "bytes=300-"


def test_download_restarts_when_file_changed_upstream(tmp_path, monkeypatch):
    new = b"x" * 500
    monkeypatch.setattr(dl, "get_session", lambda ua: FakeSession(new, '"v2"'))
    dest = tmp_path / "b.xml.gz"
    (tmp_path / "b.xml.gz.part").write_bytes(b"old" * 100)

    status, size = bulk.download_bundle(bulk.Bundle("b.xml.gz", size=999, etag='"v1"'), dest, "ua")
    assert (status, size) == ("ok", 500)
    assert dest.read_bytes() == new
