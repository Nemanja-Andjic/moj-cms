from flask import Blueprint, render_template

from .db import objavljeni_clanci

# Javni sajt: stranice koje vidi svaki posjetilac.
bp = Blueprint("javni", __name__)


@bp.route("/")
def naslovna():
    return render_template("naslovna.html", clanci=objavljeni_clanci())


# Vlastita stranica za svaku adresu koja ne postoji (greška 404).
@bp.app_errorhandler(404)
def stranica_nije_pronadjena(e):
    return render_template("404.html"), 404
