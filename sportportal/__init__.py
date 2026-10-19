import os

from flask import Flask

from . import admin, db, javni


def create_app(podesavanja=None):
    """App factory: pravi Flask aplikaciju sa datim podešavanjima.

    Testovi ovdje šalju svoju privremenu bazu, a obično pokretanje
    koristi bazu u `instance` folderu.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        IME_PORTALA="Sport Portal",
        DATABASE=os.path.join(app.instance_path, "sportportal.sqlite"),
        SECRET_KEY="dev",
    )

    if podesavanja is None:
        # Pravi tajni ključ i ostala lokalna podešavanja mogu stajati
        # u instance/config.py (taj fajl se ne stavlja na GitHub).
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(podesavanja)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(javni.bp)
    app.register_blueprint(admin.bp)
    app.cli.add_command(admin.napravi_admina_komanda)

    # Ime portala je dostupno u svim šablonima kao `ime_portala`.
    @app.context_processor
    def dodaj_ime_portala():
        return {"ime_portala": app.config["IME_PORTALA"]}

    return app
