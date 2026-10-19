from sportportal import create_app


def test_komanda_napravi_bazu_pravi_bazu_sa_kojom_sajt_radi(tmp_path):
    # Aplikacija sa novom bazom u kojoj još nema nijedne tabele.
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "nova.sqlite"),
        "SECRET_KEY": "test",
    })

    rezultat = app.test_cli_runner().invoke(args=["napravi-bazu"])

    assert rezultat.exit_code == 0
    assert "Baza je napravljena." in rezultat.output
    odgovor = app.test_client().get("/")
    assert odgovor.status_code == 200
    assert "Još nema objavljenih članaka." in odgovor.get_data(as_text=True)


def test_komanda_napravi_bazu_moze_se_pokrenuti_vise_puta(runner, client):
    # Baza iz fixture-a već ima tabele, pa je ovo drugo pokretanje.
    rezultat = runner.invoke(args=["napravi-bazu"])

    assert rezultat.exit_code == 0
    assert client.get("/").status_code == 200
