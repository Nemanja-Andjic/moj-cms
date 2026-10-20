from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext

from .db import get_db

# Probni podaci, da portal odmah izgleda kao pravi sportski portal.
# Svi klubovi i igrači su izmišljeni.

KATEGORIJE = ["Fudbal", "Košarka", "Tenis", "Rukomet"]

# `dana` je prije koliko dana je članak objavljen; None znači da je nacrt.
CLANCI = [
    {
        "kategorija": "Fudbal",
        "dana": 0,
        "naslov": "Zelengora preokretom do vrha tabele",
        "uvod": "FK Zelengora je poslije poluvremena izgubljenog sa 0:2 slavila"
        " protiv Lipovca 3:2 i preuzela prvo mjesto.",
        "tekst": "Gosti iz Lipovca su do odmora vodili sa dva gola razlike,"
        " poslije pogodaka Stefana Marića i Ilije Dragovca. Domaći tim je"
        " djelovao umorno, a navijači su na poluvrijeme ispratili igrače"
        " zviždukom.\n\n"
        "U nastavku je trener Zelengore uveo mladog Luku Ostojića, koji je"
        " za dvadeset minuta postigao dva gola. Pobjedu je u posljednjem"
        " minutu donio kapiten Andrej Kolundžić udarcem sa ivice"
        " šesnaesterca.",
    },
    {
        "kategorija": "Fudbal",
        "dana": 4,
        "naslov": "Vrbica Junior potpisao novog napadača",
        "uvod": "Napadač Damjan Prelić prelazi iz Rudara Bistrice u Vrbicu"
        " Junior i potpisao je ugovor na tri godine.",
        "tekst": "Prelić je prošle sezone bio najbolji strijelac druge lige"
        " sa 17 golova. Uprava Vrbice ga je pratila mjesecima i tvrdi da je"
        " upravo on igrač koji je klubu nedostajao u završnici akcija.\n\n"
        "Novi napadač bi mogao debitovati već u subotu, na gostovanju kod"
        " Zelengore. Kaže da je došao da osvoji titulu i da mu je velika"
        " želja da zaigra pred punim stadionom.",
    },
    {
        "kategorija": "Fudbal",
        "dana": 10,
        "naslov": "Lipovac bez pobjede već pet kola",
        "uvod": "Neriješenim rezultatom 1:1 protiv Gvozdenih Orlova Lipovac je"
        " produžio crnu seriju, a pritisak na trenera raste.",
        "tekst": "Lipovac je poveo već u desetom minutu, ali je bez ideje"
        " igrao ostatak utakmice. Orlovi su izjednačili iz penala, koji je"
        " sigurno izveo Nikola Šarac.\n\n"
        "Trener Milan Vujasin je poslije meča rekao da ekipa ima kvalitet,"
        " ali da joj nedostaje samopouzdanja. Uprava za sada ne razmišlja o"
        " promjeni na klupi.",
    },
    {
        "kategorija": "Košarka",
        "dana": 1,
        "naslov": "Borik slavio u derbiju poslije produžetka",
        "uvod": "KK Borik je pobijedio Javor 91:88 u utakmici koja je"
        " odlučena tek u produžetku.",
        "tekst": "Javor je imao šest poena prednosti na minut do kraja"
        " regularnog dijela, ali su dvije trojke Petra Lazića odvele utakmicu"
        " u produžetak. Dvorana je bila puna do posljednjeg mjesta.\n\n"
        "U produžetku je Borik bio sigurniji sa linije slobodnih bacanja."
        " Najbolji strijelac utakmice bio je centar Javora Ognjen Rakita sa"
        " 27 poena, ali to nije bilo dovoljno za pobjedu.",
    },
    {
        "kategorija": "Košarka",
        "dana": 7,
        "naslov": "Mladi bek Javora pozvan u reprezentaciju",
        "uvod": "Devetnaestogodišnji Vuk Stanišić dobio je prvi poziv u"
        " seniorsku reprezentaciju.",
        "tekst": "Stanišić ove sezone prosječno bilježi 14 poena i šest"
        " asistencija. Selektor je istakao da cijeni njegovu hrabrost i"
        " pregled igre, rijetke za igrača tih godina.\n\n"
        "U klubu su ponosni na svog vaspitanika, koji je u Javoru od"
        " desete godine. Reprezentacija se okuplja naredne sedmice pred dvije"
        " kvalifikacione utakmice.",
    },
    {
        "kategorija": "Košarka",
        "dana": 13,
        "naslov": "Plavi Delfini predstavili novog trenera",
        "uvod": "Iskusni Dragan Merlić preuzima Plave Delfine i obećava"
        " brzu i napadačku košarku.",
        "tekst": "Merlić je ranije vodio nekoliko klubova u regionu i sa dva"
        " osvojio kup. Na predstavljanju je rekao da od igrača traži prije"
        " svega borbenost i disciplinu u odbrani.\n\n"
        "Delfini su prošlu sezonu završili na sedmom mjestu, pa je cilj"
        " uprave plasman u plej-of. Prvi trening pod novim trenerom zakazan"
        " je za ponedjeljak.",
    },
    {
        "kategorija": "Tenis",
        "dana": 2,
        "naslov": "Mila Branković osvojila turnir u Rivelu",
        "uvod": "Mila Branković je u finalu pobijedila Saru Holm 6:4, 7:5 i"
        " stigla do prve titule u karijeri.",
        "tekst": "Finale je trajalo skoro dva sata, a odlučio ga je jedan"
        " brejk u svakom setu. Branković je posebno dobro servirala u"
        " ključnim trenucima i nije dozvolila nijednu brejk loptu u drugom"
        " setu.\n\n"
        "Poslije meča je rekla da je ovo najsrećniji dan u njenoj karijeri i"
        " zahvalila treneru i porodici. Titulom će napredovati dvadesetak"
        " mjesta na svjetskoj listi.",
    },
    {
        "kategorija": "Tenis",
        "dana": 8,
        "naslov": "Teodor Ilinčić ispao u četvrtfinalu",
        "uvod": "Prvi teniser zemlje izgubio je od kvalifikanta Jonasa"
        " Varga poslije tri seta.",
        "tekst": "Ilinčić je dobio prvi set lako, ali je potom imao"
        " problema sa leđima i dva puta tražio medicinsku pauzu. Varg je to"
        " iskoristio i preokrenuo meč.\n\n"
        "Ilinčićev tim kaže da povreda nije ozbiljna, ali da će propustiti"
        " naredni turnir kako bi se potpuno oporavio.",
    },
    {
        "kategorija": "Tenis",
        "dana": None,
        "naslov": "Najava: počinje dvoranska sezona",
        "uvod": "Ove sedmice počinje niz turnira u dvorani, a domaći"
        " teniseri imaju velika očekivanja.",
        "tekst": "Na prvom turniru igraće troje naših tenisera, među kojima i"
        " Mila Branković, koja dolazi poslije prve titule u karijeri.\n\n"
        "Stručnjaci očekuju da brža podloga u dvorani najviše odgovara"
        " Teodoru Ilinčiću, ako se na vrijeme oporavi od povrede.",
    },
    {
        "kategorija": "Rukomet",
        "dana": 5,
        "naslov": "RK Studenac nadigrao Taru u gostima",
        "uvod": "Rukometaši Studenca pobijedili su Taru 31:26 i ostali"
        " neporaženi ove sezone.",
        "tekst": "Utakmica je bila izjednačena do sredine drugog"
        " poluvremena, kada je golman Studenca Bojan Kecman odbranio tri"
        " sedmerca zaredom. Poslije toga gosti su brzo odmakli na pet golova"
        " razlike.\n\n"
        "Najefikasniji je bio krilni igrač Studenca Marko Jelić sa devet"
        " golova. Tara ostaje na četvrtom mjestu, sa dvije pobjede manje od"
        " vodećeg Studenca.",
    },
    {
        "kategorija": "Rukomet",
        "dana": 11,
        "naslov": "Kup: Crveni Jastrebovi u polufinalu",
        "uvod": "Crveni Jastrebovi su pobjedom nad Ravnim Poljem 28:24"
        " izborili plasman u polufinale kupa.",
        "tekst": "Jastrebovi su vodili od početka do kraja, a najveća"
        " prednost bila je osam golova. Trener je u završnici pružio priliku"
        " i mlađim igračima.\n\n"
        "U polufinalu ih čeka Studenac, koji je ove sezone najbolji tim"
        " lige. Utakmica se igra za dvije sedmice.",
    },
    {
        "kategorija": "Rukomet",
        "dana": None,
        "naslov": "Intervju sa kapitenom Tare Draganom Ćulumom",
        "uvod": "Kapiten Tare govori o lošem startu sezone i planovima za"
        " nastavak prvenstva.",
        "tekst": "Ćulum kaže da ekipa nije zadovoljna rezultatima, ali da u"
        " svlačionici vlada dobra atmosfera. Smatra da je tim izgubio"
        " nekoliko utakmica zbog sitnih grešaka u završnici.\n\n"
        "Cilj Tare ostaje plasman među prva tri tima. Ćulum vjeruje da će"
        " povratak povrijeđenih igrača donijeti preokret već u narednim"
        " kolima.",
    },
]


def baza_je_prazna():
    """Da li u bazi nema nijedne kategorije ni članka (admin se ne broji)."""
    baza = get_db()
    ima_kategorija = baza.execute("SELECT 1 FROM kategorija LIMIT 1").fetchone()
    ima_clanaka = baza.execute("SELECT 1 FROM clanak LIMIT 1").fetchone()
    return ima_kategorija is None and ima_clanaka is None


def vrijeme_za_bazu(dana):
    """Vrijeme prije `dana` dana, u obliku u kojem ga čuva baza (po UTC-u).

    Dva sata ranije, da čak i današnji članak bude objavljen u prošlosti.
    """
    vrijeme = datetime.now(timezone.utc) - timedelta(days=dana, hours=2)
    return vrijeme.strftime("%Y-%m-%d %H:%M:%S")


def ubaci_probne_podatke():
    """Ubacuje probne kategorije i članke u bazu."""
    baza = get_db()
    id_kategorije = {}
    for ime in KATEGORIJE:
        kursor = baza.execute(
            "INSERT INTO kategorija (ime, ime_za_poredjenje) VALUES (?, ?)",
            (ime, ime.casefold()),
        )
        id_kategorije[ime] = kursor.lastrowid

    for clanak in CLANCI:
        if clanak["dana"] is None:
            stanje, datum_objave = "nacrt", None
            napravljen = vrijeme_za_bazu(0)
        else:
            stanje = "objavljen"
            # Objavljen članak je napravljen isti dan kad je objavljen.
            datum_objave = napravljen = vrijeme_za_bazu(clanak["dana"])
        baza.execute(
            "INSERT INTO clanak (naslov, uvod, tekst, kategorija_id, stanje,"
            " napravljen, datum_objave) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                clanak["naslov"],
                clanak["uvod"],
                clanak["tekst"],
                id_kategorije[clanak["kategorija"]],
                stanje,
                napravljen,
                datum_objave,
            ),
        )
    baza.commit()


@click.command("ubaci-probne-podatke")
@with_appcontext
def ubaci_probne_podatke_komanda():
    """Ubacuje probne kategorije i članke, ali samo u praznu bazu."""
    if not baza_je_prazna():
        click.echo("Baza nije prazna, probni podaci nisu ubačeni.")
        return
    ubaci_probne_podatke()
    click.echo(
        f"Probni podaci su ubačeni: {len(KATEGORIJE)} kategorije"
        f" i {len(CLANCI)} članaka."
    )
