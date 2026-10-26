# Ratkaisumuistin tilannekatsaus PoC-palautusta varten

Päiväys: 26.10.2026. Projektisuunnitelma on käyttäjän ilmoituksen mukaan
palautettu Moodleen. Tämä katsaus koskee nykyistä paikallista ratkaisumuistia
projektissa `C:\AI projektityö\AI_Service_Desk_ratkaisumuisti`, haarassa
`kehitys/ratkaisumuisti`, lähtöcommitissa `9d2d397`.

Ratkaisumuistista on näyttöä rajatun työnkulun toimivuudesta: luonnos,
ihmisen vahvistus, vahvistetun tapauksen haku ja käytöstä poistaminen.
Haku-näkymän tekoälyehdotus on toteutettu, ja käyttäjä on raportoinut sen
kautta tehdyn ketjun onnistuneeksi. Hakutulosten soveltuvuus ja ehdotettujen
korjausten tekninen oikeellisuus vaativat edelleen ihmisen tarkistuksen.
26.10.2026 tehty [erillisen palautuskopion ensikäyttökoe](20_puhdas_ensikayttokoe.md)
läpäisi avaimettoman sanahakuketjun uudessa virtuaaliympäristössä sekä
uudelleenkäynnistyksen oikealla automatisoidulla Chromella. Erillinen
vektorikoe onnistui käyttäen valmiita kehitysympäristön paketteja ja paikallista
mallivälimuistia. Se ei ole puhdas vektorihaun asennuskoe tai uuden Windows-
koneen koe. [Asennusohje](21_ratkaisumuistin_asennus.md) on nyt täydennetty.
Alla oleva alkuperäinen näyttö on erotettu tämän myöhemmän kokeen tuloksista.

## Alkuperäisen tilannekatsauksen rajaus ja paikallinen lähtötilanne

Katsaus perustuu lähdekoodin, ohjeiden, Gitin paikallisten viitteiden ja
tallennettujen testiraporttien lukemiseen. AGENTS.md:tä ei löytynyt projektin
juuresta, ylemmistä hakemistoista eikä projektin ohje- ja lähdetiedostojen
hausta. Projektin README, pikaohje, tekninen kuvaus ja testiraportit luettiin.
Alkuperäistä tilannekatsausta laadittaessa ei ajettu sovellusta, testejä tai hakukokeita, tehty API-kutsuja,
käynnistetty palvelimia uudelleen eikä avattu käyttäjän tietokantaa
tietokantatoimintojen kautta. Uudet hyväksyntätulokset eivät siten synny tästä
katsauksesta. Tiedostojen tarkistussummia käytettiin säilymisen varmistamiseen.

Ennen katsauksen kirjoittamista työpuussa oli seuraavat keskeneräiset muutokset:

- Muokatut: `.gitignore`, `docs/10_poc_valitavoite_2026-10-19.md` ja
  `docs/12_solution_memory.md`.
- Seuraamattomat: `docs/16_ratkaisumuistin_haun_laatuarviointi.md`,
  `docs/17_ratkaisumuistin_arviointiaineisto.md` ja
  `docs/18_ratkaisumuistin_arviointipohja.md`.
- Staging-alueella ei ollut muutoksia. Kaikki yllä mainitut säilytettiin.

### Paikallisen ja GitHub-version erot

| Kohde | Paikallisesti todettu tila |
|---|---|
| Nykyinen haara | `kehitys/ratkaisumuisti`, HEAD `9d2d397` |
| Seurattava etähaara | `origin/feature/solution-memory`, paikallinen viite `d643fba` |
| Commit-ero | Nykyinen haara on 6 committia edellä, 0 jäljessä tätä viitettä |
| `main`, `origin/main` ja `v0.1.0-poc` | Osoittavat paikallisesti committiin `3aa6c86`, alkuperäiseen PoC-versioon |
| Etärepositorio | `https://github.com/kauppinen1977-spec/ai-service-desk-assistant.git` |

Kuusi paikallista lisäcommittia sisältävät Windowsin istuntovirheen korjauksen,
oikean paikallisen upotusmallin arviointia, rakenteiset ympäristörajaukset,
OS-aliakset ja vektorijärjestyksen korjauksen, käyttöliittymän uudistuksia sekä
Haku-näkymän tekoälyehdotuksen. Commit-tasolla eroa on 23 tiedostossa.
Paikalliset keskeneräiset dokumenttimuutokset tulevat tämän lisäksi.

Vertailu käyttää viimeksi paikallisesti tallennettuja `origin/*`-viitteitä.
GitHubin tämänhetkistä sisältöä ei tarkistettu verkosta, eikä `fetch`-, commit-
tai push-toimintoja tehty. GitHubista oletushaaran lataava uusi käyttäjä ei
näiden paikallisten viitteiden perusteella saa nykyistä ratkaisumuistia.
Myös `feature/solution-memory`-version ja tämän paikallisen version välillä
on yllä kuvattu ero; palautuksen haara tai paketti on yksilöitävä.

Katsauksen laatimishetkellä `docs/19_poc_valmiustilanne.md` jäi `.gitignore`-
säännön `/docs/*` piilottamaksi. Ensikäyttökokeen yhteydessä 26.10.2026
lisättiin sallintarivit dokumenteille 19, 20 ja 21. Ne voidaan nyt ottaa
mukaan palautukseen ilman pakottavaa Git-lisäystä. Tiedostoja ei ole stagettu,
commitoitu tai pushattu.

## 1. Toteutetut ja testatut toiminnot

Toteutuksen tarkistus kattoi tiedostot `app.py`, `solution_memory.py`,
`api_settings.py`, `memory.html` sekä ratkaisumuistin käyttämän hakureitin
`search.py`:stä. Alla testinäyttö tarkoittaa aiemmissa raporteissa kirjattua
näyttöä, ei tässä työssä uusittua testausta.

| Toiminto | Nykyinen toteutus ja näytön rajaus |
|---|---|
| Luonnoksen tallennus | SQLite-tallennus luo luonnoksen. Vain `verified`-tilaiset tietueet kuuluvat hakuun. Pysyvyys ja tilasiirtymät kuuluvat Python-/HTTP-regressioihin. |
| Ihmisen vahvistus | Edellyttää vahvistajan tunnistetta ja ilmoitusta ratkaisun kokeilemisesta kyseisessä ympäristössä. Tietueen tilaksi tulee vahvistettu. Ohjelma tallentaa ilmoituksen; se ei todista kokeilua tai henkilöllisyyttä. |
| Muokkaus | Tallentaminen palauttaa ratkaisun luonnokseksi ja poistaa vahvistuksen. Revisionumero estää vanhentuneen version ylikirjoituksen. Näille on regressiotestejä. |
| Käytöstä poistaminen | Poistamisen syy vaaditaan. Tietue poistuu hausta mutta säilyy historiassa syineen. Vanha vektorivälimuisti ei saa palauttaa luonnosta tai poistettua tietuetta hakuun; tätä tarkistetaan synteettisillä upotuksilla. |
| Paikallinen sanahaku ja vektorihaku | Haku käyttää vahvistettuja tietueita. Käyttöjärjestelmän, tuotteen ja version ilmoitetut ristiriidat suodatetaan ennen hakua ja enintään kolmen osuman valintaa. OS-aliakset ja suodatus on regressiotestattu. Ratkaisumuistin vektorihaku käyttää kosinijärjestystä rajalla 0,43 ilman alkuperäisen PoC:n uudelleenjärjestelyjä. |
| Tulosten esittäminen | Ilmoitetuilta kentiltään yhteensopivat ja puuttuvien tietojen vuoksi tarkistettavat ehdokkaat erotetaan. Molemmat tulevat samasta enintään kolmen osuman joukosta. Hakupiste ei ole varmuusprosentti. |
| Haku-näkymän tekoälyehdotus | Ensimmäinen painike avaa lähetysesikatselun. Vasta erillinen lupa ja lähetyspainike pyytävät ehdotuksen. Lähetetään ongelmakuvaus, vapaa ympäristökuvaus ja täytetyt rakenteiset ympäristökentät. Hakutuloksia, tietokannan ratkaisuja tai keskeneräistä kirjoituslomaketta ei lähetetä. Ehdotusreitti ei avaa tietokantaa. |
| Ehdotuksesta luonnokseksi | Ehdotus näkyy ensin kokeilemattomana: ratkaisuvaiheet sekä soveltuvuuden rajat. **Muokkaa ja tallenna luonnokseksi** siirtää sisällön lomakkeeseen; varsinainen tallennus vaatii erillisen **Tallenna luonnos** -painikkeen. Automaattista tallennusta tai vahvistusta ei ole. |
| Tekstin säilyminen ja muokkaus | Välilehtien vaihto, epäonnistunut pyyntö ja korvaamisen peruminen säilyttävät tekstin. Kasvava kenttä ja suuri muokkain on testattu DOM-korvikkeella sekä oikealla Chromella. Sivun päivitys voi hävittää tallentamattoman tekstin. |
| API-asetukset ja virhetilanteet | Peitetty avainkenttä, prosessin muistissa tehtävä asetuksen vaihto, kentän tyhjennys, virheluokittelu, odotustila ja saman sivun kaksoislähetyksen esto on testattu korvatuilla API-vastauksilla. Asetuksen muuttaminen ei tee ulkoista API-kutsua. |
| Uudelleenkäynnistys ja istunto | Aiempi paikallinen palvelin-/HTTP-koe osoitti tallennetun vahvistetun tietueen ja käytöstä poiston säilyvän oikeiden prosessien uudelleenkäynnistyksissä. Vanha istuntotunniste hylättiin. Tämä ei ollut käyttäjän selaimessa tekemä uudelleenkäynnistyskoe. |

### Raportoidut testitulokset

| Näyttö | Raportoitu tulos | Mitä siitä voi päätellä |
|---|---|---|
| Haku-ehdotuksen Python-regressiot, 24.10.2026 | 234/234, ei virheitä; myös paikallinen `data/search-suggestion/python-results.json` vastaa lukua | Testatut ohjelmalogiikan ja rajapinnan tapaukset läpäisivät. API-kuljetus oli korvattu, tietokannat tilapäisiä ja verkkokäyttö rajattu. |
| Haku-ehdotuksen JavaScript-/DOM-regressiot | Raportissa 42/42 testikohdetta, ratkaisumuistin osuus 36 | Käyttöliittymän testatut tilat ja tietovirrat; DOM-korvike ei osoita oikean selaimen asettelua. |
| Automatisoitu Chrome omalla testipalvelimella | 18/18 tarkistusta | Oikean selainmoottorin tarkistukset, tuotannon HTML ja korvatut vastaukset. |
| Chrome portin 8502 sivulla | Haku-ehdotus 5/5; aiemmat muokkaustoiminnot 4/4 | Sivun ja käyttökulun tarkistukset. Haku-ehdotuksen POST-pyynnöt korvattiin ennen palvelinta; 5/5 ei ole oikea API-, tallennus- tai hakuketju. |
| Palvelimen säilyvyyskoe | Vahvistettu tietue löytyi uudelleenkäynnistyksen jälkeen; poistettu pysyi poissa hausta ja historiassa | Paikallinen palvelin-/HTTP-ketju, erillään käyttäjän selainhavainnoista. |

Tuloksia ei lasketa yhteen: ajot kattavat osin samoja toimintoja.
Alkuperäisen PoC:n README:ssä olevat 161/174/248 testin luvut ja sen puhdas
Windows-asennus eivät ole nykyisen ratkaisumuistin hyväksyntätestejä.
Myös aiemmat ratkaisumuistin 194/209/217/231 testin ajot kuvaavat omia
kehitysvaiheitaan. Haun laatumittauksen 158/158 on erillinen rajattu
regressioajo, jossa kolme testiä jätettiin pois.

Lähteet: [ratkaisumuistin lisätestaus](10_poc_valitavoite_2026-10-19.md),
[API-käyttöönoton raportti](14_api_kayttoonotto_testiraportti.md) ja
[luettavuuden sekä Haku-ehdotuksen raportti](15_ratkaisumuistin_luettavuus_testiraportti.md).
Raakatulokset `data/`-hakemistossa eivät kuulu Git-julkaisuun.

## 2. Käyttäjän raportoimat onnistuneet selainkokeet

Nämä ovat käyttäjän ilmoituksia. Niitä ei esitetä tämän katsauksen tekijän
toistamina kokeina, palvelinlokista todennettuina API-kutsuina tai
yleisenä ratkaisulaadun arviointina.

| Käyttäjän ilmoittama koe | Hyväksytyksi raportoitu havainto | Näytön raja |
|---|---|---|
| Kajo77, 24.10.2026 | Luonnos ei löytynyt hausta; vahvistettu löytyi oikealla tekstillä; käytöstä poisto poisti osuman; tietue säilyi historiassa | Yhden tapauksen työnkulku. Ei uudelleenkäynnistyksen jälkeistä selainhavaintoa tai ratkaisun sanatarkkaa sisältöä. |
| Commitin `44d9cdb` jälkeinen selainkoe | Käyttäjä ilmoitti uudistetun työnkulun toimineen | Yleinen ilmoitus ei yksilöi kaikkia kenttiä, näppäimistöä tai ikkunakokoja. |
| Luettavuus ja suuri muokkain | Kasvava ratkaisukenttä, **Avaa isona** ja tekstin säilyminen palattaessa toimivat | Ei osoita koko sovelluksen saavutettavuutta tai kaikkien selainten tukea. |
| Valmis Haku-näkymän ehdotuspolku | Ehdotus pyydettiin Haku-näkymässä ja tallennettiin luonnokseksi; luonnos ei tullut sanahakuun; käytännössä kokeiltu ja vahvistettu ratkaisu löytyi sen jälkeen | Onnistunut käyttäjän ilmoittama ketju. Raportti ei yksilöi ratkaisun sisältöä, riippumatonta teknistä tarkistusta tai käytettyä avainta. |

Viimeinen havainto on [raportin 15 lopussa](15_ratkaisumuistin_luettavuus_testiraportti.md).
Se täydentää raportin aiempaa mainintaa vielä tekemättömästä käyttäjän
Haku-kokeesta. Samoin myöhempi onnistumisilmoitus pidetään erillään
[raportin 10](10_poc_valitavoite_2026-10-19.md) aiemmasta epäonnistuneesta
API-kokeesta. Aiemman sovellusvirheen vuoksi vanha `invalid_api_key`-ilmoitus
ei yksin todista palveluntarjoajan hylkäyksen tarkkaa syytä; tämä on selvitetty
[raportissa 14](14_api_kayttoonotto_testiraportti.md).

## 3. Tunnetut virheet ja rajoitteet

### Paikallinen haku ja väärät osumat

Haku palauttaa samankaltaisia aiempia tapauksia. Se ei varmista, että
korjaus ratkaisee uuden ongelman. Erityisesti sama tuote, virhekoodi tai
oirekieli voi tuoda väärän osuman myös silloin, kun sopivaa ratkaisua ei ole.
Sanahaku on vertailutaso, eikä sen yleisestä osumatarkkuudesta ole tässä
riittävää näyttöä. Vektorihaku ei ratkaise tätä puutetta automaattisesti.

[Haun laatumittaus](16_ratkaisumuistin_haun_laatuarviointi.md) käytti oikeaa
paikallista upotusmallia mutta synteettisiä ratkaisuja, kyselyitä ja odotettuja
vastauksia. Raportin erillisessä 17 kyselyn loppujaossa rakenteisilla rajauksilla:

- Vähintään yksi väärä osuma jäi 11/17 kyselyyn.
- Niistä seitsemästä kyselystä, joihin sopivaa ratkaisua ei ollut, 4/7 palautti
  silti osumia.
- Kolme väärää osumaa oli ilmoitettujen ympäristötietojen perusteella
  yhteensopivaksi merkityssä ryhmässä.

Luvut osoittavat tämän synteettisen asetelman virheitä. Ne eivät osoita
ratkaisujen teknistä oikeellisuutta, todellisten tukitapausten laatua tai
tuotantokelpoisuutta. Myöskään synteettisen aineiston hyvä top-3-löytyvyys ei
ole tällainen näyttö. Kehitys- ja loppukyselyiden laatija ja odotusten arvioija
olivat samasta kehitystiimistä. [Uusi arviointiaineisto](17_ratkaisumuistin_arviointiaineisto.md)
on myös synteettinen, ja [arviointipohja](18_ratkaisumuistin_arviointipohja.md)
on tarkistushetkellä täyttämättä; siitä ei ole hyväksyntätuloksia.

Ympäristösuodatus käyttää vain erikseen ilmoitettuja kenttiä. Puuttuva tieto
ei osoita yhteensopivuutta. Organisaatiota ei tunnisteta eikä OS:ää tai
versiota päätellä ongelmatekstistä. Täsmäävät kentät eivät erottele saman
ympäristön eri oireita. Aiemmin raportoidut OS-alias- ja PoC-heuristiikkojen
järjestysvirheet on korjattu paikallisissa committeissa, mutta väärät osumat
jäävät tunnetuksi rajoitteeksi. Hakuraja 0,43 ja tulosraja kolme ovat ennallaan.

### Tekoälyehdotus, vahvistus ja säilyvyys

- Haku-näkymän tekoälyehdotus on erillinen mallin ehdotus. Se ei ole
  verkkohaku eikä paikallisilla hakutuloksilla tai lähteillä vahvistettu vastaus.
  Automatisoiduissa regressioissa käytettiin korvattuja API-vastauksia.
- Ihmisen vahvistus koskee tiettyä aiempaa tapausta ja tallennettua versiota.
  Se ei osoita soveltuvuutta uuteen tapaukseen. Vahvistajan nimi on vapaasti
  annettu tunniste. Sovellus on paikallinen yhden käyttäjän PoC.
- Historia säilyttää käytöstä poistetun tietueen ja syyn, mutta ei kaikkia
  muokkausten aiempia tekstiversioita. Poistettua tietuetta ei voi muokata tai
  vahvistaa uudelleen; sisältö on tarvittaessa kopioitava uudeksi luonnokseksi.
- Ratkaisun tallennusraja on 8000 merkkiä. Ehdotuksen vaiheet ja rajat voivat
  yhdessä ylittää sen; käyttäjän on lyhennettävä tekstiä ennen tallennusta.
- Turvallisuuskeskeytys tunnistaa rajattuja sääntöpohjaisia tapauksia.
  Se ei kata kaikkia vaaroja tai tietoturvaongelmia.
- Tallennetut tietueet säilyvät SQLite-tiedostossa, oletuksena
  `data/solutions.sqlite3`. Tallentamaton lomaketeksti voi hävitä sivun
  päivityksessä. Selainpäivitys tarvitaan palvelimen istunnon vaihduttua.
- Käyttäjän selaimessa tekemä koko ketjun uudelleenkäynnistyskoe on edelleen
  dokumentoimatta. Palvelin-/HTTP-säilyvyyskoe on jo raportoitu erikseen.
  Lisäksi raportin 20 automatisoitu oikean Chromen koe osoitti erillisessä
  palautuskopiossa sisällön ja vahvistuksen säilyvän uudelleenkäynnistyksessä.
- Ruudunlukijaa, kosketuslaitetta ja kaikkia selainmoottoreita ei ole testattu.

### API-avain säilyy vain palvelimen käynnin ajan

Käyttöliittymässä annettu avain ja malliasetus säilyvät vain palvelinprosessin
muistissa. Ne säilyvät selaimen sulkemisessa ja sivun päivityksessä, mutta
katoavat palvelimen sammuessa. Avainta ei tallenneta sovelluksen tiedostoon,
tietokantaan, selaimen paikallistallennukseen, lokiin tai Gitiin eikä palauteta
asetustilan vastauksessa. Kaikki samaan paikalliseen palvelimeen avatut sivut
käyttävät samaa asetusta.

Uudelleenkäynnistyksessä mahdollinen peritty `OPENAI_API_KEY` ja
`OPENAI_MODEL` tulevat taas käyttöön. Siksi avain voi näyttää asetetulta,
vaikka käyttöliittymässä annettu asetus on kadonnut. **Poista avain käytöstä**
estää käytön vain nykyisen palvelinkäynnin ajaksi. `.env`-tiedostoa ei lueta
automaattisesti. Asetettu avain tai `/health`-kentän `api_key_available=true`
ei osoita avaimen, mallioikeuden tai laskutuksen toimivuutta.

Raportin 15 viimeisin käyttöönottotarkistus kirjasi lähteeksi `environment`
ja tulokseksi `not_tested`. Tämä on aiemman tarkistuksen tila, ei katsauksen
aikana uudelleen luettu nykytila. Käyttäjän ilmoittamaa myöhempää onnistumista
ei pidä tulkita kaikkien tulevien käynnistysten API-asetusten varmennukseksi.

### Käynnistysohje ja uuden käyttäjän kokeilumahdollisuus

[README](../README.md) sisältää aiemman PoC:n puhtaan Windows-asennuksen.
[Tekninen kuvaus](12_solution_memory.md) antaa nykyisen ympäristön
käynnistyskomennon porttiin 8501, kun taas [pikaohje](13_ratkaisumuistin_pikaohje.md)
olettaa tämän worktreen palvelimen jo olevan käynnissä portissa 8502.
Ensikäyttökokeen yhteydessä lisättiin [yhtenäinen asennusohje](21_ratkaisumuistin_asennus.md)
porttiin 8513 ja täydennettiin README:n, teknisen kuvauksen ja pikaohjeen
linkitys. Ohje yksilöi paikallisen haaran `kehitys/ratkaisumuisti` ja oman
tietokannan. Vanhan PoC:n ohjeet säilyvät omana historiallisena kokonaisuutenaan.

Sanahaku, käsin kirjoittaminen, luonnos, vahvistus ja käytöstä poisto eivät
tarvitse API-avainta tai vektoririippuvuuksia. Uusi tietokanta ei kuitenkaan
sisällä käyttäjän aiempia ratkaisuja: ne ovat paikallisessa, Gitin ulkopuolisessa
tiedostossa. Uudelle kokeilijalle on annettava ohje oman kuvitteellisen
tapauksen luomiseen ja vahvistamiseen ennen hakua. Vektorihaku edellyttää
erillisiä paketteja ja mallin saatavuutta; tekoälyehdotus toimivaa omaa
API-asetusta. Sovellus lukee HTML:n käynnistyksessä, joten levyn muutokset
edellyttävät palvelimen uudelleenkäynnistystä ja selaimen päivitystä.

## 4. Ennen PoC-palautusta välttämättömät tehtävät

1. **Yksilöi palautettava versio ja varmista ensikäyttö uudessa kansiossa.**
   Päivitys 26.10.2026: erillinen palautuskopio, manifesti ja uuden
   virtuaaliympäristön avaimeton ensikäyttö on tehty raportissa 20.
   Jäljellä ovat lopullisen jakelutavan valinta ja haluttaessa toisen
   käyttäjän itsenäinen ohjekokeilu. Seuraava kuvaus on alkuperäinen tavoite.
   Valitse tarkka haara/commit tai paikallinen palautuspaketti ja kirjaa ero
   GitHubin oletushaaraan sekä vanhempaan ratkaisumuistihaaraan. Sisällytä
   tarvittavat dokumentit, myös tämä katsaus; ratkaise sallintalistan puute
   myöhemmässä palautusvalmistelussa. Yhdistä ohjeeksi Python-edellytykset,
   ympäristön luonti, käynnistys, yksi selkeä portti ja `/memory`-osoite,
   sammutus sekä portti- ja istuntovirheistä jatkaminen. Tarkista ohje
   erillisellä tyhjällä tietokannalla ja uudella käyttäjällä tai puhtaassa
   kansiossa. Hyväksyntäraja: kokeilija saa ilman API-avainta tallennettua
   kuvitteellisen luonnoksen, vahvistettua sen ja löydettyä sen sanahaulla.
   Tämä tarvitaan, jotta arvioija voi kokeilla palautettua versiota ilman
   tekijän paikallisia ympäristöjä, tietokantaa tai jo käynnissä olevaa palvelinta.

2. **Täydennä toistettava selainnäyttö nykyisen version elinkaaresta.**
   Päivitys 26.10.2026: raportti 20 kattaa erillisellä tietokannalla luonnoksen,
   vahvistuksen, sanahaun ja uudelleenkäynnistyksen oikeassa automatisoidussa
   Chromessa. Se ei kata alla mainittuja muokkaus-/käytöstäpoistovaiheita
   tai paikallisesti asetetun API-avaimen elinkaarta.
   Käytä myöhemmässä erikseen tehtävässä kokeessa erillistä testitietokantaa.
   Kirjaa syöte, versio, selain, odotus ja tulos: luonnos ei haussa,
   vahvistettu haussa, muokkaus palauttaa luonnokseksi, uudelleenvahvistus,
   säilyminen palvelimen uudelleenkäynnistyksessä sekä käytöstä poisto ja
   historian säilyminen. Tarkista samalla sivun päivitys ja API-asetuksen
   katoaminen tai palautuminen käynnistysympäristöstä. Liitä nykyiset käyttäjän
   onnistumisilmoitukset ja korvattujen testien rajaukset selvästi erilleen.
   Jos palautus väittää nykyisen oikean API-yhteyden toimivan, siitä tarvitaan
   yksilöity käyttäjän koetulos tai myöhemmin erikseen sallittu API-koe;
   avaimen saatavuustila ei riitä. Tässä katsauksessa kutsua ei tehdä.
   Tämä tarvitaan erityisesti vielä puuttuvan selaimen uudelleenkäynnistysnäytön
   ja nykyiseen versioon sidotun, arvioitavan esittelyketjun vuoksi.

3. **Rajaa hakua koskevat väitteet ja dokumentoi väärät osumat esittelyssä.**
   Valitse pieni, etukäteen arvioitu tapausjoukko: sopiva tapaus,
   samankaltainen mutta sopimaton tapaus ja kysely, jolle ratkaisua ei ole.
   Tarkista tapausten sisältö ihmisen kanssa ennen hakutulosten katsomista ja
   vertaa sana- ja vektorihakua samoilla tiedoilla, jos molemmat esitetään
   palautuksessa. Raportoi myös väärät ja tyhjät tulokset sekä puuttuvien
   ympäristötietojen vaikutus. Pohjaa 18 voi käyttää merkintöihin, mutta sen
   synteettiset tapaukset eivät todista korjausten teknistä toimivuutta.
   Teknistä oikeellisuutta koskeva väite edellyttää korjauksen kokeilua ja
   tuloksen kirjaamista kyseisessä testiympäristössä. PoC:n hyväksyttävä
   rajaus on ihmisen tarkistama ehdokashaku; uuden hakualgoritmin toteutus
   ei ole tämän rajauksen edellytys. Tämä tarvitaan, jotta tunnetut väärät
   osumat eivät muutu palautuksessa perusteettomaksi lupaukseksi oikeasta ratkaisusta.

## 5. Myöhempään jatkokehitykseen sopivat tehtävät

- Laajempi riippumattomasti arvioitu aineisto, todellisia tukitapauksia
  asianmukaisesti käsiteltynä sekä teknisesti kokeillut ympäristökohtaiset
  ratkaisut. Kehitys- ja loppuarviointi pidetään erillään.
- Oireen ja organisaation erottelu, vastausta vailla olevien kyselyiden
  tunnistaminen sekä hakurajan, yhdistelmähakujen tai uudelleenjärjestyksen
  vertailu. Menetelmämuutokset arvioidaan myös heikennysten osalta ennen
  oletuskäyttöön ottamista.
- Monen käyttäjän tunnistautuminen, käyttöoikeudet, todennettava vahvistaja,
  kattava muutoshistoria sekä varmuuskopiointi- ja palautusmenettelyt.
- Avainten pysyvä turvallinen säilytys vain erikseen suunniteltuna tarpeena.
  Nykyinen vain palvelimen käynnin ajan säilyvä asetus voidaan pitää
  dokumentoituna PoC-rajauksena.
- Laajempi saavutettavuus-, selain- ja kosketuslaitetestaus sekä pidempien
  ratkaisujen hallinta. Nykyiset Chrome- ja DOM-tarkistukset säilyvät rajattuna näyttönä.

Katsauksen laatimisessa ainoa uusi tiedosto on tämä dokumentti. Ohjelmakoodia,
käyttäjän tietokantaa, vanhaa projektia tai `main`-haaraa ei muuteta;
keskeneräisiä muutoksia ei poisteta, commitoida tai pushata.
