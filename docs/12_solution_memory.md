# Ratkaisumuisti: kehitysversio

Tavoite: säilytä tukihenkilön vahvistamat ympäristökohtaiset ratkaisut ja löydä
ne myöhemmissä tukipyynnöissä. Alkuperäinen PoC säilyy tagissa `v0.1.0-poc`.
Kehitys tehdään haarassa `feature/solution-memory`, ei varaversion tagissa.

## Käynnistäminen

Nykyinen Python-käynnistystapa säilyy. Ratkaisumuistin sanahaku ja tallennus
eivät tarvitse uusia paketteja, API-avainta tai vektorimallia.

```powershell
& .\.venv\Scripts\python.exe -B .\app.py --corpus batch1 --port 8501
```

Avaa `http://127.0.0.1:8501/memory`. Alkuperäinen PoC on edelleen juuressa `/`.
Kyseessä on paikallinen yhden käyttäjän PoC. Istuntotunniste suojaa sivun
pyynnöt, mutta vahvistajan nimi ei ole todennettu käyttäjätunnus.

## Työnkulku

1. Kuvaa oireet ja ympäristö, hae aiempia vahvistettuja ratkaisuja.
2. Jos tarvitset uuden ratkaisun, täytä oikealla ongelma ja ympäristö.
3. Voit kirjoittaa ratkaisun itse tai pyytää erikseen API-ehdotuksen.
4. Tallenna luonnos. Se ei vielä näy hauissa.
5. Testaa ratkaisu ilmoitetussa ympäristössä, kirjoita vahvistajan tunniste ja
   vahvista kyseinen versio toimivaksi. Vasta nyt se tulee hakuun.
6. Muokkaus palauttaa ratkaisun luonnokseksi ja poistaa vahvistuksen.
7. Virheellisen tai vanhentuneen ratkaisun poistaminen käytöstä sulkee sen
   hauista. Tietue ja poistamisen syy säilyvät. Historiassa ei vielä säilytetä
   jokaisen muokkauksen aiempaa tekstiä; revisionumero ehkäisee vanhan
   selainversion vahingossa tekemän ylikirjoituksen.

## Haku ja tallennus

SQLite-tietokanta on oletuksena `data/solutions.sqlite3`. Polun voi vaihtaa
palvelimen `DESK_MEMORY_DB`-ympäristömuuttujalla. Tiedot säilyvät palvelimen
uudelleenkäynnistyksessä. Tietokanta ei kuulu Gitiin. Jos tarvitset varmuuskopion,
pysäytä palvelin ja kopioi tietokantatiedosto turvalliseen paikkaan.

Sanahaku käyttää nykyistä hakumoottoria ja tekstistä poimittuja sanoja; se on
vertailutaso, ei todistus hakulaadusta. Vektorihaku käyttää nykyistä paikallista
upotusmallia ja erillistä `solutions.vectors.json`-välimuistia tietokannan vieressä.
Se rakennetaan tarvittaessa uudelleen vahvistetuista tietueista, jolloin
poistettuja tai luonnokseksi muutettuja ratkaisuja ei voi palautua vanhasta
indeksistä. Alkuperäisen PoC:n välimuisteja ei muuteta.

Tulokset ovat tarkistettavia tapauksia, eivät automaattisia diagnooseja.
Ympäristön soveltuvuuden tarkistaa tukihenkilö. Nykyiset rajatut vaaratilanteiden
tunnistussäännöt keskeyttävät haun/API-kutsun tunnistetussa tapauksessa.
Ne eivät tunnista kaikkia vaaroja tai tietoturvatilanteita.

## Rakenteiset ympäristötiedot

Ratkaisulle voi tallentaa vapaan ympäristökuvauksen lisäksi valinnaiset
käyttöjärjestelmän, tuotteen ja tuotteen version. Haussa on samat kolme
rajausta. Täytä tiedot itse; kuvaustekstistä tai vanhoista tietueista ei
päätellä arvoja automaattisesti.

- Kahden ilmoitetun arvon ristiriita sulkee tietueen pois jo ennen hakua ja
  kolmen tuloksen rajausta. Tämä koskee sekä sana- että vektorihakua.
- Jos arvo puuttuu tietueesta tai hakurajauksista, ehdokas merkitään
  **Ympäristö tarkistettava**. Käyttöliittymä erottaa tietueesta ja hausta
  puuttuvat kentät. Tuntematon tieto ei tarkoita yhteensopivuutta.
- Jos kaikki kolme tietoa täsmäävät, se kerrotaan erikseen. Tietue on silti
  samankaltainen ehdokas: oire, organisaatio ja muu ympäristö on tarkistettava.
  Pelkkä hakupiste tai tietueen aiempi vahvistus ei osoita soveltuvuutta.
- Vertailu ohittaa kirjainkoon ja ylimääräiset välilyönnit. Muuten nimet ja
  versiot täsmäävät tarkasti: esimerkiksi `5.2` ja `5.20` ovat eri versioita,
  eikä `Win 11` -aliasta päätellä samaksi kuin `Windows 11`. Käytä samoja
  täsmällisiä nimiä tietueessa ja haussa. Versioalueita ei vielä tueta.

Tietokantapäivitys lisää vain kolme tyhjää, valinnaista tekstisaraketta.
Vanhat tietueet, vapaat kuvaukset, tilat, revisionumerot ja vahvistustiedot
säilyvät. Päivitys on toistettava ja tapahtuu tietokantatoiminnon kanssa
samassa transaktiossa. Ota ennen päivitystä varmuuskopio aiemman ohjeen mukaan.
Rakenteisten tietojen täydentäminen on tavallinen muokkaus: se palauttaa
ratkaisun luonnokseksi ja vaatii uuden vahvistuksen.

Paikallisen HTTP-rajapinnan kentät ovat `operating_system`, `product` ja
`product_version`. Haun `filters`-objekti käyttää samoja kenttiä. Tyhjä tai
`null` tarkoittaa tuntematonta arvoa. Vanhan asiakkaan muokkauspyynnöstä
puuttuvat uudet kentät säilyttävät jo tallennetut arvot; kentän nimenomainen
tyhjentäminen poistaa arvon. Vapaa `environment`-kuvaus säilyy ennallaan.

Ristiriitojen suodatus ei ratkaise kaikkia vastausta vailla olevia kyselyjä.
Erityisesti saman tuotteen eri oireet tai organisaatiot voivat edelleen
palauttaa samankaltaisia ehdokkaita. Katso mitatut virheet testiraportin
rakenteisten ympäristötietojen arvioinnista. Hakuraja on edelleen 0,43.

## API-ehdotukset

Palvelin käyttää nykyisiä `OPENAI_API_KEY`- ja `OPENAI_MODEL`-ympäristömuuttujia.
Avain ei siirry selaimeen. Käyttäjä valitsee lähetyksen erikseen: vain lomakkeen
ongelma ja ympäristö lähetetään. Koko ratkaisumuistia ei lähetetä palvelulle.
Kyseessä on mallin ehdotus, ei internet-haku eikä lähteillä vahvistettu vastaus.
`store:false` asetetaan palvelupyynnössä; se ei ole lupaus kaikista palveluntarjoajan
säilytyskäytännöistä. Käytä PoC:ssa vain kuvitteellisia tietoja.

Ehdotus ei tallennu automaattisesti. Tallennus luo aina luonnoksen. Ihminen
kokeilee ja vahvistaa ratkaisun erikseen. Mallin rajoitteet lisätään
lomakkeen ratkaisun perään, jotta ne säilyvät luonnoksessa.

## Tarkistus

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
node .\tests\ui_memory_test.cjs
```

Uudet testit kattavat pysyvyyden, tilasiirtymät, vahvistuksen vaatimisen,
muokkauksen, poistamisen hausta, vanhentuneet revisionumerot, synteettisen
vektori-indeksin uudelleenrakennuksen, HTTP-ketjun, istuntotunnisteet ja mockatun
API-ehdotuksen. Ne eivät osoita oikean upotusmallin tai API:n ratkaisujen laatua.
Uuden näkymän JavaScript-testi käyttää DOM-korviketta ja tarkistaa työnkulun,
erillisen API-luvan, automaattitallennuksen puuttumisen, tekstinä renderöinnin
ja vanhentuneen hakuvastauksen sivuuttamisen. Se ei ole oikea selainkoe.

24.10.2026 käyttäjän Kajo77-selainkoe hyväksyi luonnoksen rajaamisen pois
hausta, vahvistetun ratkaisun löytymisen oikealla tekstillä sekä käytöstä
poiston ja historian säilymisen. Erillinen paikallinen palvelintesti hyväksyi
säilymisen oikeiden palvelinprosessin uudelleenkäynnistysten yli.
Windowsin 403-vastauksen korjaus ja regressiotestit on kuvattu
[projektin testiraportin ratkaisumuistilisäyksessä](10_poc_valitavoite_2026-10-19.md#ratkaisumuistin-lisätestaus--24102026).

Ennen valmista PoC-esittelyä tarvitaan vielä:

- uudelleenkäynnistyksen jälkeinen säilymisen tarkistus myös oikeassa selaimessa
- erikseen käynnistetty API-koe kuvitteellisella ongelmalla
- laadukas ympäristökohtainen tapausaineisto ja vertailu tavalliseen tekstihakuun
- erillinen arviointiaineisto, myös vastausta vailla olevat ja harhaanjohtavat tapaukset.
