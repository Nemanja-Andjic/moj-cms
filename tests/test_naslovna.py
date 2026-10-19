from sportportal import create_app


def test_naslovna_prikazuje_ime_portala_kao_link_na_naslovnu(client):
    odgovor = client.get("/")

    assert odgovor.status_code == 200
    html = odgovor.get_data(as_text=True)
    assert '<a href="/"' in html
    assert "Sport Portal" in html


def test_prazna_naslovna_kaze_da_jos_nema_clanaka(client):
    odgovor = client.get("/")

    assert "Još nema objavljenih članaka." in odgovor.get_data(as_text=True)


def test_ime_portala_dolazi_iz_podesavanja(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
        "SECRET_KEY": "test",
        "IME_PORTALA": "Moj Portal",
    })
    app.test_cli_runner().invoke(args=["napravi-bazu"])

    html = app.test_client().get("/").get_data(as_text=True)

    assert "Moj Portal" in html
    assert "Sport Portal" not in html
