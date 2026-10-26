# Ratkaisumuistin erillisen palautuskopion ensikäyttökoe

Päiväys: 26.10.2026. **Tulos: 11/11 lopullisen ajon tarkistuskohtaa hyväksytty.**
Uuteen virtuaaliympäristöön ja tyhjään omaan tietokantaan perustuva
avaimeton sanahakuketju toimi. Erillinen vektorikoe onnistui olemassa olevilla
kehitysympäristön riippuvuuksilla ja mallivälimuistilla; se ei ollut puhdas
vektorihaun asennuskoe. Paketteja tai malleja ei ladattu tätä koetta varten.

## Lähdeversio ja palautuskopio

- Lähde: `C:\AI projektityö\AI_Service_Desk_ratkaisumuisti`.
- Haara: `kehitys/ratkaisumuisti`.
- Lähdecommit: `9d2d39719b8b6d4c4c09aeca38785f3effc74162`.
- Testin työhakemisto: `data/first-use-20261026/` lähdeprojektin alla.
- Ajettu kopio: `data/first-use-20261026/release/`.
- Lopullinen lähdetiedostojen palautuskopio: `data/first-use-20261026/package/`.
  Siinä on 58 tiedostoa ja lisäksi `SOURCE_MANIFEST.json`; ei ympäristöä tai tietokantaa.
- Kopion tietokanta: `release/data/solutions.sqlite3` testihakemiston alla.
- Testiosoite: `http://127.0.0.1:8513/memory`. Portin vapaus tarkistettiin
  ennen käynnistystä sitomalla siihen hetkeksi paikallinen testikuuntelija.

Kopio muodostettiin nimenomaisesta tiedostoluettelosta. Ajonaikaiset Python-
ja HTML-tiedostot, molemmat requirements-tiedostot, Gitin seuraamat julkiset
`knowledge`-tiedostot manifesteineen, README, `.gitattributes`, `.gitignore`
ja dokumentit otettiin mukaan. Testihakemisto jätettiin lopullisesta
ajonaikaisesta kopiosta pois. Yksityisiä arviointiaineistoja ei kopioitu.
`.env.example` jätettiin myös pois; sen puuttuminen ei estä avaimetonta käyttöä.

Alkuperäiseen kopioon sisältyneet commitoimattomat muutokset:

| Lähtötilan tiedostot | Sisältyminen |
|---|---|
| `.gitignore`, `docs/10_poc_valitavoite_2026-10-19.md`, `docs/12_solution_memory.md` | Työpuun nykyinen sisältö kopioitiin, ei pelkkää HEAD-versiota |
| `docs/16_ratkaisumuistin_haun_laatuarviointi.md`, `docs/17_ratkaisumuistin_arviointiaineisto.md`, `docs/18_ratkaisumuistin_arviointipohja.md` | Seuraamattomat paikalliset dokumentit kopioitiin |
| `docs/19_poc_valmiustilanne.md` | Kopioitiin, vaikka lähtötilan `.gitignore` ohitti tiedoston |

Tässä työssä korjatut ohjeet ja sallintalista siirrettiin testikopioon ennen
korjatun käynnistysohjeen koetta: `.gitignore`, README, dokumentit 12 ja 13
sekä uusi asennusohje 21. Testien jälkeen kopioon päivitettiin myös tämä
raportti ja tilannekatsauksen 19 täydennys. Ajonaikainen ohjelmakoodi pysyi
samana koko kokeen ajan. Lopullinen `package-manifest.json` testihakemistossa
luettelee mukaan hyväksytyt tiedostot ja SHA-256-tarkistussummat. Kopion
`SOURCE_MANIFEST.json` sisältää saman version ja tiedostoluettelon.

Kopioon ei otettu `.git`-hakemistoa, API-avaimia tai ympäristötiedostoja,
käyttäjän tietokantaa, olemassa olevaa virtuaaliympäristöä, Python-runtimea,
mallivälimuisteja, vektorihakuvälimuisteja tai yksityisiä aineistoja.
Kokeessa syntyneet `.venv` ja `data` kuuluvat testityöhakemistoon; ne eivät
kuulu manifestin jakelutiedostoihin eikä niitä pidä pakata palautukseen.

## Ympäristö ja puhtauden rajaus

| Osa | Todettu ympäristö |
|---|---|
| Käyttöjärjestelmä | Windows 11 Home, 64 bit, versio 10.0.26300 |
| Uuden kopion Python | Järjestelmään jo asennettu CPython 3.13.9, MSC v.1944, 64 bit |
| Uusi virtuaaliympäristö | Luotu `py -3.13 -m venv` -komennolla; `include-system-site-packages = false` |
| Uuden ympäristön paketit | Vain venvin mukana tullut pip 25.2; ei sentence-transformersia tai sovelluksen lisäpaketteja |
| Selain | Asennettu Chrome 155.0.8059.85, headless, oma tilapäinen profiili, 1280 × 900 |
| Testiajuri | Node.js v24.22.0, paikallinen Chrome DevTools -rajapinta |
| Sanahaun verkkoriippuvuudet | Ei paketti- tai mallilatauksia, ei API-avainta |

Tämä on erillisen palautuskopion ja uuden Python-virtuaaliympäristön
ensikäyttökoe samalla Windows-koneella. Se ei ole uuden Windows-koneen,
Pythonin asennuksen tai toisen ihmisen itsenäisen ohjeenkäytön testi.
Selaimen ja Pythonin olemassaoloa hyödynnettiin. Node.js tarvittiin vain
automaatioon; sovellus ei tarvitse sitä.

Tavallinen selainohjaustyökalu ei alustunut: `node_repl kernel exited
unexpectedly`, tarkempi virhe `windows sandbox failed: helper_unknown_error:
setup refresh had errors`. Myös computer-use-alustus epäonnistui. Siksi
käytettiin asennettua Chromea erillisessä headless-profiilissa. Käyttäjän
omaa selainvälilehteä ei ohjattu. Tämä on automatisoitu oikean selaimen koe,
ei käyttäjän ilmoittama manuaalinen selainkoe.

## Komennot ja suoritustapa

Ensin tarkistettiin Gitin tila ja luettiin dokumentti 19. Lähteen tila ja
tiedostojen tarkistussummat tallennettiin paikalliseen `source-manifest.json`-
tiedostoon ja aiempi diff tiedostoon `original-changes.diff`. Kopiointi tehtiin
PowerShellin `Copy-Item -LiteralPath` -komennolla tiedostoluettelon perusteella,
ei koko projektihakemiston rekursiivisena kopiona.

Kopion oman ympäristön luonti lähdeprojektin juuresta:

```powershell
py -3.13 --version
py -3.13 -m venv .\data\first-use-20261026\release\.venv
& .\data\first-use-20261026\release\.venv\Scripts\python.exe --version
```

Korjatun [asennusohjeen](21_ratkaisumuistin_asennus.md) käynnistyskomento
kopion juuresta:

```powershell
& .\.venv\Scripts\python.exe -B -c "import os,runpy; [os.environ.pop(k,None) for k in ('OPENAI_API_KEY','OPENAI_MODEL')]; os.environ['DESK_MEMORY_DB']=os.path.abspath('data/solutions.sqlite3'); os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1'); runpy.run_path('app.py',run_name='__main__')" --corpus batch1 --port 8513
```

Testiajuri luki `-c`-sisällön suoraan kopion asennusohjeesta ja käynnisti
Pythonin samoilla argumenteilla kopion juurihakemistossa. Lisäksi ajuri
poisti testilapsen perityistä asetuksista API-avaimen, malliasetuksen,
tietokantapolun ja Pythonin hakupolkujen ohitukset. Se ei muuttanut käyttäjän
pysyviä ympäristömuuttujia. Avaimen arvoa ei luettu raporttiin.

Selainajon komento lähdeprojektin juuresta:

```powershell
node .\data\first-use-20261026\first-use.cjs
```

Ajuri käynnisti ja pysäytti omat palvelimensa, avasi Chromen ja täytti
lomakkeet sekä painoi painikkeita. Palvelimen HTML, HTTP-toiminnot, SQLite-
tallennus ja haut olivat oikeita; vastauksia ei korvattu. Selaimen pyynnöistä
sallittiin vain testipalvelimen `/memory`, `/health` ja kokeen tarvitsemat
paikalliset `list`, `search`, `save`, `verify` ja `api-status` -toiminnot.
Ehdotus- ja avainasetusten muutospyynnöt sekä ulkoiset sivupyynnöt estettiin.
Faviconin esto on odotettu, ei sovelluksen toiminnallinen virhe.

## Testidata ja lopulliset tulokset

Otsikko oli `ENSIKOE20261026 harjoitusmuistio`, ongelma kuvitteellisen
harjoitusmuistion TESTI-tekstin löytäminen ja ympäristö erillinen ensikäyttökoe.
Rakenteiset tiedot: Windows 11, Harjoitusmuistio, 1.0. Ratkaisukentässä
ilmoitettiin nimenomaisesti, että tietue on vain tallennus- ja vahvistusketjun
testidata, ei teknisesti validoitu IT-korjaus. Vahvistajan testitunniste oli
`ENSIKOE-automaatiotesti`. Vahvistuskysymys hyväksyttiin automatisoidusti
tilasiirtymän koetta varten. Tätä ei esitetä ihmisen tekemänä IT-korjauksen
teknisenä validointina.

Hakuteksti oli `ENSIKOE20261026 harjoitusmuistion TESTI teksti`.
Hakusuodattimet jätettiin tyhjiksi. Siksi löytynyt tietue kuului puuttuvien
hakurajausten vuoksi tarkistettaviin ehdokkaisiin, vaikka tietueen omat
rakenteiset tiedot olivat täytettyinä.

| # | Tarkistus | Tulos |
|---|---|---|
| 1 | Dokumentoitu käynnistys ilman API-avainta | Hyväksytty: `/health` ilmoitti `batch1` ja `api_key_available=false` |
| 2 | Ratkaisumuistin avautuminen oikeassa Chromessa | Hyväksytty: `/memory` avautui kopion palvelimelta |
| 3 | Tyhjä oma tietokanta | Hyväksytty: tietokantatiedostoa ei ollut ennen käynnistystä; ensimmäiset toiminnot loivat sen ja näyttivät tyhjän muistin |
| 4 | Luonnoksen tallentaminen selaimesta | Hyväksytty: oikea `save`-toiminto ja luonnoksen tarkistusnäkymä |
| 5 | Luonnoksen puuttuminen sanahausta | Hyväksytty: testitietueen otsikko ei ollut tuloksissa |
| 6 | Vahvistus testitunnisteella | Hyväksytty: palvelin tallensi vahvistuksen erillisen vahvistustoiminnon jälkeen |
| 7 | Vahvistetun tietueen sanahaku | Hyväksytty: testitietue löytyi |
| 8 | Palvelimen pysäytys, uusi prosessi ja selaimen päivitys | Hyväksytty: tietue löytyi edelleen; sisältö ja vahvistajan tunniste säilyivät |
| 9 | Vektorihaku uudessa ympäristössä ilman paketteja | Hyväksytty rajauksen tarkistus: `search_unavailable`, ei mallilatausta |
| 10 | Sanahaku vektoririippuvuusvirheen jälkeen | Hyväksytty: sama vahvistettu tietue löytyi |
| 11 | Erillinen vektorihaku kehitysympäristön paketeilla | Hyväksytty: paikallinen malli löysi saman tietueen; ei puhdas asennus |

Lopullisen ajon JavaScript-poikkeuksia oli 0. Lopuksi vain testitietokantaan tehty
lukutilainen tarkistus antoi SQLite-eheyden tulokseksi `ok` sekä yhden
`verified`-tietueen revisionumerolla 2 ja odotetulla testivahvistajalla.
Tämä ei ole koko regressiotestisarjan uusinta. Yhden testitietueen löytyminen osoittaa
käynnistys-, tallennus- ja hakuketjun toimintaa tässä asetelmassa. Se ei
mittaa hakutarkkuutta tai ratkaisujen teknistä oikeellisuutta.

## Erillinen vektorikoe ja käytetyt välimuistit

Uuden `.venv`-ympäristön sanahakutestissä ei ollut vektoririippuvuuksia.
Erillisessä kokeessa sama kopion `app.py` käynnistettiin lähdeprojektin
olemassa olevalla `.venv\Scripts\python.exe`-tulkilla, edelleen kopion
työhakemistossa, kopion tietokannalla ja portissa 8513. Kopion uusi ympäristö
ei saanut näitä paketteja eikä `--system-site-packages`-asetusta.

Käytetyt valmiit paketit: CPython 3.13.15, sentence-transformers 5.7.0,
torch 2.14.1+cpu, transformers 5.20.2, numpy 2.5.4 ja huggingface-hub 2.3.0.

```text
HF_HOME=C:\AI projektityö\AI_Service_Desk_ratkaisumuisti\.model-cache
HF_HUB_CACHE=<HF_HOME>\hub
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_HUB_DISABLE_TELEMETRY=1
```

Malli: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
Paikallisen Hugging Face -välimuistin snapshot:
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Se sijaitsi hakemistossa
`.model-cache/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/`.
Mukana oli ennestään 470 641 600 tavun `model.safetensors` sekä tokenizer- ja
asetustiedostot. Mallia ei kopioitu palautuskopioon eikä ladattu verkosta.
Muodostettu testitietueiden upotusvälimuisti oli vain
`release/data/solutions.vectors.json`. Käyttäjän omaa ratkaisu- tai
runbook-vektorivälimuistia ei käytetty tietueiden hakemistona.

Lisäksi ajettiin mallin latauksen erillinen vianrajaus:

```powershell
& .\.venv\Scripts\python.exe -B .\data\first-use-20261026\vector-probe.py
```

Se esti Pythonin `socket.connect`-yhteydet auditointikoukulla ja latasi saman
paikallisen mallin. Lataus ja ensimmäinen testiupotus valmistuivat 65,28
sekunnissa; upotuksen koko oli 384. Tämä esilataus ja käyttöjärjestelmän
tiedostovälimuisti saattoivat nopeuttaa lopullista selainajoa. Tulosta ei
pidä kutsua puhtaaksi tai kylmäksi vektorihaun ensiasennukseksi.

Pip-asennuksia: 0. Mallilatauksia verkosta: 0. OpenAI- tai muita ulkoisia
API-kutsuja: 0. Offline-proben verkkoyhteydet oli estetty; varsinaisen
sovelluskokeen mallikirjastoille asetettiin yllä olevat offline-asetukset.
Offline-asetukset eivät ole yleinen käyttöjärjestelmätason palomuuri.

## Löydetyt puutteet, korjaukset ja uusinnat

1. **Alkuperäinen lyhyt käynnistysohje ei riittänyt uudessa kansiossa.**
   Dokumentin 12 komento ei löytänyt `.venv\Scripts\python.exe`-tiedostoa,
   koska ohje oletti ympäristön valmiiksi. Lisättiin asennusohje 21, jossa on
   Python-edellytys, ympäristön luonti, oma tietokanta, avaimeton käynnistys,
   portti, `/memory` ja uudelleenkäynnistys. README sekä dokumentit 12 ja 13
   linkittävät siihen. Korjatun ohjeen vaihe toistettiin onnistuneesti.
2. **Portit ja versio-ohjeet olivat hajallaan.** Uusi ohje yksilöi nykyisen
   paikallisen haaran ja testikopion portin 8513. Tekijän vanhan portin 8502
   käyttöä ei tarvita. GitHub-versioiden eroa ei poistettu dokumentoinnista.
3. **Vektorivirhe mainitsee puuttuvan `asenna_vektorihaku.bat`-tiedoston.**
   Asennusohje ohjaa käyttämään palautuksessa olevia README:n pip-/Python-
   komentoja. Ohjelman virhetekstiä ei muutettu tässä työssä.
4. **Ensimmäisen testiajurin sammutustarkistus epäonnistui.** Windowsin
   lopetussignaali täytti `signalCode`-kentän, mutta ajuri odotti vain
   `exitCode`-arvoa. Palvelin oli sammunut. Korjattiin vain paikallinen
   testiajuri ja uusittiin koe; aiemman ajon tulos säilytettiin.
5. **Toisen ajon vektorivaihe ylitti ajurin 60 sekunnin odotusrajan.**
   Edeltävät kymmenen tarkistusta läpäisivät. Verkon estävä paikallinen
   latauskoe valmistui 65,28 sekunnissa. Testiajurin odotusraja nostettiin
   180 sekuntiin, ja lopullinen uusinta läpäisi 11/11. Sovelluskoodia tai
   hakualgoritmia ei muutettu aikakatkaisun vuoksi.
6. **Dokumentti 19 ei kuulunut Git-sallintalistaan.** Lisättiin sallintarivit
   dokumenteille 19, 20 ja 21. Muut alkuperäiset sallintarivit säilytettiin.

## Todisteet, loppusiivous ja jäljelle jäävät rajat

Paikalliset todisteet ovat `data/first-use-20261026/`-hakemistossa:
`results.json` (11 hyväksyttyä tarkistusta, pyyntöluettelo ja prosessit),
`first-use.cjs`, `vector-probe.py`, `vector-probe.json`, `server.log`,
`source-manifest.json`, `package-manifest.json` sekä `browser/`-kuvakaappaukset.
Kuvakaappauksia katsottiin; ne näyttävät kulloisenkin näkyvän näkymän,
ja sisältö-/tilatarkistukset tehtiin myös selaimen DOMista. Ensimmäisten
yritysten virheet ovat `attempt1-failure.json` ja `attempt2-failure.json`.
Aiemmat testitietokannat siirrettiin nimille `attempt1.sqlite3` ja
`attempt2.sqlite3`; ne eivät ole käyttäjän tietokantoja tai palautusaineistoa.

Testipalvelimet suljettiin ajurin omista käynnistysolioista. Lopullisen ajon
PID:t olivat 21340, 21820 ja 6576. Chromen oma testiprofiili suljettiin.
Portissa 8513 ei loppukatselmuksessa ollut kuuntelijaa. Portissa 8502 ei
ollut kuuntelijaa lähtö- tai loppukatselmuksessa; sitä ei pysäytetty tai
käynnistetty tässä työssä.

Käyttäjän `data/solutions.sqlite3`-tiedoston SHA-256 oli ennen ja jälkeen:
`F3909C9F7B6B63A652C01DA3EC0028DED6B21FD1BED2BB8F756F00B0AC95DD25`.
Sitä ei avattu testitietokantana. Vanhassa projektissa ei tehty muutoksia.
`main` säilyi commitissa `3aa6c862825261ba3000dfd03cfa5ff08c89dad3`, nykyinen
haara commitissa `9d2d397`. Mitään ei commitoitu tai pushattu.

Tämä koe ei testannut oikeaa tekoälyehdotusta, API-avaimen kelvollisuutta,
käyttöliittymässä asetetun avaimen elinkaarta, käytöstä poistoa, muokkauksen
uudelleenvahvistusta, muita selaimia tai riippumatonta hakulaatua. Niiden
aiempi näyttö ja puutteet ovat [tilannekatsauksessa 19](19_poc_valmiustilanne.md).
Uusi käyttäjä voi nyt seurata testattua avaimetonta asennus- ja käyttökulkua;
toisen käyttäjän itsenäinen kokeilu ja lopullisen jakelutavan valinta ovat
edelleen erillisiä tehtäviä.
