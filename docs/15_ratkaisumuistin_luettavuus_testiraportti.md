# Ratkaisumuistin tekoälyehdotuksen luettavuus ja muokkaus – 24.10.2026

Käyttäjä vahvisti oman selainkokeensa onnistuneen: kasvava ratkaisukenttä,
**Avaa isona** ja tekstin säilyminen suuresta näkymästä palattaessa toimivat.
Tämä havainto täydentää alla dokumentoitua automatisoitua Chrome-tarkistusta.

## Rajaus ja aiemman työn säilyminen

Työ tehtiin projektissa `C:\AI projektityö\AI_Service_Desk_ratkaisumuisti`,
haarassa `kehitys/ratkaisumuisti`. AGENTS.md:tä ei löytynyt projektista eikä
ylemmistä hakemistoista. Ennen muutoksia tarkistettiin Git-tila ja nykyinen
diff. Aiemmat keskeneräiset API-korjaukset, dokumentit ja testit säilytettiin.
Paikallinen vertailupohja on Gitin ulkopuolella `data/ui-readability/`-kansiossa.

Tämän työn muutokset koskevat `memory.html`:ää, sen DOM-testiä, uutta
Chrome-selaintestiä, pikaohjetta, tätä raporttia ja uusien tiedostojen
Git-sallintalistaa. API-avaimen käsittelyä, palvelimen Python-koodia,
tietokantarakennetta, hakumoottoria, hakurajaa tai aineistoa ei muutettu.
Vanhaa projektia tai main-haaraa ei muutettu. Mitään ei commitoitu tai pushattu.

## Toteutettu käyttäytyminen

- Ratkaisukentän lähtökoko on noin 12 tekstiriviä. Se kasvaa sisällön mukaan
  noin 20 riviin, minkä jälkeen sisältöä vieritetään kentän sisällä.
  Käyttäjän käsin suurentamaa korkeutta kunnioitetaan myöhemmässä kirjoituksessa.
- **Avaa isona** näyttää suuren, ikkunaan mukautuvan muokkaimen. Sama
  textarea-elementti siirretään dialogiin ja palautetaan lomakkeelle;
  tekstin kopioinnista tai erillisten muokkauspuskureiden synkronoinnista
  aiheutuvaa hävikkiä ei ole. `form="editor"` säilyttää lomakeyhteyden.
  Teksti, valinta ja vieritys säilyvät avattaessa.
- Muokkaimen sulkeminen painikkeella tai Escillä säilyttää sisällön.
  Kohdistus palautuu avaamispainikkeeseen. Tab ja Shift+Tab pysyvät dialogin
  tekstikentässä ja sulkemispainikkeessa. Myöhäinen close-tapahtuma ei palauta
  kenttää pois nopeasti uudelleen avatusta muokkaimesta.
- Tekoälyehdotus näytetään ensin lukunäkymässä otsikoilla **Ratkaisuvaiheet**
  ja **Soveltuvuuden rajat ja puuttuvat tiedot**. Merkintä kertoo ehdotuksen
  olevan kokeilematon ja tallentamaton. Rivinvaihdot säilyvät, pitkät rivit
  rivittyvät ja sisältö asetetaan `textContent`-ominaisuudella.
  Mallin HTML:ää, linkkejä tai komentosarjoja ei tulkita HTML:ksi.
- **Muokkaa ja tallenna luonnokseksi** siirtää otsikon sekä molemmat
  sisältöosat lomakkeeseen. Nykyisen otsikon/ratkaisun korvaaminen kysytään.
  Peruminen säilyttää molemmat tekstit. Muuttuneelle ongelma-/ympäristökuvaukselle
  ei siirretä vanhaa ehdotusta huomaamatta. Siirto ei kutsu tallennusrajapintaa.
- **Tallenna luonnos**, ihmisen vahvistus ja käytöstä poisto käyttävät
  entisiä palvelintoimintoja. Tallennukseen menee edelleen yksi `solution`-teksti,
  jossa myös soveltuvuuden rajat säilyvät. Vanhoja ratkaisuja ei jaotella
  uudelleen eikä sisältöä migroida.
- Aiempi 8000 merkin tallennusraja on ennallaan. Jos uuden ehdotuksen osat
  ylittävät yhdessä rajan, teksti säilyy kokonaisuudessaan ja käyttäjää
  ohjataan lyhentämään sitä ennen tallennusta. Mitään ei katkaista.

## Automaattiset regressiot

Python: **231/231 testiä hyväksytty**. Ajettiin
`unittest.defaultTestLoader.discover('tests')` offline-asetuksilla ja
`socket.create_connection`-suojauksella, joka sallii vain localhost-yhteydet.
API-avain tyhjennettiin vain erillisestä testiprosessista. Testit käyttävät
tilapäisiä testitietokantoja; käyttäjän tietokantaan ei kohdistettu testitoimintoja.

DOM-/JavaScript-regressio: **35/35 testikohdetta hyväksytty**, joista
ratkaisumuistin `ui_memory_test.cjs` sisältää **29** testitapausta.
Uudet/muutetut tapaukset kattavat lukunäkymän ilman kenttien ylikirjoitusta,
erillisen siirron ja tallennuksen, perumisen, muuttuneen ongelman,
epäluotettavan HTML:n, suuren muokkaimen ja kohdistuksen, myöhäisen
sulkemistapahtuman, automaattisen/käsin tehdyn koon, pitkän vanhan ratkaisun
ja ylipitkän yhdistetyn ehdotuksen. Aiemmat tallennus-, vahvistus- ja
käytöstäpoistotestit läpäisivät.

Komento:

```text
node --test tests/ui_memory_test.cjs tests/ui_state_test.cjs tests/ui_candidate_visibility_test.cjs tests/ui_safety_stop_test.cjs tests/ui_startup_fact_test.cjs tests/ui_ticket_clear_test.cjs tests/ui_batch1_test.cjs
```

## Oikean selaimen tarkistus

Selaintesti suoritettiin oikealla asennetulla **Chrome 155.0.8059.85** -selaimella
headless-tilassa, erillisessä testiprofiilissa. Testi käynnistää oman localhost-
palvelimen, joka tarjoaa tuotannon HTML-/JavaScript-tiedoston ja korvatut
vastaukset. Se ei käytä portin 8502 palvelinta, käyttäjän tietokantaa tai
API-avainta. Testisivun ulkoiset verkkopyynnöt estetään DevTools-rajapinnassa.

```text
node tests/ui_memory_browser_test.cjs
```

Tulos: **13/13 selaintarkistusta hyväksytty**.

| Tarkistus | Havainto |
|---|---|
| Pitkä vanha teksti | Koko sisältö avautui ja säilyi muokkauksessa sekä korvatussa tallennuksessa. |
| Automaattinen koko | 24 px rivikorkeus, kentän korkeus 502 px; noin 20 riviä sekä reunat ja tyhjä tila. Pidempi sisältö vieri kentän sisällä. |
| Käsin suurentaminen | Chromen oikeasta koonmuutoskahvasta suurennus 597 px:iin; myöhempi kirjoitus säilytti korkeuden. |
| Näppäimistö | Enter avasi muokkaimen; kohdistus oli tekstissä. Tab/Shift+Tab kiersivät sisällä. Esc ja sulkemispainike säilyttivät tekstin ja palauttivat kohdistuksen. |
| Ehdotuksen lukeminen | Lomakkeen teksti pysyi ennallaan. HTML- ja script-merkkijonot näkyivät tekstinä eikä niitä suoritettu. |
| Ehdotuksen siirto | Peruminen säilytti keskeneräisen tekstin. Hyväksytty siirto sisälsi myös rajat eikä tehnyt tallennusta. |
| Ikkunat | 1280 × 900, 320 × 700, 320 × 480 ja 760 × 600. Ei vaakaylivuotoa; tekstikenttä pysyi muokkaimen sisällä ja sulkemispainike saavutettavana. |

Testauksen aikana korjattiin Tab-kohdistuksen karkaaminen ja nopean
sulkemisen/uudelleenavaamisen ajoitusongelma. Kuvakaappausten tarkistus
paljasti myös matalan muokkaimen toistuvan ohjetekstin vievän tilaa;
sama ohje jätettiin vain lomakkeelle ja muokkaimeen oma lyhyt ohje.
Korjausten jälkeen selaintesti uusittiin ja lopulliset kuvakaappaukset katsottiin.

Paikalliset todisteet: `data/ui-readability/browser/results.json`,
`desktop-long.png`, `desktop-modal.png`, `narrow-preview.png`,
`narrow-modal.png`, `modal-320x480.png` ja `modal-760x600.png`.
Nämä eivät kuulu Gitiin. Testi teki **0 ulkoista API-kutsua**.

## Säilyvyys ja tarkistusten rajat

Käyttäjän `data/solutions.sqlite3` säilyi bittitasolla ennallaan tämän työn
lähtötilanteeseen verrattuna. SHA-256:
`9b806116d7129893f83893cc122caa512e3e7881a9657862b6b8aba2f47118c0`.
Myös `api_settings.py`, `app.py`, `desk.py`, `solution_memory.py`, `search.py`
ja `corpus.py` verrattiin lähtötilan tarkistussummiin: kaikki ennallaan.
`git diff --check` läpäisi.

Tarkistus on automatisoitu oikean Chrome-selaimen koe ja kuvakaappausten
visuaalinen katselmus. Ruudunlukijaa, kosketuslaitetta, mobiilin
näyttönäppäimistöä tai Firefoxia/Safaria ei testattu. Oikeaa API-vastausta
ei pyydetty, eikä testaus osoita tekoälyn ratkaisujen laatua.

Käynnissä olevaa portin 8502 palvelinta ei pysäytetty tai käynnistetty
uudelleen, jotta nykyinen prosessissa oleva API-asetus säilyy. Tämä palvelin
lataa HTML-sivun käynnistyksessä; muutettu näkymä tulee sen käyttöön
seuraavassa käynnistyksessä. Selaintesti käytti muutettua tiedostoa suoraan
omalla testipalvelimellaan. Uudelleenkäynnistyksen yhteydessä on huomioitava
paikallisen API-asetuksen aiemmin dokumentoitu säilyvyys.

## Keskeytyneen tehtävän jatkotarkistus 24.10.2026

Ensin luettiin Gitin tila ja nykyiset toteutukset. Haara oli edelleen
`kehitys/ratkaisumuisti`, ja kaikki aiemmat muutokset sekä uudet tiedostot
säilytettiin. AGENTS.md:tä ei löytynyt projektin tiedostoista, piilotetut
hakemistot mukaan lukien, eikä poluista `C:\AGENTS.md` tai
`C:\AI projektityö\AGENTS.md`. Ohjetiedostoa ei siksi voitu lukea.

Ennen testien käynnistämistä luettiin prosessilista. Projektin palvelin
`app.py --corpus batch1 --port 8502` oli käynnissä; aiempia testiajoja ei
näkynyt. Palvelinta ei pysäytetty, käynnistetty uudelleen tai käytetty testeissä.

Kaikki neljä sovittua toimintoa olivat jo toteutettuina: kasvava ratkaisukenttä,
suuri muokkain, kahteen osaan jaettu ehdotuksen lukunäkymä sekä erillinen siirto
muokkaukseen ilman automaattitallennusta. Toteutusta ei kirjoitettu uudelleen.
Jatkokierroksella uusittiin seuraavat tarkistukset nykyisille tiedostoille:

- JavaScript-/DOM-regressiot: **35/35 hyväksytty**, ratkaisumuistin osuus **29**.
- Python-testit: **231/231 hyväksytty**, ei virheitä tai epäonnistumisia.
  API-avain tyhjennettiin vain testiprosessin ympäristöstä ja mallikirjastot
  asetettiin offline-tilaan. Pythonin auditointisuoja salli vain localhost-
  testiyhteydet, esti yhteydet porttiin 8502 ja salli SQLite-yhteydet vain
  tilapäishakemiston testitietokantoihin. Estettyjen operaatioiden määrä oli **0**.
- Chrome-selaintesti: **13/13 hyväksytty**, versio **155.0.8059.85**.
  Testi käytti omaa localhost-palvelinta ja korvattuja vastauksia. Ulkoisia
  API-kutsuja oli **0**. Uusitut kapean lukunäkymän ja 320 × 480 -muokkaimen
  kuvakaappaukset katsottiin: osiot erottuivat, teksti rivittyi ja sulkemispainike
  pysyi näkyvissä.
- `api_settings.py`, `app.py`, `desk.py`, `solution_memory.py`, `search.py`,
  `corpus.py` ja `data/solutions.sqlite3` säilyivät tarkistussummiltaan ennallaan
  sekä tämän jatkokierroksen että aiemman paikallisen vertailupohjan suhteen.

Python-jatkotarkistuksen tulos on paikallisessa tiedostossa
`data/ui-readability/resume-python-results.json`. Selaintestin `results.json`
ja kuvakaappaukset päivitettiin onnistuneesta uudesta ajosta. Saman hakemiston
vanhemmat `failure.*`-tiedostot ovat aiemman korjauskierroksen todisteita;
niitä ei poistettu, eivätkä ne ole jatkotarkistuksen tulos.

Pikaohjeeseen lisättiin tieto käynnissä olevan palvelimen vanhasta HTML:stä ja
uudelleenkäynnistyksen vaikutuksesta paikalliseen API-asetukseen. Toimintojen
toteutus ja testaus ovat valmiit. Käyttöönotto portin 8502 palvelimeen jäi
seuraavaan käynnistykseen. Oikeita API-kutsuja ei tehty, eikä vanhaa projektia,
main-haaraa tai käyttäjän tietokantaa muutettu. Mitään ei commitoitu tai pushattu.

## Käynnissä olevan palvelimen korjaus ja selainvarmistus 24.10.2026

Käyttäjä ilmoitti, ettei muutos näy hänen selaimessaan. Todellinen syy oli
käynnissä olevan palvelimen vanha HTML-kopio: `app.py` lukee `MEMORY_PAGE`:n
moduulin latautuessa ja palauttaa saman merkkijonon jokaisessa `/memory`-
pyynnössä. Aiempi erillinen testipalvelin käytti uusinta tiedostoa, mutta
portin 8502 vanhaa palvelinta ei silloin käynnistetty uudelleen.

Ennen korjausta portin `127.0.0.1:8502` omisti PID **5600**, jonka Python-
käynnistin oli PID **23292**. Molempien suoritettavat tiedostot olivat tämän
projektin omissa Python-hakemistoissa. Komento oli
`app.py --corpus batch1 --port 8502`, ja prosessi oli käynnistetty klo 17.40.55.
Lisäksi löytyi saman projektin toinen käynnistysyritys, PID **11080** ja sen
käynnistin **9616**; se ei ollut tarkistushetkellä portin kuunteleva prosessi.

HTTP:llä luettu sivu ei sisältänyt `expand-solution`-painiketta eikä
`rows="12"`-kenttää, vaikka levyn nykyisessä `memory.html`:ssä molemmat olivat.
Sivua verrattiin tiedostoon normalisoimalla ainoastaan palvelimen istuntotunnus;
sisällöt erosivat. Kyse oli palvelimen vanhasta versiosta. Nykyistä
käyttöliittymätoteutusta ei tarvinnut muuttaa.

Pysäytettiin vain edellä tunnistetut tämän projektin Python-palvelinprosessit
ja niiden Python-käynnistimet. Uusi palvelin käynnistettiin projektihakemistossa
absoluuttisella komennolla:

```text
"C:\AI projektityö\AI_Service_Desk_ratkaisumuisti\.venv\Scripts\python.exe" -B "C:\AI projektityö\AI_Service_Desk_ratkaisumuisti\app.py" --corpus batch1 --port 8502
```

Uusi kuunteleva prosessi oli PID **30408**, käynnistin **34472**. Uuden
`/memory`-vastauksen sisältö vastasi levyn tiedostoa istuntotunnusta lukuun
ottamatta. `/health` ilmoitti `ok: true` ja aineistoksi `batch1`.

**API-asetuksen vaikutus:** ennen uudelleenkäynnistystä tila oli
`configured: true`, `source: local`, `last_result: success`. Paikallinen,
vain prosessin muistissa ollut asetus katosi. Uusi tila oli `configured: true`,
`source: environment`, `last_result: not_tested`, malli `gpt-4.1-mini`.
Käynnistysympäristön asetus tuli siis käyttöön; avainta ei luettu, tulostettu,
kopioitu tai testattu OpenAI-palvelussa. Asetustilan lukupyyntö on paikallinen
eikä tee ulkoista API-kutsua.

### Oikean Chromen tarkistus juuri portissa 8502

Tavallisen selainvälilehden ohjausta yritettiin kahdesti. Työkalu ei alustunut:
`node_repl kernel exited unexpectedly`, ja tarkempi virhe oli
`windows sandbox failed: orchestrator_helper_exit_nonzero: setup helper exited with status Some(1)`.
Siksi käyttäjän omaa selainvälilehteä ei ohjattu tai päivitetty.

Asennettua **Chrome 155.0.8059.85** -selainta käytettiin sen sijaan headless-
tilassa erillisessä testiprofiilissa. Testi avasi suoraan käynnissä olevan
palvelimen osoitteen **http://127.0.0.1:8502/memory**. Tässä tarkistuksessa ei
käytetty korvattua HTML:ää, API-vastauksia tai erillistä testipalvelinta.
Selaimen verkkopyynnöistä sallittiin vain kyseisen `/memory`-sivun GET-pyyntö;
kaikki POST-pyynnöt ja muut osoitteet estettiin. Faviconin pyyntö estettiin.

Testiin `tests/ui_memory_browser_test.cjs` lisättiin tämä erillinen `--live`-tila:

```text
node tests/ui_memory_browser_test.cjs --live
```

Tulos: **4/4 hyväksytty**:

| Tarkistus | Tulos |
|---|---|
| Painikkeen näkyminen | Kirjoita ratkaisu -välilehdellä näkyi **Avaa isona**. |
| Sisällön mukana kasvaminen | Oikealla tekstinsyötöllä kentän korkeus kasvoi **310 → 502 px**; pidempi sisältö vieri sisällä. |
| Suuri muokkain ja sulkeminen | Enter avasi muokkaimen. Siellä kirjoitettu lisäys säilyi kokonaan sulkemispainikkeella palattaessa, ja kohdistus palautui avaamispainikkeeseen. |
| Escillä paluu | Uudelleenavaus ja Esc säilyttivät saman muokatun tekstin. |

JavaScript-poikkeuksia ei havaittu tarkistuksen aikana. Selain ei lähettänyt
yhtään POST-pyyntöä. Luonnosta ei tallennettu eikä API-ehdotusta pyydetty.
Selaimen kuvakaappaukset `live-editor.png` ja `live-expanded.png` katsottiin:
painike näkyi ja suuri muokkain sisälsi lisätyn tekstin sekä sulkemispainikkeen.
Todisteet ovat paikallisesti `data/ui-readability/live-server/`-hakemistossa:
`before.json`, `after.json`, palvelimen käynnistyslokit ja `browser/results.json`
sekä kuvakaappaukset. Ne eivät kuulu Gitiin.

Selaintestin alkuperäinen, korvattuja vastauksia käyttävä ajotila tarkistettiin
muutoksen jälkeen: **13/13 hyväksytty**. Sovelluksen Python-koodia tai
käyttöliittymän HTML:ää ei muutettu tällä korjauskierroksella.

Käyttäjän tietokannan SHA-256 ennen ja jälkeen tämän korjauksen oli
`8dceca42c3b59ce23621addc08b6652f6c2e6810d496aa7e8d7c85770363dd4f`.
Vertailu koskee tämän korjauskierroksen lähtötilannetta. Aiemmat muutokset
säilytettiin; vanhaa projektia ja main-haaraa ei muutettu eikä mitään pushattu.

Käynnissä olevan palvelimen korjaus on valmis. Käyttäjän jo auki oleva välilehti
voi edelleen sisältää vanhan sivun ja istuntotunnuksen: mahdollinen
tallentamaton teksti pitää kopioida talteen ennen sivun päivittämistä.

## Tekoälyehdotus suoraan Haku-näkymässä – 24.10.2026

Ennen työtä luettiin Gitin tila, nykyinen toteutus ja käynnissä olevat prosessit.
AGENTS.md:tä ei löytynyt projektista tai yläkansioista. Työ jatkui haarassa
`kehitys/ratkaisumuisti`, ja aiemmat keskeneräiset muutokset säilytettiin.
Käyttäjän oman selainkokeen onnistuminen kirjattiin raportin alkuun.
Paikallinen tämän kierroksen vertailupohja on `data/search-suggestion/`.

### Toteutettu käyttökulku

- Hakutulosten yhteydessä on **Pyydä tekoälyehdotus**. Se avaa Haku-näkymään
  esikatselun eikä siirry kirjoituslomakkeeseen tai tee API-pyyntöä.
- Esikatselu näyttää jo annetun ongelmakuvauksen, täytetyt käyttöjärjestelmä-,
  tuote- ja versiotiedot sekä valinnaisen vapaan ympäristökuvauksen. Tyhjät
  ympäristötiedot näytetään puuttuvina. Hakutuloksia, tietokannan ratkaisuja
  tai kirjoituslomakkeen tekstiä ei välitetä ehdotuspalvelulle.
- Vasta lähetyslupa ja **Lähetä ja pyydä ehdotus** käynnistävät pyynnön.
  Jokaisen lähetettävän kentän muuttaminen nollaa lähetysluvan. Tyhjä vapaa
  ympäristökuvaus ja puuttuvat erilliset ympäristötiedot sallitaan.
- Ehdotus näytetään samassa Haku-näkymässä olemassa olevalla lukunäkymällä:
  **Ratkaisuvaiheet** sekä **Soveltuvuuden rajat ja puuttuvat tiedot**.
  HTML-merkinnät säilyvät tekstinä. Ehdotus on merkitty kokeilemattomaksi ja
  tallentamattomaksi. Haun ja kirjoituslomakkeen omat ehdotukset säilyvät
  erikseen välilehteä vaihtaessa.
- **Muokkaa ja tallenna luonnokseksi** kysyy ennen keskeneräisen lomakkeen
  korvaamista. Peruminen säilyttää molemmat tekstit ja jättää käyttäjän
  Haku-näkymään. Hyväksytty siirto avaa uuden luonnoksen; aiempaa tietue-ID:tä
  tai vahvistusta ei siirretä. Tallennus tehdään edelleen erillisellä painikkeella.
- Hyväksyttyyn siirtoon sisältyvät ongelma, ilmoitetut ympäristötiedot, otsikko,
  vaiheet ja rajat. Jos vapaa ympäristökuvaus puuttui, muokkauslomakkeeseen
  asetetaan näkyvä teksti **Vapaata ympäristökuvausta ei ilmoitettu.** Tämä ei
  ole tekoälypalvelulle lähetetty lisätieto, eikä käyttäjältä vaadita kuvauksen
  keksimistä luonnoksen tallentamiseksi.
- Jos alkuperäiset haun tiedot muuttuvat ehdotuksen saamisen jälkeen, vanhan
  ehdotuksen siirto estetään. Ehdotus säilyy luettavana.
- Odotuspainike, 45 sekunnin odotusohje, kenttien lukitus, kaksoislähetyksen
  esto sekä virhekoodien ja täsmäohjeiden näyttö säilyvät molemmissa poluissa.

Palvelimen muutos rajoittuu `solution_memory.py`:n ehdotuspolkuun: vapaa
ympäristökuvaus on ehdotuksessa valinnainen, ilmoitetut ympäristökentät
validoidaan ja välitetään mallille erillisinä tietoina, ja turvallisuustarkistus
kattaa myös ne. `suggest` käsitellään ennen `Memory`-olion luontia, joten
ehdotuksen pyytäminen ei avaa tai alusta ratkaisumuistin tietokantaa.
Hakumoottoria, hakurajaa, aineiston laajuutta, tallennusrajoja tai API-avaimen
tallennustapaa ei muutettu. Myös kirjoituslomakkeen aiempi ehdotuspolku toimii.

### Testitulokset

| Tarkistus | Tulos |
|---|---|
| Python-regressiot | **234/234 hyväksytty**. Kolme uutta tapausta kattavat valinnaiset/erilliset tiedot, ehdotuksen tietokannattomuuden, virheelliset kentät ja ympäristötietojen turvallisuustarkistuksen. |
| JavaScript-/DOM-regressiot | **42/42 hyväksytty**, joista ratkaisumuistin testit **36**. Seitsemän uutta käyttökulkutestiä kattavat esikatselun, luvan, kaikki kentät, tyhjät valinnaiset tiedot, siirron ja perumisen, erilliset ehdotukset, odotuksen, virheet ja turvallisuuspysäytyksen. |
| Chrome, oma testipalvelin | **18/18 hyväksytty**, sisältäen aiemmat 13 sekä viisi Haku-ehdotuksen tarkistusta. |
| Chrome, portin 8502 nykyinen sivu | **5/5 Haku-ehdotuksen tarkistusta hyväksytty**; HTML luettiin oikeasta käynnissä olevasta palvelimesta ja POST-vastaukset korvattiin selaimessa. |
| Chrome, aiemmat muokkaustoiminnot portissa 8502 | **4/4 hyväksytty**: painike, kasvu, suuri muokkain ja tekstin säilyminen myös Escillä. |

Python-testit ajettiin tyhjällä vain testiprosessin API-avaimella ja
offline-asetuksilla. Auditointisuoja salli vain erilliset localhost-testiyhteydet
ja tilapäishakemistossa olevat testitietokannat sekä esti portin 8502 käytön.
Estettyjen operaatioiden määrä oli **0**. Testien API-vastaukset olivat korvattuja.

Selaimena oli asennettu **Chrome 155.0.8059.85** headless-tilassa ja omassa
testiprofiilissa. Suoraan porttiin 8502 kohdistuva tarkistus ajettiin komennolla:

```text
node tests/ui_memory_browser_test.cjs --live-search
```

Tämä ajotila salli palvelimelle vain `/memory`-sivun GET-pyynnöt. Haku-,
ehdotus- ja asetustilapyynnöt korvattiin Chromen DevTools-rajapinnassa ennen
niiden lähettämistä palvelimelle. Muita pyyntöjä ei sallittu. Siksi oikea
API-ehdotus, tietokantahaku tai luonnoksen tallennus ei voinut käynnistyä.
Koe kattoi myös odottavan pyynnön kaksoispainalluksen, tarkan virhekoodin ja
ohjeen sekä tyhjät valinnaiset tiedot. Tulokset ja kuvakaappaukset ovat
`data/search-suggestion/browser-live/`-hakemistossa. Käyttäjän tavallista
selainvälilehteä ei ohjattu; aiemmin todettu selainohjaustyökalun Windows-
alustusongelma kierrettiin asennetun Chromen erillisellä testiprofiililla.

### Käyttöönotto ja säilyvyys

Lopulliset selaintarkistukset ajettiin peräkkäin. Kaksi tätä ennen rinnakkain
ajettua tarkistusta jäi odottamaan päättymistään; vain niiden tunnistetut
testiajurit ja omat Chrome-testiprofiilit suljettiin. Testin DevTools-komennoille
lisättiin 15 sekunnin aikakatkaisu. Peräkkäinen uusinta päättyi normaalisti:
Haku-polku **5/5**, aiemmat muokkaustoiminnot **4/4**, testipalvelin **18/18**.
Lähetysesikatselun sekä leveän ja 320 px leveän lukunäkymän kuvakaappaukset
katsottiin. Portin 8502 kokeissa JavaScript-poikkeuksia oli **0**.

Ennen käyttöönottoa portin 8502 sivulta puuttui uusi lähetysesikatselu eikä
sen sisältö vastannut muutettua tiedostoa. Pysäytettiin vain tämän projektin
aiemmin tunnistetut palvelinprosessit **30408** ja **34472**, ja palvelin
käynnistettiin uudelleen absoluuttisella tämän projektin `app.py`-polulla,
aineistolla `batch1` ja portilla `8502`. Uudelleenkäynnistyksen jälkeen
`/memory` vastasi levyn tiedostoa istuntotunnuksen korvausta lukuun ottamatta.
Nykyinen näkymä on siten käytössä myös käynnissä olevassa palvelimessa.

API-asetuksen tila oli sekä ennen että jälkeen uusimman käynnistyksen
`configured: true`, `source: environment`, `last_result: not_tested` ja
malli `gpt-4.1-mini`. Prosessin paikalliset asetukset katoavat aina
uudelleenkäynnistyksessä; tällä kierroksella käytössä oli jo ympäristöasetus.
Avainta ei luettu tai testattu ulkoisessa palvelussa. Oikeita API-kutsuja oli **0**.

Käyttäjän tietokannan SHA-256 säilyi tämän kierroksen lähtötilanteesta:
`8dceca42c3b59ce23621addc08b6652f6c2e6810d496aa7e8d7c85770363dd4f`.
Pikaohje päivitettiin uuteen käyttökulkuun. Käyttäjän tietokantaa, vanhaa
projektia ja main-haaraa ei muutettu, eikä mitään pushattu.

Jäljelle jäävät testauksen rajat: oikean API-palvelun vastausta tai avaimen
kelvollisuutta ei testattu, eikä tällä kierroksella tehty ruudunlukija-,
kosketuslaite- tai muiden selainmoottorien koetta. Uuden Haku-polun käyttäjän
oma selainkoe on vielä tekemättä. Vanha välilehti pitää päivittää; mahdollinen
mahdollinen tallentamaton teksti on kopioitava talteen ennen päivitystä.

## Käyttäjän ilmoittama selainkoe

Käyttäjä raportoi kokeilleensa valmista Haku-näkymän työnkulkua oikeassa
selaimessa. Hänen ilmoituksensa mukaan tekoälyehdotus pyydettiin Haku-näkymässä,
tallennettiin luonnokseksi, luonnos ei tullut sanahaun tuloksiin, ja käytännössä
kokeiltu sekä vahvistettu ratkaisu löytyi tämän jälkeen haulla.

Tulos on käyttäjän ilmoittama koe, eikä sitä väitetä agentin toistamaksi
käyttöliittymä- tai API-testiksi. Raportoidut tilasiirtymät vastaavat
luonnosten hakurajausta ja vahvistettujen tietueiden hakua.
