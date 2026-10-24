# Ratkaisumuisti: kehitysversio

Käyttäjän [pikaohje](13_ratkaisumuistin_pikaohje.md) kuvaa nykyiset välilehdet ja työnkulun.

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

1. Aloita **Haku**-välilehdellä ongelmasta ja ympäristörajauksista.
   Hakutulokset ovat aiempien tapausten ehdokkaita, eivät varmoja vastauksia.
2. Siirry haun jälkeen **Kirjoita uusi ratkaisu**- tai **Siirry API-ehdotukseen**
   -painikkeella lomakkeeseen. Siirtyminen ei tee API-kutsua.
3. Kirjoita ratkaisu itse tai pyydä erikseen kokeilematon API-ehdotus.
   Ehdotus ei tallennu automaattisesti.
4. **Tallenna luonnos** säilyttää tekstin lomakkeessa ja kertoo luonnostilan.
   **Siirry luonnoksen tarkistamiseen** avaa juuri tallennetun tietueen
   **Hallinta ja historia** -välilehdellä. Uudet tallentamattomat muutokset
   pitää tallentaa ennen tämän siirtymän käyttämistä.
5. Kokeile tallennettu versio ilmoitetussa ympäristössä. Kirjoita vahvistajan
   tunniste ja valitse **Vahvista aiempi tapaus** vasta kokeilun jälkeen.
   Vahvistus koskee aiempaa tapausta tässä ympäristössä, ei uutta ongelmaa.
6. **Muokkaa** avaa lomakkeen; tallennus palauttaa tietueen luonnokseksi ja
   poistaa aiemman vahvistuksen.
7. **Poista käytöstä** sulkee vanhentuneen tietueen hausta. Tietue ja syy
   säilyvät historiassa. Jokaisen muokkauksen aiempaa tekstiä ei säilytetä;
   revisionumero ehkäisee vanhan selainversion vahingossa tekemän ylikirjoituksen.

Välilehden vaihtaminen ja epäonnistunut pyyntö säilyttävät lomaketekstin.
Sivun päivittäminen voi hävittää tallentamattoman tekstin. Näppäimistön
käyttö ja virheestä jatkaminen on kuvattu pikaohjeessa.

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
- Vertailu ohittaa kirjainkoon ja ylimääräiset välilyönnit. Tunnetut
  käyttöjärjestelmän kirjoitusasut, kuten `Win 11`, `win11` ja `Windows11`,
  vastaavat arvoa `Windows 11`. Samoin `Win 10` vastaa Windows 10:tä,
  `Mac OS 15` macOS 15:tä sekä `Ubuntu24.04`, `Debian12` ja `Android15`
  niiden välilyönnillisiä nimiä. Normalisointi koskee vain vertailua eikä
  muuta tallennettuja arvoja. Eri käyttöjärjestelmäversioita tai editioita
  ei yhdistetä. Tuote- ja versiokenttiin ei sovelleta OS-aliaksia:
  esimerkiksi `5.2` ja `5.20` ovat edelleen eri versioita.
  Versioalueita ja mielivaltaisia kirjoitusasujen arvauksia ei tueta.

Tulokset erotetaan kahteen ryhmään:

1. **Ilmoitettujen ympäristötietojen perusteella yhteensopivat ehdokkaat**:
   käyttöjärjestelmä, tuote ja versio on ilmoitettu molemmin puolin ja ne
   täsmäävät. Merkintä ei takaa oireen, organisaation tai korjauksen sopivuutta.
2. **Puuttuvien tietojen vuoksi tarkistettavat ehdokkaat**: vähintään yksi
   tieto puuttuu tietueesta tai hakurajauksista. Puuttuminen ei tarkoita
   yhteensopivuutta eikä merkintä lupaa ratkaisun toimivuutta.

Jos ensimmäinen ryhmä on tyhjä, se kerrotaan selvästi, vaikka tarkistettavia
osumia olisi. Molemmat ryhmät muodostetaan saman enintään kolmen osuman
hakutuloksesta; kyse ei ole erillisistä hauista kummallekin ryhmälle.

Ratkaisumuistin vektorihaku käyttää puhdasta kosinijärjestystä nykyisellä
0,43:n rajalla. PoC:n hakusana-, turvallisuuslähde- ja postilaatikkoheuristiikkoja
tai erikoiskyselysuodatusta ei sovelleta tähän vektorijärjestykseen.
Ratkaisumuistin oma turvallisuuskeskeytys ja ympäristösuodatus tehdään silti
ennen hakua. Alkuperäisen PoC:n oletushaku ja sen heuristiikat säilyvät.
Kummankin näkyvän ryhmän sisällä järjestys seuraa kosinipisteitä.

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
Haun `hits` säilyttää yhteisen pistejärjestyksen; `compatible_hits` ja
`review_hits` sisältävät samojen osumien yllä kuvatut erilliset ryhmät.

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
