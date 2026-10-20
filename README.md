# AI Service Desk Assistant – PoC

Paikallinen IT-palvelupisteen avustajaprototyyppi. Julkaisuun rajattu
`batch1`-kokonaisuus sisältää 30 kuvitteellisen harjoitusorganisaation runbookia.
Sovellus erottaa hakuehdokkaat hyväksytystä ratkaisuehdotuksesta ja näyttää
ratkaisuvaiheiden lähteet, alkuperäiset vaihenumerot ja versiot.

Maksuton sanahakudemo toimii Pythonin standardikirjastolla. Valinnaisessa
live-tilassa OpenAI valitsee soveltuvista lähteistä enintään yhden; sovellus
kokoaa näytettävät vaiheet runbookista. Mallin omia ratkaisuvaiheita ei näytetä.
Vaaratilanteen deterministinen `safety_stop` ohittaa haun ja mallikutsun.

## Asiakasnäkymä ja IT-diagnostiikka

Asiakasnäkymä näyttää vastauksen tilan, hyväksytyt ratkaisuvaiheet,
tarkentavat kysymykset, jatkotoimet ja lähdeviitteet. Oletuksena suljettu
**IT-asiantuntijan diagnostiikka** avataan otsikosta hiirellä tai näppäimistöllä.
Se sisältää hakuehdokkaat, pisteet, soveltuvuus- ja hylkäysperusteet,
tekstiosatunnukset, käsittelytilan, hakutavan, mallin käytön ja havaintojen
tunnistusselitykset. Osion avaaminen ei lähetä uutta pyyntöä eikä rajaa käyttöoikeuksia.
Turvallisuuskeskeytys ja ensiohjeet näkyvät heti asiakasnäkymässä.

Sovellus voi kysyä havaintoja myös ilman valittua ratkaisulähdettä.
Lähteettöminä hyväksytään vain kolme sovelluksen omaa, täsmällisesti sallittua
tarkennuskysymystyyppiä:

- Epäselvä työpalvelu tai ohjelma: mikä palvelu ei avaudu ja mikä virheilmoitus näkyy.
- Ristiriitaiset internet- ja VPN-havainnot: toimivatko verkkosivut samalla laitteella
  ilman VPN-yhteyttä ja mitä etäyhteyden virheilmoituksessa lukee.
- Samanaikaiset laitteen ja viestitilan ongelmat: missä kumpikin tilailmoitus
  näkyy ja mitä ilmoituksissa tarkalleen lukee.

Nämä kysymykset eivät vahvista diagnoosia tai anna toimintavaltuuksia.
Tunnistus perustuu rajattuihin tekstisääntöihin. Ratkaisuvaiheita ei näytetä
ilman hyväksyttyä lähdettä. Turvallisuuskeskeytys ohittaa tarkennuskysymykset.

## PoC-tilanne 20.10.2026

Käyttäjä vahvisti Edge-kokeissa asiakasnäkymän, diagnostiikan avaamisen ja
sulkemisen, VPN-hakudemon sekä turvonneen akun turvallisuuskeskeytyksen toimivan.
Käyttäjän vahvistama oikea OpenAI-live-kutsu tuotti VPN-001:n kolme hyväksyttyä
ratkaisuvaihetta ja tarkentavan kysymyksen. Tämä yksittäinen kokeilu ei ole
kielimallin riippumaton laatuarviointi.

Paikallisen kehitysympäristön automaattiset tarkistukset 20.10.2026:

| Tarkistus | Tulos ja rajaus |
|---|---|
| Python | 248/248: julkaisukopion 174 testiä ja 74 paikallista lisätestiä |
| JavaScript | 7/7 käyttöliittymätestimoduulia; kaksi tarvitsee yksityiset raporttisyötteet |
| Uusi demoketju | 9/9 vaatimustarkistusta ja 24 renderöityä vastausta 12 demokortista |
| Batch1-käyttöliittymätesti | 96/96 tallennetun demo-/mock-live-vastauksen renderöintiä |

Automaattiset ajot eivät tehneet OpenAI-kutsuja. Python-ajot tehtiin
kehitysympäristön Python 3.14.2:lla ja JavaScript-ajot Node.js v24.22.0:lla.
Ne eivät ole uusi puhtaan asennuksen testi. Arviointiohjelman baseline-/holdout-
aineistoja lataavaa testimoduulia ei ajettu. Paikallisen 248 testin kokonaisuuden
sekä kahden raporttisyötteitä tarvitsevan JavaScript-moduulin toistaminen
edellyttää myös julkaisemattomia aineistoja tai työkaluja. Käyttöliittymätestit
käyttävät DOM-korviketta; niiden tulokset eivät korvaa visuaalista selainkoetta.

## Aiempi PoC-tilanne 19.10.2026

Käyttäjän ilmoittamassa live-tilan selainkokeessa VPN-001 näytti kolme
ratkaisuvaihetta, tarkentavan kysymyksen ja lähdeviitteet. Oikean API-kutsun
onnistumista ei ole erikseen vahvistettu palvelinlokista. Mockattu HTTP-live-ketju
ja JavaScriptin renderöintitesti läpäisivät tarkistukset; ne eivät ole oikean
kielimallin tai selaimen testejä.

Käyttäjän vahvistama puhdas Windows-asennus tavallisessa PowerShellissä onnistui:
58/58 julkaisutiedostoa tarkistettiin SHA-256:lla, Python 3.13.9 ja
vektoririippuvuudet toimivat ja 161/161 Python-testiä läpäisi. Batch1-indeksi
muodostui (30 ohjetta, 162 tekstiosaa), ja offline-valmistelu onnistui.
Edge-selaimen vektorihakukokeessa VPN-001 oli ensimmäinen ehdokas; NET-003 ja
NET-004 hylättiin soveltumattomina. Tämä oli hakudemon testi, ei oikean
OpenAI-vastauksen tai koko riippumattoman testiaineiston arviointi.

- [PoC-välitavoitteen testiraportti](docs/10_poc_valitavoite_2026-10-19.md)
- [Julkaisusuunnitelma ja tarkistusraportti](docs/11_github_julkaisusuunnitelma_2026-10-19.md)

Ei tuotantokäyttöön. Käytä vain kuvitteellisia tukipyyntöjä. Organisaatiokohtaiset
menettelyt vaativat ihmisen tarkistuksen. Sovellus ei tee oikeusmuutoksia,
turvallisuusilmoituksia tai tiketin siirtoa käyttäjän puolesta.

## Puhdas Windows-asennus: maksuton sanahakudemo

Tämä asennuspolku edellyttää 64-bittistä Python 3.13:a ja Windowsin
`py`-käynnistintä. Todettu versio on Python 3.13.9. Pelkkä toisen Python-version
tai Anacondan olemassaolo ei takaa, että `py -3.13` toimii. Aja komennot
tavallisessa Windows PowerShellissä omalla käyttäjätunnuksellasi; Codexin
rajoitetun suoritusympäristön tulos ei vastaa tavallisen PowerShellin verkkoyhteyttä.

Lataa projektin hyväksytty julkaisukopio
[GitHub-repositoriosta](https://github.com/kauppinen1977-spec/ai-service-desk-assistant)
ja pura se omaan kansioon. Avaa PowerShell ja siirry kansioon, jossa `app.py`
sijaitsee. Käytä uutta kansiota; älä korvaa olemassa olevaa virtuaaliympäristöä.

```powershell
py -3.13 --version
if ($LASTEXITCODE -ne 0) { throw 'Asenna Python 3.13 ja varmista py-käynnistimen toiminta ennen jatkamista.' }
py -3.13 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtuaaliympäristön luonti epäonnistui.' }
& .\.venv\Scripts\python.exe --version
```

Ensimmäisen komennon pitää tulostaa `Python 3.13.x`. Jos saat `No installed
Python found` tai `py` ei löydy, asenna Python 3.13 ja sen käynnistin ja avaa
PowerShell uudelleen. Älä ohita tätä vaihetta tai luo ympäristöä vahingossa
toisella tulkilla. Olemassa olevaan toimivaan `.venv`-kansioon ei ajeta
luontikomentoa uudelleen. Python 3.14 ei ole tämän puhtaan asennuspolun testattu versio.

Virtuaaliympäristöä ei tarvitse aktivoida eikä PowerShellin suorituspolitiikkaa
muuttaa. `requirements.txt` ei sisällä asennettavia paketteja:
sanahakudemo ei tarvitse pip-asennusta, API-avainta tai upotusmallia.

Käynnistä 30 runbookin sovellus seuraavasti. Komento poistaa mahdollisen
API-avaimen vain palvelinprosessin ympäristöstä, estää mallikirjastojen
verkkolataukset ja jättää PowerShell-istunnon ympäristön ennalleen:

```powershell
& .\.venv\Scripts\python.exe -B -c "import os,runpy; os.environ.pop('OPENAI_API_KEY',None); os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1'); runpy.run_path('app.py',run_name='__main__')" --corpus batch1 --port 8501
```

Avaa `http://127.0.0.1:8501`. Tarkista `Ohjekokonaisuus: batch1`.
Valitse **Vain haku** ja **Sanahaku**; käyttöliittymän oletushakutapa on vektorihaku,
joten valinta pitää vaihtaa ennen ensimmäistä analyysiä.

Kokeile: `VPN ei yhdistä. Tavalliset verkkosivut avautuvat ilman VPN-yhteyttä.`
Odotus: VPN-001 hyväksytään soveltuvaksi hakuehdokkaaksi, mutta demo ei valitse
ratkaisua eikä näytä ehdokkaiden toimintavaiheita. OpenAI-kutsua ei tehdä.
Onnistunut analyysi tyhjentää syötekentän ja säilyttää vastauksen; virhe säilyttää syötteen.

Lopeta palvelin Ctrl+C:llä. Jos portti on varattu, käytä `--port 8502` ja avaa
vastaava osoite. Tarkista oikea palvelin tarvittaessa osoitteesta `/health`:
avaimettomassa demossa `corpus` on `batch1` ja `api_key_available` on `false`.
Jos tiedot eivät täsmää, älä jatka analyysiin vaan tarkista osoite ja palvelin.
Käynnistys ilman `--corpus batch1` -valintaa käyttää alkuperäistä
20 ohjeen `legacy20`-aineistoa.

## Valinnainen paikallinen vektorihaku

Tämä vaihe tarvitsee aluksi verkkoyhteyden pakettien ja upotusmallin lataamiseen.
Se ei käytä OpenAI API:a. Tarkista organisaatiosi lupa latauksiin.
Suorita projektin juuresta, kun edellinen palvelin on pysäytetty:

```powershell
& .\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'PyTorch-asennus epäonnistui. Älä jatka vektorihakuun.' }
& .\.venv\Scripts\python.exe -m pip install -r .\requirements-vector.txt
if ($LASTEXITCODE -ne 0) { throw 'Vektoririippuvuuksien asennus epäonnistui.' }
& .\.venv\Scripts\python.exe -B .\valmistele_haku.py --corpus batch1
if ($LASTEXITCODE -ne 0) { throw 'Batch1-indeksin valmistelu epäonnistui.' }
```

Ensimmäinen valmistelu hakee tarvittaessa mallin
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` ja kirjoittaa
paikallisen `data/vectors-batch1.json`-välimuistin. Valmistelun pitäisi ilmoittaa
`Valmis: 30 ohjetta`, tekstiosien määrä ja kokeiluhaun tulos. Nykyisellä
aineistolla puhtaassa testissä muodostui 162 tekstiosaa. Älä jatka, jos
valmistelu epäonnistuu. Paketteja tai mallia ei sisällytetä Git-julkaisuun.

Kun malli on paikallisesti saatavilla, voit tarkistaa valmistelun ilman
mallin verkkolatausta:

```powershell
& .\.venv\Scripts\python.exe -B .\valmistele_haku.py --corpus batch1 --offline
if ($LASTEXITCODE -ne 0) { throw 'Offline-valmistelu epäonnistui.' }
```

Myös offline-valmistelu voi kirjoittaa erän vektorivälimuistin; se ei ole
pelkkä lukutarkistus. Käynnistä tämän jälkeen sovellus yllä olevalla
avaimettomalla komennolla ja valitse **Vain haku** sekä **Vektorihaku**.
Offline-ympäristömuuttujat ohjaavat mallikirjastoja, eivät muodosta yleistä palomuuria.
Ilman niitä hakukoodi voi yrittää ladata puuttuvan mallin verkosta.

Todetussa Edge-kokeessa yllä oleva VPN-pyyntö nosti VPN-001:n ensimmäiseksi
ehdokkaaksi. NET-003 ja NET-004 eivät läpäisseet soveltuvuussuodatusta.
Hakuehdokkaiden toimintavaiheita ei pidä tulkita valituksi ratkaisuksi:
maksuton demo ei muodosta OpenAI-ratkaisuehdotusta.

## Valinnainen OpenAI-live-tila

Live-analyysi voi aiheuttaa API-kulun. Pelkkä palvelimen käynnistäminen ei tee
mallikutsua. Käytä erikseen hyväksyttyä API-avainta ja vain kuvitteellista pyyntöä.
Pysäytä avaimeton palvelin ennen uudelleenkäynnistystä.

```powershell
$avain = Read-Host 'OpenAI API-avain' -AsSecureString
$env:OPENAI_API_KEY = ([System.Net.NetworkCredential]::new('', $avain).Password).Trim()
$env:OPENAI_MODEL = 'gpt-4.1-mini'
& .\.venv\Scripts\python.exe -B .\app.py --corpus batch1 --port 8501
```

Avaa sama osoite, valitse **OpenAI – lähteisiin sidottu ratkaisuehdotus** ja
ensimmäiseen kokeeseen **Sanahaku**. Käytä yllä olevaa VPN-pyyntöä.
Kun malli valitsee VPN-001:n `suggestion`-tilassa, sovellus näyttää alkuperäiset
vaiheet 2–4 ja virheilmoituskysymyksen. Malli voi myös pyytää lisätietoja tai pidättäytyä.

`.env.example` sisältää vain muuttujien nimet. Sovellus ei lataa `.env`-tiedostoa
automaattisesti. Älä kirjoita avainta lähdekoodiin, tukipyyntöön tai versionhallintaan.
Avain on palvelinprosessissa tavallisena ympäristömuuttujana; salattu syöte estää
sen näkymisen kirjoitetussa komennossa. Kokeen jälkeen pysäytä palvelin ja sulje
PowerShell-istunto tai poista muuttuja:

```powershell
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Variable avain -ErrorAction SilentlyContinue
```

## Julkaisuun rajatut testit

Julkaisukopio sisältää seitsemän yksityisistä arviointiaineistoista riippumatonta
Python-testimoduulia, yhteensä 174 testiä. Paikallisessa 248 testin ajossa oli
lisäksi 74 testiä, joiden tarvitsemia aineistoja tai työkaluja ei julkaista.
Python-testit käyttävät synteettisiä upotuksia ja mockattuja vastauksia;
ne eivät mittaa oikean mallin laatua.
Testit voivat kirjoittaa omia väliaikaistiedostojaan, ja HTTP-testit käyttävät localhostia.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Tämä discovery-komento koskee rajattua julkaisukopiota. Täysi paikallinen
kehityskansio sisältää lisäksi yksityisiin arviointiaineistoihin liittyviä testejä.
Rajattu testivalikoima voidaan ajaa kummassakin seuraavasti:

```powershell
& .\.venv\Scripts\python.exe -B -c "import sys,unittest; sys.path.insert(0,'tests'); names=['test_search','test_response_rules','test_summary','test_http','test_safety_stop','test_hybrid_fallback','test_startup_applicability']; result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names)); sys.exit(not result.wasSuccessful())"
```

Julkaisukopio sisältää seitsemän JavaScript-käyttöliittymätestimoduulia.
Niistä viisi voidaan ajaa julkisilla tiedostoilla. Valinnainen Node.js tarvitaan
vain näihin testeihin; npm-paketteja ei tarvitse asentaa. Aja projektin juuressa:

```powershell
node --version
node .\tests\ui_state_test.cjs
node .\tests\ui_candidate_visibility_test.cjs
node -e "const fs=require('node:fs'); const html=fs.readFileSync('index.html','utf8'); (async()=>{for(const name of ['ui_safety_stop_test','ui_startup_fact_test','ui_ticket_clear_test']){const result=await require('./tests/'+name+'.cjs')(html); console.log(name,result); if(result.failed || result.passed===false)process.exitCode=1;}})().catch(e=>{console.error(e);process.exitCode=1;});"
```

Jos `node` ei löydy, avaa PowerShell uudelleen asennuksen jälkeen tai käytä
oman Node.js-asennuksesi täydellistä polkua. Sovellus itse ei tarvitse Node.js:ää.
JavaScript-testit käyttävät DOM-korviketta, eivät oikeaa selainta tai OpenAI API:a.

### Kaksi yksityisiä raporttisyötteitä tarvitsevaa JavaScript-moduulia

`ui_demo_chain_test.cjs` ja `ui_batch1_test.cjs` julkaistaan testikoodina,
mutta niiden tarvitsemat paikalliset arviointiraportit eivät kuulu julkaisuun.
Niiden puuttuminen julkaisukopiosta on tarkoituksellista. Raportteja,
kehitysaineistoja, holdouteja tai baselinea ei lisätä Gitiin testien ajamista varten.

Demoketjutesti saa argumenttina raportin, joka sisältää 12 demokorttia sekä
niiden kontrolloidut ja sanahaun vastaukset. Testin poistumiskoodi 2 tarkoittaa
epäonnistuneita vaatimustarkistuksia, ei onnistunutta ajoa. Batch1-testi on
vientifunktio, jolle annetaan raportin `records`-lista (96 vastausta) ja HTML.
Pelkkä `node tests/ui_batch1_test.cjs` ei suorita testejä.

Vain paikallisessa kehitysympäristössä, jossa oikeat raportit ovat jo saatavilla,
voit ajaa seuraavat esimerkit. Korvaa `<aikaleima>` oman raporttisi hakemistolla:

```powershell
node .\tests\ui_demo_chain_test.cjs '.\evaluation\demo_chain_runs\<aikaleima>\demo_observations.json'
node -e "const fs=require('node:fs'); const report=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); require('./tests/ui_batch1_test.cjs')(report.records,fs.readFileSync('index.html','utf8')).then(result=>{console.log(result);if(result.passed===false)process.exitCode=1;}).catch(e=>{console.error(e);process.exitCode=1;});" '.\evaluation\batch1_runs\<aikaleima>\controlled_final_responses.json'
```

19.10.2026 päivätyt julkaisuraportit kuvaavat aiempaa rajausta, jossa nämä
kaksi JavaScript-moduulia jätettiin pois. Tässä päivityksessä julkaistaan vain
niiden testikoodi; yksityisten raporttien rajaus säilyy.

## Julkaisurajaus

`.gitignore` sallii vain tarkistetun tiedostoluettelon. Uudet tiedostot on
hyväksyttävä erikseen. Yksityiset arviointiaineistot, holdoutit, tulokset, koko
jäädytetty baseline, varmuuskopiot, paikalliset välimuistit ja ympäristöt jätetään pois.
Niitä ei poisteta paikallisesta projektista. Aiemmat tulokset säilyvät yksityisinä.

Alkuperäisten 20 ohjeen `owner`-kentissä on tekijän nimi; 10 uudessa ohjeessa
omistaja on kuvattu projektin tekijänä.
Tekijä on hyväksynyt nimen näkymisen julkisessa repositoriossa.
Runbookien metatietoja ei ole muutettu. Lisenssitiedostoa ei lisätä tässä vaiheessa;
julkinen näkyvyys ei itsessään anna lupaa koodin uudelleenkäyttöön.
Riippumaton loppuarviointi ja organisaatiokohtainen hyväksyntä ovat kesken.
