import pytest

from sportportal import create_app
from sportportal.db import napravi_tabele


@pytest.fixture
def app(tmp_path):
    """Aplikacija sa novom, privremenom bazom za svaki test."""
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
        "SECRET_KEY": "test",
    })
    with app.app_context():
        napravi_tabele()
    return app


@pytest.fixture
def client(app):
    """Šalje HTTP zahtjeve aplikaciji, kao browser."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Pokreće komande u terminalu (Flask CLI)."""
    return app.test_cli_runner()


@pytest.fixture
def admin_klijent(client, runner):
    """Klijent na kojem je admin već prijavljen."""
    runner.invoke(args=["napravi-admina"], input="marko\ntajna123\ntajna123\n")
    client.post(
        "/admin/prijava",
        data={"korisnicko_ime": "marko", "lozinka": "tajna123"},
    )
    return client
