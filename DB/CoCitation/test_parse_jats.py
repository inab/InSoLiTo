"""Tests for parse_jats.py on small hand-written JATS snippets. Run: pytest test_parse_jats.py"""

import gzip

import pytest

from parse_jats import classify_section, norm_doi, parse_file

ARTICLE = """<?xml version="1.0"?>
<article article-type="research-article" xmlns:xlink="http://www.w3.org/1999/xlink">
<body>
  <sec><title>1. Introduction</title>
    <p>Tool A is popular [<xref ref-type="bibr" rid="R3">3</xref>]. Others exist
       [<xref ref-type="bibr" rid="R1">1</xref>&#x2013;<xref ref-type="bibr" rid="R4">4</xref>].</p>
  </sec>
  <sec sec-type="methods"><title>Methods</title>
    <sec><title>Data processing</title>
      <p>Spectra were processed with X<sup><xref ref-type="bibr" rid="R5">5</xref></sup>
         and then Y<sup><xref ref-type="bibr" rid="R2 R6">2,6</xref></sup>. Stats used Z
         <xref ref-type="bibr" rid="R7">7-8</xref>.</p>
    </sec>
  </sec>
  <table-wrap><table><tr><td>see <xref ref-type="bibr" rid="R9">9</xref></td></tr></table></table-wrap>
  <sec sec-type="ref-list"><ref-list>
    <ref id="R1"><label>1</label><element-citation><article-title>One</article-title>
       <pub-id pub-id-type="pmid">111</pub-id></element-citation></ref>
    <ref id="R2"><label>2</label><mixed-citation>Two. https://doi.org/10.1000/ABC.</mixed-citation></ref>
    <ref id="R3"><label>3</label><element-citation><pub-id pub-id-type="doi">10.1/three</pub-id>
       <pub-id pub-id-type="pmcid">PMC333</pub-id></element-citation></ref>
    <ref id="R4"><label>4</label><element-citation/></ref>
    <ref id="R5"><label>5</label><element-citation/></ref>
    <ref id="R6"><label>6</label><element-citation/></ref>
    <ref id="R7"><label>7</label><element-citation/></ref>
    <ref id="R8"><label>8</label><element-citation/></ref>
    <ref id="R9"><label>9</label><element-citation/></ref>
    <ref id="R10"><label>10</label><mixed-citation><named-content content-type="citation-string">
       Altschul S. F. (1990). Basic local alignment search tool. J. Mol. Biol.</named-content>
       <ext-link ext-link-type="pmid" xlink:href="2231712"/><ext-link ext-link-type="pmcid" xlink:href="PMC1234"/>
       <ext-link ext-link-type="google-scholar" xlink:href="journal=J. Mol. Biol.&amp;title=Basic local alignment search tool&amp;author=S. F. Altschul&amp;publication_year=1990&amp;doi=10.1016/S0022-2836(05)80360-2"/>
    </mixed-citation></ref>
  </ref-list></sec>
</body>
</article>"""


@pytest.fixture
def parsed(tmp_path):
    path = tmp_path / "PMC999.xml.gz"
    with gzip.open(path, "wb") as fh:
        fh.write(ARTICLE.encode())
    return parse_file(path)


def test_article_row(parsed):
    art, refs, ments = parsed
    assert art["pmcid"] == "PMC999"
    assert art["status"] == "ok"
    assert art["n_refs"] == 10
    assert art["n_unresolved_mentions"] == 0


def test_mention_order_and_ranges(parsed):
    _, _, ments = parsed
    assert [(m["ref_id"], m["via"]) for m in ments] == [
        ("R3", "xref"),                              # [3]
        ("R1", "xref"), ("R2", "range"), ("R3", "range"), ("R4", "xref"),  # [1–4] expanded
        ("R5", "xref"),                              # <sup>5</sup>
        ("R2", "multi-rid"), ("R6", "multi-rid"),    # rid="R2 R6"
        ("R7", "xref"), ("R8", "text-range"),        # "7-8" inside one xref
        ("R9", "xref"),                              # table cell
    ]
    assert [m["mention_idx"] for m in ments] == list(range(len(ments)))


def test_sections_sentences_tables(parsed):
    _, _, ments = parsed
    by = {(m["ref_id"], m["via"]): m for m in ments}
    assert by[("R3", "xref")]["sec_class"] == "intro"
    assert by[("R5", "xref")]["sec_class"] == "methods"
    assert by[("R5", "xref")]["sec_title"] == "Data processing"
    # Same paragraph, different sentences
    assert by[("R3", "xref")]["block_idx"] == by[("R1", "xref")]["block_idx"]
    assert by[("R3", "xref")]["sentence_idx"] < by[("R1", "xref")]["sentence_idx"]
    # X and Y in the same sentence; Z in the next one
    assert by[("R5", "xref")]["sentence_idx"] == by[("R6", "multi-rid")]["sentence_idx"]
    assert by[("R7", "xref")]["sentence_idx"] > by[("R5", "xref")]["sentence_idx"]
    assert by[("R9", "xref")]["in_table"] is True
    assert not any(m["sec_class"] == "back" for m in ments)  # ref-list xrefs ignored


def test_references_ids_and_rank(parsed):
    _, refs, _ = parsed
    r = {x["ref_id"]: x for x in refs}
    assert r["R1"]["pmid"] == "111" and r["R1"]["title"] == "One"
    assert r["R2"]["doi"] == "10.1000/abc"           # found in text, normalised
    assert r["R3"]["pmcid_ref"] == "PMC333"
    assert r["R3"]["cited_rank"] == 1                 # first cited, though 3rd in list
    assert r["R9"]["cited_rank"] is not None and r["R9"]["cited_rank_text"] is None
    assert r["R10"]["cited_rank"] is None             # never cited
    assert r["R4"]["citation_text"] is not None       # no IDs -> raw text kept for fuzzy matching


def test_reference_from_ext_links(parsed):
    """Europe PMC citation-string style: IDs and metadata only in ext-links."""
    _, refs, _ = parsed
    r = {x["ref_id"]: x for x in refs}["R10"]
    assert r["pmid"] == "2231712"
    assert r["pmcid_ref"] == "PMC1234"
    assert r["doi"] == "10.1016/s0022-2836(05)80360-2"
    assert r["title"] == "Basic local alignment search tool"
    assert r["year"] == "1990" and r["first_author"] == "Altschul"
    assert r["citation_text"] is None                 # has IDs, so raw text not kept


@pytest.mark.parametrize("title,expected", [
    ("Introduction", "intro"), ("1. Introduction", "intro"), ("IV. Methods", "methods"),
    ("2.3 Statistical analysis", "methods"), ("Results and Discussion", "results_discussion"),
    ("Acknowledgements", "back"), ("The role of X in Y", "other"),
])
def test_classify_section(title, expected):
    assert classify_section(None, title) == expected


def test_norm_doi():
    assert norm_doi("https://doi.org/10.1/ABC.") == "10.1/abc"
    assert norm_doi("doi: 10.1/x") == "10.1/x"
