# PicoAir-ePaper
[WIP] Pi Pico based device with ePaper display to show temperature, humidity, ppm and time.

I used GoogleAI to generate this README.md so i know what to buy, what features i would like and how to connect it together. I will translate it to english at a later date.

# 🍃 PicoAir-ePaper (Open-Source CO2 & Meteo Stanice)

Tento projekt představuje plně autonomní, nízkoenergetickou a naprosto tichou stanici pro měření kvality vzduchu (**CO₂ v ppm**), teploty a vlhkosti. 

Srdcem projektu je **Raspberry Pi Pico 2 W** (čip RP2350), data zobrazuje úsporný **2.13" e-Paper** displej a o přesný čas se stará hardwarový RTC modul **DS3231**. Celé zařízení je navrženo pro maximální výdrž při napájení z recyklované Li-Ion baterie z jednorázové e-cigarety.

## ✨ Hlavní vlastnosti
* **Absolutně tichý provoz:** Na rozdíl od běžných stanic (např. IKEA) projekt nevyužívá žádný hlučný větráček. Měření ppm probíhá na bázi přirozené difuze vzduchu.
* **Modulární hardware a autodetekce:** Firmware při startu automaticky skenuje I²C sběrnici. Pokud chybí CO₂ senzor nebo RTC hodiny, kód se přizpůsobí. Jako nouzový zdroj teploty umí vyčíst interní senzor v CPU Pica.
* **Modulární vzhled (JSON Layouts & Fonty):** Rozvržení prvků, podpora pro inverzní bloky (černá pozadí pod textem) a vlastní fonty jsou definovány v externím souboru `layouts.json`. Vzhled obrazovky lze měnit bez zásahu do Python kódu.
* **Jedno chytré tlačítko:** Ovládání celé stanice pomocí jediného fyzického tlačítka na základě délky stisku:
  * *Krátký stisk:* Přepnutí na další grafické téma (Layout).
  * *Podržení > 2 sekundy:* Přepnutí do nouzového **Debug menu** (zobrazí surová data, teplotu CPU a reálné napětí baterie i při poškozeném layoutu).
* **Wi-Fi a NTP synchronizace:** Bezdrátová konektivita slouží k automatickému seřízení přesného času z internetu. Wi-Fi se zapne pouze na pár sekund při startu a poté se hardwarově vypne pro maximální úsporu baterie.
* **Konfigurace přes `.env`:** Přihlašovací údaje k Wi-Fi, obnovovací frekvence a volba jednotek (°C / °F) jsou bezpečně odděleny v souboru `.env`, který se nenahrává na GitHub.

---

## 🛒 Kusovník (BOM) & Kde koupit

Níže naleznete seznam všech potřebných komponent. Pokud již vlastníte desku Pico a e-Paper displej, zbývající součástky vás vyjdou na **přibližně 900 Kč** (při nákupu z ČR s prémiovým senzorem).

| Komponenta | Popis a specifikace | Kde koupit (Příklad) |
| :--- | :--- | :--- |
| **Raspberry Pi Pico 2 W** | Výkonný mikrokontrolér s čipem RP2350 a Wi-Fi konektivitou. | [Pico 2 W na RPishop](https://rpishop.cz) |
| **Waveshare 2.13" e-Paper (rev2.1)** | Úsporný černobílý displej (250×122 px), spotřebovává energii jen při překreslení. | [Waveshare 2.13" na Botland](https://botland.store) |
| **LaskaKit SCD41** | Špičkový, tichý fotoakustický senzor CO₂ (ppm), teploty a vlhkosti vzduchu. | [Senzor SCD41 na LaskaKit](https://laskakit.cz) |
| **Modul RTC DS3231** | Extrémně přesné hardwarové hodiny reálného času komunikující přes I²C. | [Modul DS3231 na LaskaKit](https://laskakit.cz) |
| **Nabíjecí modul TP4056** | Nabíječka Li-Ion baterií přes USB-C s integrovanou ochranou proti podbití. | [TP4056 USB-C na LaskaKit](https://laskakit.cz) |
| **Baterie z e-cigarety** | Recyklovaný Li-Ion článek (např. typ 13300/13400) o kapacitě cca 350-500 mAh. | *Zdarma (Recyklace)* |
| **Malé neodymové magnety** | Vykuchané z podů e-cigaret (např. SYX podů). Slouží jako neviditelný zámek obou půlek krabičky. | *Zdarma (Recyklace)* |
| **Větší neodymové magnety** | Silnější magnety zapuštěné do zadní stěny pro uchycení stanice na lednici nebo futra. | Vlastní zásoby / e-shop |
| **Taktilní tlačítko (1ks)** | Obyčejné spínací tlačítko do DPS nebo krabičky pro ovládání stanice. | Jakýkoliv elektro obchod |

---

## 🗺️ Schéma zapojení (Pinout)

Všechny periferie se připojují přímo na piny Raspberry Pi Pico 2 W podle následujícího schématu. Displej využívá sběrnici SPI0, zatímco senzor CO₂ a hodiny RTC sdílejí společnou I²C1 sběrnici. Měření napětí baterie (VSYS) probíhá interně přes ADC29.

```text
       [ RASPBERRY PI PICO 2 W ]
             +-----------+
  (SPI) DC --| 1      40 |-- VBUS (Snímání 5V z USB pro indikaci nabíjení)
 (SPI) RST --| 2      39 |-- VSYS <--- Výstup OUT+ z nabíječky TP4056
       GND --| 3      38 |-- GND  <--- Společná zem (OUT- z TP4056)
(SPI) BUSY --| 4      37 |-- 3V3_EN
  (SPI) CS --| 5      36 |-- 3V3 OUT ---> [Společné VCC pro displej, RTC i SCD41]
 (SPI) CLK --| 6      35 |-- GP28
 (SPI) DIN --| 7      34 |-- GND

             |           |
 (Tlačítko) -| GP6    GP27 |- SCL    ---> [Společný SCL pro RTC i CO2 senzor]

             |        GP26 |- SDA    ---> [Společný SDA pro RTC i CO2 senzor]
             +-----------+
```

---

## 📂 Struktura souborů v projektu

Pro správný vývoj ve **VS Code (s rozšířením MicroPico)** a následný běh v zařízení dodržujte tuto strukturu:

```text
💾 PicoAir-ePaper (Root repositáře)
 ├── 📁 3D_Models/            # Parametrický model krabičky pro 3D tisk
 │    ├── 📄 krabicka.scad    # Zdrojový kód pro OpenSCAD
 │    ├── 📄 predni_dil.3mf   # Export pro moderní slicery
 │    └── 📄 zadni_dil.3mf    # Export pro moderní slicery
 ├── 📁 firmware/             # Kompletní kód pro nahrání do Pica
 │    ├── 📄 main.py          # Hlavní program / firmware stanice
 │    ├── 📄 settings.json    # Automaticky ukládaný stav (aktivní téma atd.)
 │    ├── 📄 layouts.json     # Definice souřadnic, inverzí a fontů pro témata
 │    └── 📁 drivers/
 │         ├── 📄 epd2in13_V2.py # Ovladač pro Waveshare e-Paper
 │         ├── 📄 ds3231.py      # Ovladač pro RTC modul
 │         └── 📄 scd4x.py       # Ovladač pro CO2 senzor
 ├── 📄 .gitignore            # Ignoruje lokální .env a settings.json
 ├── 📄 .env.example          # Vzorový konfigurační soubor pro uživatele
 └── 📄 README.md             # Tato dokumentace
```

---

## ⚙️ Konfigurace souboru `.env`

Před prvním nahráním kódu vytvořte v kořenovém adresáři soubor `.env`. Zde můžete nastavit jednotky teploty a obnovovací frekvenci.

```text
WIFI_SSID="Nazev_Vasi_Wifi"
WIFI_PASSWORD="Vase_Tajne_Heslo"

# Konfigurace stanice
TEMPERATURE_UNIT="C"         # Možnosti: "C" pro Celsius, "F" pro Fahrenheit
DISPLAY_REFRESH_RATE=60      # Frekvence měření a obnovy displeje v sekundách
```

---

## 🖨️ 3D Tisk & Parametrická krabička (OpenSCAD)

Pouzdro je kompletně navrženo v programu **OpenSCAD**. Zdrojový soubor `krabicka.scad` je plně parametrický, takže si průměry otvorů pro magnety můžete upravit na začátku souboru.

* **Konstrukce zámků:** V rozích krabičky jsou připraveny otvory s tiskovou tolerancí pro malé magnety z e-cigaret (SYX pody), které drží obě půlky u sebe bez šroubů.
* **Uchycení na lednici:** Na zadní straně jsou hlubší kapsy pro větší neodymové magnety, které jsou v přímém kontaktu s kovovým povrchem.
* **Termální management:** Krabička obsahuje vnitřní přepážku, která izoluje senzor SCD41 od tepla generovaného procesorem Pico 2 W. Větrací otvory jsou umístěny na spodní i horní hraně komory senzoru pro zajištění přirozeného komínového proudění vzduchu.

---

## 🛡️ Ochrana e-Paper displeje (Anti-Ghosting)
Kód v `main.py` obsahuje bezpečnostní mechanismus, který počítá částečná obnovení obrazovky (*partial refresh*). Aby nedocházelo k degradaci e-paperu a vzniku "duchů", firmware automaticky po každých 20 cyklech vyvolá jeden kompletní plný refresh (*full refresh*), který displej stoprocentně vyčistí.
