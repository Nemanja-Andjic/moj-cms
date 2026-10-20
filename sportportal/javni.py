import re
from datetime import datetime, timezone

from flask import Blueprint, abort, render_template, session

from .db import clanak_za_citanje, objavljeni_clanci

# Javni sajt: stranice koje vidi svaki posjetilac.
bp = Blueprint("javni", __name__)


@bp.route("/")
def naslovna():
    return render_template("naslovna.html", clanci=objavljeni_clanci())


@bp.route("/clanak/<int:id_clanka>")
def clanak(id_clanka):
    clanak = clanak_za_citanje(id_clanka)
    # Nacrt vidi samo prijavljeni admin (pregled prije objave). Posjetilac
    # dobija istu stranicu kao za članak koji ne postoji.
    if clanak is None or (
        clanak["stanje"] == "nacrt" and not session.get("admin_prijavljen")
    ):
        abort(404)

    return render_template("clanak.html", clanak=clanak)


# Datum objave u šablonu: {{ clanak.datum_objave | datum_objave }} daje npr. 20.10.2026.
@bp.app_template_filter("datum_objave")
def datum_objave(vrijeme_iz_baze):
    # Baza čuva vrijeme po UTC-u ("2026-10-20 22:30:00"), a datum objave
    # prikazujemo po lokalnom vremenu računara.
    vrijeme = datetime.fromisoformat(vrijeme_iz_baze).replace(tzinfo=timezone.utc)
    return vrijeme.astimezone().strftime("%d.%m.%Y.")


# Tekst članka podijeljen na pasuse: prazan red (i kad u njemu ima
# razmaka) počinje novi pasus.
@bp.app_template_filter("pasusi")
def pasusi(tekst):
    return [pasus.strip() for pasus in re.split(r"\n\s*\n", tekst) if pasus.strip()]


# Vlastita stranica za svaku adresu koja ne postoji (greška 404).
@bp.app_errorhandler(404)
def stranica_nije_pronadjena(e):
    return render_template("404.html"), 404
