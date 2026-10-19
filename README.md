# AI Service Desk Assistant – PoC

Paikallinen IT-palvelupisteen avustajaprototyyppi. Julkaisuun rajattu
`batch1`-kokonaisuus sisältää 30 kuvitteellisen harjoitusorganisaation runbookia.
Sovellus erottaa hakuehdokkaat hyväksytystä ratkaisuehdotuksesta ja näyttää
ratkaisuvaiheiden lähteet, alkuperäiset vaihenumerot ja versiot.

Maksuton sanahakudemo toimii Pythonin standardikirjastolla. Valinnaisessa
live-tilassa OpenAI valitsee soveltuvista lähteistä enintään yhden; sovellus
kokoaa näytettävät vaiheet runbookista. Mallin omia ratkaisuvaiheita ei näytetä.
Vaaratilanteen deterministinen `safety_stop` ohittaa haun ja mallikutsun.

## PoC-tilanne 19.10.2026

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

Lataa projektin hyväksytty julkaisukopio ja pura se omaan kansioon.
Etärepositorion osoitetta ei ole vielä määritetty. Avaa PowerShell ja siirry
kansioon, jossa `app.py` sijaitsee. Käytä uutta kansiota; älä korvaa olemassa
olevaa virtuaaliympäristöä.

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

Julkaisukopio sisältää seitsemän aineistoista riippumatonta Python-testimoduulia
ja viisi JavaScriptin käyttöliittymätestimoduulia. Python-testit käyttävät
synteettisiä upotuksia ja mockattuja vastauksia; ne eivät mittaa oikean mallin laatua.
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

Valinnainen Node.js tarvitaan vain käyttöliittymätesteihin:

```powershell
node .\tests\ui_state_test.cjs
node .\tests\ui_candidate_visibility_test.cjs
```

JavaScript-testit käyttävät DOM-korviketta, eivät oikeaa selainta.
Uudelleenkäytettävät safety-stop-, käynnistys- ja kentäntyhjennystestimoduulit
ovat myös mukana; niiden vientifunktiot kuvataan julkaisuraportissa.

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
