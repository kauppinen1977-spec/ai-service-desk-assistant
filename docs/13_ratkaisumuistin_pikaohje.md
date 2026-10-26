# Ratkaisumuistin pikaohje

Uudelle käyttäjälle: [palautuskopion ensiasennus ja avaimeton kokeilu](21_ratkaisumuistin_asennus.md)
käyttää porttia 8513. Tämän pikaohjeen portti 8502 viittaa tekijän aiempaan
kehityspalvelimeen; korvaa se oman palvelimesi portilla.

Avaa `http://127.0.0.1:8502/memory`, kun tämän worktreen palvelin on käynnissä.
Aloitusnäkymä on **Haku**. Muut välilehdet ovat **Kirjoita ratkaisu** ja
**Hallinta ja historia**. Välilehden vaihtaminen säilyttää lomaketekstin.

**Käyttöönoton tilanne 24.10.2026:** portin 8502 palvelin on käynnistetty
uudelleen tästä projektista myös Haku-näkymän tekoälyehdotusta varten.
Kasvava ratkaisukenttä, **Avaa isona** ja uusi ehdotuspolku on
varmistettu oikealla Chromella suoraan osoitteessa
`http://127.0.0.1:8502/memory`. Kopioi mahdollinen vanhan selainvälilehden
tallentamaton teksti talteen ennen sivun päivittämistä: palvelimen istunto
vaihtui. Prosessin muistissa annetut API-asetukset katoavat uudelleenkäynnistyksessä.
Uusimman käynnistyksen edellä ja jälkeen palvelin ilmoitti käyttävänsä
käynnistysympäristön asetusta, jonka kelvollisuutta
ei testattu. Palvelin lukee HTML:n käynnistyksessään, joten myös myöhemmät
HTML-muutokset vaativat palvelimen uudelleenkäynnistyksen ja sivun päivityksen.

## 1. Hae aiempi tapaus

Kirjoita oireet ja tarkka virheilmoitus **Ongelman kuvaus** -kenttään.
Anna mahdollisuuksien mukaan käyttöjärjestelmä, tuote ja tuotteen versio.
Valitse sanahaku tai valmiiksi asennetun paikallisen mallin vektorihaku ja
paina **Hae aiempia ratkaisuja**.

Rajaukset ovat valinnaisia. Ristiriitaiset ilmoitetut arvot suljetaan pois;
tyhjä arvo jää tuntemattomaksi, eikä sitä päätellä ongelmatekstistä.
Tunnetut OS-aliakset, kuten Win 11 ja Windows 11, vastaavat toisiaan.
Tuoteversiot 5.2 ja 5.20 ovat eri arvoja.

Tuloksissa erotetaan:

- **Ilmoitettujen ympäristötietojen perusteella yhteensopivat ehdokkaat**:
  ilmoitetut kentät täsmäävät, mutta oire ja muu ympäristö on tarkistettava.
- **Puuttuvien tietojen vuoksi tarkistettavat ehdokkaat**: näet mistä
  tietueen tai haun kentistä tieto puuttuu. Puuttuminen ei ole yhteensopivuutta.

Kumpikaan ryhmä ei lupaa varmasti toimivaa ratkaisua. Vahvistus koskee
aiempaa tapausta tietyssä ympäristössä. Hakupisteet eivät ole varmuusprosentteja.
**Näytä ratkaisuvaiheet** avaa ehdokkaan sisällön. Jos yhteensopivia
hakuehdokkaita ei löydy, se kerrotaan myös tarkistettavien osumien yhteydessä.

## 2. Kirjoita uusi ratkaisu tai pyydä tekoälyehdotus

Haun jälkeen paina hakutulosten yhteydessä **Pyydä tekoälyehdotus**.
Pysyt Haku-näkymässä. Näet ensin **Tarkista tekoälypalvelulle lähetettävät tiedot**:
jo antamasi ongelmakuvauksen sekä täytetyt käyttöjärjestelmä-, tuote- ja
versiotiedot ja vapaan ympäristökuvauksen. Voit halutessasi antaa vapaan
ympäristökuvauksen Haku-näkymän valinnaisessa kentässä. Sitä ei käytetä haussa.
Mitään valinnaista ympäristötietoa ei tarvitse täyttää ehdotuksen saamiseksi.

Tarkista tiedot, valitse erillinen lähetyslupa ja paina **Lähetä ja pyydä ehdotus**.
Haku tai ensimmäisen painikkeen painaminen ei lähetä tietoja tekoälypalvelulle.
Vain esikatselussa ilmoitetut tiedot lähetetään; hakutuloksia, tietokannan
ratkaisuja tai kirjoituslomakkeen keskeneräistä tekstiä ei lähetetä.
Lähetettävän kentän muuttaminen poistaa aiemman lähetysluvan.

Kokeilematon ehdotus avautuu samaan Haku-näkymään. Voit lukea sen, palata
hakutuloksiin tai valita **Muokkaa ja tallenna luonnokseksi**. Siirto avaa
ehdotuksen uutena luonnoksena kirjoituslomakkeeseen; se ei tallenna mitään
eikä muuta aiempaa tallennettua tietuetta. Jos lomakkeella on tallentamatonta
tekstiä, sen korvaaminen kysytään. **Peruuta** säilyttää lomakkeen ja ehdotuksen.
Haun ongelmakuvaus ja ympäristötiedot kopioituvat hyväksytyssä siirrossa.
Jos et antanut vapaata ympäristökuvausta, lomakkeeseen merkitään
**Vapaata ympäristökuvausta ei ilmoitettu.** Voit täydentää sitä itse.

Voit myös valita **Kirjoita uusi ratkaisu**, jolloin haun ongelmakuvaus ja
ympäristötiedot kopioidaan lomakkeeseen käsin kirjoittamista varten.
Keskeneräisen lomakkeen korvaaminen kysytään tällöinkin.

Kirjoituslomakkeen aiempi ehdotuspolku säilyy: avaa
**Halutessasi: pyydä tekoälyehdotus**, täytä ongelman kuvaus ja vapaa ympäristökuvaus,
anna erillinen lähetyslupa ja paina **Pyydä tekoälyehdotus**.
Kutsu voi aiheuttaa API-kulun; käytä vain kuvitteellisia tietoja.

### Paikalliset API-asetukset

Avaa sivun yläosasta **Paikalliset API-asetukset**. Asetuksen tila kertoo,
onko avain asetettu ja tuleeko se palvelimen käynnistysympäristöstä vai tämän
käynnin aikana annetusta paikallisesta asetuksesta. **Avain asetettu ei tarkoita,
että avaimen kelvollisuus, mallioikeus tai laskutus olisi tarkistettu.**
Tilaa voi päivittää **Näytä asetuksen tila** -painikkeella.

Luo omassa OpenAI API -projektissasi avain, jolla on oikeus Responses-pyyntöihin.
Liitä pelkkä avain peitettyyn **Uusi API-avain** -kenttään ilman lainausmerkkejä.
Oletusmalli on `gpt-4.1-mini`; käytä omassa projektissasi sallittua mallia.
Paina **Ota käyttöön**. Muutos vaikuttaa seuraavaan pyyntöön heti,
ilman PowerShell-komentoja tai palvelimen uudelleenkäynnistystä.
Mallin vaihtaminen edellyttää avaimen syöttämistä uudelleen.

Asetuksen käyttöönotto **ei tee API-kutsua**. Syöttökenttä tyhjennetään
myös virheessä. Avain lähetetään vain paikalliselle palvelimelle ja varsinaisen
ehdotuspyynnön yhteydessä OpenAI-palvelulle; palvelin ei palauta sitä selaimeen.
Avainta ei tallenneta tiedostoon, selaimen paikallistallennukseen, lokiin,
ratkaisumuistin tietokantaan tai Gitiin. Älä itse kirjoita avainta ratkaisukenttiin.

**Säilyvyys:** paikallinen asetus on vain palvelinprosessin muistissa.
Se säilyy selaimen päivittämisessä ja sulkemisessa, mutta katoaa palvelimen
sammuessa. Kaikki samaan paikalliseen palvelimeen avatut sivut käyttävät
samaa asetusta. Uudelleenkäynnistyksessä palvelin käyttää jälleen sille
periytynyttä `OPENAI_API_KEY`- ja `OPENAI_MODEL`-ympäristöasetusta, jos sellaiset
ovat olemassa. `.env`-tiedostoa ei lueta automaattisesti.
**Poista avain käytöstä** estää avaimen käytön tämän palvelinkäynnin ajaksi;
se ei peru avainta OpenAI-palvelussa eikä poista käynnistysympäristön asetusta.

Ehdotuspyynnön aikana näet lähetys- ja odotusilmoituksen sekä odotuspainikkeen.
Kentät ja painikkeet lukitaan, jotta sama sivu ei lähetä kaksoispyyntöä.
Automaattisia uusintayrityksiä ei tehdä. Asetuksen tila päivittyy pyynnön jälkeen.

Kirjoituslomakkeen ehdotuspolussa lähetetään vain sen ongelman kuvaus ja
vapaa ympäristökuvaus. Haku-näkymän ehdotus sisältää lisäksi täytetyt
käyttöjärjestelmä-, tuote- ja versiotiedot. Kummankin polun ehdotus on
**kokeilematon**, eikä se ole verkkohaku tai vahvistettu ratkaisu.
Ehdotus avautuu ensin luettavaksi kahteen osaan: **Ratkaisuvaiheet** ja
**Soveltuvuuden rajat ja puuttuvat tiedot**. Rivinvaihdot säilyvät ja pitkät
rivit rivittyvät ikkunaan. Mallin sisältö näytetään tekstinä; HTML-merkintöjä
tai komentosarjoja ei suoriteta. Lomakkeen teksti ei muutu ehdotusta pyydettäessä.

Kun haluat muokata ehdotusta, paina vastauksen yhteydessä
**Muokkaa ja tallenna luonnokseksi**. Tämä painike
**siirtää** otsikon, ratkaisuvaiheet ja rajat lomakkeeseen. Se ei tallenna
mitään. Kirjoituslomakkeelta pyydetyn ehdotuksen siirto kysyy ennen nykyisen
otsikon tai ratkaisun korvaamista ja säilyttää muut kentät. Haku-näkymästä
siirto kysyy ennen keskeneräisen lomakkeen korvaamista ja kopioi haun tiedot.
**Peruuta** säilyttää oman tekstisi ja ehdotuksen lukunäkymän.
Molempien näkymien omat ehdotukset säilyvät välilehteä vaihtaessa.
Jos muutat jotakin ehdotukseen lähetettyä tietoa vastauksen saamisen jälkeen, siirto estetään
ja sinua ohjataan pyytämään ehdotus uusilla tiedoilla.

Muokkaa lomakkeessa ja paina vasta sitten erillistä **Tallenna luonnos**
-painiketta. Ehdotus ei tallennu tai vahvistu automaattisesti.

Jos pyyntö epäonnistuu, lomaketeksti säilyy. Seuraa juuri virheen toimintaohjetta:

| Virhekoodi | Seuraava toimi |
|---|---|
| `missing_api_key` | Syötä avain paikallisissa API-asetuksissa ja ota käyttöön. |
| `invalid_key_format` | Liitä pelkkä avain ilman lainausmerkkejä tai sisäisiä välilyöntejä. Kyse on paikallisesta muototarkistuksesta. |
| `invalid_api_key` | Palvelu yksilöi avaimen hylätyksi. Ota oikean API-projektin voimassa oleva avain käyttöön. |
| `api_authentication` | Tarkista avain, projekti- ja organisaatiojäsenyys. HTTP 401 ei yksin todista väärää avainta. |
| `api_forbidden` | Tarkista Responses-oikeus, projektijäsenyys ja IP-/organisaatiorajoitukset ylläpitäjän kanssa. |
| `api_billing` | Korjaa API-projektin saldo, laskutus tai käyttöbudjetti ennen uutta yritystä. |
| `api_model_access` / `api_not_found` | Tarkista mallin tunniste ja saatavuus projektissasi. Vaihda tarvittaessa mallia asetuksissa. |
| `api_rate_limit` | Odota ja tarkista kutsurajat; jos tarkka syy puuttuu, tarkista myös saldo. |
| `api_connection` / `api_timeout` | Tarkista verkko, välityspalvelin, TLS-varmenteet ja palomuuri. Aikakatkaistu pyyntö on voinut aiheuttaa kulun. |
| `api_bad_request` / `api_format` | Ilmoita virhekoodi ylläpitäjälle: mallin tai vastausmuodon yhteensopivuus on tarkistettava. |
| `api_unavailable` | Odota ja yritä myöhemmin. Avainta ei todettu virheelliseksi. |

Virheilmoitus sisältää sovelluksen virhekoodin. Palvelimen JSON-vastaus sisältää
lisäksi HTTP-virheissä palveluntarjoajan HTTP-tilan ja tunnistetun turvallisen
virhekoodin, jos se oli saatavilla. Palveluntarjoajan raakavirhettä ei näytetä,
koska se voi sisältää salaisuuksia.

## 3. Tallenna ja tarkista luonnos

Täytä otsikko, ongelma, vapaa ympäristökuvaus sekä ratkaisuvaiheet ja rajat.
**Ratkaisuvaiheet ja soveltuvuuden rajat** -kentässä näkyy aluksi noin
12 tekstiriviä. Kenttä kasvaa sisällön mukaan noin 20 riviin asti ja käyttää
sen jälkeen sisäistä vieritystä. Voit suurentaa sitä myös vetämällä
alakulmasta; seuraava kirjoitus ei pienennä käsin suurennettua kenttää.

**Avaa isona** avaa tekstin suureen muokkaimeen. Kirjoitukset säilyvät, kun painat
**Sulje ja palaa lomakkeelle** tai Esc. Kohdistus palautuu Avaa isona
-painikkeeseen. Tab ja Shift+Tab kiertävät muokkaimen tekstikentän ja
sulkemispainikkeen välillä. Suuri muokkain ei tallenna luonnosta puolestasi.

Merkkimäärä näkyy kentän yhteydessä. Tallennuksen aiempi 8000 merkin raja on
ennallaan. Jos ehdotuksen vaiheet ja rajat ylittävät yhdessä rajan, kaikki
teksti säilyy: lyhennä sitä itse ennen tallennusta. Mitään ei katkaista
hiljaisesti. Myös vanhat ratkaisut avautuvat kokonaisina samassa kentässä.

Erilliset käyttöjärjestelmä-, tuote- ja versiokentät ovat valinnaisia.
Paina **Tallenna luonnos**. Ilmoitus kertoo, ettei luonnos vielä näy haussa.

**Siirry luonnoksen tarkistamiseen** avaa hallinnasta juuri tallennetun
luonnoksen ratkaisuvaiheineen. Lomaketeksti säilyy tallennuksen jälkeen.
Jos muokkaat sitä lisää, tarkistuspainike piilotetaan, kunnes tallennat muutokset.

## 4. Vahvista aiempi tapaus

Tarkista tallennettu sisältö ja kokeile juuri tätä versiota ilmoitetussa
ympäristössä. Kirjoita **Vahvistajan nimi tai tunniste**, valitse luonnoksesta
**Vahvista aiempi tapaus** ja hyväksy kokeilua koskeva kysymys vasta kokeilun jälkeen.
Tietue tulee vahvistettuna hakuun. Vahvistus ei takaa toimivuutta uudessa ongelmassa.

## 5. Muokkaa tai poista käytöstä

**Hallinta ja historia** ryhmittelee tietueet tekstein:

| Tila | Merkitys |
|---|---|
| Luonnos | Ei haussa; odottaa kokeilua ja vahvistusta |
| Vahvistettu | Kokeiltu aiemmassa tapauksessa ilmoitetussa ympäristössä; mukana haussa |
| Poistettu käytöstä | Ei haussa; tietue ja poistamisen syy säilyvät historiassa |

**Muokkaa** avaa tietueen lomakkeeseen. Tallennus palauttaa sen luonnokseksi
ja poistaa aiemman vahvistuksen. Muutos on kokeiltava ja vahvistettava uudelleen.

**Poista käytöstä** pyytää syyn. Peruminen ei muuta tietuetta. Käytöstä poistettua
tietuetta ei voi enää muokata tai vahvistaa. Historia näyttää tietueen ja syyn,
mutta ei kaikkia muokkausten aiempia tekstiversioita. **Päivitä lista** hakee tilanteen uudelleen.

## Virheet, näppäimistö ja kapea ikkuna

Virhe näkyy erillisessä ilmoituksessa. Lomaketeksti ja hakurajaukset säilyvät;
korjaa puuttuva tieto tai yritä uudelleen. Myös poistamisen syy säilyy seuraavan
yrityksen oletustekstinä, jos käytöstä poistaminen epäonnistuu. Jos tallennus tai vahvistus onnistui
mutta listan päivitys epäonnistui, käyttöliittymä kertoo tämän erikseen.
Pelkkä listavirhe ei tarkoita, että onnistunut tallennus pitäisi tehdä uudelleen.

Tab siirtyy painikkeisiin ja kenttiin. Välilehtipalkissa vasen/oikea nuoli sekä
Home/End siirtävät kohdistusta; Enter tai välilyönti avaa valitun välilehden.
Kohdistus näkyy reunuksena. Ratkaisuvaiheet saa auki myös näppäimistöllä.
Kapeassa ikkunassa ympäristökentät asettuvat allekkain ja painikkeet rivittyvät.

Sivun päivittäminen tai sulkeminen voi hävittää tallentamattoman tekstin.
Tallennetut tietueet säilyvät. Palvelimen uudelleenkäynnistyksen jälkeen
päivitä sivu, jotta istunto uusiutuu.
