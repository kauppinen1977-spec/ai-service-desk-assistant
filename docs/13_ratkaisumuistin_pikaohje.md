# Ratkaisumuistin pikaohje

Uudelle käyttäjälle: [palautuskopion ensiasennus ja avaimeton kokeilu](21_ratkaisumuistin_asennus.md)
käyttää porttia 8513. Tämän SOC-worktreen paikallinen kehityspalvelin käynnistetään
porttiin 8511 alla olevilla SOC-polkuohjeilla. Portin 8502 viittaukset alempana
ovat 24.10.2026 kirjattuja historiallisia käyttöönottotietoja.

Avaa `http://127.0.0.1:8511/memory`, kun SOC-worktreen palvelin on käynnissä.
Aloitusnäkymä on **Haku**. Muut välilehdet ovat **Kirjoita ratkaisu** ja
**Hallinta ja historia**. Välilehden vaihtaminen säilyttää lomaketekstin.

**Historiallinen käyttöönoton tilanne 24.10.2026:** portin 8502 palvelin on käynnistetty
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
Valitse sanahaku, valmiiksi asennetun paikallisen mallin vektorihaku tai
**Yhteishaku (kokeilu)** ja paina **Hae aiempia ratkaisuja**. Oletus on
sanahaku. Jos yhteishaun merkitysmalli ei ole käytettävissä, näytetään viesti
ja sanarajahaun tulokset. Yhteishaku ei löydä pelkästään vapaaseen
ympäristökuvaukseen tallennettua tunnistetta yksinään.

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
**Näytä ratkaisu** avaa ehdokkaan sisällön. Jos yhteensopivia
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

Kirjoituslomakkeen ehdotuspolussa lähetetään ongelman kuvaus ja vapaa
ympäristökuvaus sekä verkkohakua käytettäessä täytetyt ympäristökentät.
Haku-näkymän ehdotus sisältää myös täytetyt käyttöjärjestelmä-, tuote- ja
versiotiedot. Kummassakin voidaan ilmoittaa valmistajan verkkotunnus ja laitteen
tarkka malli. Lähetyksen esikatselu näyttää lähetettävät tiedot. Ratkaisumuistin
tietueita ei lähetetä. Ehdotus ja kaikki sen komennot ovat **kokeilemattomia**.
Ehdotus avautuu ensin luettavaksi kahteen osaan: **Ratkaisuvaiheet** ja
**Soveltuvuuden rajat ja puuttuvat tiedot**. Rivinvaihdot säilyvät ja pitkät
rivit rivittyvät ikkunaan. Mallin sisältö näytetään tekstinä; HTML-merkintöjä
tai komentosarjoja ei suoriteta. Lomakkeen teksti ei muutu ehdotusta pyydettäessä.

Valinnalla **Etsi myös valmistajan päivitys- ja tukilinkit verkosta** käytetään
Responses API:n verkkohakua vasta erillisen lähetysluvan jälkeen. Se käyttää
ulkoista palvelua ja voi aiheuttaa kuluja. Syötä itse valmistajan verkkotunnus
ilman protokollaa; ilman sitä linkkejä ei näytetä. Verkkohaku on yleinen:
verkkotunnus ohjaa hakua, mutta sitä ei käytetä API:n hakusuodattimena.
Sovellus hyväksyy vain verkkotunnusta tai sen aliverkkotunnusta vastaavat,
verkkohakupalvelun lähdetiedoissa mainitut osoitteet. Ilman verkkohakua linkit merkitään tarkistamattomiksi.
Verkkotunnuksen, lähteen ja yhteensopivuuden oikeellisuus on aina tarkistettava
itse. Täsmällinen latausehdotus edellyttää tarkkaa mallia ja käyttöjärjestelmää;
puutteelliset tai ristiriitaiset tiedot voivat jättää jäljelle vain yleisen
tukisivun. Sovellus ei lataa tai asenna päivityksiä.

Verkkohaku käyttää nykyistä asetettua mallia, eikä sovellus vaihda sitä.
Mallin ja API-projektin on tuettava `web_search`-työkalua; virheessä tarkista
mallin tuki ja käyttöoikeudet. Oletusmalli `gpt-4.1-mini` tukee OpenAI:n
dokumentaation mukaan verkkohakua, mutta on merkitty vanhentuvaksi. Yksi oikea
API-koe palautti, ettei tämä malli tue verkkohakutyökalun `filters`-asetusta.
Pyyntöä muutettiin tämän jälkeen yleiseksi verkkohauksi ilman tätä asetusta;
linkkien verkkotunnus ja lähde tarkistetaan sovelluksessa. Muutettua pyyntöä ei
ole vielä kokeiltu oikealla API-kutsulla. Saatavuus
riippuu projektista. Katso [Responses-verkkohaku](https://developers.openai.com/api/docs/guides/tools-web-search)
ja [mallin tiedot](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Toiminto ei vaadi erillistä Python-kirjastoa. Oikeaa maksullista integraatiota
ei ole testattu tässä muutoksessa: testit käyttävät korvattuja vastauksia.
Jos palvelu hylkää `tools`-parametrin, näytettävä turvallinen kuvaus on
sovelluksen tiivistelmä eikä alkuperäinen virheviesti. Virheilmoituksessa
voidaan näyttää myös palvelun viestissä esiintyneitä ennalta sallittuja
teknisiä termejä; niiden esiintyminen ei yksin todista virheen syytä.
Verkkohaku ja rakenteinen vastaus on dokumentoitu erikseen, mutta niiden
yhteistä toimivuutta tässä API-projektissa ei ole vahvistettu korvatuilla
vastauksilla. Virhe ei todista valmistajan sivuston estoa. Sovellus ei vaihda
mallia eikä ohita sovelluksen verkkotunnus- tai lähdetarkistusta automaattisesti.

Ehdotuksen **Verkkohaun diagnostiikka** kertoo hakukutsujen tilat, API:n
lähdemerkintöjen ja URL-viitteiden määrät, niistä poimitut yksilölliset
lähdeosoitteet sekä mallin ehdottamien ja hyväksyttyjen linkkien määrät ja
hylkäysten syyt. Määrät eivät paljasta sivujen osoitteita.
Tiedot ovat vain kyseisen ehdotuksen yhteydessä eivätkä tallennu lokiin tai
tietokantaan. Jos malli ei ehdota lähteisiin perustuvaa, tilanteeseen sopivaa
linkkiä, sovellus ei muodosta linkkiä pelkän verkkotunnuksen perusteella.
Yleinen valmistajan tukisivu esitetään erillään täsmälliseksi ehdotetusta
lataussivusta. Lähde ja verkkotunnus eivät todista yhteensopivuutta.
Ehdotuksen otsikot ja korostukset muotoillaan esikatselussa; muotoilumerkit
säilyvät luonnokseen siirrettävässä tekstissä. Osoitteet käsitellään alla
kuvatulla tavalla ennen esikatselua ja siirtoa.

Tekoälyehdotuksen komentokortit rajataan tunnistettavaan PowerShell- ja
komentokehotesyntaksiin. Samat toimintaohjeet jätetään pois, kun ne esiintyvät
jo ratkaisuvaiheissa täsmälleen; muut näytetään erikseen avattavina. Ne
siirtyvät ja kopioituvat ratkaisun mukana erillisenä osana. Tunnistus ei todista komennon turvallisuutta tai toimivuutta;
komennot ovat kokeilemattomia. Ehdotustekstien osoitteet tarkistetaan samalla
verkkotunnus- ja lähdesäännöllä kuin linkkikortit. Tarkistamaton osoite
korvataan tekstissä ilmoituksella, eikä sitä siirretä luonnokseen. Jos
komennossa on tarkistamaton osoite, komentoa ei voi siirtää, kopioida tai
ladata. Ilman verkkohakua erillinen linkki voi edelleen näkyä tarkistamattomana;
sen osoitetta ei hyväksytä suoritettavan skriptin sisällöksi.

Kun haluat muokata ehdotusta, paina vastauksen yhteydessä
**Muokkaa ja tallenna luonnokseksi**. Tämä painike
**siirtää** otsikon, ratkaisuvaiheet ja rajat lomakkeeseen. Se ei tallenna
mitään. Valitse erikseen esikatselussa ne ehdotetut komennot ja linkit, jotka
haluat siirtää; valitsemattomia ei siirretä. Kirjoituslomakkeelta pyydetyn ehdotuksen siirto kysyy ennen nykyisen
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

### Työkalut ja linkit

Kirjoituslomakkeen **Työkalut ja linkit (valinnainen)** -osiosta voit lisätä
useita komentoja ja linkkejä. Ilmoita kullekin komennolle tyyppi, täsmällinen
sisältö, käyttötarkoitus, soveltuva ympäristö ja oikeustarve. Valitse, onko
kyse vain tarkistuksesta vai järjestelmää muuttavasta komennosta. Muuttavalle
komennolle tarvitaan vaikutusten kuvaus ja palautusohje tai tieto siitä, ettei
palautusohjetta ole. Sovellus ei suorita komentoja.

Komento on aluksi **kokeilematon**. Ihmisen testaamalle komennolle on annettava
testaajan tunniste, testausaika ja testiympäristö. Ratkaisun vahvistaminen ei
merkitse komentoa testatuksi. Komennon sisällön tai tyypin muuttaminen poistaa
aiemman testausmerkinnän: tallenna uusi sisältö, testaa se ja merkitse testaus
erikseen. Tallennettu muokkaus palauttaa koko ratkaisun luonnokseksi, joka on
vahvistettava uudelleen.

Linkille annetaan nimi, http- tai https-osoite ja käyttötarkoitus. Suosi
valmistajien ja palveluntarjoajien omia ohjeita ja tarkista linkin kohde.
Sovellus ei päättele linkkiä viralliseksi.

Valitun ratkaisun oikeassa palstassa osio näkyy vain, jos tietueeseen on
tallennettu työkaluja tai linkkejä. **Näytä** avaa koodin ja **Kopioi** kopioi
vain komennon sisällön. PowerShellin **Lataa .ps1** ja komentokehotteen
**Lataa .bat** tallentavat saman sisällön
tiedostoon. Koko ratkaisun jako, kopiointi ja tulostus sisältävät myös työkalut
ja niiden vaikutus- ja testaustiedot. Hallinnan **Työkalujen muutoshistoria**
näyttää tallennetut työkalujen aiemmat sisällöt ja versiot.

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

Hallinta näyttää kullekin ratkaisulle yhden suljetun rivin. Avaa tai sulje
nykyisen version tiedot painamalla ratkaisun otsikkoa. Rivin **Poista käytöstä**
on erillinen toiminto. Avatusta ratkaisusta voi avata suuren lukunäkymän,
muokata, jakaa, kopioida tai tulostaa. **Muokkaa** avaa tietueen lomakkeeseen;
onnistunut tallennus palauttaa hallintaan ja avaa muokatun rivin. Tallennus
palauttaa tietueen luonnokseksi ja poistaa aiemman vahvistuksen. Muutos on
kokeiltava ja vahvistettava uudelleen.

**Poista käytöstä** pyytää syyn. Peruminen ei muuta tietuetta. Käytöstä poistettua
tietuetta ei voi enää muokata tai vahvistaa. **Versiohistoria** avautuu kunkin
ratkaisun sisältä. Siinä säilyvät tästä toiminnosta alkaen tallennetut aiemmat
versiot tiloineen, sisältöineen ja työkaluineen. Vanhan version voi lukea isona,
jakaa, kopioida tai tulostaa. **Luo tästä uusi luonnos** avaa sisällön uutena
tallentamattomana luonnoksena; aiempaa vahvistusta tai työkalujen testausmerkintää
ei siirretä. Alkuperäistä versiota ei muuteta. Ennen historiatoimintoa
tallentamattomia versioita ei voi palauttaa, ja niiden puuttumisesta ilmoitetaan.
Aiempi työkalukohtainen historia säilyy erikseen luettavissa.
**Päivitä lista** hakee tilanteen uudelleen.

### Poista pysyvästi

Jos tietue on tarkoitus poistaa kokonaan sovelluksesta, avaa sen rivi ja
**Lisätoiminnot**, ja valitse **Poista pysyvästi**. Toiminto on erillinen
käytöstä poistamisesta ja on käytettävissä myös vahvistetuille ja käytöstä
poistetuille tietueille. Vahvistusikkuna näyttää otsikon ja tunnisteen.
Kirjoita otsikko täsmälleen ja paina erillistä **Poista pysyvästi** -painiketta;
**Peruuta** ja Esc sulkevat ikkunan muuttamatta tietoja.

Pysyvä poisto poistaa ratkaisun, sen tallennetut versiot, työkaluhistorian,
komennot ja linkit. Toimintoa ei voi perua sovelluksessa. Aiemmissa
varmuuskopioissa voi edelleen olla kopio tiedoista. Tämä ei ole lupaus
levytason turvallisesta hävittämisestä.

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

## Työkalujen testit 29.10.2026

Erillistä testitietokantaa käyttänyt Chrome 156 -koe tarkisti hakutuloksen,
näppäimistövalinnan, PowerShell-sisällön ja komentokehotekomennon tarkan
kopioinnin, `.ps1`-tiedoston sisällön, kopiointivirheen, linkin, jakamisen,
tulostuksen, pitkän rivin ja 375 pikselin näkymän. Lomakkeella tarkistettiin
tallennus, uudelleenavaus, vahvistus, komennon muutos, testausmerkinnän
nollautuminen, työkaluhistoria ja uudelleenvahvistus. Ajetut komennot olivat
testitietokannan tekstiä: sovellus ei suorittanut niitä eikä tehnyt ulkoisia
API-kutsuja. Automaattiset Python-testit käyttivät erillisiä väliaikaisia
tietokantoja ja tarkistivat myös vanhan tietokannan migraation sekä
vaarallisten linkkien hylkäyksen.

Tekoälytyökalujen muutoksen testit 29.10.2026 käyttivät korvattuja API- ja
verkkohakuvastauksia. Ne tarkistivat muun muassa lähdetietojen ja verkkotunnuksen
rajauksen, puuttuvan mallin ja ristiriitaisen käyttöjärjestelmän, vaaralliset
URL-muodot, kokeilemattomuuden sekä tallennuksen erilliseen tietokantaan.
Chrome-kokeessa tarkistettiin esikatselu, peruutus, valikoiva siirto, tarkka
kopiointi ja .bat-tiedoston sisältö sekä kapea näkymä. Oikeaa verkkohakua tai
maksullista API-integraatiota ei tehty.

## Kaksivaiheinen verkkohaku

Kun verkkohaku on valittu, lähetysesikatselu kertoo, että hyväksyntä voi
käynnistää enintään kaksi erillistä API-pyyntöä ja että molemmista sekä
verkkohakutyökalusta voi syntyä kuluja. Käyttöliittymä näyttää vaiheet
**1/2 Haetaan lähteitä** ja **2/2 Muodostetaan ratkaisuehdotus**.
Hakuvaihe käyttää nykyistä valittua mallia, Responses API:n web_search
-työkalua ja include-asetusta web_search_call.action.sources ilman
ratkaisun JSON-skeemaa tai verkkotunnussuodatinta. Valmistajan verkkotunnus
ohjaa hakukyselyä, ja sovellus tarkistaa lähteiden URL-osoitteet sekä
hostname-arvot itse.

Toinen pyyntö lähetetään vain, jos ensimmäinen palauttaa sovelluksen
tarkistuksen läpäisseitä valmistajan lähteitä. Mukaan siirtyvät vain
ongelman ja ilmoitetun ympäristön tiedot sekä hyväksyttyjen lähteiden URL,
otsikko, saatavilla oleva tekstikatkelma ja rajattu hakuyhteenveto.
Verkkosisältö käsitellään epäluotettavana tietona. Ehdotuksen linkkikortti
hyväksytään vain, jos täsmällinen URL esiintyy vaiheen 1 lähteissä ja
valmistajan verkkotunnuksessa. Lähde tai verkkotunnus ei itsessään osoita
laitteen ja päivityksen yhteensopivuutta.

Jos hyväksyttäviä lähteitä ei saada, vaihetta 2 ei lähetetä. Näytetään
ilmoitus siitä, ettei päivityslinkkiä voitu varmistaa, sekä erillinen
mahdollisuus pyytää tavallinen tekoälyehdotus ilman varmennettuja
verkkolinkkejä. Se vaatii uuden esikatselun ja lähetysluvan. Hakuvaiheen
virheessä toista pyyntöä ei tehdä; ehdotusvaiheen virheessä automaattista
uusintaa ei tehdä ja lomaketekstit säilyvät. Vaiheiden lähde- ja
ehdotustilat näkyvät erillisinä diagnostiikassa.

OpenAI:n virallisen verkkohakuohjeen mukaan Responses API käyttää
web_search-työkalua; lähteiden näyttöä varten pyydetään
web_search_call.action.sources ja käytetyt URL-viitteet ovat
url_citation-merkintöjä. Ohjeen yksinkertainen hakuesimerkki ei vaadi
ratkaisuvastauksen JSON-skeemaa. Katso [Responses API:n verkkohakuohje](https://developers.openai.com/api/docs/guides/tools-web-search).

### Kaksivaiheisen muutoksen testiraportti

Käyttöliittymätestit ja erillisen testikannan kanssa ajettavat Python-testit
käyttävät korvattuja vastauksia; ne eivät tee maksullisia API-kutsuja.
Ne tarkistavat yhden pyynnön polun ilman hakua, kahden pyynnön järjestyksen
hyväksyttävillä lähteillä, toisen pyynnön ohituksen lähteiden puuttuessa tai
hakuvaiheen virheessä, toisen vaiheen virheen ja lomaketekstien säilymisen,
lähde- ja verkkotunnustarkistuksen, istuntoon sidotun kertakäyttöisen
lähdehaun sekä mobiili- ja näppäimistökäytön. Korvatuilla vastauksilla
testaus ei vahvista OpenAI-palvelun reaaliaikaista lähdehakua. Edellinen
oikea koe palautti yhden completed-hakutoiminnon mutta nolla lähdettä;
seuraava integraatiokoe on tehtävä erillisellä luvalla enintään kahdella
API-pyynnöllä ja sen onnistumiskriteeri on vähintään yksi lähteenä palautettu,
valmistajan verkkotunnukseen sopiva URL sekä sitä vastaava hyväksytty
linkkikortti.
Testiajon toteutuneet tulokset: tests/test_memory_ai_tools.py 20/20,
tests/test_api_setup.py 19/19, tests/test_memory_http.py 7/7 ja
tests/ui_memory_test.cjs 62/62 hyväksytty. Chromium 156 -selainregressio
synthetic-vastausten paikallisella testipalvelimella hyväksyi aiemmat
SOC-näkymä-, esikatselu-, jakamis-, tulostus-, näppäimistö- ja
320 pikselin mobiilitarkistukset; verkkohakupolussa korvattiin molemmat
API-vaiheet ja testin mittari raportoi 0 ulkoista API-kutsua. Käyttäjän
tietokantaa ei käytetty. Oikeaa integraatiokoetta ei tehty tämän muutoksen
yhteydessä.

## SOC-worktreen käynnistys porttiin 8511

Käynnistä tämä SOC-versio tavallisessa PowerShellissä näin. Komennot asettavat
työskentelykansioksi SOC-worktreen, käyttävät sen omaa `app.py`-tiedostoa ja
osoittavat tietokantapolun täsmälleen SOC:n `data/solutions-soc.sqlite3`
-tiedostoon. Corpus on `batch1`.

```powershell
$socRoot = 'C:\AI projektityö\AI_Service_Desk_ratkaisumuisti_SOC'
Set-Location $socRoot
$env:DESK_MEMORY_DB = [IO.Path]::GetFullPath((Join-Path $socRoot 'data\solutions-soc.sqlite3'))
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
py -3.13 -B (Join-Path $socRoot 'app.py') --corpus batch1 --port 8511
```

Jos `py -3.13` ei ole käytettävissä, käytä asennetun Python 3.13:n
suoritettavaa tiedostoa täydellä polulla. Pidä `Set-Location`, `app.py` ja
`DESK_MEMORY_DB` SOC-worktreen poluissa; älä käytä toisen worktreen suhteellista
`app.py`-polkua tai tietokantaa. Tarkista selaimessa
`http://127.0.0.1:8511/health`: corpus-arvon pitää olla `batch1`.
Ratkaisumuistin sivu on `http://127.0.0.1:8511/memory`.

API-avain ja mallivalinta **Ota käyttöön** -toiminnolla ovat palvelinprosessin
muistissa. Palvelimen uudelleenkäynnistys palauttaa asetukset käynnistysympäristön
`OPENAI_API_KEY`- ja `OPENAI_MODEL`-arvoista, jos ne ovat prosessin ympäristössä;
`.env`-tiedostoa ei lueta automaattisesti. Jos mallia ei ole käynnistysympäristössä
määritelty, sovellus käyttää oletuksena `gpt-4.1-mini`-mallia. Käyttöliittymässä
tehty mallivalinta pitää asettaa uudelleen palvelimen uudelleenkäynnistyksen
jälkeen. Älä kirjoita API-avainta tähän ohjeeseen tai komentohistoriaan.

Käyttäjän vahvistama oikea verkkohakukoe tehtiin mallilla `gpt-4.1` ja palautti
valmistajan lähteitä. Erillisessä oikeassa selainkokeessa NVIDIA-linkki avasi
yleisen ajurihakusivun; sivu ei ollut yksilöidyn ajuripaketin lataus eikä osoittanut
laitteen ja käyttöjärjestelmän yhteensopivuutta. Tämä yksittäinen koe ei takaa
myöhempien hakujen tulosta tai päivityksen soveltuvuutta.
