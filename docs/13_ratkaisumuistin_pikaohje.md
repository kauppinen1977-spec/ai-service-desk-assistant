# Ratkaisumuistin pikaohje

Avaa `http://127.0.0.1:8502/memory`, kun tämän worktreen palvelin on käynnissä.
Aloitusnäkymä on **Haku**. Muut välilehdet ovat **Kirjoita ratkaisu** ja
**Hallinta ja historia**. Välilehden vaihtaminen säilyttää lomaketekstin.

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

## 2. Kirjoita uusi ratkaisu tai pyydä API-ehdotus

Haun jälkeen valitse **Kirjoita uusi ratkaisu** tai **Siirry API-ehdotukseen**.
Ongelmateksti ja erilliset rajaukset kopioidaan lomakkeeseen. Täytä myös
vapaa ympäristökuvaus itse. Siirtyminen ei lähetä tietoja tai tallenna mitään.
Jos lomakkeella on tallentamatonta tekstiä, sen korvaaminen kysytään erikseen.

Voit kirjoittaa ratkaisun kokonaan itse. API-ehdotusta varten avaa
**Halutessasi: pyydä API-ehdotus**, täytä ongelman kuvaus ja vapaa ympäristökuvaus,
anna erillinen lähetyslupa ja paina **Pyydä API-ehdotus**. Palvelimen API-asetusten
on oltava valmiina. Kutsu voi aiheuttaa kulun; käytä vain kuvitteellisia tietoja.

Vain ongelman kuvaus ja vapaa ympäristökuvaus lähetetään. Ehdotus on
**kokeilematon**, eikä se ole verkkohaku tai vahvistettu ratkaisu.
Se ei tallennu automaattisesti. Tarkista teksti ja sen mukana tulevat rajoitteet.
Jos ehdotus korvaisi nykyisen otsikon ja ratkaisun, korvaaminen kysytään.

## 3. Tallenna ja tarkista luonnos

Täytä otsikko, ongelma, vapaa ympäristökuvaus sekä ratkaisuvaiheet ja rajat.
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
