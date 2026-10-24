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

Ennen valmista PoC-esittelyä tarvitaan vielä:

- oikea Windows-/selainkoe tallennuksesta uudelleenkäynnistykseen ja poistamiseen
- erikseen käynnistetty API-koe kuvitteellisella ongelmalla
- laadukas ympäristökohtainen tapausaineisto ja vertailu tavalliseen tekstihakuun
- erillinen arviointiaineisto, myös vastausta vailla olevat ja harhaanjohtavat tapaukset.
