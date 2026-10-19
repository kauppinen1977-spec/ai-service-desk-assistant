# PoC-välitavoitteen testiraportti – 19.10.2026

AI Service Desk Assistantin työversiossa on saavutettu rajattu, käyttäjälle
näkyvän vastausketjun PoC-välitavoite. Raportti erottaa käyttäjän ilmoittamat
selainhavainnot paikallisista mockatuista testeistä. Kyse ei ole
tuotantovalmiuden, riippumattoman loppuarvioinnin tai kaikkien tilanteiden
turvallisuuden hyväksynnästä.

## Todisteet ja niiden rajat

- Käyttäjän ilmoittama selainhavainto: VPN-001:n vastaus näkyi OpenAI-live-tilassa.
  Selainkuva osoittaa vastauksen, mutta API-kutsun onnistumista ei ole erikseen
  vahvistettu palvelinlokista. Kuvan tiedostopolkua ei ole kirjattu tähän raporttiin.
- Käyttäjän ilmoittamat käytännön havainnot: epäselvä käynnistysongelma johti
  lisätietopyyntöön ja vaarallinen akku turvallisuuskeskeytykseen ilman
  OpenAI-kutsua. Näitä ei ajettu uudelleen tätä dokumenttia laadittaessa.
- Paikallinen mockattu testi: oikea HTTP-reitti, sanahaku, soveltuvuussuodatus,
  mallikutsun muodostus, vastauksen jäsennys ja validointi. Ulkoisen API:n
  vastaus korvattiin testivastauksella. Aineistona oli `batch1` (30 runbookia).
- Käyttöliittymän JavaScript renderöi saman mockatun HTTP-vastauksen
  DOM-korvikkeessa. Tämä ei ole oikeassa selaimessa tehty testi.

## 1. VPN-001: live-tilan käyttäjälle näkyvä vastaus

Selainhavainnon mukaan OpenAI-live-tilassa näkyi kolme hyväksyttyä
ratkaisuvaihetta, tarkentava kysymys ja lähdeviitteet. API-kutsun onnistuminen
jää erikseen vahvistettavaksi; pelkkä selainkuva tai käyttöliittymän
valmistumisviesti ei ole riippumaton vahvistus mallipalvelun vastauksesta.

Paikallisen mockatun testin täsmällinen tukipyyntö oli:

> VPN ei yhdistä. Tavalliset verkkosivut avautuvat ilman VPN-yhteyttä.

Mockatussa testissä saatu ja käyttöliittymään renderöity vastaus:

> **Ratkaisuehdotus**
> Valittu ohje: VPN-yhteyden perustarkistus.
>
> 1. Sulje VPN-sovellus ja käynnistä se uudelleen.
> 2. Kirjaa tarkka virheilmoitus ja yhteysongelman alkamisaika.
> 3. Jos yhteys ei palaudu, toimita tiedot IT-tuelle. Älä muuta tietoturva-asetuksia.
>
> **Tarkentavat kysymykset**
> Mikä tarkka virheilmoitus näkyy VPN-yhteyden muodostuksessa?
>
> Jatkokäsittely tarvittaessa IT-tuessa.

Lähde: `VPN-001`, versio `0.2 / 15.10.2026`, alkuperäiset vaiheet 2, 3 ja 4.
Käyttöliittymän juokseva numerointi 1–3 ei muuta lähteen alkuperäisiä
vaihenumeroita. Internettarkistus (alkuperäinen vaihe 1) ohitettiin, koska
käyttäjä oli jo vahvistanut verkkosivujen avautuvan.

VPN-001 läpäisi soveltuvuussuodatuksen. Mallille annettiin tässä testissä vain
tämä hyväksytty lähde. Näkyvät vaiheet olivat sanatarkasti runbookista.
Hakuehdokkaiden toimintavaiheita ei renderöity. Onnistuminen tyhjensi
syötekentän ja säilytti käsitellyn vastauksen.

## 2. Epäselvä käynnistysongelma

Havainto: sovellus pyysi lisätietoja eikä tehnyt OpenAI-kutsua.

Toistamiseen tarkoitettu esimerkkipyyntö:

> Tietokone ei käynnisty.

Nykyisen ketjun tarkoitettu tulos on `insufficient`, ei arvattu ratkaisu.
Sovellus kysyy, mitä viimeisellä käynnistysyrityksellä tapahtui: oliko kone
mykkä, näkyikö virran merkkejä vai pysähtyikö käynnistys logoon tai
virheilmoitukseen. Ilman vahvistettua käynnistysvaihetta läheiset runbookit
eivät kelpaa ratkaisuksi eikä tavallisia toimintavaiheita näytetä.
Tämän kohdan esimerkki ei ole väite selainkokeen sanatarkasta syötteestä.

## 3. Turvonnut ja kuumeneva akku

Havainto: sovellus tuotti `safety_stop`-vastauksen DEVICE-004:n perusteella
ilman OpenAI-kutsua. Turvallisuuskeskeytys ohittaa tavallisen haun ja mallin.

Työversion turvallisuusyhteenveto:

> Turvallisuuskeskeytys. Lopeta laitteen käyttö ja lataaminen heti.
> Älä käynnistä tai lataa laitetta uudelleen äläkä käsittele tai testaa akkua.
> Älä avaa laitetta itse. Ota heti yhteys IT-tukeen.
> Kerro vain jo havaitut tiedot, jos se on turvallista. Älä tee uusia tarkistuksia.
> Ilmoitusta ei ole tehty puolestasi.

Ainoa lähteistetty toimintavaihe:

> Jos akku on turvonnut tai laite kuumenee poikkeavasti, lopeta käyttö ja ota yhteys IT-tukeen.

Lähde: `DEVICE-004`, alkuperäinen vaihe 2, versio `0.2 / 15.10.2026`.
Latausilmaisimen selvittämisvaihetta, laturin testausta tai tarkentavia
kysymyksiä ei näytetä vaaratilanteessa. IT-ilmoitusta ei tehdä automaattisesti.

## 4. Mockatun live-ketjun suojaukset

Yksi muistissa määritelty HTTP-ketjutesti sisälsi neljä tarkistusta:

| Tarkistus | Havaittu tulos |
|---|---|
| Sallittu VPN-001-valinta | HTTP 200, `suggestion`, alkuperäiset vaiheet 2–4 |
| Malli lisää oman `steps`-kentän | HTTP 502, `invalid_model_output`; ratkaisua ei näytetä |
| Malli valitsee suodatuksen ulkopuolisen NET-004-lähteen | HTTP 502, `invalid_model_output` |
| Malli kirjoittaa oman ohjeen `summary`-kenttään | Mallin teksti ei päädy näkyvään vastaukseen; sovellus kokoaa yhteenvedon itse |

Kaikki neljä tarkistusta läpäisivät. Lisäksi käyttöliittymän renderöintitarkistus
läpäisi: näkyvät toimintavaiheet vastasivat HTTP-vastauksen hyväksyttyjä
vaiheita, hakuehdokkaan ohitettu internettarkistus ei näkynyt ja syötekenttä tyhjeni.

Malli valitsee tilan ja lähteen; sovellus muodostaa toimintavaiheet.
Valinnan ylimääräiset kentät ja tuntemattomat lähteet hylätään paikallisesti.
Lopuksi tarkistetaan vaiheiden teksti, lähde, alkuperäinen vaihenumero ja versio.
API:n JSON-skeema vaatii vakioyhteenvedon. Paikallinen valintavalidointi ei
yksin vaadi tätä vakiotekstiä, mutta mallin yhteenveto korvataan eikä sitä näytetä.

Mockatun vastauksen tekninen `model_used=true` tarkoitti live-koodihaaran
suorittamista. Se ei tässä testissä tarkoita oikean kielimallin käyttöä.
Ulkoinen verkkoliikenne ja tiedostokirjoitukset estettiin testissä;
vain paikallinen HTTP-liikenne sallittiin. Testi suoritettiin Anacondan
Python 3.13.9:llä, ei projektin Python 3.14.2 -tulkilla.

DEVICE-004-korjauksen jälkeen aiemmin samalla päivällä ajettu koko
Python-testikokonaisuus läpäisi 326/326 testiä ja kohdennettu
turvallisuuskokonaisuus 12/12 testiä. Baseline-eheystarkistus vahvisti
96/96 tiedoston säilyneen. Näitä tarkistuksia ei ajettu uudelleen tämän
dokumentointityön yhteydessä.

## Tunnetut rajoitukset

- Todellisen OpenAI-kutsun onnistumisesta puuttuu erillinen palvelinpuolen
  vahvistus. Mockattu testi ei osoita API-avaimen, mallin tai laskutuksen toimivuutta.
- Nykyinen HTTP-palvelin ei oletuksena tuota kutsun onnistumisen todentavaa
  palvelinlokia. Mahdollinen havaittavuusmuutos vaatii erillisen hyväksynnän.
- Mockattu päästä päähän -testi käytti oikeaa sanahakua, ei vektorihakua.
- Internet-havainnon tunnistus riippuu sanamuodosta: ”verkkosivut avautuvat”
  tunnistuu, mutta ”verkkosivut toimivat” ei tässä kokeessa tunnistunut.
  Jälkimmäisessä tilanteessa sovellus voi toistaa runbookin internettarkistuksen.
- Lähdeviite ja sanatarkka ohje eivät yksin todista ohjeen soveltuvuutta.
  Malli voi edelleen tehdä väärän tilavalinnan annettujen lähteiden sisällä.
- Turvallisuustunnistus ja soveltuvuussäännöt ovat rajattuja. Kaikkien
  parafraasien, ristiriitojen ja vaaratilanteiden kattavuutta ei ole osoitettu.
- Näillä kehitystesteillä ei osoiteta riippumatonta yleistymiskykyä tai
  tuotantoturvallisuutta. Organisaatiokohtaiset menettelyt vaativat ihmistarkistuksen.

## Seuraavat testit ja hyväksyntärajat

1. Vahvista erikseen hyväksytyssä oikeassa live-kokeessa API-kutsun onnistuminen
   palvelinpuolen todisteella. Älä tallenna avainta tai tarpeettomia tukipyyntötietoja.
2. Toista VPN-001 oikeassa selaimessa paikallisella vektorihaulla; tarkista lähde,
   soveltuvuus, alkuperäiset vaihenumerot ja ettei ehdokkaiden vaiheita näy.
3. Tarkista selaimessa epäselvä käynnistys, vaarallinen akku ja niiden vastatapaukset.
   Varmista lisätietopyyntö, turvallisuusetusija ja mallikutsun ohitus.
4. Tarkista virhepolut: puuttuva tai virheellinen avain, aikakatkaisu, kesken jäänyt
   mallivastaus ja hylätty lähdevalinta. Virheessä syöte säilyy eikä vanha vastaus näy.
5. Tarkista turvallisuusohjeiden näkyvyys, lähdelinkit ja käytettävyys Edge-selaimessa.

Oikeat API-kokeet ja mahdolliset lokitusmuutokset hyväksytään erikseen.
Tässä dokumentointivaiheessa ei tehty API-kutsuja, uusia arviointiajoja,
koodimuutoksia tai runbook-muutoksia. Jäädytettyä
`evaluation/baselines/batch1-30-20261019-v1`-versiota ei muutettu.
Riippumatonta holdout B:tä ei avattu eikä batch2-erää aloitettu.
