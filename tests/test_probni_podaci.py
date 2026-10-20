from datetime import datetime, timedelta, timezone

from sportportal import db
from sportportal.db import get_db
from sportportal.javni import pasusi


def svi_clanci(app):
    with app.app_context():
        return get_db().execute(
            "SELECT naslov, uvod, tekst, stanje, datum_objave,"
            " kategorija.ime AS kategorija"
            " FROM clanak JOIN kategorija ON kategorija.id = clanak.kategorija_id"
        ).fetchall()


def imena_kategorija(app):
    with app.app_context():
        return [red["ime"] for red in db.kategorije()]


def test_nad_praznom_bazom_ubacuje_4_kategorije_i_12_clanaka(app, runner):
    rezultat = runner.invoke(args=["ubaci-probne-podatke"])

    assert rezultat.exit_code == 0
    assert "Probni podaci su ubačeni" in rezultat.output
    assert imena_kategorija(app) == ["Fudbal", "Košarka", "Rukomet", "Tenis"]
    clanci = svi_clanci(app)
    assert len(clanci) == 12
    for ime in ["Fudbal", "Košarka", "Tenis", "Rukomet"]:
        assert len([c for c in clanci if c["kategorija"] == ime]) == 3


def test_dva_clanka_su_nacrti_a_deset_je_objavljeno(app, runner):
    runner.invoke(args=["ubaci-probne-podatke"])

    clanci = svi_clanci(app)
    nacrti = [c for c in clanci if c["stanje"] == "nacrt"]
    objavljeni = [c for c in clanci if c["stanje"] == "objavljen"]
    assert len(nacrti) == 2
    assert len(objavljeni) == 10
    # Nacrt nikad nije objavljen, pa nema datum objave.
    assert all(c["datum_objave"] is None for c in nacrti)


def test_datumi_objave_su_rasporedjeni_kroz_posljednje_dvije_sedmice(app, runner):
    runner.invoke(args=["ubaci-probne-podatke"])

    # Baza čuva vrijeme po UTC-u, bez oznake zone.
    sada = datetime.now(timezone.utc).replace(tzinfo=None)
    datumi = [
        datetime.fromisoformat(c["datum_objave"])
        for c in svi_clanci(app)
        if c["stanje"] == "objavljen"
    ]
    assert all(sada - timedelta(days=14) <= d <= sada for d in datumi)
    # Raspoređeni su: najmanje 7 različitih dana, ne svi istog dana.
    assert len({d.date() for d in datumi}) >= 7


def test_svaki_clanak_ima_naslov_uvod_i_bar_dva_pasusa_teksta(app, runner):
    runner.invoke(args=["ubaci-probne-podatke"])

    clanci = svi_clanci(app)
    assert len({c["naslov"] for c in clanci}) == 12
    for clanak in clanci:
        assert clanak["naslov"].strip()
        assert clanak["uvod"].strip()
        assert len(pasusi(clanak["tekst"])) >= 2


def test_objavljeni_probni_clanci_se_vide_na_javnom_sajtu(app, runner, client):
    runner.invoke(args=["ubaci-probne-podatke"])

    stranica = client.get("/").get_data(as_text=True)
    for clanak in svi_clanci(app):
        if clanak["stanje"] == "objavljen":
            assert clanak["naslov"] in stranica
        else:
            assert clanak["naslov"] not in stranica


def test_admin_u_bazi_ne_smeta_ubacivanju(app, runner):
    runner.invoke(args=["napravi-admina"], input="marko\ntajna123\ntajna123\n")

    rezultat = runner.invoke(args=["ubaci-probne-podatke"])

    assert "Probni podaci su ubačeni" in rezultat.output
    assert len(svi_clanci(app)) == 12


def test_kad_postoji_kategorija_ne_mijenja_nista(app, runner):
    with app.app_context():
        db.dodaj_kategoriju("Šah")

    rezultat = runner.invoke(args=["ubaci-probne-podatke"])

    assert "Baza nije prazna, probni podaci nisu ubačeni" in rezultat.output
    assert imena_kategorija(app) == ["Šah"]
    assert svi_clanci(app) == []


def test_kad_postoji_clanak_ne_mijenja_nista(app, runner):
    with app.app_context():
        db.dodaj_kategoriju("Šah")
        db.dodaj_clanak("Naslov", "Uvod", "Tekst", "1")

    rezultat = runner.invoke(args=["ubaci-probne-podatke"])

    assert "Baza nije prazna, probni podaci nisu ubačeni" in rezultat.output
    assert imena_kategorija(app) == ["Šah"]
    assert len(svi_clanci(app)) == 1


def test_drugo_pokretanje_ne_ubacuje_podatke_ponovo(app, runner):
    runner.invoke(args=["ubaci-probne-podatke"])

    rezultat = runner.invoke(args=["ubaci-probne-podatke"])

    assert "Baza nije prazna, probni podaci nisu ubačeni" in rezultat.output
    assert len(imena_kategorija(app)) == 4
    assert len(svi_clanci(app)) == 12
