-- Šema baze za Sport Portal. "IF NOT EXISTS" znači da ponovno pokretanje
-- komande `napravi-bazu` ne briše postojeće podatke.

-- Admin: najviše jedan red (id je uvijek 1).
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    korisnicko_ime TEXT NOT NULL,
    hash_lozinke TEXT NOT NULL
);

-- Kategorija: `ime` je onako kako ga admin napiše, a `ime_za_poredjenje`
-- je isto ime malim slovima (Python casefold, radi i za č, ć, š, ž, đ).
-- Baza ne dozvoljava dva ista `ime_za_poredjenje`, pa ne mogu postojati
-- "Fudbal" i "FUDBAL" u isto vrijeme.
CREATE TABLE IF NOT EXISTS kategorija (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ime TEXT NOT NULL,
    ime_za_poredjenje TEXT NOT NULL UNIQUE
);

-- Članak: uvijek pripada jednoj kategoriji. Kategorija koja ima članke
-- ne može se obrisati (strani ključ). `datum_objave` je prazan dok članak
-- nije prvi put objavljen.
CREATE TABLE IF NOT EXISTS clanak (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naslov TEXT NOT NULL,
    uvod TEXT NOT NULL,
    tekst TEXT NOT NULL,
    kategorija_id INTEGER NOT NULL REFERENCES kategorija (id),
    stanje TEXT NOT NULL DEFAULT 'nacrt' CHECK (stanje IN ('nacrt', 'objavljen')),
    napravljen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datum_objave TEXT
);
