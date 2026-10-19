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
        " ORDER BY datum_objave DESC"
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
