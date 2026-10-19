from sportportal.db import get_db


def prijava_uspijeva(client, korisnicko_ime, lozinka):
    odgovor = client.post(
        "/admin/prijava",
        data={"korisnicko_ime": korisnicko_ime, "lozinka": lozinka},
    )
    client.post("/admin/odjava")
    return odgovor.status_code == 302


def test_komanda_pravi_admina_sa_kojim_se_moze_prijaviti(runner, client):
    rezultat = runner.invoke(
        args=["napravi-admina"], input="marko\ntajna123\ntajna123\n"
    )

    assert rezultat.exit_code == 0
    assert "Admin je napravljen." in rezultat.output
    assert prijava_uspijeva(client, "marko", "tajna123")


def test_komanda_trazi_da_se_lozinka_ponovi(runner, client):
    rezultat = runner.invoke(
        args=["napravi-admina"], input="marko\ntajna123\ndruga\ntajna123\ntajna123\n"
    )

    assert "Lozinke se ne poklapaju." in rezultat.output
    assert prijava_uspijeva(client, "marko", "tajna123")


def test_komanda_kad_admin_postoji_mijenja_lozinku(runner, client):
    runner.invoke(args=["napravi-admina"], input="marko\nstara123\nstara123\n")

    rezultat = runner.invoke(args=["napravi-admina"], input="nova123\nnova123\n")

    assert rezultat.exit_code == 0
    assert "marko" in rezultat.output
    assert "Lozinka je promijenjena." in rezultat.output
    assert prijava_uspijeva(client, "marko", "nova123")
    assert not prijava_uspijeva(client, "marko", "stara123")


def test_postoji_najvise_jedan_admin(app, runner):
    runner.invoke(args=["napravi-admina"], input="marko\nstara123\nstara123\n")
    runner.invoke(args=["napravi-admina"], input="nova123\nnova123\n")

    with app.app_context():
        broj = get_db().execute("SELECT COUNT(*) FROM admin").fetchone()[0]
    assert broj == 1


def test_lozinka_se_u_bazi_cuva_samo_kao_hash(app, runner):
    runner.invoke(args=["napravi-admina"], input="marko\ntajna123\ntajna123\n")

    with app.app_context():
        hash_lozinke = get_db().execute(
            "SELECT hash_lozinke FROM admin"
        ).fetchone()[0]
    assert "tajna123" not in hash_lozinke
    # Werkzeug hash počinje imenom algoritma, npr. "scrypt:...".
    assert hash_lozinke.startswith(("scrypt:", "pbkdf2:"))
