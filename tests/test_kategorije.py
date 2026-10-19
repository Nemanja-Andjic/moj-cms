import pytest


def dodaj(klijent, ime):
    return klijent.post("/admin/kategorije", data={"ime": ime}, follow_redirects=True)


def stranica_kategorija(klijent):
    """HTML stranice kategorija, sa svim razmacima i novim redovima
    svedenim na po jedan razmak (lakše je tražiti dijelove tabele)."""
    html = klijent.get("/admin/kategorije").get_data(as_text=True)
    return " ".join(html.split())


def test_stranica_kategorija_trazi_prijavu(client):
    odgovor = client.get("/admin/kategorije")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/prijava"


def test_dodata_kategorija_se_vidi_na_stranici_kategorija(admin_klijent):
    odgovor = dodaj(admin_klijent, "Fudbal")

    assert odgovor.status_code == 200
    assert "Fudbal" in stranica_kategorija(admin_klijent)


def napravi_clanak(klijent, id_kategorije):
    """Priprema: nacrt u datoj kategoriji, napravljen kroz admin panel."""
    klijent.post("/admin/clanci/novi", data={
        "naslov": "Naslov",
        "uvod": "Uvod",
        "tekst": "Tekst",
        "kategorija_id": id_kategorije,
    })


def test_stranica_kategorija_prikazuje_broj_clanaka(admin_klijent):
    dodaj(admin_klijent, "Fudbal")
    dodaj(admin_klijent, "Tenis")
    napravi_clanak(admin_klijent, 1)
    napravi_clanak(admin_klijent, 1)

    html = stranica_kategorija(admin_klijent)

    assert "<td>Fudbal</td> <td>2</td>" in html
    assert "<td>Tenis</td> <td>0</td>" in html


def test_razmaci_oko_imena_se_uklanjaju(admin_klijent):
    dodaj(admin_klijent, "   Fudbal  ")

    assert "<td>Fudbal</td>" in stranica_kategorija(admin_klijent)


@pytest.mark.parametrize("ime", ["", "    "])
def test_prazno_ime_se_odbija(admin_klijent, ime):
    odgovor = dodaj(admin_klijent, ime)

    assert "Ime kategorije ne može biti prazno." in odgovor.get_data(as_text=True)
    assert "<tbody> </tbody>" in stranica_kategorija(admin_klijent)


@pytest.mark.parametrize("postojece, novo", [
    ("Fudbal", "Fudbal"),
    ("Fudbal", "FUDBAL"),
    ("Fudbal", "  fudbal "),
    ("Košarka", "KOŠARKA"),
    ("Čačak đaci", "čAČAK ĐACI"),
    ("Šah i žice", "ŠAH I ŽICE"),
    ("Ćevap kup", "ćEVAP KUP"),
])
def test_ime_koje_vec_postoji_se_odbija(admin_klijent, postojece, novo):
    dodaj(admin_klijent, postojece)

    odgovor = dodaj(admin_klijent, novo)

    assert f"Kategorija {postojece} već postoji." in odgovor.get_data(as_text=True)
    assert stranica_kategorija(admin_klijent).count("<tr> <td>") == 1


def preimenuj(klijent, id_kategorije, novo_ime):
    return klijent.post(
        f"/admin/kategorije/{id_kategorije}/preimenuj",
        data={"ime": novo_ime},
        follow_redirects=True,
    )


def test_stranica_kategorija_ima_link_za_preimenovanje(admin_klijent):
    dodaj(admin_klijent, "Fudbal")

    assert 'href="/admin/kategorije/1/preimenuj"' in stranica_kategorija(admin_klijent)


def test_stranica_za_preimenovanje_prikazuje_trenutno_ime(admin_klijent):
    dodaj(admin_klijent, "Fudbal")

    html = admin_klijent.get("/admin/kategorije/1/preimenuj").get_data(as_text=True)

    assert 'value="Fudbal"' in html


def test_admin_moze_preimenovati_kategoriju(admin_klijent):
    dodaj(admin_klijent, "Fudbal")

    preimenuj(admin_klijent, 1, "  Mali fudbal ")

    html = stranica_kategorija(admin_klijent)
    assert "<td>Mali fudbal</td>" in html
    assert "<td>Fudbal</td>" not in html


def test_kategoriji_se_mogu_promijeniti_samo_velika_i_mala_slova(admin_klijent):
    dodaj(admin_klijent, "košarka")

    preimenuj(admin_klijent, 1, "Košarka")

    assert "<td>Košarka</td>" in stranica_kategorija(admin_klijent)


@pytest.mark.parametrize("novo_ime, poruka", [
    ("KOŠARKA", "Kategorija Košarka već postoji."),
    ("   ", "Ime kategorije ne može biti prazno."),
])
def test_preimenovanje_odbija_lose_ime(admin_klijent, novo_ime, poruka):
    dodaj(admin_klijent, "Fudbal")
    dodaj(admin_klijent, "Košarka")

    odgovor = preimenuj(admin_klijent, 1, novo_ime)

    assert poruka in odgovor.get_data(as_text=True)
    assert "<td>Fudbal</td>" in stranica_kategorija(admin_klijent)


def test_preimenovanje_nepostojece_kategorije_daje_404(admin_klijent):
    assert admin_klijent.get("/admin/kategorije/99/preimenuj").status_code == 404


def test_brisanje_prvo_trazi_potvrdu(admin_klijent):
    dodaj(admin_klijent, "Fudbal")
    assert 'href="/admin/kategorije/1/obrisi"' in stranica_kategorija(admin_klijent)

    html = admin_klijent.get("/admin/kategorije/1/obrisi").get_data(as_text=True)

    assert "Da li sigurno želiš obrisati kategoriju Fudbal?" in html
    assert '<form method="post">' in html
    # Samo otvaranje stranice za potvrdu ne briše ništa.
    assert "<td>Fudbal</td>" in stranica_kategorija(admin_klijent)


def test_admin_moze_obrisati_praznu_kategoriju(admin_klijent):
    dodaj(admin_klijent, "Fudbal")
    dodaj(admin_klijent, "Tenis")

    odgovor = admin_klijent.post("/admin/kategorije/1/obrisi")

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/kategorije"
    html = stranica_kategorija(admin_klijent)
    assert "<td>Fudbal</td>" not in html
    assert "<td>Tenis</td>" in html


@pytest.mark.parametrize("broj_clanaka, poruka", [
    (1, "Kategorija Fudbal ima 1 članak i ne može se obrisati."),
    (3, "Kategorija Fudbal ima 3 članka i ne može se obrisati."),
    (5, "Kategorija Fudbal ima 5 članaka i ne može se obrisati."),
])
def test_kategorija_sa_clancima_se_ne_moze_obrisati(
    admin_klijent, broj_clanaka, poruka
):
    dodaj(admin_klijent, "Fudbal")
    for _ in range(broj_clanaka):
        napravi_clanak(admin_klijent, 1)
    assert 'href="/admin/kategorije/1/obrisi"' not in stranica_kategorija(admin_klijent)

    odgovor = admin_klijent.post("/admin/kategorije/1/obrisi", follow_redirects=True)

    assert poruka in odgovor.get_data(as_text=True)
    assert "<td>Fudbal</td>" in stranica_kategorija(admin_klijent)


def test_brisanje_nepostojece_kategorije_daje_404(admin_klijent):
    assert admin_klijent.post("/admin/kategorije/99/obrisi").status_code == 404


def test_admin_panel_ima_link_do_kategorija(admin_klijent):
    html = admin_klijent.get("/admin/").get_data(as_text=True)

    assert 'href="/admin/kategorije"' in html
