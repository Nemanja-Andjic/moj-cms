import sqlite3

import pytest

from sportportal.db import get_db


def dodaj_kategoriju(klijent, ime):
    klijent.post("/admin/kategorije", data={"ime": ime})


def napravi_clanak(klijent, naslov="Derbi u subotu", kategorija_id=1, **polja):
    """Šalje formu za novi članak. Polja koja test ne navede dobijaju
    neku ispravnu vrijednost."""
    podaci = {
        "naslov": naslov,
        "uvod": "Kratak uvod.",
        "tekst": "Cijeli tekst članka.",
        "kategorija_id": kategorija_id,
    }
    podaci.update(polja)
    return klijent.post("/admin/clanci/novi", data=podaci, follow_redirects=True)


def stranica_clanaka(klijent):
    """HTML liste članaka, sa razmacima svedenim na po jedan."""
    html = klijent.get("/admin/clanci").get_data(as_text=True)
    return " ".join(html.split())


def test_stranica_clanaka_trazi_prijavu(client):
    odgovor = client.get("/admin/clanci")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/prijava"


def test_novi_clanak_je_nacrt_u_listi_clanaka(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")

    odgovor = napravi_clanak(admin_klijent, "Derbi u subotu")

    assert odgovor.status_code == 200
    assert (
        "<td>Derbi u subotu</td> <td>Fudbal</td> <td>Nacrt</td>"
        in stranica_clanaka(admin_klijent)
    )


def test_lista_clanaka_prikazuje_najnoviji_clanak_gore(app, admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Stariji članak")
    napravi_clanak(admin_klijent, "Noviji članak")
    napravi_clanak(admin_klijent, "Najstariji članak")
    # Treći članak "vraćamo u prošlost", da se vidi da redoslijed ide po
    # vremenu kad je članak napravljen, a ne po redoslijedu unosa.
    with app.app_context():
        baza = get_db()
        baza.execute(
            "UPDATE clanak SET napravljen = '2000-01-01 00:00:00' WHERE id = 3"
        )
        baza.commit()

    html = stranica_clanaka(admin_klijent)

    assert (
        html.index("Noviji članak")
        < html.index("Stariji članak")
        < html.index("Najstariji članak")
    )


def test_lista_clanaka_prikazuje_objavljen_clanak(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Tenis")
    napravi_clanak(admin_klijent, "Finale")
    objavi(admin_klijent, 1)

    assert (
        "<td>Finale</td> <td>Tenis</td> <td>Objavljen</td>"
        in stranica_clanaka(admin_klijent)
    )


@pytest.mark.parametrize("polje, poruka", [
    ("naslov", "Naslov je obavezan."),
    ("uvod", "Uvod je obavezan."),
    ("tekst", "Tekst je obavezan."),
    ("kategorija_id", "Kategorija je obavezna."),
])
def test_clanak_bez_obaveznog_polja_se_ne_cuva(admin_klijent, polje, poruka):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    podaci = {
        "naslov": "Derbi u subotu",
        "uvod": "Kratak uvod.",
        "tekst": "Cijeli tekst članka.",
        "kategorija_id": "1",
        polje: "   ",
    }

    odgovor = admin_klijent.post("/admin/clanci/novi", data=podaci)

    html = odgovor.get_data(as_text=True)
    assert poruka in html
    # Ono što je admin već unio ostaje u formi.
    for ime, vrijednost in podaci.items():
        if ime not in (polje, "kategorija_id"):
            assert vrijednost in html
    assert "<tbody> </tbody>" in stranica_clanaka(admin_klijent)


def test_izabrana_kategorija_ostaje_izabrana_kad_forma_ima_gresku(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    dodaj_kategoriju(admin_klijent, "Tenis")

    odgovor = napravi_clanak(admin_klijent, naslov="", kategorija_id=2)

    html = " ".join(odgovor.get_data(as_text=True).split())
    assert '<option value="2" selected>Tenis</option>' in html


def test_bez_kategorija_umjesto_forme_stoji_link_na_kategorije(admin_klijent):
    html = admin_klijent.get("/admin/clanci/novi").get_data(as_text=True)

    assert "Prvo napravi bar jednu kategoriju" in html
    assert 'href="/admin/kategorije"' in html
    assert '<form method="post">' not in html


def objavi(klijent, id_clanka):
    klijent.post(f"/admin/clanci/{id_clanka}/objavi")


def izmijeni(klijent, id_clanka, **polja):
    podaci = {
        "naslov": "Derbi u subotu",
        "uvod": "Kratak uvod.",
        "tekst": "Cijeli tekst članka.",
        "kategorija_id": "1",
    }
    podaci.update(polja)
    return klijent.post(
        f"/admin/clanci/{id_clanka}/izmijeni", data=podaci, follow_redirects=True
    )


def test_forma_za_izmjenu_prikazuje_postojeci_clanak(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    dodaj_kategoriju(admin_klijent, "Tenis")
    napravi_clanak(
        admin_klijent, "Finale", kategorija_id=2, uvod="Uvod finala.", tekst="Tekst finala."
    )
    assert 'href="/admin/clanci/1/izmijeni"' in stranica_clanaka(admin_klijent)

    html = admin_klijent.get("/admin/clanci/1/izmijeni").get_data(as_text=True)

    assert 'value="Finale"' in html
    assert "Uvod finala." in html
    assert "Tekst finala." in html
    assert '<option value="2" selected>Tenis</option>' in " ".join(html.split())


@pytest.mark.parametrize("objavljen, stanje", [(False, "Nacrt"), (True, "Objavljen")])
def test_izmjena_clanka_ne_mijenja_stanje(admin_klijent, objavljen, stanje):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    dodaj_kategoriju(admin_klijent, "Tenis")
    napravi_clanak(admin_klijent, "Stari naslov")
    if objavljen:
        objavi(admin_klijent, 1)

    izmijeni(admin_klijent, 1, naslov="  Novi naslov ", kategorija_id="2")

    html = stranica_clanaka(admin_klijent)
    assert f"<td>Novi naslov</td> <td>Tenis</td> <td>{stanje}</td>" in html
    assert "Stari naslov" not in html


def test_izmjena_bez_obaveznog_polja_se_odbija(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Stari naslov")

    odgovor = izmijeni(admin_klijent, 1, naslov="Novi naslov", uvod="")

    html = odgovor.get_data(as_text=True)
    assert "Uvod je obavezan." in html
    assert 'value="Novi naslov"' in html
    assert "<td>Stari naslov</td>" in stranica_clanaka(admin_klijent)


def test_izmjena_nepostojeceg_clanka_daje_404(admin_klijent):
    assert admin_klijent.get("/admin/clanci/99/izmijeni").status_code == 404


def test_brisanje_clanka_prvo_trazi_potvrdu(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    assert 'href="/admin/clanci/1/obrisi"' in stranica_clanaka(admin_klijent)

    html = admin_klijent.get("/admin/clanci/1/obrisi").get_data(as_text=True)

    assert "Da li sigurno želiš obrisati članak Derbi u subotu?" in html
    assert '<form method="post">' in html
    # Samo otvaranje stranice za potvrdu ne briše ništa.
    assert "<td>Derbi u subotu</td>" in stranica_clanaka(admin_klijent)


def test_admin_moze_obrisati_clanak(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    napravi_clanak(admin_klijent, "Finale kupa")

    odgovor = admin_klijent.post("/admin/clanci/1/obrisi")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/clanci"
    html = stranica_clanaka(admin_klijent)
    assert "Derbi u subotu" not in html
    assert "<td>Finale kupa</td>" in html
    assert admin_klijent.get("/admin/clanci/1/izmijeni").status_code == 404


def test_brisanje_nepostojeceg_clanka_daje_404(admin_klijent):
    assert admin_klijent.post("/admin/clanci/99/obrisi").status_code == 404


def test_kategorija_se_moze_obrisati_kad_joj_se_obrisu_clanci(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    napravi_clanak(admin_klijent, "Finale kupa")
    admin_klijent.post("/admin/clanci/1/obrisi")

    html = admin_klijent.get("/admin/kategorije").get_data(as_text=True)
    assert "<td>Fudbal</td> <td>1</td>" in " ".join(html.split())

    admin_klijent.post("/admin/clanci/2/obrisi")
    odgovor = admin_klijent.post("/admin/kategorije/1/obrisi")

    assert odgovor.headers["Location"] == "/admin/kategorije"
    assert "<td>Fudbal</td>" not in admin_klijent.get("/admin/kategorije").get_data(
        as_text=True
    )


def test_baza_ne_dozvoljava_brisanje_kategorije_sa_nacrtom(app, admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")

    # I kad bi kod zaboravio provjeru, baza sama odbija brisanje.
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute("DELETE FROM kategorija WHERE id = 1")


def test_kategorija_sa_objavljenim_clankom_se_ne_moze_obrisati(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    objavi(admin_klijent, 1)

    odgovor = admin_klijent.post("/admin/kategorije/1/obrisi")

    assert (
        "Kategorija Fudbal ima 1 članak i ne može se obrisati."
        in odgovor.get_data(as_text=True)
    )


def test_admin_panel_ima_link_do_clanaka(admin_klijent):
    html = admin_klijent.get("/admin/").get_data(as_text=True)

    assert 'href="/admin/clanci"' in html
