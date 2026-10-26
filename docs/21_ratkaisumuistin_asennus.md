# Ratkaisumuistin palautuskopion ensikäyttö Windowsissa

Tämä ohje koskee nykyistä `kehitys/ratkaisumuisti`-kehitysversiota ja siitä
tehtyä palautuskopiota. GitHubin oletushaara tai vanhempi
`feature/solution-memory` ei välttämättä sisällä samoja toimintoja. Tarkista
palautuksen mukana ilmoitettu lähdecommit ja commitoimattomien muutosten luettelo.
Ensikäyttökokeen tulokset ovat [raportissa 20](20_puhdas_ensikayttokoe.md).

## 1. Tarkista kopio ja Python

Pura hyväksytty palautuskopio uuteen omaan kansioon. Älä kopioi toisen
käyttäjän `.venv`-ympäristöä, `data`-tietokantaa, API-avaimia tai mallivälimuistia.
Kopiossa pitää olla Python- ja HTML-tiedostot sekä `knowledge`-hakemisto
alkuperäisine alihakemistoineen. Pelkkä `memory.html` tai sen avaaminen
tiedostona ei riitä. Avaa tavallinen PowerShell ja siirry kopion juureen:

```powershell
Set-Location 'C:\oma\palautuskopio'
py -3.13 --version
if ($LASTEXITCODE -ne 0) { throw 'Asenna 64-bittinen Python 3.13 ja py-käynnistin.' }
py -3.13 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtuaaliympäristön luonti epäonnistui.' }
& .\.venv\Scripts\python.exe --version
```

Kansion nimi korvataan oman kopion polulla. Testattu järjestelmään asennettu
Python on 3.13.9. Uusi ympäristö käyttää sen perus-Pythonia; Pythonin itsensä
asentamista ei ole testattu tässä. Luo ympäristö vain kerran uudessa kansiossa.
Aktivointia, PowerShellin suorituspolitiikan muutosta tai pip-asennusta ei
tarvita sanahakuun. `requirements.txt` ei sisällä asennettavia paketteja.

Ajonaikainen kokeilupaketti ei sisällä `tests`-hakemistoa. README:n erilliset
kehitystestikomennot tarvitsevat testitiedostot täydestä lähdekoodikopiosta;
niitä ei tarvita tämän ohjeen selainkokeiluun.

## 2. Käynnistä avaimeton sanahakukokeilu

Portiksi on valittu 8513, jotta aiempaan portin 8502 palvelimeen ei tarvitse
koskea. Jos 8513 on varattu, valitse toinen vapaa portti ja muuta myös selaimen
osoite. Suorita kopion juuresta:

```powershell
& .\.venv\Scripts\python.exe -B -c "import os,runpy; [os.environ.pop(k,None) for k in ('OPENAI_API_KEY','OPENAI_MODEL')]; os.environ['DESK_MEMORY_DB']=os.path.abspath('data/solutions.sqlite3'); os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1'); runpy.run_path('app.py',run_name='__main__')" --corpus batch1 --port 8513
```

Komento tyhjentää mahdollisen API-asetuksen vain palvelimen omasta ympäristöstä
ja pakottaa tietokannan tämän kopion `data/solutions.sqlite3`-tiedostoon.
PowerShell-istunnon ympäristö jää ennalleen. Mallikirjastojen verkkolataukset
ohjataan offline-tilaan; tämä ei ole yleinen verkkopalomuuri. Palvelimen
käynnistys ei tee OpenAI-kutsua. Tietokanta syntyy ensimmäisessä
ratkaisumuistitoiminnossa. Aiemman käyttäjän tietoja ei ole mukana.

Avaa **http://127.0.0.1:8513/memory**. Palvelimen konsolitulosteen `/`-osoite
avaa alkuperäisen PoC:n; lisää `/memory` ratkaisumuistia varten.
Osoitteessa `http://127.0.0.1:8513/health` pitää näkyä `corpus: batch1` ja
`api_key_available: false`. Käytä **Sanahaku – ei lisäasennuksia** -valintaa.
Tyhjä hakutulos uudessa kopiossa on odotettu.

## 3. Luo ensimmäinen kuvitteellinen tapaus

Avaa **Kirjoita ratkaisu** ja täytä otsikko, ongelma, vapaa ympäristökuvaus
sekä ratkaisuvaiheet ja soveltuvuuden rajat. Rakenteiset ympäristökentät ovat
valinnaisia. Käytä vain harjoitustietoa; esimerkiksi `ENSIKOE20261026`,
ongelma "Harjoitusmuistion TESTI-teksti pitää löytää uudelleen" ja ratkaisu
"Kirjoita harjoitusmuistioon TESTI ja tarkista, että sama teksti näkyy.
Tämä on tallennusketjun harjoitus, ei IT-korjausohje."

Paina **Tallenna luonnos**. **Siirry luonnoksen tarkistamiseen** avaa tietueen
hallinnassa. Luonnos ei kuulu hakuun. Tarkista tallennettu teksti ja kokeile
harjoituksen toiminto erillisessä testiympäristössä. Kirjoita vahvistajan
tunniste ja paina **Vahvista aiempi tapaus**, hyväksyen kysymys vain, jos
kokeilu on tehty. Ohjelma kirjaa ihmisen ilmoituksen, ei tarkista sen totuutta.

Palaa **Haku**-välilehdelle ja hae tunnisteella sekä ongelman sanoilla.
Vahvistetun tietueen pitäisi löytyä. Puuttuvien ympäristötietojen merkintä
on odotettu, jos rakenteisia kenttiä ei annettu. Osuma ei todista ratkaisun
soveltuvuutta uuteen tapaukseen.

## 4. Pysäytä ja tarkista säilyminen

Pysäytä vain oman PowerShell-ikkunasi palvelin **Ctrl+C**:llä. Käynnistä se
uudelleen samalla komennolla samasta kopiosta. Päivitä selain, koska
istuntotunniste vaihtuu. Hae sama tapaus ja tarkista sisältö sekä vahvistus.
Tietokantatiedosto säilyy palvelimen pysäytyksessä; älä poista `data`-kansiota.
Tallentamattomat lomaketekstit on kopioitava talteen ennen sivun päivitystä.

Jos saat `session_expired`-virheen, päivitä sivu tallentamattoman tekstin
talteenoton jälkeen. Porttivirheessä valitse vapaa portti. Älä pysäytä vierasta
palvelinta. Lopuksi sammuta vain oma testipalvelimesi Ctrl+C:llä.

## Valinnaiset vektorihaku ja tekoälyehdotus

Vektorihaku vaatii erikseen asennetut riippuvuudet ja paikallisen upotusmallin.
Asennus- ja mallin valmisteluohje on [README:ssä](../README.md#valinnainen-paikallinen-vektorihaku).
Offline-käynnistys ei voi ladata puuttuvaa mallia. Ilman riippuvuuksia
vektorihaku voi palauttaa `search_unavailable`; palaa sanahakuun.
Vanha virheteksti saattaa mainita `asenna_vektorihaku.bat`-tiedoston, jota
palautuskopio ei sisällä. Käytä sen sijaan yllä linkitettyjä README:n
Python-/pip-komentoja, jos haluat asentaa valinnaisen vektorihaun.
Valmiin kehitysympäristön pakettien tai mallivälimuistin käyttö ei ole puhdas
vektorihaun asennuskoe. Kirjaa niiden alkuperä erikseen.
Paikallisen mallin ensimmäinen lataus muistiin voi kestää yli minuutin myös
ilman verkkolatausta; tämän kokeen erillinen lataustarkistus kesti 65,28 sekuntia.

Tekoälyehdotus ei kuulu avaimettomaan ensikäyttökokeeseen. Sen käyttäminen
vaatii oman API-asetuksen ja erillisen lähetysluvan. Käyttöliittymässä annettu
avain säilyy vain palvelimen nykyisen käynnin ajan. Avaimen asettaminen ei
vielä osoita sen kelvollisuutta. Tässä ohjeessa ei pyydetä API-kutsua.
