import re


def test_stranica_ucitava_pico_css_iz_projekta(client):
    html = client.get("/").get_data(as_text=True)

    assert 'href="/static/pico.min.css"' in html
    css = client.get("/static/pico.min.css")
    assert css.status_code == 200
    assert b"Pico CSS" in css.data


def test_stranica_ne_trazi_nista_sa_interneta(client):
    html = client.get("/").get_data(as_text=True)

    vanjski_linkovi = re.findall(r'(?:href|src)="(?:https?:)?//', html)
    assert vanjski_linkovi == []
