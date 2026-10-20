# Sport Portal

Sport Portal je mali CMS (sistem za upravljanje sadržajem) za sportski portal. Repo i folder projekta zovu se `moj-cms`. Admin u admin panelu piše i objavljuje članke, a posjetioci ih čitaju na javnom sajtu.

Šta portal može:

- **Javni sajt**: naslovna stranica sa najnovijim objavljenim člancima, stranica svakog članka i filtriranje članaka po kategoriji.
- **Admin panel** (samo za prijavljenog admina):
  - dodavanje, preimenovanje i brisanje kategorija (kategorija koja ima članke ne može se obrisati),
  - pisanje, izmjena i brisanje članaka,
  - objavljivanje članka i povlačenje objavljenog članka nazad u nacrt.
- Svaki novi članak počinje kao **nacrt** koji posjetioci ne vide, dok ga admin ne **objavi**.

Pojmovi koje projekat koristi (članak, nacrt, objavljen, kategorija...) objašnjeni su u [`GLOSSARY.md`](GLOSSARY.md). Zašto je portal napravljen u Pythonu, Flask-u i SQLite-u piše u [ADR-0001](docs/adr/0001-python-flask-sqlite.md).

## Potrebni programi

- **Python 3.14 ili noviji** sa [python.org](https://www.python.org/downloads/). Testovi na GitHub-u se pokreću na Python-u 3.14, pa je to najniža verzija za koju se zna da radi. Pri instalaciji označi kvadratić **„Add python.exe to PATH"**.
- **Git** sa [git-scm.com](https://git-scm.com/download/win). Uz njega dolazi i **Git Bash**.

Da provjeriš da je sve instalirano, otvori PowerShell ili Git Bash i ukucaj:

```
python --version
git --version
```

Obje komande treba da ispišu broj verzije.

## Instalacija

Sve komande u nastavku se kucaju u terminalu. Uz svaki korak gdje se komande razlikuju data je verzija za **Git Bash** i za **PowerShell**; tamo gdje je data samo jedna, radi u oba.

### 1. Kloniranje repoa

Kloniranje znači skidanje projekta sa GitHub-a na tvoj računar:

```
git clone https://github.com/Nemanja-Andjic/moj-cms.git
cd moj-cms
```

Sve ostale komande pokreći iz foldera `moj-cms`.

### 2. Virtuelno okruženje

Virtuelno okruženje je poseban folder (`.venv`) u koji se instaliraju biblioteke samo za ovaj projekat, da se ne miješaju sa drugim Python projektima na računaru. Pravi se jednom:

```
python -m venv .venv
```

Zatim ga treba **aktivirati**, i to svaki put kad otvoriš novi terminal:

Git Bash:

```bash
source .venv/Scripts/activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Kad je okruženje aktivno, na početku reda u terminalu piše `(.venv)`.

> Ako PowerShell javi da je pokretanje skripti zabranjeno („running scripts is disabled on this system"), pokreni jednom ovu komandu pa probaj ponovo:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 3. Instalacija zavisnosti

Zavisnosti su biblioteke koje projekat koristi (Flask, waitress i pytest). Spisak je u `requirements.txt`. Sa aktivnim virtuelnim okruženjem pokreni:

```
pip install -r requirements.txt
```

## Baza, admin i probni podaci

Podaci portala čuvaju se u SQLite bazi, u fajlu `instance/sportportal.sqlite`. Folder `instance` se ne stavlja na GitHub, pa ga svako pravi kod sebe.

### Pravljenje baze

```
flask --app sportportal napravi-bazu
```

Komanda pravi tabele. Ako baza već postoji, postojeći podaci ostaju netaknuti.

### Pravljenje admin naloga

```
flask --app sportportal napravi-admina
```

Komanda pita za korisničko ime i dva puta za lozinku. Dok kucaš lozinku, ništa se ne prikazuje na ekranu; to je normalno. U bazu se ne upisuje sama lozinka, nego samo njen hash (poseban zapis iz kojeg se lozinka ne može vratiti, ali se može provjeriti da li je unesena lozinka tačna).

**Promjena lozinke:** pokreni istu komandu ponovo. Pošto admin već postoji, komanda neće pitati za korisničko ime, nego samo za novu lozinku.

### Ubacivanje probnih podataka (nije obavezno)

Da portal ne bi bio prazan dok ga isprobavaš, možeš ubaciti nekoliko probnih kategorija i članaka:

```
flask --app sportportal ubaci-probne-podatke
```

Probni podaci se ubacuju samo u praznu bazu (bez ijedne kategorije i članka), da se ne bi pomiješali sa pravim sadržajem.

## Tajni ključ (SECRET_KEY)

Flask tajnim ključem potpisuje kolačić (cookie) kojim pamti da je admin prijavljen. Ako neko zna ključ, može da se predstavi kao prijavljen admin. U kodu je zato samo probni ključ `"dev"`, koji je dovoljan za razvoj, ali za pravo korištenje treba postaviti svoj.

1. Napravi nasumičan ključ:

   ```
   python -c "import secrets; print(secrets.token_hex())"
   ```

   Komanda ispiše dug niz slova i cifara, npr. `3f9a1c...`.

2. U folderu `instance` napravi fajl `config.py` sa jednim redom, u koji umjesto tačkica staviš ključ iz prvog koraka:

   ```python
   SECRET_KEY = "..."
   ```

   Ako fajl praviš u Notepad-u, pri čuvanju u polju „Save as type" izaberi **All files (\*.\*)**. Inače Notepad sačuva fajl kao `config.py.txt`, a portal takav fajl neće pročitati i neće ti javiti grešku.

Portal sam čita `instance/config.py` pri pokretanju. Ključ nikome ne šalji i ne stavljaj ga na GitHub (folder `instance` je već u `.gitignore`). Ako promijeniš ključ, admin će morati ponovo da se prijavi.

## Pokretanje

Portal se može pokrenuti na dva načina.

### Razvojni način (dok se piše kod)

```
flask --app sportportal run --debug
```

U razvojnom načinu Flask sam ponovo učitava kod čim sačuvaš izmjenu, a kad se desi greška, u pregledaču prikazuje detalje o njoj. Zato se ovaj način koristi **samo** dok se radi na kodu, nikad za normalno korištenje.

- Sajt: <http://127.0.0.1:5000/>
- Admin panel: <http://127.0.0.1:5000/admin/>

### Lokalni server preko waitress-a (za normalno korištenje)

[Waitress](https://docs.pylonsproject.org/projects/waitress/) je pravi web server za Python aplikacije koji radi i na Windows-u. Ne prikazuje detalje grešaka i ne učitava kod ponovo, pa je pravi izbor kad se portal koristi, a ne razvija.

```
waitress-serve --listen=127.0.0.1:8080 --call sportportal:create_app
```

Kad server krene, ispiše `Serving on http://127.0.0.1:8080`.

- Sajt: <http://127.0.0.1:8080/>
- Admin panel: <http://127.0.0.1:8080/admin/>

Server (bilo koji od ova dva) se zaustavlja sa **Ctrl+C** u terminalu.

## Testovi

Testovi su u folderu `tests` i pišu se sa [pytest-om](https://docs.pytest.org/). Pokreću se ovako:

```
pytest
```

Testovi prave svoju privremenu bazu, pa ne diraju tvoje podatke.

## Kako je projekat rađen

- **GitHub issue-i i PR-ovi:** rad je organizovan kroz male zadatke u [GitHub Issues](https://github.com/Nemanja-Andjic/moj-cms/issues), posebne grane i pull request-ove (PR), pa se u istoriji vidi šta je kad i zašto urađeno.
- **Matt Pocock skillovi:** projekat je pravljen uz Claude Code i [skillove Matt-a Pocock-a](https://github.com/mattpocock/skills): planiranje i rječnik pojmova (`GLOSSARY.md`), važne odluke zapisane kao ADR-ovi (kratki zapisi o tome šta je odlučeno i zašto, u `docs/adr/`), razbijanje plana na issue-e, pisanje koda tako da se prvo napiše test pa tek onda kod (TDD) i pregled koda prije spajanja. Uputstva za agente su u `docs/agents/`.
- **GitHub Actions:** na svaki pull request GitHub sam pokrene sve testove na Linux-u (`.github/workflows/testovi.yml`), pa se odmah vidi ako izmjena nešto pokvari.

Kod je pisan uz Claude Code, a ja sam vodio planiranje, donosio odluke, provjeravao urađeno i radio na GitHub-u (issue-i, grane, commit-i i PR-ovi).

## About (English)

Sport Portal is a small content management system for a sports news site, built with Python, Flask and SQLite. An admin writes articles in an admin panel, sorts them into categories and publishes them, while visitors read published articles on the public site and filter them by category. It runs locally on Windows, either in Flask's development mode or on a local server with waitress. The work was organized through GitHub issues, branches and pull requests, with tests running on GitHub Actions. The code was written with Claude Code, while I led the planning, decisions, review and GitHub work.
