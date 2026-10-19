# Python + Flask + SQLite, stranice se prave na serveru

Sport Portal pravimo u Pythonu sa Flask-om, podatke čuvamo u SQLite bazi (jedan fajl na disku), a HTML stranice pravimo na serveru pomoću Jinja šablona, bez JavaScript frameworka. Razlog: projekat mora raditi lokalno na Windows-u bez instaliranja posebnog servera baze, autor je početnik, a rok za prvu verziju je kratak. Python je već bio instaliran, a Flask ima najmanje „magije" i najlakše se čita.

## Razmotrene opcije

- **Node.js + Express + SQLite + EJS**: jednako jednostavno i Node je takođe bio instaliran, ali je Python odabran kao čitljiviji za početnika.
- **PHP**: nije instaliran na računaru.
- **Server baze (PostgreSQL, MySQL)**: zahtijeva posebnu instalaciju i pokretanje; SQLite je dovoljan za jednog admina i lokalni rad.
- **React ili sličan frontend framework**: dodaje drugi projekat i build korak, a portalu ne treba.

## Posljedice

SQLite je dovoljan dok portal radi lokalno sa jednim adminom. Ako portal jednog dana bude javno na internetu sa mnogo istovremenih izmjena, prelazak na server baze bi tražio izmjene u kodu koji radi sa bazom.
