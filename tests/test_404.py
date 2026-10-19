def test_nepostojeca_adresa_vraca_stranicu_nije_pronadjena(client):
    odgovor = client.get("/ova-adresa-ne-postoji")

    assert odgovor.status_code == 404
    html = odgovor.get_data(as_text=True)
    assert "Stranica nije pronađena" in html
    assert "Sport Portal" in html


def test_stranica_nije_pronadjena_ima_link_na_naslovnu(client):
    html = client.get("/ova-adresa-ne-postoji").get_data(as_text=True)

    assert '<a href="/">Nazad na naslovnu</a>' in html
