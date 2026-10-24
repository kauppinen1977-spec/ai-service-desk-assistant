# Ratkaisumuistin API-käyttöönoton korjaus – 24.10.2026

## Rajaus ja lähtötilanne

Työ tehtiin projektissa `C:\AI projektityö\AI_Service_Desk_ratkaisumuisti`,
haarassa `kehitys/ratkaisumuisti`. Projektin juuresta, sen ylähakemistoista tai
projektin tiedostohausta ei löytynyt AGENTS.md:tä. Lähtötilanteen ainoa
Git-muutos oli `docs/10_poc_valitavoite_2026-10-19.md`:n 83 rivin lisäys;
se säilytettiin. Vanhaa projektia, main-haaraa, hakua tai aineistoa ei muutettu.
Muutoksia ei pushattu eikä commitoitu.

## Portti 8502 ja asetusten todellinen lähde

Alkuhavainnossa kuuntelija oli PID **21820**, osoite `127.0.0.1:8502`.
Windowsin QueryFullProcessImageNameW varmisti suoritustiedostoksi tämän projektin
`.python-runtime\cpython-3.13.15-windows-x86_64-none\python.exe`.
Vanhempi oli PID **28332**, tämän projektin `.venv\Scripts\python.exe`.
Jatkon tarkistuksessa havaittiin myös PID **13620** / vanhempi **30748** samoilla
suoritustiedostopoluilla. Siksi prosessin tunnistusta ei perusteta pelkkään
aiemmin kirjattuun PID-numeroon. Paikallinen `/health` ilmoitti `corpus=batch1`
ja `api_key_available=true`; tämä ei todista avaimen kelvollisuutta.

Aiempaa käynnistystä kuvaava paikallinen `data/key-rotation/rotate-key-8502.ps1`
asettaa avaimen omaan prosessiympäristöönsä ja käynnistää `app.py --corpus batch1
--port 8502`. Python-palvelin perii tuon ympäristön. Aiempi `desk.request_model`
luki jokaisessa kutsussa **palvelinprosessin** `OPENAI_API_KEY`-muuttujan.
Toisessa PowerShellissä asetettu muuttuja ei muuta jo käynnissä olevan
palvelimen ympäristöä. `.env`-tiedostoa ei ole eikä sovellus lataa sitä.
Avaimen arvoa ei tulostettu tai luettu diagnostiikkaraporttiin; tarkistukset
käyttivät vain saatavuustilaa, koodia ja prosessipolkuja.

## Toistuvan avainvirheen varmennettu syy ja todistuksen raja

Varmennettu ohjelmavirhe oli **kaikkien HTTP 401 -vastausten nimeäminen vääräksi
API-avaimeksi**. Koodi ei lukenut palveluntarjoajan `error.code`-kenttää.
Myös HTTP 429 yhdisti laskutus-/saldovirheen ja kutsurajan.

Aiemman kokeen `data/key-rotation/live-key-test.json` sisältää vain sovelluksen
HTTP 502 -vastauksen ja sen itse muodostaman `invalid_api_key`-koodin.
Vanha koodipolku osoittaa tämän tarkoittaneen palveluntarjoajan HTTP 401:tä;
se ei osoita palveluntarjoajan palauttaneen `invalid_api_key`-koodia.
Alkuperäistä turvallista virhekoodia ei säilytetty, joten **varsinaista
palveluntarjoajan hylkäyssyytä ei voida jälkikäteen todistaa**. Väärää avainta,
oikeusongelmaa tai muuta tunnistautumisongelmaa ei arvata syyksi.

Aiempi raportti osoittaa erikseen myös prosessiympäristöjen eron: valmistelun
ympäristössä avain oli saatavilla mutta vanha palvelin ilmoitti sen puuttuvan.
Tämä selittää tuon puuttuvan asetuksen, ei myöhemmän 401-hylkäyksen tarkkaa syytä.
Tässä työssä ei tehty uutta oikeaa API-kutsua.

Virheluokittelun lähteenä käytettiin [OpenAI:n virallista virhekoodiohjetta](https://developers.openai.com/api/docs/guides/error-codes).
HTTP-tilan lisäksi tarkistetaan virhekoodi, jotta tunnistautuminen, oikeudet,
mallin saatavuus, saldo ja kutsuraja saavat eri toimintaohjeen.

## Toteutus

- `api_settings.py`: vain prosessin muistiin tehtävä avain- ja malliasetus.
  Paikallinen arvo ohittaa perityn ympäristön heti seuraavassa pyynnössä.
  Avaimen poisto ei palauta vanhaa ympäristöavainta tämän käynnin aikana.
- `/api/memory/api-settings` ja `api-status`: istuntotunnisteella suojatut
  paikalliset POST-toiminnot. Vastauksessa on vain saatavuus, lähde, malli,
  säilyvyys ja viimeisin turvallinen tulosluokka. Asetusreitit eivät käytä
  ratkaisumuistin tietokantaa eivätkä API:a. Vastauksia ei välimuistiteta.
- Peitetty avainkenttä tyhjennetään onnistumisessa ja virheessä. Avainta ei
  palauteta selaimeen, tallenneta selaimen paikallistallennukseen, lokiin,
  tietokantaan tai tiedostoon. Kaikki samaan palvelimeen avatut sivut käyttävät
  samaa asetusta. Palvelimen sammutus hävittää paikallisen muutoksen;
  uudelleenkäynnistyksessä mahdollinen peritty ympäristöasetus on taas voimassa.
- `desk.request_model`: HTTPS POST `/v1/responses`, `Authorization: Bearer`,
  JSON-skeema, `store=false`, 45 sekunnin aikakatkaisu. Avain kuuluu vain
  otsakkeeseen. Malli ja avain otetaan samasta asetustilanteesta.
  Uudelleenohjauksia ei seurata, jotta Authorization ei siirry toiseen osoitteeseen.
- Virheissä erotetaan puuttuva/muotovirheinen paikallinen asetus, yksilöity
  hylätty avain, muu tunnistautuminen, oikeudet, mallin saatavuus, laskutus,
  kutsuraja, verkko/TLS/DNS, aikakatkaisu ja pyyntö-/vastausmuoto.
  HTTP-virheestä palautetaan lisäksi alkuperäinen HTTP-tila ja vain
  sallintalistaan kuuluva virhekoodi; muu koodi on `unrecognized`.
  Raakavirhettä tai palveluntarjoajan vapaata tekstiä ei palauteta tai lokiteta.
- **Pyydä tekoälyehdotus** näyttää lähetys-/odotustilan ja lukitsee sivun kentät
  käsittelyn ajaksi. Saman sivun kaksoispainallus ei lähetä toista pyyntöä.
  Automaattisia uusintayrityksiä ei ole. Virhe säilyttää kaikki ratkaisukentät,
  ja onnistuminenkin kysyy ennen olemassa olevan otsikon/ratkaisun korvaamista.
  Ehdotus ei tallennu tai vahvistu automaattisesti.
- Paikallista sivua ja sen istuntotunnistetta ei tarjota vieraan Host-nimen alla.

## Testit ja tulokset

Lopullinen Python-regressio: **231/231 hyväksytty**. Uudessa
`tests/test_api_setup.py`:ssä on 14 testimetodia; virheluokittelutesti kattaa
21 korvattua HTTP-virhevastausta. Tarkistettiin myös rikkinäiset/ylisuuret
vastaukset, mallin keskeneräinen tai väärä vastaus, DNS/TLS/yhteysvirheet,
suora ja URLErroriin kääritty aikakatkaisu, avaimen vaihto sekä vanhan
vastauksen sivuuttaminen asetuksen vaihdon jälkeen.

Python-testiajossa ulkoiset `socket.create_connection`-yhteydet estettiin;
vain localhost sallittiin HTTP-regressioille. Hugging Face -kirjastot olivat
offline-tilassa ja käynnistysympäristön API-avain tyhjennettiin testiprosessista.
API-testit käyttävät vain synteettisiä avaimia ja korvattua kuljetusta.
Pyynnön URL, POST, Bearer-otsake, malli, sisältö, JSON-skeema ja `store=false`
tarkistettiin. Avaimen vaihtaminen vaikuttaa seuraavaan korvattuun kutsuun.
Raakavirheeseen lisätty synteettinen salaisuus ei päädy HTTP-vastaukseen.

Käyttöliittymäregressio: **28/28 testikohdetta hyväksytty**, joista
`ui_memory_test.cjs` sisältää **22** ratkaisumuistin DOM-testiä.
Muut kuusi itsenäistä skriptiä läpäisivät myös omat sisäiset tarkistuksensa.
Testattiin peitetty kenttä, asetuksen tila ja tyhjennys, tekstien säilyminen,
tarkat virheohjeet, eteneminen, kaksoispainallus sekä tallennuksen puuttuminen.
`git diff --check` läpäisi.

Komennot: Pythonin `unittest.defaultTestLoader.discover('tests')` yllä kuvatulla
verkkosuojauksella sekä
`node --test tests/ui_memory_test.cjs tests/ui_state_test.cjs tests/ui_candidate_visibility_test.cjs tests/ui_safety_stop_test.cjs tests/ui_startup_fact_test.cjs tests/ui_ticket_clear_test.cjs tests/ui_batch1_test.cjs`.
Syötetiedoston vaativa `ui_demo_chain_test.cjs` ei kuulu itsenäiseen testiajoon;
sen yritys ilman aiempaa havaintotiedostoa päättyi puuttuvaan argumenttiin.

**Oikeaa selainkoetta ei tehty.** Selaintyökalun käynnistys epäonnistui myös
uudelleenalustuksen jälkeen: `windows sandbox failed: helper_unknown_error:
setup refresh had errors`. DOM-testit eivät osoita visuaalista asettelua,
ruudunlukijakäyttöä tai oikean API-palvelun toimivuutta.

## Käyttöönoton tilanne

Vanhan palvelimen pysäytys palautti Windowsin `Käyttö estetty` -virheen.
Prosessipolut varmennettiin ennen pysäytysyritystä. Windowsin korotetulla
toiminnolla pysäytettiin vain varmennettu tämän projektin palvelin
(PID 21820, vanhempi 28332). Portin vapautuminen tarkistettiin ennen uuden
prosessin käynnistystä. Uusi palvelin käynnistettiin tavallisella Start-Processilla.

**Käyttöönotto valmistui porttiin 8502.** Lopullisen kuuntelijan PID oli
**5600**, käynnistäjän PID **23292**. Parametrit ovat edelleen
`app.py --corpus batch1 --port 8502`, ja tietokantapolku on tämän projektin
`data/solutions.sqlite3`. Uusi palvelin käynnistettiin tarkoituksella ilman
perittyä API-avainta, jotta aiempi epäselvä asetus ei siirry käyttöön.
Käyttäjä antaa avaimen uuteen paikalliseen asetusnäkymään.

Paikalliset GET `/health`, GET `/memory` ja istuntotunnisteella suojattu
POST `/api/memory/api-status` onnistuivat. Uusi sivu tarjosi asetusnäkymän ja
**Pyydä tekoälyehdotus** -toiminnon. Tila oli `configured=false`, `source=none`,
`model=gpt-4.1-mini`, `last_result=not_tested`. Tässä tarkistuksessa tehtiin
**0 ehdotuspyyntöä ja 0 ulkoista API-kutsua**.

Tietokannan tarkistussumma säilyi ennen ja jälkeen käyttöönoton samana.
Paikalliset, Gitin ulkopuolelle jäävät todisteet ovat
`data/api-setup/deployment.json`, `stop-result.json` ja `readiness.json`.
Ne sisältävät vain turvallisia tila- ja tarkistussummatietoja.

Ennen uuden sivuversion avaamista käyttäjän on kopioitava mahdolliset vanhan
sivun tallentamattomat tekstit talteen: sivun päivitys vaihtaa ladatun
käyttöliittymän. Uuden näkymän asetusmuutokset ja API-virheet eivät tyhjennä
ratkaisulomaketta. Avaimen vaihto ei vaadi enää palvelimen uudelleenkäynnistystä.

Tietokannan lähtötarkistussumma:
`C8AF7E3ACEE130EFD4A5A460B66485C1553FC5AC9D9C6D1E84D5567308986F59`.
