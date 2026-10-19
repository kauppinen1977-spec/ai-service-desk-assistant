# GitHub-julkaisusuunnitelma ja tarkistusraportti – 19.10.2026

## Päätös ja rajaus

Valmistellaan pieni PoC-lähdekoodijulkaisu: sovellus, 30 runbookia ja manifesti,
riippuvuuksien määrittely, nykyinen käyttöohje, PoC-testiraportti ja
yksityisistä arviointiaineistoista riippumaton testivalikoima.
Suunniteltu tiedostomäärä on **58**, joista 30 on runbookeja.
Tämä raportti ei ole lupa julkaisuun, API-kokeisiin tai batch2:n aloittamiseen.

Projektissa ei ole Git-repositoriota eikä tähän kansioon määritettyä
etärepositoriota. Git-repositoriota ei alustettu, eikä commitia tai pushia tehty.
Julkaisuosoitetta ei keksitty eikä lisenssiä lisätty.

## Julkaistavat tiedostot

Alla oleva luettelo on julkaisun sallintalista, ei nykyisen Git-indeksin tuloste.
`.gitignore` rajaa julkaisun näihin tiedostoihin. Uuden tiedoston lisääminen
vaatii julkaisurajauksen tietoisen päivityksen.

### Sovellus, riippuvuudet ja ympäristöesimerkki (12)

```text
.gitignore
.env.example
README.md
app.py
desk.py
response_rules.py
search.py
corpus.py
index.html
valmistele_haku.py
requirements.txt
requirements-vector.txt
```

`requirements.txt` ei asenna paketteja: sanahaku käyttää standardikirjastoa.
`requirements-vector.txt` määrittelee Sentence Transformers -riippuvuuden.
PyTorchin CPU-asennus ja batch1-mallin valmistelu neuvotaan README:ssä.
`.env.example` sisältää tyhjän avainkentän; se ei ole toimiva avain eikä
sovellus lataa tiedostoa automaattisesti.

### Runbookit ja manifesti (31)

```text
knowledge/DEVICE-001.json
knowledge/DEVICE-002.json
knowledge/DEVICE-003.json
knowledge/DEVICE-004.json
knowledge/DEVICE-005.json
knowledge/IAM-001.json
knowledge/IAM-002.json
knowledge/IAM-003.json
knowledge/IAM-004.json
knowledge/IAM-005.json
knowledge/IAM-006.json
knowledge/MAIL-001.json
knowledge/MAIL-002.json
knowledge/MAIL-003.json
knowledge/MAIL-004.json
knowledge/MAIL-005.json
knowledge/NET-002.json
knowledge/NET-003.json
knowledge/NET-004.json
knowledge/VPN-001.json
knowledge/batch1/DEVICE-006.json
knowledge/batch1/DEVICE-007.json
knowledge/batch1/DEVICE-008.json
knowledge/batch1/DEVICE-009.json
knowledge/batch1/DEVICE-010.json
knowledge/batch1/DEVICE-011.json
knowledge/batch1/DEVICE-012.json
knowledge/batch1/IAM-007.json
knowledge/batch1/IAM-008.json
knowledge/batch1/IAM-009.json
knowledge/corpora/batch1.json
```

20 alkuperäistä ja 10 batch1-ohjetta julkaistaan muuttumattomina.
Manifestin SHA-256-viittausten pitää täsmätä kaikkiin 30 runbookiin.
Työversion DEVICE-004-turvallisuusrajaus toteutetaan sovelluksessa;
se ei muuta jäädytettyä runbook-sisältöä tai baselinea.

### Dokumentit (2)

```text
docs/10_poc_valitavoite_2026-10-19.md
docs/11_github_julkaisusuunnitelma_2026-10-19.md
```

README on nykyisen julkaisun ensisijainen asennusohje. Vanhoja
`ALOITA_TASTA.md`- ja päivityspakettiohjeita ei sisällytetä tähän julkaisuun.
PoC-raportissa mainitut yksityiset polut ovat historiallisia viittauksia;
niiden sisältö ei sisälly julkaisuun.

### Hyväksytty testivalikoima ja esimerkkivastaus (13)

```text
tests/test_search.py
tests/test_response_rules.py
tests/test_summary.py
tests/test_http.py
tests/test_safety_stop.py
tests/test_hybrid_fallback.py
tests/test_startup_applicability.py
tests/ui_state_test.cjs
tests/ui_candidate_visibility_test.cjs
tests/ui_safety_stop_test.cjs
tests/ui_startup_fact_test.cjs
tests/ui_ticket_clear_test.cjs
tests/fixtures/v03_vpn_response.json
```

Seitsemän Python-moduulia eivät tarvitse yksityisiä arviointiaineistoja.
Ne kattavat hakusääntöjä ja synteettistä vektorihakua, soveltuvuutta,
turvallisuusetusijaa, lähteistettyjen vastausten kokoamista, hybridivarahakua
sekä paikallista HTTP-ketjua. Synteettiset hakupisteet eivät ole laatumittaus.
Aiemmista tapauksista syntyneet regressiot eivät ole riippumaton loppuarviointi.

Viisi JavaScript-moduulia tarkistavat DOM-korvikkeessa tilat, lähdeviitteet,
ehdokkaiden vaiheiden piilottamisen, turvallisuuskeskeytyksen, käynnistyshavainnon
ja syötekentän tyhjentymisen. Ne eivät ole oikean selaimen testejä.
`ui_state_test.cjs` lukee julkaistavan `v03_vpn_response.json`-esimerkin.
Tämä historiallinen 0.3-fixture on renderöintisyöte, ei tuore mallivastaus tai
nykyisen haun laatutulos. Sen `model_used=true` ei todista todellista API-kutsua.

Suorat Node-komennot on annettu README:ssä. Myös muut kolme moduulia voi ajaa
projektin juuressa niiden olemassa olevalla vientifunktiolla, esimerkiksi:

```powershell
node -e "const fs=require('node:fs'); require('./tests/ui_safety_stop_test.cjs')(fs.readFileSync('index.html','utf8')).then(console.log).catch(e=>{console.error(e);process.exitCode=1})"
node -e "const fs=require('node:fs'); require('./tests/ui_startup_fact_test.cjs')(fs.readFileSync('index.html','utf8')).then(console.log).catch(e=>{console.error(e);process.exitCode=1})"
node -e "const fs=require('node:fs'); require('./tests/ui_ticket_clear_test.cjs')(fs.readFileSync('index.html','utf8')).then(console.log).catch(e=>{console.error(e);process.exitCode=1})"
```

## Pois jätettävät tiedostot ja hakemistot

| Rajaus | Peruste |
|---|---|
| Koko `evaluation/` | Yksityiset kehitys- ja arviointiaineistot, holdoutit, tulokset, käsinarviot ja jäädytetty baseline |
| Koko `evaluation/baselines/` | Julkaisu ei saa sisältää vajaata baselinea; koko hakemisto jätetään pois |
| Holdout-nimiset tiedostot ja hakemistot | Riippumattoman arvioinnin suojaaminen; holdout B:n sisältöä ei avattu |
| `palautus/` | Palautus- ja raportointiaineisto ei kuulu tähän lähdekoodijulkaisuun |
| `backups/`, ZIPit ja varmuuskopiot | Sisältöä ei hyväksytty julkiseksi; ZIPejä ei avattu |
| `data/`, mallivälimuistit ja `.venv/` | Paikallinen ympäristö ja generoitu data; muodostetaan käyttäjän koneella |
| `.env`, `.env.*` paitsi tyhjä esimerkki, avain- ja tunnistetiedostot | Salaisuuksien suojaaminen |
| Lokit, Python-välimuistit, työkalujen välimuistit ja väliaikaistiedostot | Paikalliset tuotokset |
| `arvioi_haku.py`, `arvioi_lopputesti.py`, `arvioi_toiminta.py` | Arviointityökalut tarvitsevat pois rajattuja aineistoja |
| `test_desk.py`, `test_demo_chain.py`, `test_batch1.py`, `test_applicability_evidence.py`, `test_arvioi_toiminta.py` | Sidokset yksityisiin aineistoihin; paikalliset tiedostot säilyvät |
| `test_update.py` ja päivitystyökalut | Vanhan päivityspaketin työnkulku ei sisälly puhtaaseen asennukseen |
| `ui_demo_chain_test.cjs`, `ui_batch1_test.cjs` | Julkaisun ulkopuolisia testisyötteitä tai raportteja vaativa työnkulku |
| Vanhat dokumentit, runbook-mallipohja ja muut sallintalistan ulkopuoliset tiedostot | Julkaisun koon ja ohjeiden ristiriitojen rajaaminen |

Mitään näistä ei poisteta paikallisesta projektista. Vanhat 66 regressiotapausta,
48 kehitystapausta, aiemmat mittaukset ja baseline säilyvät yksityisinä ennallaan.
Git-ohitukset eivät estä tiedoston pakottamista mukaan `git add -f` -komennolla
eivätkä poista jo versionhallinnassa olevaa tiedostoa. Tässä kansiossa ei vielä
ole Git-indeksiä.

## Komentojen tarkistus lähdekoodista

| Komento tai valinta | Lähdekoodin peruste |
|---|---|
| `app.py --corpus batch1 --port 8501` | `app.py`: corpus- ja porttiparametrit, localhost-sidonta |
| Demo/live ja keyword/vector | Käyttöliittymän valinnat ja HTTP-pyynnön kentät; eivät app.py:n CLI-parametreja |
| `valmistele_haku.py --corpus batch1` | Skriptin argparse; muodostaa `data/vectors-batch1.json`-välimuistin |
| `--offline` valmistelussa | Asettaa mallikirjastojen offline-ympäristömuuttujat |
| PyTorchin CPU-asennus ja vector-riippuvuudet | Nykyisen `asenna_vektorihaku.bat`-työkalun asennuskomennot |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | `desk.call_model()`; oletusmalli `gpt-4.1-mini` |
| Sanahaku ilman paketteja | Hakumoduulin perustuonnit; Sentence Transformers tuodaan vasta vektorihaussa |
| `py -3.13 -m venv .venv` ja unittest | Pythonin työkalukomennot; eivät projektin omia CLI-valintoja |

Vanha asennus-BAT luo virtuaaliympäristön ja valmistelee oletuksena legacy20:n.
Siksi sitä ei sisällytetä uuden julkaisun asennuspolkuun. README neuvoo
batch1:n valmistelun eksplisiittisesti eikä oleta julkaistavaa vektorivälimuistia.
Offline-muuttujat eivät ole yleinen verkkoesto. Pakettiasennukset ja ensimmäinen
mallin hankinta vaativat verkkoyhteyden. Niitä ei tehty tätä raporttia laadittaessa.

## Tietosuoja- ja salaisuustarkistus

Julkaistavan sovelluksen, dokumenttien, valittujen testien, VPN-fixturen ja
runbookien tekstisisällöt tarkistettiin avainmallien ja henkilötietoviitteiden
varalta. Avainarvoja tai muita salaisuuksia ei tulostettu.
Esimerkkipyynnöissä ja VPN-fixturessa ei havaittu henkilötietoja tai salaisuuksia.

- Ei havaittuja OpenAI-/GitHub-/AWS-avainmallisia arvoja, yksityisiä avaimia,
  sähköpostiosoitteita, suomalaisen henkilötunnuksen mallisia arvoja tai paikallisia
  käyttäjähakemistopolkuja julkaistavassa sisällössä.
- **Poikkeus henkilötiedottomuuteen:** alkuperäisten 20 runbookin `owner`-kentässä
  on tekijän henkilönimi. 10 uudessa ohjeessa omistaja on kuvattu projektin tekijänä.
  Tekijä on hyväksynyt nimen näkymisen julkisessa repositoriossa.
  Runbookien metatietoja ei muuteta.
- `.env.example` sisältää tyhjän avainkentän. Testien mock-tunnisteet eivät ole
  toimivia palveluavaimia.
- Poissuljettujen ZIPien, mallien ja yksityisten arviointiaineistojen sisältöä
  ei hyväksytä tämän tarkistuksen perusteella julkaistavaksi.
- Holdout B:tä ei avattu. Kuvailevien avainmallien skannaus ei todista kaikkien
  salaisuuksien puuttumista; lopullinen julkaistava sisältö on tarkistettava uudelleen.

## Suoritetut tarkistukset

- Seitsemän julkaisuun valittua Python-testimoduulia: **161/161 läpäisi**
  Anacondan Python 3.13.9:llä. Ensimmäisellä ajolla yksi localhost-HTTP-testi
  katkesi virheeseen `WinError 10053`; koko rajatun valikoiman uusinta läpäisi.
  Virheen syytä ei todettu, eikä testiä tai suojausasetuksia muutettu.
- JavaScript: ehdokasnäkyvyys 17/17, safety_stop-renderöinnit 3/3,
  käynnistyshavainnon renderöinti, syötekentän tyhjennys- ja virhepolut sekä
  UI state/render -testi läpäisivät. Suoritus tapahtui Node.js:n VM/DOM-korvikkeessa.
- Sovellusparametrit, manifestin 30 ohjetta ja testien tiedostoriippuvuudet
  tarkistettiin lähdekoodista. Ensimmäisessä dokumentointivaiheessa asennus- ja
  verkkolatauskomentoja ei ajettu; myöhempi puhdas asennus kuvataan alla.
- Staattinen sääntötarkistus vastasi täsmälleen 58 tiedoston sallintalistaa.
  Kaikki 14 poissulkukokeilua (salaisuudet, välimuistit, baseline, holdout-polku
  ja uudet hyväksymättömät tiedostot) jäivät pois. Tämä ei ole
  `git check-ignore`- tai staging-tarkistus, koska repositoriota ei alusteta.
- Kaikkien 30 manifestilähteen SHA-256-tarkistukset täsmäsivät. Sovelluskoodin
  ja knowledge-hakemiston tiedostojen alku- ja lopputarkistussummat olivat samat.
  Julkaistavan tekstin avain- ja henkilötietomallien tarkistuksesta ei tullut
  uusia löydöksiä; tekijänimet ovat edellä erikseen kuvattu henkilötietohavainto.
  Markdownin koodilohkot ja UTF-8-merkistö tarkistettiin.
- Tämän työn tiedostomuutokset rajataan `.gitignore`- ja README-tiedostoihin sekä
  tähän uuteen raporttiin. Sovelluskoodiin, runbookeihin ja testidataan ei tehdä muutoksia.

## Puhtaan Windows-asennuksen vahvistetut tulokset

Todisteen lähde on käyttäjän ilmoittama testi tavallisessa Windows PowerShellissä
erillisessä `AI-Desk-Clean-Test`-kansiossa. Alla olevia tuloksia ei väitetä
tässä dokumentointivaiheessa uudelleen ajetuiksi. Palvelinlokia, koko pip-lokia
tai selaintallennetta ei ole liitetty tähän raporttiin.

| Vaihe | Käyttäjän vahvistama tulos |
|---|---|
| Julkaisukopio | 58/58 tiedostoa kopioitu SHA-256-tarkistuksella; alkuperäistä ympäristöä ei kopioitu |
| Python | Python 3.13.9 toimi uudessa ympäristössä |
| Riippuvuudet | PyTorch ja vektoririippuvuudet asentuivat |
| Python-testit | 161/161 läpäisi |
| Batch1-valmistelu | 30 ohjetta ja 162 tekstiosaa; oma vektori-indeksi muodostui |
| Offline-valmistelu | Onnistui paikallisella mallilla |
| Edge ja vektorihaku | VPN-001 ensimmäinen ehdokas; NET-003 ja NET-004 hylättiin soveltumattomina |

Tulos vahvistaa tämän 30 ohjeen julkaisukopion paikallisen asennuksen ja
yhden vektorihakupyynnön käyttäjälle näkyvän ketjun. Se ei ole kaikkien
hakutapausten laatumittaus, riippumaton holdout-arviointi tai oikean
OpenAI-live-vastauksen onnistumisen vahvistus. Käyttäjän uusi tulos ei myöskään
vahvista Node.js:n CLI-testien suorittamista; aiemmat JavaScript-tulokset
olivat VM/DOM-testejä. Pakettien täsmällisiä asennettuja versioita ei toimitettu.

Codexin aiemmassa testissä `py -3.13` ei löytänyt tulkkia, mutta Anacondasta
luotu eristetty 3.13.9-ympäristö toimi. Siellä paketti-indeksin yhteys estyi
socket-virheeseen 10013. Se ei kumoa tavallisessa PowerShellissä onnistunutta
asennusta eikä osoita Python 3.13:n yhteensopivuusvirhettä.

README on päivitetty edellyttämään toimivaa `py -3.13` -komentoa tavallisessa
PowerShellissä, erottamaan maksuton sanahaku ja valinnainen vektorihaku sekä
pysäyttämään asennusketju virheelliseen paluukoodiin. Tekijänimen julkaisu on
hyväksytty ja lisenssitiedosto jätetään käyttäjän päätöksen mukaisesti lisäämättä.
Tämän viimeistelyn muutokset koskevat vain README:tä ja tätä raporttia.
Julkaistavien tiedostojen määrä säilyy 58:ssa. Dokumenttien päivityksen vuoksi
aiemman kopion SHA-256-summat eivät kuvaa näitä kahta uutta dokumenttiversiota;
mahdollinen lopullinen julkaisukopio pitää synkronoida ja tarkistaa uudelleen.

Viimeistelyn uusintatarkistuksessa raportin 58 tiedostoa vastasivat staattisesti
`.gitignore`-rajausta. Yhdeksän poissulkukokeilua jäivät pois; julkaistavan
tekstin salaisuus- ja henkilötietomallien skannauksessa ei ollut uusia löydöksiä.
Hyväksytty owner-nimi säilyi ohjeissa. Kaikki 30 manifestitarkistusta täsmäsivät,
ja sovelluskoodin sekä knowledge-hakemiston tarkistussummat säilyivät ennallaan.
Tässä viimeistelyssä ei ajettu yksikkötestejä tai uutta asennusta.

## Turvallinen Git-alustus ja ensimmäinen commit – vain hyväksynnän jälkeen

Seuraavat komennot ovat suunnitelma. Niitä ei ole suoritettu.
Aja ne tavallisessa PowerShellissä alkuperäisen projektin juuressa.
Varmista ensin, ettei kansio ole jo osa toista Git-repositoriota:

```powershell
git --version
git rev-parse --show-toplevel
```

Nykytilassa jälkimmäisen kuuluu ilmoittaa, ettei repositoriota ole.
Jos se palauttaa hakemistopolun, keskeytä ja tarkista olemassa oleva repo.
Hyväksyttyä uutta alustusta varten:

```powershell
git init -b main
if ($LASTEXITCODE -ne 0) { throw 'Git-alustus epäonnistui.' }
git status --short --untracked-files=all
git check-ignore -v -- .env .env.local .venv/Scripts/python.exe data/vectors-batch1.json backups/example.zip evaluation/baselines/batch1-30-20261019-v1/manifest.json
git add --dry-run -- .
```

Varmista, että yksityiset polut ohittuvat ja kuivaharjoittelu näyttää vain
yllä olevat 58 tiedostoa. Lue tämän raportin neljä `text`-luetteloa ja lisää
vain niiden tiedostot staging-alueelle:

```powershell
$report = Get-Content -Raw -Encoding UTF8 .\docs\11_github_julkaisusuunnitelma_2026-10-19.md
$fence = ([char]96).ToString() * 3
$blocks = [regex]::Matches($report, ('(?ms)^' + $fence + 'text\r?\n(.*?)^' + $fence + '\s*$'))
$files = @($blocks | ForEach-Object { $_.Groups[1].Value -split '\r?\n' } | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Sort-Object -Unique)
if ($blocks.Count -ne 4 -or $files.Count -ne 58) { throw 'Odottamaton julkaisuluettelo.' }
git add -- $files
if ($LASTEXITCODE -ne 0) { throw 'Staging epäonnistui.' }
$staged = @(git diff --cached --name-only)
if ($LASTEXITCODE -ne 0) { throw 'Staging-luetteloa ei saatu.' }
if (@(Compare-Object $files $staged).Count -ne 0) { throw 'Staging ei vastaa julkaisuluetteloa.' }
git diff --cached --stat
git diff --cached --check
git ls-files -ci --exclude-standard
```

Viimeisen komennon ei pidä tulostaa ohitettavia seurattuja tiedostoja.
Tarkista staged-sisältö paikallisesti salaisuuksien varalta ennen commitia;
älä kopioi mahdollisia salaisuuksia keskusteluun. Älä käytä `git add -f` -komentoa.
Varmista myös, että Gitin commit-tekijän nimi ja sähköposti ovat tarkoitetut
julkiset metatiedot. Runbookin owner-nimen hyväksyntä ei valitse Git-identiteettiä.

Vasta tarkistusten ja erillisen commit-hyväksynnän jälkeen:

```powershell
git commit -m "Initial PoC release: batch1 with 30 runbooks"
git status --short --branch
```

Etärepositoriota ei lisätä eikä pushia tehdä tällä suunnitelmalla.

## Jäljellä olevat rajaukset

1. Lisenssiä ei lisätä tässä vaiheessa. Tämä on tietoinen päätös, ei avoin
   tekijänimen hyväksyntäeste. Julkinen näkyvyys ei anna automaattista
   uudelleenkäyttölupaa.
2. Riippuvuuksia ei ole täsmällisesti lukittu; tuleva pip-asennus voi tuottaa
   eri versiot. Python 3.14:n puhdasta vektoriasennusta ei ole osoitettu.
3. Oikean OpenAI-palvelun onnistuminen, riippumaton yleistymiskyky ja kaikki
   turvallisuusparafraasit eivät ole tämän asennustestin todentamia.
4. Oikea Git-ohitus- ja staging-tarkistus voidaan tehdä vasta hyväksytyn
   alustuksen jälkeen. Nykyinen tarkistus on staattinen.
5. Ennen julkaisua hyväksytään vielä Git-alustus, ensimmäinen commit,
   etärepositorion näkyvyys ja mahdollinen push erikseen.

Git-julkaisua, API-kutsuja, holdout B:n avaamista tai batch2:ta ei aloitettu.
