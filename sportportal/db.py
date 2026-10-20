import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Vraća konekciju na bazu za trenutni zahtjev (pravi je ako ne postoji)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # Redovi iz baze se mogu čitati po imenu kolone: red["naslov"].
        g.db.row_factory = sqlite3.Row
        # SQLite ne provjerava strane ključeve dok mu se to ne kaže.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def zatvori_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def napravi_tabele():
    """Pravi tabele iz schema.sql. Postojeće tabele i podaci ostaju netaknuti."""
    with current_app.open_resource("schema.sql") as f:
        get_db().executescript(f.read().decode("utf-8"))


@click.command("napravi-bazu")
@with_appcontext
def napravi_bazu_komanda():
    """Pravi bazu sa tabelama za admina, kategorije i članke."""
    napravi_tabele()
    click.echo("Baza je napravljena.")


def init_app(app):
    app.teardown_appcontext(zatvori_db)
    app.cli.add_command(napravi_bazu_komanda)


def objavljeni_clanci():
    """Najviše 20 objavljenih članaka, najnoviji gore."""
    return get_db().execute(
        "SELECT clanak.id, naslov, uvod, datum_objave, kategorija.ime AS kategorija"
        " FROM clanak JOIN kategorija ON kategorija.id = clanak.kategorija_id"
        " WHERE stanje = 'objavljen'"
        # Članci objavljeni u istoj sekundi: noviji ima veći id.
        " ORDER BY datum_objave DESC, clanak.id DESC"
        " LIMIT 20"
    ).fetchall()


def admin():
    """Admin iz baze (korisničko ime i hash lozinke), ili None ako ga još nema."""
    return get_db().execute(
        "SELECT korisnicko_ime, hash_lozinke FROM admin WHERE id = 1"
    ).fetchone()


def sacuvaj_admina(korisnicko_ime, hash_lozinke):
    """Pravi admina, ili mu mijenja podatke ako već postoji (uvijek id = 1)."""
    baza = get_db()
    baza.execute(
        "INSERT INTO admin (id, korisnicko_ime, hash_lozinke) VALUES (1, ?, ?)"
        " ON CONFLICT (id) DO UPDATE SET"
        " korisnicko_ime = excluded.korisnicko_ime,"
        " hash_lozinke = excluded.hash_lozinke",
        (korisnicko_ime, hash_lozinke),
    )
    baza.commit()


def kategorije():
    """Sve kategorije sa brojem članaka u svakoj, poredane po imenu."""
    return get_db().execute(
        "SELECT kategorija.id, ime, COUNT(clanak.id) AS broj_clanaka"
        " FROM kategorija LEFT JOIN clanak ON clanak.kategorija_id = kategorija.id"
        " GROUP BY kategorija.id"
        " ORDER BY ime_za_poredjenje"
    ).fetchall()


def kategorija(id_kategorije):
    """Jedna kategorija sa brojem članaka u njoj, ili None ako ne postoji."""
    return get_db().execute(
        "SELECT kategorija.id, ime, COUNT(clanak.id) AS broj_clanaka"
        " FROM kategorija LEFT JOIN clanak ON clanak.kategorija_id = kategorija.id"
        " WHERE kategorija.id = ?"
        " GROUP BY kategorija.id",
        (id_kategorije,),
    ).fetchone()


def greska_u_imenu_kategorije(ime, id_kategorije=None):
    """Vraća poruku o grešci ako se kategorija ne smije zvati `ime`, inače None.

    `ime` mora već biti bez razmaka na početku i kraju. Kod preimenovanja
    se šalje i `id_kategorije`, da kategorija ne bi smetala sama sebi
    (npr. kad se "fudbal" mijenja u "Fudbal").
    """
    if not ime:
        return "Ime kategorije ne može biti prazno."
    # casefold() pretvara ime u mala slova, i to radi i za č, ć, š, ž, đ.
    postojeca = get_db().execute(
        "SELECT id, ime FROM kategorija WHERE ime_za_poredjenje = ?",
        (ime.casefold(),),
    ).fetchone()
    if postojeca is not None and postojeca["id"] != id_kategorije:
        return f"Kategorija {postojeca['ime']} već postoji."
    return None


def dodaj_kategoriju(ime):
    """Pravi kategoriju. Vraća poruku o grešci, ili None ako je sve u redu."""
    # Razmake na početku i kraju imena uklanjamo odmah.
    ime = ime.strip()
    greska = greska_u_imenu_kategorije(ime)
    if greska is not None:
        return greska

    baza = get_db()
    baza.execute(
        "INSERT INTO kategorija (ime, ime_za_poredjenje) VALUES (?, ?)",
        (ime, ime.casefold()),
    )
    baza.commit()
    return None


def preimenuj_kategoriju(id_kategorije, ime):
    """Mijenja ime kategorije. Vraća poruku o grešci, ili None ako je sve u redu."""
    ime = ime.strip()
    greska = greska_u_imenu_kategorije(ime, id_kategorije)
    if greska is not None:
        return greska

    baza = get_db()
    baza.execute(
        "UPDATE kategorija SET ime = ?, ime_za_poredjenje = ? WHERE id = ?",
        (ime, ime.casefold(), id_kategorije),
    )
    baza.commit()
    return None


def obrisi_kategoriju(id_kategorije):
    """Briše praznu kategoriju. Vraća poruku o grešci, ili None ako je obrisana."""
    kategorija_za_brisanje = kategorija(id_kategorije)
    broj = kategorija_za_brisanje["broj_clanaka"]
    if broj > 0:
        return (
            f"Kategorija {kategorija_za_brisanje['ime']} ima {broj} {clanaka(broj)}"
            " i ne može se obrisati."
        )

    baza = get_db()
    baza.execute("DELETE FROM kategorija WHERE id = ?", (id_kategorije,))
    baza.commit()
    return None


def clanaka(broj):
    """Riječ "članak" u obliku koji ide uz dati broj: 1 članak, 3 članka, 5 članaka."""
    if broj % 10 == 1 and broj % 100 != 11:
        return "članak"
    if broj % 10 in (2, 3, 4) and broj % 100 not in (12, 13, 14):
        return "članka"
    return "članaka"


def clanci():
    """Svi članci (nacrti i objavljeni) sa imenom kategorije, najnoviji gore."""
    return get_db().execute(
        "SELECT clanak.id, naslov, stanje, kategorija.ime AS kategorija"
        " FROM clanak JOIN kategorija ON kategorija.id = clanak.kategorija_id"
        # Članci napravljeni u istoj sekundi: noviji ima veći id.
        " ORDER BY napravljen DESC, clanak.id DESC"
    ).fetchall()


def clanak(id_clanka):
    """Jedan članak (sva polja), ili None ako ne postoji."""
    return get_db().execute(
        "SELECT id, naslov, uvod, tekst, kategorija_id, stanje"
        " FROM clanak WHERE id = ?",
        (id_clanka,),
    ).fetchone()


def clanak_za_citanje(id_clanka):
    """Članak sa imenom kategorije, za stranicu članka, ili None ako ne postoji."""
    return get_db().execute(
        "SELECT clanak.id, naslov, uvod, tekst, stanje, datum_objave,"
        " kategorija.ime AS kategorija"
        " FROM clanak JOIN kategorija ON kategorija.id = clanak.kategorija_id"
        " WHERE clanak.id = ?",
        (id_clanka,),
    ).fetchone()


def greska_u_clanku(naslov, uvod, tekst, kategorija_id):
    """Vraća poruku o grešci ako u članku nešto nedostaje, inače None.

    Tekstualna polja moraju već biti bez razmaka na početku i kraju.
    """
    if not naslov:
        return "Naslov je obavezan."
    if not uvod:
        return "Uvod je obavezan."
    if not tekst:
        return "Tekst je obavezan."
    # Kategorija mora postojati u bazi, a ne samo biti poslata.
    if not kategorija_id.isdigit() or kategorija(int(kategorija_id)) is None:
        return "Kategorija je obavezna."
    return None


def dodaj_clanak(naslov, uvod, tekst, kategorija_id):
    """Pravi novi članak. Vraća poruku o grešci, ili None ako je sačuvan.

    Svaki novi članak je nacrt (to je podrazumijevano stanje u bazi).
    """
    naslov, uvod, tekst = naslov.strip(), uvod.strip(), tekst.strip()
    greska = greska_u_clanku(naslov, uvod, tekst, kategorija_id)
    if greska is not None:
        return greska

    baza = get_db()
    baza.execute(
        "INSERT INTO clanak (naslov, uvod, tekst, kategorija_id) VALUES (?, ?, ?, ?)",
        (naslov, uvod, tekst, int(kategorija_id)),
    )
    baza.commit()
    return None


def izmijeni_clanak(id_clanka, naslov, uvod, tekst, kategorija_id):
    """Mijenja članak. Vraća poruku o grešci, ili None ako je sačuvan.

    Stanje članka (nacrt ili objavljen) ostaje kakvo je bilo.
    """
    naslov, uvod, tekst = naslov.strip(), uvod.strip(), tekst.strip()
    greska = greska_u_clanku(naslov, uvod, tekst, kategorija_id)
    if greska is not None:
        return greska

    baza = get_db()
    baza.execute(
        "UPDATE clanak SET naslov = ?, uvod = ?, tekst = ?, kategorija_id = ?"
        " WHERE id = ?",
        (naslov, uvod, tekst, int(kategorija_id), id_clanka),
    )
    baza.commit()
    return None


def obrisi_clanak(id_clanka):
    """Trajno briše članak, bez obzira da li je nacrt ili objavljen."""
    baza = get_db()
    baza.execute("DELETE FROM clanak WHERE id = ?", (id_clanka,))
    baza.commit()


def objavi_clanak(id_clanka):
    """Prebacuje članak u stanje objavljen.

    Datum objave se postavlja samo pri prvom objavljivanju, pa povučen
    pa ponovo objavljen članak zadržava prvobitni datum.
    """
    baza = get_db()
    baza.execute(
        "UPDATE clanak SET stanje = 'objavljen',"
        " datum_objave = COALESCE(datum_objave, CURRENT_TIMESTAMP)"
        " WHERE id = ?",
        (id_clanka,),
    )
    baza.commit()


def povuci_clanak(id_clanka):
    """Vraća objavljen članak u nacrt. Datum objave ostaje zapamćen."""
    baza = get_db()
    baza.execute("UPDATE clanak SET stanje = 'nacrt' WHERE id = ?", (id_clanka,))
    baza.commit()
