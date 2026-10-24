# PoC-välitavoitteen testiraportti – 19.10.2026

AI Service Desk Assistantin työversiossa on saavutettu rajattu, käyttäjälle
näkyvän vastausketjun PoC-välitavoite. Raportti erottaa käyttäjän ilmoittamat
selainhavainnot paikallisista mockatuista testeistä. Kyse ei ole
tuotantovalmiuden, riippumattoman loppuarvioinnin tai kaikkien tilanteiden
turvallisuuden hyväksynnästä.

## Todisteet ja niiden rajat

- Käyttäjän ilmoittama selainhavainto: VPN-001:n vastaus näkyi OpenAI-live-tilassa.
  Selainkuva osoittaa vastauksen, mutta API-kutsun onnistumista ei ole erikseen
  vahvistettu palvelinlokista. Kuvan tiedostopolkua ei ole kirjattu tähän raporttiin.
- Käyttäjän ilmoittamat käytännön havainnot: epäselvä käynnistysongelma johti
  lisätietopyyntöön ja vaarallinen akku turvallisuuskeskeytykseen ilman
  OpenAI-kutsua. Näitä ei ajettu uudelleen tätä dokumenttia laadittaessa.
- Paikallinen mockattu testi: oikea HTTP-reitti, sanahaku, soveltuvuussuodatus,
  mallikutsun muodostus, vastauksen jäsennys ja validointi. Ulkoisen API:n
  vastaus korvattiin testivastauksella. Aineistona oli `batch1` (30 runbookia).
- Käyttöliittymän JavaScript renderöi saman mockatun HTTP-vastauksen
  DOM-korvikkeessa. Tämä ei ole oikeassa selaimessa tehty testi.

## 1. VPN-001: live-tilan käyttäjälle näkyvä vastaus

Selainhavainnon mukaan OpenAI-live-tilassa näkyi kolme hyväksyttyä
ratkaisuvaihetta, tarkentava kysymys ja lähdeviitteet. API-kutsun onnistuminen
jää erikseen vahvistettavaksi; pelkkä selainkuva tai käyttöliittymän
valmistumisviesti ei ole riippumaton vahvistus mallipalvelun vastauksesta.

Paikallisen mockatun testin täsmällinen tukipyyntö oli:

> VPN ei yhdistä. Tavalliset verkkosivut avautuvat ilman VPN-yhteyttä.

Mockatussa testissä saatu ja käyttöliittymään renderöity vastaus:

> **Ratkaisuehdotus**
> Valittu ohje: VPN-yhteyden perustarkistus.
>
> 1. Sulje VPN-sovellus ja käynnistä se uudelleen.
> 2. Kirjaa tarkka virheilmoitus ja yhteysongelman alkamisaika.
> 3. Jos yhteys ei palaudu, toimita tiedot IT-tuelle. Älä muuta tietoturva-asetuksia.
>
> **Tarkentavat kysymykset**
> Mikä tarkka virheilmoitus näkyy VPN-yhteyden muodostuksessa?
>
> Jatkokäsittely tarvittaessa IT-tuessa.

Lähde: `VPN-001`, versio `0.2 / 15.10.2026`, alkuperäiset vaiheet 2, 3 ja 4.
Käyttöliittymän juokseva numerointi 1–3 ei muuta lähteen alkuperäisiä
vaihenumeroita. Internettarkistus (alkuperäinen vaihe 1) ohitettiin, koska
käyttäjä oli jo vahvistanut verkkosivujen avautuvan.

VPN-001 läpäisi soveltuvuussuodatuksen. Mallille annettiin tässä testissä vain
tämä hyväksytty lähde. Näkyvät vaiheet olivat sanatarkasti runbookista.
Hakuehdokkaiden toimintavaiheita ei renderöity. Onnistuminen tyhjensi
syötekentän ja säilytti käsitellyn vastauksen.

## 2. Epäselvä käynnistysongelma

Havainto: sovellus pyysi lisätietoja eikä tehnyt OpenAI-kutsua.

Toistamiseen tarkoitettu esimerkkipyyntö:

> Tietokone ei käynnisty.

Nykyisen ketjun tarkoitettu tulos on `insufficient`, ei arvattu ratkaisu.
Sovellus kysyy, mitä viimeisellä käynnistysyrityksellä tapahtui: oliko kone
mykkä, näkyikö virran merkkejä vai pysähtyikö käynnistys logoon tai
virheilmoitukseen. Ilman vahvistettua käynnistysvaihetta läheiset runbookit
eivät kelpaa ratkaisuksi eikä tavallisia toimintavaiheita näytetä.
Tämän kohdan esimerkki ei ole väite selainkokeen sanatarkasta syötteestä.

## 3. Turvonnut ja kuumeneva akku

Havainto: sovellus tuotti `safety_stop`-vastauksen DEVICE-004:n perusteella
ilman OpenAI-kutsua. Turvallisuuskeskeytys ohittaa tavallisen haun ja mallin.

Työversion turvallisuusyhteenveto:

> Turvallisuuskeskeytys. Lopeta laitteen käyttö ja lataaminen heti.
> Älä käynnistä tai lataa laitetta uudelleen äläkä käsittele tai testaa akkua.
> Älä avaa laitetta itse. Ota heti yhteys IT-tukeen.
> Kerro vain jo havaitut tiedot, jos se on turvallista. Älä tee uusia tarkistuksia.
> Ilmoitusta ei ole tehty puolestasi.

Ainoa lähteistetty toimintavaihe:

> Jos akku on turvonnut tai laite kuumenee poikkeavasti, lopeta käyttö ja ota yhteys IT-tukeen.

Lähde: `DEVICE-004`, alkuperäinen vaihe 2, versio `0.2 / 15.10.2026`.
Latausilmaisimen selvittämisvaihetta, laturin testausta tai tarkentavia
kysymyksiä ei näytetä vaaratilanteessa. IT-ilmoitusta ei tehdä automaattisesti.

## 4. Mockatun live-ketjun suojaukset

Yksi muistissa määritelty HTTP-ketjutesti sisälsi neljä tarkistusta:

| Tarkistus | Havaittu tulos |
|---|---|
| Sallittu VPN-001-valinta | HTTP 200, `suggestion`, alkuperäiset vaiheet 2–4 |
| Malli lisää oman `steps`-kentän | HTTP 502, `invalid_model_output`; ratkaisua ei näytetä |
| Malli valitsee suodatuksen ulkopuolisen NET-004-lähteen | HTTP 502, `invalid_model_output` |
| Malli kirjoittaa oman ohjeen `summary`-kenttään | Mallin teksti ei päädy näkyvään vastaukseen; sovellus kokoaa yhteenvedon itse |

Kaikki neljä tarkistusta läpäisivät. Lisäksi käyttöliittymän renderöintitarkistus
läpäisi: näkyvät toimintavaiheet vastasivat HTTP-vastauksen hyväksyttyjä
vaiheita, hakuehdokkaan ohitettu internettarkistus ei näkynyt ja syötekenttä tyhjeni.

Malli valitsee tilan ja lähteen; sovellus muodostaa toimintavaiheet.
Valinnan ylimääräiset kentät ja tuntemattomat lähteet hylätään paikallisesti.
Lopuksi tarkistetaan vaiheiden teksti, lähde, alkuperäinen vaihenumero ja versio.
API:n JSON-skeema vaatii vakioyhteenvedon. Paikallinen valintavalidointi ei
yksin vaadi tätä vakiotekstiä, mutta mallin yhteenveto korvataan eikä sitä näytetä.

Mockatun vastauksen tekninen `model_used=true` tarkoitti live-koodihaaran
suorittamista. Se ei tässä testissä tarkoita oikean kielimallin käyttöä.
Ulkoinen verkkoliikenne ja tiedostokirjoitukset estettiin testissä;
vain paikallinen HTTP-liikenne sallittiin. Testi suoritettiin Anacondan
Python 3.13.9:llä, ei projektin Python 3.14.2 -tulkilla.

DEVICE-004-korjauksen jälkeen aiemmin samalla päivällä ajettu koko
Python-testikokonaisuus läpäisi 326/326 testiä ja kohdennettu
turvallisuuskokonaisuus 12/12 testiä. Baseline-eheystarkistus vahvisti
96/96 tiedoston säilyneen. Näitä tarkistuksia ei ajettu uudelleen tämän
dokumentointityön yhteydessä.

## Tunnetut rajoitukset

- Todellisen OpenAI-kutsun onnistumisesta puuttuu erillinen palvelinpuolen
  vahvistus. Mockattu testi ei osoita API-avaimen, mallin tai laskutuksen toimivuutta.
- Nykyinen HTTP-palvelin ei oletuksena tuota kutsun onnistumisen todentavaa
  palvelinlokia. Mahdollinen havaittavuusmuutos vaatii erillisen hyväksynnän.
- Mockattu päästä päähän -testi käytti oikeaa sanahakua, ei vektorihakua.
- Internet-havainnon tunnistus riippuu sanamuodosta: ”verkkosivut avautuvat”
  tunnistuu, mutta ”verkkosivut toimivat” ei tässä kokeessa tunnistunut.
  Jälkimmäisessä tilanteessa sovellus voi toistaa runbookin internettarkistuksen.
- Lähdeviite ja sanatarkka ohje eivät yksin todista ohjeen soveltuvuutta.
  Malli voi edelleen tehdä väärän tilavalinnan annettujen lähteiden sisällä.
- Turvallisuustunnistus ja soveltuvuussäännöt ovat rajattuja. Kaikkien
  parafraasien, ristiriitojen ja vaaratilanteiden kattavuutta ei ole osoitettu.
- Näillä kehitystesteillä ei osoiteta riippumatonta yleistymiskykyä tai
  tuotantoturvallisuutta. Organisaatiokohtaiset menettelyt vaativat ihmistarkistuksen.

## Seuraavat testit ja hyväksyntärajat

1. Vahvista erikseen hyväksytyssä oikeassa live-kokeessa API-kutsun onnistuminen
   palvelinpuolen todisteella. Älä tallenna avainta tai tarpeettomia tukipyyntötietoja.
2. Toista VPN-001 oikeassa selaimessa paikallisella vektorihaulla; tarkista lähde,
   soveltuvuus, alkuperäiset vaihenumerot ja ettei ehdokkaiden vaiheita näy.
3. Tarkista selaimessa epäselvä käynnistys, vaarallinen akku ja niiden vastatapaukset.
   Varmista lisätietopyyntö, turvallisuusetusija ja mallikutsun ohitus.
4. Tarkista virhepolut: puuttuva tai virheellinen avain, aikakatkaisu, kesken jäänyt
   mallivastaus ja hylätty lähdevalinta. Virheessä syöte säilyy eikä vanha vastaus näy.
5. Tarkista turvallisuusohjeiden näkyvyys, lähdelinkit ja käytettävyys Edge-selaimessa.

Oikeat API-kokeet ja mahdolliset lokitusmuutokset hyväksytään erikseen.
Tässä dokumentointivaiheessa ei tehty API-kutsuja, uusia arviointiajoja,
koodimuutoksia tai runbook-muutoksia. Jäädytettyä
`evaluation/baselines/batch1-30-20261019-v1`-versiota ei muutettu.
Riippumatonta holdout B:tä ei avattu eikä batch2-erää aloitettu.

## Ratkaisumuistin lisätestaus – 24.10.2026

Tämä lisäys koskee erillistä ratkaisumuistin worktreetä, haaraa
`kehitys/ratkaisumuisti` ja lähtöcommittia `d643fba`. Vanhan projektin
`main`-työpuuta ei muutettu. Testiympäristö on Windows, worktreen oma
Python 3.13.15 -virtuaaliympäristö ja paikallinen osoite
`http://127.0.0.1:8502/memory` (`batch1`, sanahaku).

### Käyttäjän ilmoittama selainkoe: Kajo77

Käyttäjä ilmoitti seuraavat tulokset 24.10.2026. Nämä ovat käyttäjän
selainhavaintoja, eivät automaation suorittama selainkoe.

| Vaihe | Havaittu tulos | Tulos |
|---|---|---|
| Luonnoksen tallennus ja haku | Kajo77-luonnos ei löytynyt hausta | Hyväksytty |
| Vahvistus ja haku | Vahvistettu ratkaisu löytyi ja näytti oikean tekstin | Hyväksytty |
| Käytöstä poisto ja haku | Osuma katosi hakutuloksista | Hyväksytty |
| Historia käytöstä poiston jälkeen | Tietue säilyi historiassa | Hyväksytty |

Selainkoe vahvistaa tämän tapauksen työnkulun. Käyttäjän ilmoitus ei sisällä
uudelleenkäynnistyksen jälkeistä selainhavaintoa eikä ratkaisun sanatarkkaa
sisältöä; niitä ei päätellä tässä raportissa.

### Paikallinen palvelin- ja uudelleenkäynnistystesti

Aiemmassa saman päivän paikallisessa HTTP-kokeessa luotiin erillinen
kuvitteellinen `PAIKALLISTESTI 20261024: VPN E42` -tietue. Oikean
palvelinprosessin uudelleenkäynnistyksen jälkeen vahvistetun tietueen sisältö,
vahvistustiedot ja hakukelpoisuus säilyivät. Käytöstä poiston ja toisen
uudelleenkäynnistyksen jälkeen tietue sekä poistamisen syy säilyivät
historiassa, mutta tietue ei palautunut hakuun. SQLite-eheystarkistus oli `ok`.
Vanha istuntotunniste hylättiin uudelleenkäynnistyksen jälkeen 403-vastauksella;
selain on päivitettävä ennen jatkamista.

Tämä on paikallisen palvelimen toimintotesti, ei selaimessa tehty
uudelleenkäynnistyskoe. Paikallinen tarkistustulos on tallessa Gitin
ulkopuolella tiedostossa `data/local-memory-check.json`; tietokantaa tai
sen sisältöä ei liitetä tähän raporttiin.

### Windows-korjaus ja regressiotestit

Alkuperäisessä testiajossa 190/192 Python-testiä läpäisi. Kahdessa
istuntotunnisteen hylkäystestissä Windowsin yhteys katkesi virheeseen
`WinError 10053` ennen odotettua HTTP 403 -vastausta. Palvelin vastasi
lukematta ensin POST-pyynnön sisältöä.

`app.py` tarkistaa nyt ensin sisältöpituuden nykyisellä kokorajalla, lukee
rajatun sisällön ja tarkistaa sitten istuntotunnisteen. Väärällä tai
puuttuvalla tunnisteella sisältöä ei jäsennetä JSONiksi eikä sovelluslogiikkaa
suoriteta. Ylisuuri pyyntö hylätään ennen sisällön lukemista; tällöin
kokorajan 400-virhe on ensisijainen myös väärällä tunnisteella.

`tests/test_http.py` sisältää kaksi uutta regressiotestiä:

- Väärä ja puuttuva istuntotunniste: vastausta ei saa kirjoittaa ennen
  sisällön kuluttamista. Tarkistus kattaa alkuperäisen vastausreitin ja kaikki
  kuusi ratkaisumuistin toimintoa. Virheellinen JSON ei saa ohittaa
  istuntotarkistusta, eikä vastaus- tai ratkaisumuistilogiikka saa käynnistyä.
- Molempien reittiperheiden kokorajat: ylisuurta pyyntöä ei lueta eikä
  välitetä sovelluslogiikalle.

Testi käyttää oikeaa HTTP-vastauskoodia muistivirroilla ja havaitsee
lukemattoman sisällön deterministisesti. Se ei riipu Windowsin TCP-katkoksen
ajoituksesta. Uusi 403-regressiotesti epäonnistuu lähtöcommitin käsittelijällä
ja läpäisee korjatulla käsittelijällä.

### Tämän muutoksen automaattinen tarkistus

Tarkistuskomennot worktreen juuressa:

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests
node .\tests\ui_memory_test.cjs
git diff --check
```

Tulokset: **194/194 Python-testiä hyväksytty**, ratkaisumuistin
JavaScript-käyttöliittymätesti hyväksytty ja `git diff --check` hyväksytty.
JavaScript-testi käyttää DOM-korviketta. API-ehdotusten testit käyttävät
mockattuja vastauksia; oikeita API-kutsuja ei tehty. Testiprosessin
API-avain poistettiin ympäristöstä ja mallien verkkolataukset estettiin.

Tämä työ ei muuta `main`-haaraa eikä lisää tietokantaa, lokeja tai paikallista
virtuaaliympäristöä Gitiin. Oikea API-koe, upotusmallin hakulaadun arviointi ja
uudelleenkäynnistyksen jälkeinen selainkoe jäävät erikseen tehtäviksi.

## Ratkaisumuistin oikean upotusmallin koe – 24.10.2026

Koe tehtiin nykyisessä `kehitys/ratkaisumuisti`-worktreessä commitin `f3a9aee`
päällä. Sovellus- tai hakukoodia ei muutettu. Nykyinen tietokanta säilytettiin;
kuvitteellisille tapauksille luotiin erillinen tietokanta hakemistoon
`data/vector-evaluation/run-20261024T084240124854Z`.
Tietokanta ja sen oma vektorivälimuisti eivät kuulu Gitiin.

### Riippuvuudet ja paikallinen malli

Worktreen Python 3.13.15 -virtuaaliympäristöön asennettiin
`requirements-vector.txt`:n riippuvuudet käyttäen CPU-versiota PyTorchista.
Keskeiset toteutuneet versiot: sentence-transformers 5.7.0,
torch 2.14.1+cpu, transformers 5.20.2, huggingface-hub 2.3.0 ja NumPy 2.5.4.
`uv pip check` hyväksyi kaikki 42 asennettua pakettia. Vanhan projektin
virtuaaliympäristöä ei käytetty eikä muutettu.

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` löytyi jo
paikallisesta välimuistista. Revisio on
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Malli kopioitiin tämän
worktreen `.model-cache/hub`-hakemistoon; painotiedoston tarkistussumma
varmistettiin samaksi kuin lähteessä. Mallia ei ladattu verkosta.

Koe käytti sovelluksen oikeaa `search.encoder()`-latausta ja `Memory.search()`-
hakua CPU:lla. Upotusten ulottuvuus oli 384. Mallin latauksen ja hakukokeiden
aikana verkkoyhteydet estettiin Pythonin audit-koukulla; yhteysyrityksiä oli 0.
API-avain poistettiin prosessin ympäristöstä. Verkkoliikennettä tarvittiin
vain riippuvuuspakettien lataamiseen pakettivarastoista, ei ulkoiseen
malli-inferenssiin tai API-kokeeseen.

### Aineisto, odotukset ja tulokset

Ennen mallin latausta lukittiin 11 kuvitteellisen tietueen aineisto ja 19
kyselyä odotuksineen: 9 vahvistettua, 1 luonnos ja 1 käytöstä poistettu tietue.
Vahvistus on tässä testitila, ei oikean tukiratkaisun hyväksyntä. Sopivuus
edellytti oireen lisäksi oikeaa organisaatiota, käyttöjärjestelmää ja
ilmoitettua ohjelmaversiota. Hakuraja oli koko kokeen **0,43** ja tulosmäärän
raja **3**. Aineistoa, kyselyjä tai hakurajaa ei muutettu tulosten perusteella.

| Kokeen osa | Tulos |
|---|---|
| Eri sanoin kuvatut ongelmat | Oikea tietue ensimmäisenä 3/3; kaikissa myös väärän ympäristön osumia |
| Samankaltaiset eri ympäristön tapaukset | Oikea ensimmäisenä 7/8, top-3:ssa 8/8; jokaisessa myös soveltumattomia osumia |
| Sopivaa ratkaisua ei ole | Tyhjä tulos vain 1/6; virheellisiä osumia 5/6 |
| Luonnoksen ja poistetun tietueen omat haut | Kumpikaan tietue ei palannut hakuun, mutta molemmat kyselyt palauttivat muita vääriä osumia |
| Vahvistetun tietueen käytöstä poisto | Tietue poistui hausta ja välimuistin tunniste vaihtui |
| Vahvistetun tietueen muokkaus luonnokseksi | Tietue poistui hausta ja välimuistin tunniste vaihtui |

**Puuttuvat oikeat tulokset:** 0/11 kyselyä, joille aineistossa oli sopiva
vahvistettu tietue, jäi ilman oikeaa top-3-osumaa. Oikea ensimmäinen osuma
puuttui yhdessä näistä kyselyistä. Tulokset eivät osoita yleistä hakukattavuutta.

**Väärät osumat:** pääkokeen 19 kyselystä 18 palautti vähintään yhden
soveltumattoman osuman; tällaisia osumia oli yhteensä 35. Esimerkkejä:

- E03, Koivun Windows/AuroraVPN 6.1: ensimmäisenä väärä 5.2-tietue
  pisteillä **0,832618**; oikea 6.1-tietue vasta toisena, **0,814910**.
- N02, Ubuntu/AuroraVPN: aineistossa ei ole Ubuntu-ratkaisua, mutta
  Windows-tietue tuli ensimmäiseksi pisteillä **0,778964**.
- N04, uusi Leppä-organisaatio: aineistossa ei ole sen ratkaisua, mutta
  Koivun tietue tuli ensimmäiseksi pisteillä **0,866090**.
- N01, ulkoisen näytön vilkkuminen: osumaksi tuli verkkolevykansion
  käyttöoikeusratkaisu pisteillä **0,471605**.
- N06, älykortinlukija: haku palautti tulostinratkaisuja pisteillä
  **0,449666** ja **0,440154**.
- N05, PostgreSQL-kyselyn lukitusaikakatkaisu: ainoa kuudesta tavallisesta
  vastausta vailla olevasta tapauksesta, jossa haku palautti tyhjän tuloksen.

Nykyinen haku sisällyttää ympäristön tekstiin, mutta ei suodata organisaatiota,
käyttöjärjestelmää tai ohjelmaversiota erillisinä ehtoina. Semanttinen
samankaltaisuus auttaa löytämään aihepiirin, mutta kokeessa se ei riittänyt
ympäristön soveltuvuuden tai vastauksen puuttumisen tunnistamiseen.
Tilasuodatus toimi, vaikka poistettujen tapausten kyselyt tuottivat edelleen
muita soveltumattomia osumia. Hakurajan nostaminen ei yksin korjaisi havaittuja
korkeapisteisiä ympäristövirheitä. Hakukoodia tai rajaa ei muutettu.

### Todisteet ja säilyminen

[Paikallinen yksityiskohtainen raportti](../data/vector-evaluation/run-20261024T084240124854Z/report.md)
sisältää kaikki kyselyt, odotukset, palautetut tietueet pisteineen ja
välimuistin tilamuutoskokeet. Samassa paikallisessa testihakemistossa ovat
`fixtures.json`, `results.json`, `requirements-installed.txt`, erillinen
`fictional-solutions.sqlite3` ja sen `.vectors.json`-välimuisti. Ne ovat
Gitin ulkopuolella; paikallinen raporttilinkki toimii tässä worktreessä.

Toistettava koeskripti: `data/vector-evaluation/run_vector_evaluation.py`.
Jokainen ajo luo uuden testihakemiston eikä kirjoita nykyiseen tietokantaan.
Koeaineisto on pieni etukäteen laadittu kehitysaineisto, ei riippumaton
arviointiaineisto tai laatulupaus.

Nykyisen `data/solutions.sqlite3`-tietokannan SHA-256 ennen ja jälkeen kokeen:
`3819b6162a2c0ee2513beeb209d8fcc9ebc735bd14f3f8733b05f2c4e814f83c`.
Erillisen testitietokannan SQLite-eheystarkistus hyväksyttiin. Tilamuutosten
jälkeen siinä on 7 vahvistettua, 2 luonnosta ja 2 käytöstä poistettua tietuetta.

Riippuvuuksien asennuksen jälkeen **194/194 Python-testiä** ja ratkaisumuistin
JavaScript-testi hyväksyttiin. Nämä regressiotestit läpäisevät, vaikka yllä
kuvatussa oikean mallin laatukokeessa havaittiin soveltumattomia osumia.
Commit `f3a9aee`, nykyinen tietokanta ja vanha projekti säilytettiin.

## Rakenteisten ympäristötietojen parannus ja loppuarviointi – 24.10.2026

Edellinen oikean mallin arviointiraportti tallennettiin ensin paikalliseen
commitiin **`9abeaf1`**. Sen edeltäjä `f3a9aee` säilyy historiassa.
Toteutus koskee vain `kehitys/ratkaisumuisti`-worktreetä.

### Rajattu toteutus

Ratkaisulle ja haulle lisättiin valinnaiset `operating_system`, `product`
ja `product_version`. Vapaa `environment`-kuvaus säilyy. Ilmoitettujen
kenttien ristiriidat suljetaan pois ennen sana- tai vektorihakua ja top-3-rajaa.
Puuttuva arvo ei ole yhteensopivuuslupaus: tulos merkitään tarkistettavaksi,
ja tietueesta sekä hakurajauksista puuttuvat kentät eritellään.

Kaikkien kolmen kentän täsmääminen ilmaisee vain ilmoitettujen arvojen
samuuden. Sovellus näyttää edelleen samankaltaisia **ehdokkaita** ja pyytää
tarkistamaan oireet sekä muun ympäristön. Organisaatiolle ei lisätty tässä
vaiheessa rakenteista kenttää. Hakutekstistä ei päätellä rakenteisia rajauksia.
Vertailu normalisoi kirjainkoon ja välilyönnit; aliaksia tai versioalueita ei
päätellä. Hakuraja pysyi **0,43:ssa**, tulosmäärän raja **3:ssa** ja `search.py`
muuttumattomana. Hakurajaa, aineistoa tai kyselyjä ei sovitettu tuloksiin.

### Kehitysaineisto ja erilliset loppuarviointikyselyt

Aineisto lukittiin ennen toteutusta tiedostoon
`tests/fixtures/memory_environment_cases.json`: 19 aiempaa kehityskyselyä ja
17 uutta loppuarviointikyselyä. Kyselyiden ja odotusten tiedoston SHA-256 on
`2b4a9d73be6eb43033df9df7cd64610fe926cdf6fe6d6b5307a53e2f3298f675`.

Sama kuvitteellinen 11 tietueen tapausaineisto sisältää 9 vahvistettua,
yhden luonnoksen ja yhden käytöstä poistetun tietueen. Rakenteiset arvot
kirjoitettiin käsin vain testiaineistoon. Saarnin VPN-tietueelta jätettiin
versio ja vanhaa tietuetta jäljittelevältä verkkolevytapaukselta kaikki kolme
arvoa puuttumaan. Tulostintapauksille ei keksitty puuttuvaa tuoteversiota.
Käyttäjän tietueiden uusia kenttiä ei täytetty näistä testeistä.

Loppuarvioinnin uudet kyselyt laadittiin saman kehitystyön yhteydessä;
kyse ei ole riippumattomasta holdout-aineistosta. Toteutuksen tarkistussummat
jäädytettiin kehityskokeen ja kooditarkistuksen jälkeen ennen loppuarviointia.
Hakutoteutus on sama kehitys- ja loppukokeessa. Käyttöliittymän tarkistusviestiä
täsmennettiin ennen jäädytystä; hakukoodia ei muutettu loppukokeen perusteella.

### Tulokset oikealla upotusmallilla

Malli oli sama paikallinen monikielinen MiniLM, revisio
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, CPU, 384 ulottuvuutta.
Vertailun molemmat puolet käyttivät samoja kuvitteellisia tietueita ja
sanatarkasti samoja hakutekstejä: ennen = ilman rakenteisia rajauksia,
jälkeen = erikseen annetut rakenteiset rajaukset käytössä.

| Mittari | Kehitys: ennen → jälkeen | Loppuarviointi: ennen → jälkeen |
|---|---|---|
| Oikea ensimmäinen osuma | 10/11 → 11/11 | 9/10 → 7/10 |
| Oikea tietue top-3:ssa | 11/11 → 11/11 | 10/10 → 9/10 |
| Hylätty oikea ratkaisu | 0 → 0 | 0 → 1 |
| Puuttuva oikea top-3-tulos | 0 → 0 | 0 → 1 |
| Väärien osumien määrä | 35 → 14 | 32 → 20 |
| Kyselyjä, joissa väärä osuma | 18/19 → 8/19 | 15/17 → 10/17 |
| Ei sopivaa tietuetta, silti osumia | 7/8 → 3/8 | 6/7 → 4/7 |

Vastausta vailla olevien tapausten määrät sisältävät myös vain luonnoksena
ja vain käytöstä poistettuna löytyvän tapauksen. Väärä osuma tarkoittaa
etukäteen määritetyn oireen ja ympäristön kannalta soveltumatonta tietuetta;
se lasketaan virheeksi myös silloin, kun käyttöliittymä merkitsee sen
asianmukaisesti tarkistettavaksi.

**Loppuarvioinnin keskeiset regressiot ja jäljelle jääneet väärät osumat:**

- **F12, hylätty oikea:** hakurajauksen `Win 11` hylkäsi tietueen, jonka arvo
  on `Windows 11`. Nämä tarkoittavat kokeessa samaa käyttöjärjestelmää.
  Tarkka vertailu aiheutti yhden väärän hylkäyksen ja puuttuvan top-3-tuloksen.
- **F17, väärä ensimmäinen:** oikea VPN-tietue sai **0,833909**, mutta vanha
  hakusanaheuristiikka nosti puutteellisen verkkolevytietueen (**0,498315**)
  sen edelle. Diagnostiikan peruste `unique_title_or_keyword_term` käytti
  sanaa `verkkosivut`: kuuden kirjaimen sanavartalo yhdistyi verkkolevyohjeen
  hakusanoihin. Suodatus toi tämän puutteellisen tietueen kolmen ehdokkaan
  joukkoon. Kenttien kirjainkoko- ja välilyöntinormalisointi toimi oikein.
- **F11, puuttuva hakuversion arvo:** hakutekstissä mainittiin 6.1, mutta
  erillinen versiorajaus oli tyhjä. Versiota ei päätelty tekstistä. Väärä
  5.2-tietue jäi ensimmäiseksi (**0,870941**), oikea 6.1 toiseksi (**0,864221**).
  Molemmat näytettiin puuttuvan hakutiedon vuoksi tarkistettavina.
- **F07, eri organisaatio:** Leppä-yrityksen kysely palautti Koivun VPN-tietueen
  (**0,898432**). Kolmen rakenteisen kentän samuus ei ratkaise organisaatioeroa.
- **F08, eri oire samassa ympäristössä:** 40 minuutin jälkeen katkeava yhteys
  palautti yhteyden avaamisen E42-virheen ratkaisun (**0,667108**).
  Ympäristörajaukset eivät osoita oireen tai korjauksen sopivuutta.
- **F13, puuttuva tietueen versio:** versioon 5.20 palautui Saarnin tietue
  (**0,875963**), jonka versio on tuntematon. Se jäi tarkistettavaksi;
  tunnettuun 5.2-versioon kuuluvat ristiriitaiset tietueet rajattiin pois.
- **F15, poistettu tapaus:** käytöstä poistettu skanneritietue ei palannut,
  mutta haku palautti puutteellisen verkkolevytietueen (**0,440632**).

Nämä ovat todettuja laatupuutteita. Väärien osumien väheneminen ei tässä
kokeessa merkinnyt oikeiden ykkösosumien paranemista loppuarvioinnissa.
Erityisesti puuttuvien tietojen ehdokkaiden järjestys ja OS-aliasten hallittu
käsittely tarvitsevat seuraavan erillisen korjauksen ja uusia arviointikyselyjä.
Heuristiikkaa tai aliaksia ei muutettu tämän loppuarvioinnin läpäisemiseksi.

### Puuttuvien tietojen raportointi

Loppuarvioinnin 17 kyselystä 12 palautti vähintään yhden tarkistettavan
osuman. Palautuneissa osumissa oli 18 kertaa puuttuva tietueen kenttäjoukko
ja 7 kertaa puuttuva hakukenttäjoukko. Nämä ovat osumakohtaisia määriä,
eivät eri tietueiden määriä, ja sama osuma voi kuulua molempiin lukuihin.
Kaikki kolme tietoa täsmäsi myös kolmessa väärässä osumassa; siksi tämä
merkintä ei tarkoita ratkaisun soveltuvuuden hyväksyntää.

F10:n vanhaa tietuetta jäljittelevä verkkolevyohje löytyi oikeana osumana
(**0,711715**), mutta kaikki sen rakenteiset tiedot merkittiin puuttuviksi.
F09:n hakurajauksista puuttuvaa käyttöjärjestelmää ei päätelty MacBook-sanasta.
Luonnokset ja käytöstä poistetut tietueet jäivät molemmissa kokeissa haun
ulkopuolelle, vaikka niiden kyselyt saattoivat tuottaa muita vääriä osumia.

### Tietokannan säilyminen ja regressiotestit

Ensin otettiin varmuuskopio ja testattiin migraatio käyttäjän tietokannan
erillisellä kopiolla. Migraatio lisättiin vasta hyväksyttyjen testien jälkeen
nykyiseen `data/solutions.sqlite3`-tiedostoon: **2/2 tietuetta ja kaikkien
aiempien sarakkeiden arvot säilyivät**, mukaan lukien tekstit, tilat,
revisionumerot, vahvistukset ja poistamisen syyt. Kolme uutta arvoa ovat
kaikissa vanhoissa tietueissa `NULL`. SQLite-eheystarkistus hyväksyttiin.
Tiedoston tarkistussumma muuttui skeemalisäyksen vuoksi; se ei ole
bittitasolla sama tiedosto. Varmuuskopio on Gitin ulkopuolella hakemistossa
`data/backups/environment-migration-20261024T091105920843Z`.

**209/209 Python-testiä** ja laajennettu ratkaisumuistin JavaScript-testi
hyväksyttiin. Uudet testit kattavat migraation säilyvyyden, toistettavuuden
ja rollbackin, kaikki kolme ristiriitaa molemmilla hakutavoilla, puuttuvat
tiedot, kokorajat ja validoinnin, rajauksen ennen top-3-valintaa,
välimuistin vaihtuvat rajaukset, tilasuodatuksen, HTTP-kentät sekä lomakkeen
ja hakurajausten kulun käyttöliittymässä. JavaScript-testi käyttää
DOM-korviketta; uutta oikean selaimen koetta ei tässä ajettu.

### Toistaminen ja paikalliset todisteet

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests
node .\tests\ui_memory_test.cjs
& .\.venv\Scripts\python.exe -B .\tests\evaluate_memory_environment.py --split development
& .\.venv\Scripts\python.exe -B .\tests\evaluate_memory_environment.py --split final
```

Loppuarviointi vaatii paikallisen
`data/environment-evaluation/implementation-freeze.json`-tiedoston ja
jäädytystä vastaavat lähdekoodin sekä aineiston tarkistussummat. Nykyisessä
worktreessä jäädytys on tallessa. Muutetun toteutuksen arviointi edellyttää
uutta erillistä jäädytystä ja uusia loppuarviointikyselyjä.

- [Kehityskokeen kaikki kyselyt ja pisteet](../data/environment-evaluation/development-20261024T090227966419Z/report.md)
- [Loppuarvioinnin kaikki kyselyt, hylkäykset ja puuttuvat tiedot](../data/environment-evaluation/final-20261024T090439121704Z/report.md)
- Loppuarvioinnin `ranking-diagnostics.json` näyttää F11- ja F17-järjestysten syyt.
- Kummankin raportin vieressä ovat koneelliset tulokset, testitietokanta,
  vektorivälimuisti, aineistokopio ja asennettujen riippuvuuksien versiot.
- Käyttäjän migraation tarkistus: `data/environment-evaluation/user-database-migration.json`.

Paikalliset raporttilinkit toimivat tässä worktreessä. Tietokantoja,
varmuuskopioita ja paikallisia malli- tai vektorivälimuisteja ei lisätä Gitiin.
Ulkoisia API-kutsuja ei tehty, muutoksia ei pushattu eikä vanhaa projektia
muutettu. Uusi näkymä käynnistettiin paikallisesti osoitteeseen
`http://127.0.0.1:8502/memory` ilman API-avainta. Palvelimen
uudelleenkäynnistyksen jälkeen selain on päivitettävä.

## OS-aliasten ja ratkaisumuistin vektorijärjestyksen korjaus – 24.10.2026

Lähtöversio on `2404b9e`. Korjaus rajattiin tunnettuihin OS-kirjoitusasuihin,
ratkaisumuistin vektorijärjestykseen ja pyydettyyn ehdokasryhmien erotteluun.
Hakurajaa **0,43** tai top-3-rajaa ei muutettu. Käyttäjän tietokantaan ei
kirjoitettu eikä skeemaa muutettu tässä korjauksessa.

### Normalisointi ja järjestysregression syy

OS-vertailu tunnistaa Windows 10:n ja 11:n tunnetut `Win`- ja välilyönnittömät
kirjoitusasut sekä rajatut macOS 15-, Ubuntu 24.04-, Debian 12- ja Android 15
-kirjoitusasut. Esimerkiksi `Win 11`, `win11`, `Windows11` ja `Windows 11`
tarkoittavat samaa käyttöjärjestelmää. Normalisointi on vain vertailussa;
tallennettuja arvoja ei kirjoiteta uudelleen. Versioita, aliversioita tai
editioita ei poisteta tai yhdistetä. Tuote- ja versiokenttiin ei sovelleta
OS-aliaksia: esimerkiksi `5.2` ja `5.20` pysyvät eri arvoina.

Aiemman F17-regression syy oli PoC:n `_rerank_same_category`-heuristiikka:
kuuden kirjaimen sanavartalo yhdisti sanan `verkkosivut` verkkolevyohjeeseen.
Se nosti verkkolevytietueen (**0,498315**) VPN-tietueen (**0,833909**) edelle.
Ratkaisumuisti käyttää nyt vektorikyselyssä `apply_poc_heuristics=False`-
valintaa: järjestys on puhtaasti kosinisamankaltaisuuden mukainen.
PoC:n uudelleenjärjestelyjä tai erikoiskyselysuodatusta ei käytetä tässä
vektoripolussa. Ratkaisumuistin oma turvallisuuskeskeytys ja ympäristörajaus
säilyvät ennen hakua. Sanahaun pisteytykseen ei tehty muutoksia.

`VectorSearch.query()` käyttää edelleen oletuksena PoC:n aiempia heuristiikkoja.
PoC:n `vector_search()`- ja hybridipolkuja ei muutettu. Oletuskyselyn vastaukset
olivat identtiset commitista `2404b9e` ladatun hakumoottorin kanssa kaikissa
**38/38** kehitys- ja loppuarvioinnin vertailuissa samoilla ehdokasjoukoilla.
Lisäksi alkuperäiset regressiotestit säilytettiin ja ajettiin.

### Ehdokasryhmät ja merkintöjen rajat

API:n `hits` on yhteinen puhdas vektorijärjestys. Sen osajoukot erotetaan:

- `compatible_hits`: kaikki kolme ilmoitettua ympäristöarvoa ovat tiedossa
  molemmin puolin ja täsmäävät vertailussa. Näyttöteksti rajaa yhteensopivuuden
  **ilmoitettuihin tietoihin**, eikä takaa oireen tai korjauksen sopivuutta.
- `review_hits`: vähintään yksi ympäristöarvo puuttuu. Puuttuvat tietueen ja
  kyselyn kentät näytetään erikseen. Tarkistusmerkintä ei lupaa toimivuutta.

Käyttöliittymä näyttää nämä ryhmät erikseen ja kummankin sisällä pistejärjestyksessä.
Jos ensimmäinen ryhmä on tyhjä, käyttöliittymä ja API:n viesti kertovat sen
selvästi myös silloin, kun tarkistettavia ehdokkaita on. Kumpikin ryhmä on
samasta enintään kolmesta osumasta; tulosmääriä tai erillisiä hakukiintiöitä
ryhmille ei lisätty. Loppuarvioinnissa ensimmäinen ryhmä puuttui **11/21**
kyselystä; näistä **7** palautti tarkistettavia ehdokkaita.

### Aineiston erottelu ja kolmen tavan vertailu

Aiemmat 17 loppuarviointikyselyä ovat nyt kehitysaineistoa. Ennen toteutusta
laadittiin ja lukittiin **21 uutta kyselyä**, joiden sanatarkka teksti ei ole
aiemmissa aineistoissa. Sama kuvitteellinen tapausaineisto säilyi. Uudet
kyselyt sisältävät tarkoituksella useita alias- ja versiorajojen vastatapauksia.
Ne ovat saman kehitystyön tekijän laatimia, eivät riippumaton holdout-aineisto.
Aineiston SHA-256: `54e104e2d6a546133f94bfe6d43991f03254f2d85b0adb4c29cf680d3f15b91f`.

Vertailut tehtiin samalla oikealla paikallisella MiniLM-mallilla
(revisio `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, CPU, 384 ulottuvuutta)
kolmessa tilassa:

1. **Lähtöversio:** commitin `2404b9e` tiukka OS-vertailu ja PoC-heuristiikat.
2. **OS-korjaus + PoC:** korjatut aliakset mutta vanha heuristinen järjestys.
3. **Lopullinen:** korjatut aliakset ja ratkaisumuistin puhdas vektorijärjestys.

Toteutus tarkistettiin kehityskokeen jälkeen ja jäädytettiin tarkistussummilla
ennen uuden loppuaineiston ensimmäistä ajoa. Hakukoodia, kyselyjä tai rajaa
ei muutettu loppuarvioinnin perusteella.

| Mittari | Kehitys: lähtö → OS + PoC → lopullinen | Uusi loppuarviointi: lähtö → OS + PoC → lopullinen |
|---|---|---|
| Oikea ensimmäinen osuma yhteisessä `hits`-listassa | 7/10 → 8/10 → 8/10 | 3/12 → 8/12 → 10/12 |
| Oikea tietue top-3:ssa | 9/10 → 10/10 → 10/10 | 6/12 → 12/12 → 12/12 |
| Väärin hylätty oikea ratkaisu | 1 → 0 → 0 | 6 → 0 → 0 |
| Puuttuva oikea top-3-tulos | 1 → 0 → 0 | 6 → 0 → 0 |
| Väärien osumien määrä | 20 → 21 → 21 | 17 → 23 → 23 |
| Kyselyjä, joissa väärä osuma | 10/17 → 11/17 → 11/17 | 12/21 → 12/21 → 12/21 |
| Ei sopivaa ratkaisua, silti osumia | 4/7 → 4/7 → 4/7 | 5/9 → 5/9 → 5/9 |

Uuden ryhmitellyn näkymän ensimmäinen näkyvä ehdokas oli myös oikein
**10/12** positiivisessa loppukyselyssä. Vertailun päämittari on yllä yhteisen
`hits`-listan järjestys; ryhmittely ei tarkoita samaa kuin koko listan näyttäminen
yhtenä pistejärjestyksenä.

### Korjausten tulokset ja myös heikennykset

- Kehityksen **F12**: `Win 11` ei enää hylkää oikeaa Windows 11 -ratkaisua.
  Oikea VPN-tietue löytyi ensimmäisenä (**0,863843**).
- Kehityksen **F17**: puhdas järjestys palauttaa oikean VPN-tietueen
  (**0,833909**) verkkolevytapauksen (**0,498315**) edelle.
- **Kehityksen F05 heikkeni:** aiempi heuristiikka nosti oikean Saarnin
  tapauksen ensimmäiseksi. Puhdas kosinijärjestys nostaa Koivun tapauksen
  (**0,848271**) Saarnin (**0,830824**) edelle. Organisaatio ei ole tässä
  rajauksessa rakenteinen kenttä. Heuristiikan poistaminen menetti siis myös
  yhden hyödyllisen noston; tätä ei piilotettu tai korjattu aineistoon sovittamalla.
- Uuden loppuarvioinnin **H01**: OS-normalisoinnin jälkeinen PoC-järjestys
  nosti verkkolevyn ensimmäiseksi. Puhdas vektorijärjestys palautti oikean
  VPN-tietueen (**0,803819**) verkkolevyn (**0,468487**) edelle.
- **H21**: puuttuva tuoterajaus ei johda yhteensopivuusväitteeseen. Kaikki
  ehdokkaat jäävät tarkistettaviksi, ja puhdas järjestys nosti oikean VPN:n
  (**0,840998**) verkkolevyn (**0,439461**) edelle.
- **Väärien osumien määrä kasvoi** kehityksessä 20:stä 21:een ja uusissa
  loppukyselyissä 17:stä 23:een. Aliasvirheen korjaus avasi aiemmin virheellisen
  OS-ristiriidan vuoksi suljettuja ehdokkaita. Osa niistä on silti väärän
  organisaation tai puuttuvien tietojen tapauksia. Hakutulosjoukot ovat samat
  OS-korjaus + PoC- ja puhdas vektori -vertailuissa; niiden ero on järjestys.

### Jäljelle jääneet väärät osumat ja puuttuvat tiedot

Kaikki 12 oikeaa loppuratkaisua löytyivät, mutta **H09**:ssä väärä Koivun
ratkaisu (**0,780291**) jäi oikean Saarnin (**0,762207**) edelle. **H10**:ssä
hakuversion puuttuminen jätti molemmat VPN-versiot tarkistettaviksi:
väärä 5.2 oli **0,863561** ja oikea 6.1 **0,857948**. Versiota ei päätelty
hakutekstistä automaattisesti.

Vastausta vailla olevien yhdeksän kyselyn viisi virheellistä osumajoukkoa:

| Koe | Väärä osuma tai syy |
|---|---|
| H03, Windows 10 | Puutteellinen verkkolevytietue 0,445989; tunnetut Windows 11 -tietueet suljettiin pois |
| H04, tuotteen versio 5.20 | Saarnin tietue 0,754177, jonka versio puuttuu; tunnettuja 5.2-versioita ei yhdistetty 5.20:een |
| H14, yhteys toimii mutta video pätkii | Yhteyden avaamisen E42-tietue 0,731805 ei vastaa oiretta |
| H15, Leppä-organisaatio | Koivun tietue 0,791196; sama OS, tuote ja versio eivät osoita organisaation soveltuvuutta |
| H18, esityskaukosäädin | Outlook-tietue 0,462495; kaikki hakurajaukset puuttuvat |

Loppukokeessa palautui yhteensä **10 ilmoitettujen tietojen perusteella
yhteensopivaksi luokiteltua** ja **25 puuttuvien tietojen vuoksi tarkistettavaa**
osumaa. Kolme väärää osumaa oli ensimmäisessä ryhmässä. Merkinnät eivät siis
osoita ratkaisun toimivuutta, vaan ainoastaan ilmoitettujen kenttien tilanteen.
Luonnokset ja käytöstä poistetut tietueet pysyivät pois hausta kaikissa ajoissa.

### Regressiotestit, säilyminen ja toistaminen

Molemmat aiemmin havaitut virheet toistettiin ensin uusilla testeillä
lähtökoodissa. Korjauksen jälkeen **217/217 Python-testiä** ja laajennettu
ratkaisumuistin JavaScript-testi hyväksyttiin. Uudet tarkistukset kattavat
aliasvertailun molempiin suuntiin ilman tietojen uudelleenkirjoitusta,
OS- ja tuoteversioiden sekä editioiden erottelun, tunnetun järjestysregression,
PoC-oletuksen säilymisen, PoC-heuristiikkojen ohittamisen vain puhtaassa
vektoripolussa, turvallisuuskeskeytyksen säilymisen, API:n ehdokasryhmät,
ryhmien erottelun käyttöliittymässä sekä yhteensopivien puuttumisen ilmoituksen.
JavaScript-testi käyttää DOM-korviketta; uutta oikean selaimen koetta ei ajettu.

Käyttäjän tietokanta säilyi bittitasolla ennallaan, SHA-256
`b2082b2b89d36f015b02123eef56e7173a8312ac2d01ea3ddb022d7c401374e3`.
Molempien tietueiden kaikki arvot tarkistettiin samoiksi ennen sovelluksen
uudelleenkäynnistystä. Korjaus ei tee skeemapäivitystä tai metatietojen täyttöä.
Vanhaa projektia ei muutettu. Ulkoisia API-kutsuja ja pushia ei tehty.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests
node .\tests\ui_memory_test.cjs
& .\.venv\Scripts\python.exe -B .\tests\evaluate_memory_ranking.py --split development
& .\.venv\Scripts\python.exe -B .\tests\evaluate_memory_ranking.py --split final
```

Loppuarviointi edellyttää tämän toteutuksen paikallista jäädytystiedostoa
`data/ranking-evaluation/implementation-freeze.json`. Sen tarkistussummat
estävät muuttuneen toteutuksen nimeämisen samaksi loppuarvioinniksi.
Vertailu lukee lähtökoodin paikallisesta commitista `2404b9e`.

- [Kaikki 17 kehityskyselyä, kolme järjestystä ja pisteet](../data/ranking-evaluation/development-20261024T093341698646Z/report.md)
- [Kaikki 21 uutta loppukyselyä, kolme järjestystä, ryhmät ja virheet](../data/ranking-evaluation/final-20261024T093554464018Z/report.md)
- Molempien paikallisten raporttien vieressä ovat `results.json`, lukittu
  aineistokopio, erillinen testitietokanta ja sen oma vektorivälimuisti.
- Käynnistyksen ja käyttäjän tietokannan tarkistus: `data/ranking-evaluation/application-check.json`.

Paikalliset raportit ja tietokannat ovat Gitin ulkopuolella. Sovellus on
käynnissä osoitteessa `http://127.0.0.1:8502/memory` ilman API-avainta.
Selain on päivitettävä palvelimen uudelleenkäynnistyksen jälkeen.
