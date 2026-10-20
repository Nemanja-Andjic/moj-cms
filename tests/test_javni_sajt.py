from sportportal.db import get_db


def dodaj_kategoriju(klijent, ime):
    klijent.post("/admin/kategorije", data={"ime": ime})


def napravi_clanak(klijent, naslov="Derbi u subotu", kategorija_id=1, **polja):
    podaci = {
        "naslov": naslov,
        "uvod": "Kratak uvod.",
        "tekst": "Cijeli tekst članka.",
        "kategorija_id": kategorija_id,
    }
    podaci.update(polja)
    klijent.post("/admin/clanci/novi", data=podaci)


def objavi(klijent, id_clanka):
    return klijent.post(f"/admin/clanci/{id_clanka}/objavi")


def povuci(klijent, id_clanka):
    return klijent.post(f"/admin/clanci/{id_clanka}/povuci")


def html_bez_razmaka(odgovor):
    """HTML odgovora, sa razmacima svedenim na po jedan."""
    return " ".join(odgovor.get_data(as_text=True).split())


def postavi_datum_objave(app, id_clanka, datum):
    """Članak "vraća u prošlost", da test ne zavisi od trenutnog vremena."""
    with app.app_context():
        baza = get_db()
        baza.execute(
            "UPDATE clanak SET datum_objave = ? WHERE id = ?", (datum, id_clanka)
        )
        baza.commit()


def test_objavljen_clanak_se_vidi_na_naslovnoj(admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu", uvod="Veliki derbi grada.")

    odgovor = objavi(admin_klijent, 1)

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/clanci"
    html = html_bez_razmaka(client.get("/"))
    assert '<a href="/clanak/1">Derbi u subotu</a>' in html
    assert "Fudbal" in html
    assert "Veliki derbi grada." in html
    assert "Još nema objavljenih članaka." not in html


def test_naslovna_redja_clanke_po_datumu_objave_najnoviji_gore(app, admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    for naslov in ("Srednji članak", "Najnoviji članak", "Najstariji članak"):
        napravi_clanak(admin_klijent, naslov)
    for id_clanka in (1, 2, 3):
        objavi(admin_klijent, id_clanka)
    # Datumi su namjerno drugačijim redom nego što su članci napravljeni.
    postavi_datum_objave(app, 1, "2026-03-05 12:00:00")
    postavi_datum_objave(app, 2, "2026-03-10 12:00:00")
    postavi_datum_objave(app, 3, "2026-03-01 12:00:00")

    html = html_bez_razmaka(client.get("/"))

    assert (
        html.index("Najnoviji članak")
        < html.index("Srednji članak")
        < html.index("Najstariji članak")
    )
    assert "Fudbal · 10.03.2026." in html


def test_naslovna_prikazuje_najvise_20_clanaka(app, admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    for broj in range(1, 22):
        napravi_clanak(admin_klijent, f"Članak broj {broj}.")
        objavi(admin_klijent, broj)
        postavi_datum_objave(app, broj, f"2026-03-{broj:02d} 12:00:00")

    html = client.get("/").get_data(as_text=True)

    assert html.count("<article>") == 20
    assert "Članak broj 21." in html
    assert "Članak broj 1." not in html
    # Stariji članak se i dalje otvara preko direktnog linka.
    assert "Članak broj 1." in client.get("/clanak/1").get_data(as_text=True)


def test_nacrt_se_ne_vidi_na_naslovnoj(admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Tajni nacrt")

    html = client.get("/").get_data(as_text=True)

    assert "Tajni nacrt" not in html
    assert "Još nema objavljenih članaka." in html


def test_stranica_clanka_prikazuje_cijeli_clanak(app, admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Košarka")
    napravi_clanak(
        admin_klijent,
        "Finale lige",
        kategorija_id=1,
        uvod="Odlučujuća utakmica.",
        tekst="Prvi pasus,\ni dalje prvi.\n\nDrugi pasus.\r\n\r\nTreći pasus.",
    )
    objavi(admin_klijent, 1)
    postavi_datum_objave(app, 1, "2026-05-15 12:00:00")

    odgovor = client.get("/clanak/1")

    assert odgovor.status_code == 200
    html = html_bez_razmaka(odgovor)
    assert "<h1>Finale lige</h1>" in html
    assert "Košarka · 15.05.2026." in html
    assert "Odlučujuća utakmica." in html
    # Prazan red u tekstu pravi novi pasus.
    assert "<p>Prvi pasus, i dalje prvi.</p>" in html
    assert "<p>Drugi pasus.</p>" in html
    assert "<p>Treći pasus.</p>" in html


def test_html_u_tekstu_se_prikazuje_kao_tekst(admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Opasan <b>naslov</b>", tekst="<script>alert(1)</script>")
    objavi(admin_klijent, 1)

    html = client.get("/clanak/1").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<b>naslov</b>" not in html


def test_posjetilac_ne_vidi_nacrt(admin_klijent, client):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Tajni nacrt")
    admin_klijent.post("/admin/odjava")

    odgovor = client.get("/clanak/1")

    assert odgovor.status_code == 404
    html = odgovor.get_data(as_text=True)
    assert "Stranica nije pronađena" in html
    assert "Tajni nacrt" not in html


def test_nepostojeci_clanak_daje_404(client):
    odgovor = client.get("/clanak/99")

    assert odgovor.status_code == 404
    assert "Stranica nije pronađena" in odgovor.get_data(as_text=True)


def test_povucen_clanak_nestaje_sa_sajta(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    objavi(admin_klijent, 1)

    odgovor = povuci(admin_klijent, 1)

    assert odgovor.status_code == 302
    assert odgovor.headers["Location"] == "/admin/clanci"
    assert "<td>Nacrt</td>" in admin_klijent.get("/admin/clanci").get_data(as_text=True)
    admin_klijent.post("/admin/odjava")
    assert "Derbi u subotu" not in admin_klijent.get("/").get_data(as_text=True)
    assert admin_klijent.get("/clanak/1").status_code == 404


def test_ponovo_objavljen_clanak_zadrzava_prvobitni_datum_objave(app, admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    objavi(admin_klijent, 1)
    postavi_datum_objave(app, 1, "2026-02-14 12:00:00")

    povuci(admin_klijent, 1)
    # Povučen članak (nacrt) i dalje pamti datum objave.
    assert "14.02.2026." in admin_klijent.get("/clanak/1").get_data(as_text=True)
    objavi(admin_klijent, 1)

    assert "Fudbal · 14.02.2026." in html_bez_razmaka(admin_klijent.get("/"))
    assert "Fudbal · 14.02.2026." in html_bez_razmaka(admin_klijent.get("/clanak/1"))


def test_izmjena_objavljenog_clanka_se_odmah_vidi_na_sajtu(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Stari naslov", tekst="Stari tekst.")
    objavi(admin_klijent, 1)

    admin_klijent.post(
        "/admin/clanci/1/izmijeni",
        data={
            "naslov": "Novi naslov",
            "uvod": "Novi uvod.",
            "tekst": "Novi tekst.",
            "kategorija_id": "1",
        },
    )

    admin_klijent.post("/admin/odjava")
    assert '<a href="/clanak/1">Novi naslov</a>' in admin_klijent.get("/").get_data(
        as_text=True
    )
    html = admin_klijent.get("/clanak/1").get_data(as_text=True)
    assert "Novi tekst." in html
    assert "Stari" not in html


def test_lista_clanaka_ima_objavi_za_nacrt_i_povuci_za_objavljen(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Nacrt članak")
    napravi_clanak(admin_klijent, "Objavljen članak")
    objavi(admin_klijent, 2)

    html = html_bez_razmaka(admin_klijent.get("/admin/clanci"))

    assert (
        '<form method="post" action="/admin/clanci/1/objavi">'
        ' <button type="submit">Objavi</button>'
    ) in html
    assert (
        '<form method="post" action="/admin/clanci/2/povuci">'
        ' <button type="submit">Povuci</button>'
    ) in html
    assert "/admin/clanci/1/povuci" not in html
    assert "/admin/clanci/2/objavi" not in html


def test_admin_moze_pregledati_nacrt(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Tajni nacrt", tekst="Tekst nacrta.")
    assert 'href="/clanak/1">Pregled</a>' in admin_klijent.get("/admin/clanci").get_data(
        as_text=True
    )

    odgovor = admin_klijent.get("/clanak/1")

    assert odgovor.status_code == 200
    html = odgovor.get_data(as_text=True)
    assert "Nacrt – posjetioci ovo ne vide" in html
    assert "Tekst nacrta." in html


def test_objavljen_clanak_nema_traku_nacrt(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    objavi(admin_klijent, 1)

    html = admin_klijent.get("/clanak/1").get_data(as_text=True)

    assert "Nacrt – posjetioci ovo ne vide" not in html


def test_objavi_i_povuci_traze_prijavu(admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Derbi u subotu")
    admin_klijent.post("/admin/odjava")

    odgovor = objavi(admin_klijent, 1)

    assert odgovor.headers["Location"] == "/admin/prijava"
    assert povuci(admin_klijent, 1).headers["Location"] == "/admin/prijava"
    assert admin_klijent.get("/clanak/1").status_code == 404


def test_objavi_i_povuci_nepostojeci_clanak_daju_404(admin_klijent):
    assert objavi(admin_klijent, 99).status_code == 404
    assert povuci(admin_klijent, 99).status_code == 404


def test_clanci_objavljeni_u_istoj_sekundi_noviji_gore(app, admin_klijent):
    dodaj_kategoriju(admin_klijent, "Fudbal")
    napravi_clanak(admin_klijent, "Prvi objavljen")
    napravi_clanak(admin_klijent, "Drugi objavljen")
    for id_clanka in (1, 2):
        objavi(admin_klijent, id_clanka)
        postavi_datum_objave(app, id_clanka, "2026-03-01 12:00:00")

    html = admin_klijent.get("/").get_data(as_text=True)

    assert html.index("Drugi objavljen") < html.index("Prvi objavljen")
