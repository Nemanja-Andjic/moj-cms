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
