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


@bp.route("/clanci")
def clanci():
    return render_template("admin/clanci.html", clanci=db.clanci())


@bp.route("/clanci/novi", methods=["GET", "POST"])
def novi_clanak():
    greska = None
    clanak = {}
    if request.method == "POST":
        clanak = request.form
        greska = db.dodaj_clanak(
            clanak["naslov"], clanak["uvod"], clanak["tekst"], clanak["kategorija_id"]
        )
        if greska is None:
            return redirect(url_for("admin.clanci"))

    return render_template(
        "admin/clanak_forma.html",
        naslov_stranice="Novi članak",
        clanak=clanak,
        kategorije=db.kategorije(),
        greska=greska,
    )


# Izmjena koristi istu formu kao novi članak.
@bp.route("/clanci/<int:id_clanka>/izmijeni", methods=["GET", "POST"])
def izmijeni_clanak(id_clanka):
    clanak = db.clanak(id_clanka)
    if clanak is None:
        abort(404)

    greska = None
    if request.method == "POST":
        clanak = request.form
        greska = db.izmijeni_clanak(
            id_clanka,
            clanak["naslov"],
            clanak["uvod"],
            clanak["tekst"],
            clanak["kategorija_id"],
        )
        if greska is None:
            return redirect(url_for("admin.clanci"))

    return render_template(
        "admin/clanak_forma.html",
        naslov_stranice="Izmijeni članak",
        clanak=clanak,
        kategorije=db.kategorije(),
        greska=greska,
    )


# Kao i kod kategorija: GET prikaže stranicu za potvrdu, a tek dugme na
# njoj (POST) zaista briše članak.
@bp.route("/clanci/<int:id_clanka>/obrisi", methods=["GET", "POST"])
def obrisi_clanak(id_clanka):
    clanak = db.clanak(id_clanka)
    if clanak is None:
        abort(404)

    if request.method == "POST":
        db.obrisi_clanak(id_clanka)
        return redirect(url_for("admin.clanci"))

    return render_template("admin/obrisi_clanak.html", clanak=clanak)


@bp.route("/clanci/<int:id_clanka>/objavi", methods=["POST"])
def objavi_clanak(id_clanka):
    if db.clanak(id_clanka) is None:
        abort(404)

    db.objavi_clanak(id_clanka)
    return redirect(url_for("admin.clanci"))


@bp.route("/clanci/<int:id_clanka>/povuci", methods=["POST"])
def povuci_clanak(id_clanka):
    if db.clanak(id_clanka) is None:
        abort(404)

    db.povuci_clanak(id_clanka)
    return redirect(url_for("admin.clanci"))
