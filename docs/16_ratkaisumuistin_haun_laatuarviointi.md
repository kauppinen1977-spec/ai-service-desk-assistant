# Ratkaisumuistin haun laatumittaus

Päiväys: 24.10.2026. Arviointi tehtiin offline-tilassa paikallisella
upotusmallilla ja erillisillä synteettisillä tietokannoilla. Käyttäjän
`data/solutions.sqlite3`-tietokantaa ei avattu arvioinnin tietokannaksi.
Ulkoisia API-kutsuja ei tehty. PoC:n hakua, hakurajaa 0,43 tai tulosrajaa
3 ei muutettu.

## Aineisto ja vertailuasetelma

Käytössä oli `tests/fixtures/memory_environment_cases.json`-aineiston kaksi
erillistä kyselyjakoa: 19 kehitystapausta sekä 17 loppuarvioinnin tapausta.
Molemmissa tehtiin parivertailu samalla kuvitteellisella ratkaisuaineistolla
ja samalla hakukoodilla. Ennen-mittauksessa kyselyn rakenteisia
käyttöjärjestelmä-, tuote- ja versiorajauksia ei annettu haulle. Jälkeen-
mittauksessa käytettiin kuhunkin tapaukseen ennalta kirjoitettuja,
valinnaisia rakenteisia rajauksia. Vapaa ongelmakuvaus ja aineisto pysyivät
ennallaan. Hakurajaa tai aineiston laajuutta ei muutettu.

Loppujako oli lukittu kehitysmuutosten mittaamisen ajaksi, mutta sen tapaukset
on laatinut sama kehitystiimi ja se käyttää samaa synteettistä aineistoa.
Tulosta käsitellään kehitysjoukosta erillisenä tapausjakona, ei riippumattoman
arvioijan tai todellisen käyttödatan validointina. Sama arvioija määritteli
odotetut vastaukset.

## Tulokset

| Mittari | Kehitys: ilman rajauksia | Kehitys: rajauksilla | Loppu: ilman rajauksia | Loppu: rajauksilla |
|---|---:|---:|---:|---:|
| Tapauksia | 19 | 19 | 17 | 17 |
| Sopiva ratkaisu, oikea ensimmäinen | 10/11 | 11/11 | 8/10 | 8/10 |
| Sopiva ratkaisu top-3:ssa | 11/11 | 11/11 | 10/10 | 10/10 |
| Väärä osuma top-3:ssa | 35 | 14 | 32 | 21 |
| Tapauksia, joissa vähintään yksi väärä osuma | 18/19 | 8/19 | 15/17 | 11/17 |
| Ei sopivaa ratkaisua, mutta osumia | 7/8 | 3/8 | 6/7 | 4/7 |
| Väärä osuma ilmoitettujen tietojen perusteella yhteensopivaksi merkittynä | 0 | 2 | 0 | 3 |

Kehitysjoukossa valinnaiset rakenteiset rajaukset paransivat ensimmäisen
osuman oikeellisuutta yhdellä tapauksella ja vähensivät väärien top-3-osumien
määrää 21:llä. Yhtäkään odotettua ratkaisua ei kadonnut. Erillisessä
loppujaossa top-3-löytyvyys säilyi, ensimmäisen osuman oikeellisuus ei
muuttunut, väärät osumat vähenivät 11:llä ja väärää osumaa sisältäneitä
tapauksia oli neljä vähemmän.

Kehitys- ja loppumittausten erot ovat heikennystuloksia, jotka on säilytetty
raportissa: rajaukset eivät nostaneet loppujoukon ensimmäisen osuman
osumatarkkuutta, ja molemmissa jaoissa osa vääristä osumista luokittui
puutteellisten tietojen sijasta yhteensopivaksi. Tällainen luokitus kertoo
vain annettujen rakenteisten kenttien yhtenevyydestä, ei oireen tai
ratkaisun sopivuudesta.

## Virheiden syyt ja päätös

Jäljelle jäävät virheet painottuvat tapauksiin, joissa tietokannassa ei ole
ratkaisua mutta kysely jakaa tuotteen, virhekoodin tai yleisen oirekielen
vahvistetun ratkaisun kanssa. Vektorihaku tunnistaa tekstuaalisen
samankaltaisuuden, ei sitä, onko ehdotettu korjaus kokeiltu juuri kuvatulle
oireelle tai organisaatiolle. Rakenteiset rajaukset auttavat vain käyttäjän
ilmoittamissa kentissä; ne eivät tunnista organisaatiota eivätkä ratkaise
saman ympäristön eri oireita. Vapaa ympäristökuvaus ja rakenteiset kentät
pysyvät valinnaisina.

Pisteiden yhdistämiseen tai uudelleenjärjestykseen ei otettu muutosta
oletuskäyttöön. Mittaus ei anna näyttöä yleisestä oireiden erottelusta, ja
pelkkä ympäristöyhteensopivuuden nostaminen voisi asettaa väärän mutta
kentiltään yhteensopivan ratkaisun oikean, puutteellisemmin tallennetun
tapauksen edelle. Hakuraja ja enintään kolmen tuloksen raja pysyivät
ennallaan. Nykyinen käyttöliittymä varoittaa, etteivät osumat tai pisteet
takaa soveltuvuutta.

Toteutettu tarkistus ei siis sisältänyt uutta hakualgoritmin muutosta;
se vahvisti jo käytössä olevien valinnaisten ympäristörajausten vaikutuksen
ja kirjasi rajat. Yleistettävä uudelleenjärjestys edellyttää laajempaa,
riippumattomasti annotoitua arviointia, jossa on samaa ympäristöä jakavia
eri oireita ja riittävästi tapauksia, joissa oikeaa ratkaisua ei ole.

Raportin ajot:

- Kehitys: `data/environment-evaluation/development-20261024T160511116349Z/`
- Loppu: `data/environment-evaluation/final-20261024T160959822578Z/`

Molemmat käyttivät offline-mallia. Erillisen Python-regressioajon tulos oli
158/158 hyväksyttyä testiä; kolme kirjoittavaa tai muuhun aihealueeseen
kuuluvaa hakutestiä jätettiin pois kyseisestä rajatusta ajosta. Virheellinen
ensimmäinen testikomennon moduuliluettelo tunnistettiin (kaksi puuttuvaa
testimoduulia), ja korjattu komento suoritettiin onnistuneesti.
