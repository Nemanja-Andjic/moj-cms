import pytest


@pytest.fixture
def admin(runner):
    """Pravi admina komandom u terminalu, kao što bi to uradio pravi admin."""
    runner.invoke(args=["napravi-admina"], input="marko\ntajna123\ntajna123\n")


def prijavi_se(client, korisnicko_ime="marko", lozinka="tajna123"):
    return client.post(
        "/admin/prijava",
        data={"korisnicko_ime": korisnicko_ime, "lozinka": lozinka},
    )


def test_neprijavljen_posjetilac_biva_preusmjeren_na_prijavu(client):
    odgovor = client.get("/admin/")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/prijava"


def test_prijava_sa_tacnim_podacima_vodi_u_admin_panel(client, admin):
    odgovor = prijavi_se(client)

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/"
    panel = client.get("/admin/")
    assert panel.status_code == 200
    assert "Admin panel" in panel.get_data(as_text=True)


@pytest.mark.parametrize("korisnicko_ime, lozinka", [
    ("marko", "pogresna"),
    ("janko", "tajna123"),
])
def test_prijava_sa_pogresnim_podacima_prikazuje_gresku(
    client, admin, korisnicko_ime, lozinka
):
    odgovor = prijavi_se(client, korisnicko_ime, lozinka)

    assert odgovor.status_code == 200
    assert "Pogrešno korisničko ime ili lozinka." in odgovor.get_data(as_text=True)
    assert client.get("/admin/").status_code == 302


def test_prijava_bez_admina_prikazuje_gresku(client):
    odgovor = prijavi_se(client)

    assert "Pogrešno korisničko ime ili lozinka." in odgovor.get_data(as_text=True)


def test_admin_panel_ima_dugme_za_odjavu(client, admin):
    prijavi_se(client)

    html = client.get("/admin/").get_data(as_text=True)

    assert '<form method="post" action="/admin/odjava">' in html
    assert "Odjava" in html


def test_poslije_odjave_admin_stranice_opet_traze_prijavu(client, admin):
    prijavi_se(client)

    odgovor = client.post("/admin/odjava")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/prijava"
    assert client.get("/admin/").headers["Location"] == "/admin/prijava"


def test_prijava_traje_dok_se_browser_ne_zatvori(client, admin):
    odgovor = prijavi_se(client)

    # Kolačić bez roka trajanja browser briše kad se zatvori.
    kolacic = odgovor.headers["Set-Cookie"]
    assert "Expires" not in kolacic
    assert "Max-Age" not in kolacic
