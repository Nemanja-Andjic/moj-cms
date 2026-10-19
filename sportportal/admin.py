import click
from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash

from . import db

# Admin panel: sve stranice pod /admin.
bp = Blueprint("admin", __name__, url_prefix="/admin")


@click.command("napravi-admina")
@with_appcontext
def napravi_admina_komanda():
    """Pravi admin nalog, ili mijenja lozinku ako admin već postoji."""
    postojeci = db.admin()
    if postojeci is None:
        korisnicko_ime = click.prompt("Korisničko ime")
    else:
        korisnicko_ime = postojeci["korisnicko_ime"]
        click.echo(f"Admin {korisnicko_ime} već postoji. Unesi novu lozinku.")

    lozinka = trazi_lozinku()
    # U bazu ide samo hash lozinke, nikad sama lozinka.
    db.sacuvaj_admina(korisnicko_ime, generate_password_hash(lozinka))

    if postojeci is None:
        click.echo("Admin je napravljen.")
    else:
        click.echo("Lozinka je promijenjena.")


def trazi_lozinku():
    """Traži lozinku dva puta, sve dok se oba unosa ne poklope."""
    while True:
        lozinka = click.prompt("Lozinka", hide_input=True)
        ponovljena = click.prompt("Ponovi lozinku", hide_input=True)
        if lozinka == ponovljena:
            return lozinka
        click.echo("Lozinke se ne poklapaju. Pokušaj ponovo.")


# Prije svake admin stranice, osim prijave: neprijavljenog posjetioca
# šaljemo na prijavu.
@bp.before_request
def trazi_prijavu():
    if request.endpoint != "admin.prijava" and not session.get("admin_prijavljen"):
        return redirect(url_for("admin.prijava"))


@bp.route("/")
def panel():
    return render_template("admin/panel.html")


@bp.route("/prijava", methods=["GET", "POST"])
def prijava():
    greska = None
    if request.method == "POST":
        admin = db.admin()
        if (
            admin is not None
            and request.form["korisnicko_ime"] == admin["korisnicko_ime"]
            and check_password_hash(admin["hash_lozinke"], request.form["lozinka"])
        ):
            # Brišemo sve staro iz sesije prije nego što zapamtimo prijavu.
            session.clear()
            session["admin_prijavljen"] = True
            return redirect(url_for("admin.panel"))
        # Ista poruka za pogrešno ime i pogrešnu lozinku, da se ne otkrije
        # koje od to dvoje je tačno.
        greska = "Pogrešno korisničko ime ili lozinka."

    return render_template("admin/prijava.html", greska=greska)


@bp.route("/odjava", methods=["POST"])
def odjava():
    session.clear()
    return redirect(url_for("admin.prijava"))


@bp.route("/kategorije", methods=["GET", "POST"])
def kategorije():
    greska = None
    if request.method == "POST":
        greska = db.dodaj_kategoriju(request.form["ime"])
        if greska is None:
            return redirect(url_for("admin.kategorije"))

    return render_template(
        "admin/kategorije.html", kategorije=db.kategorije(), greska=greska
    )


@bp.route("/kategorije/<int:id_kategorije>/preimenuj", methods=["GET", "POST"])
def preimenuj_kategoriju(id_kategorije):
    kategorija = db.kategorija(id_kategorije)
    if kategorija is None:
        abort(404)

    greska = None
    ime = kategorija["ime"]
    if request.method == "POST":
        ime = request.form["ime"]
        greska = db.preimenuj_kategoriju(id_kategorije, ime)
        if greska is None:
            return redirect(url_for("admin.kategorije"))

    return render_template(
        "admin/preimenuj_kategoriju.html",
        kategorija=kategorija,
        ime=ime,
        greska=greska,
    )


# Brisanje ide u dva koraka: GET prikaže stranicu za potvrdu, a tek dugme
# na njoj (POST) zaista briše kategoriju.
@bp.route("/kategorije/<int:id_kategorije>/obrisi", methods=["GET", "POST"])
def obrisi_kategoriju(id_kategorije):
    kategorija = db.kategorija(id_kategorije)
    if kategorija is None:
        abort(404)

    greska = None
    if request.method == "POST":
        greska = db.obrisi_kategoriju(id_kategorije)
        if greska is None:
            return redirect(url_for("admin.kategorije"))

    return render_template(
        "admin/obrisi_kategoriju.html", kategorija=kategorija, greska=greska
    )
