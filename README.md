# PicoAir-ePaper
[WIP] Pi Pico based device with ePaper display to show temperature, humidity, ppm and time.

I used GoogleAI to generate this README.md so i know what to buy, what features i would like and how to connect it together. I will translate it to english at a later date.

# 🍃 PicoAir-ePaper (Open-Source CO2 & Meteo Stanice)

Tento projekt představuje plně autonomní, nízkoenergetickou a naprosto tichou stanici pro měření kvality vzduchu (**CO₂ v ppm**), teploty a vlhkosti. 

Srdcem projektu je **Raspberry Pi Pico 2 W** (čip RP2350), data zobrazuje úsporný **2.13" e-Paper** displej a o přesný čas se stará hardwarový RTC modul **DS3231**. Celé zařízení je navrženo pro maximální výdrž při napájení z recyklované Li-Ion baterie z jednorázové e-cigarety.

## ✨ Hlavní vlastnosti
* **Absolutně tichý provoz:** Na rozdíl od běžných stanic (např. IKEA) projekt nevyužívá žádný hlučný větráček. Měření ppm probíhá na bázi přirozené difuze vzduchu.
* **Modulární vzhled (JSON Layouts):** Rozvržení prvků na displeji je definováno v externím souboru `layouts.json`. Vzhled obrazovky lze měnit bez zásahu do zdrojového kódu.
* **Multifunkční tlačítko:** Ovládání celé stanice pomocí jediného tlačítka na základě délky stisku (Krátký stisk = Přepnutí °C/°F | 2s držení = Změna grafického tématu | 10s držení = Vypnutí/Zapnutí Wi-Fi).
* **Wi-Fi a NTP synchronizace:** Bezdrátová konektivita slouží k automatickému seřízení přesného času z internetu. Wi-Fi se zapne pouze na pár sekund při startu a poté se hardwarově vypne pro maximální úsporu baterie.
* **Bezpečné uložení hesel:** Přihlašovací údaje k Wi-Fi jsou bezpečně odděleny v souboru `.env`, který se nenahrává na GitHub.

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
| **Taktilní tlačítko (1ks)** | Obyčejné spínací tlačítko do DPS nebo krabičky pro ovládání stanice. | Jakýkoliv elektro obchod / GME |

---

## 🗺️ Schéma zapojení (Pinout)

Všechny periferie se připojují přímo na piny Raspberry Pi Pico 2 W podle následujícího schématu. Displej využívá sběrnici SPI0, zatímco senzor CO₂ a hodiny RTC sdílejí společnou I²C1 sběrnici.

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

## 📂 Struktura souborů v zařízení

Pro správný běh projektu je nutné do kořenového adresáře Raspberry Pi Pico nahrát následující strukturu souborů:

```text
💾 Raspberry Pi Pico 2 W
 ├── 📄 .env                  # Vaše privátní nastavení (Wi-Fi SSID, hesla, refresh rate)
 ├── 📄 settings.json         # Automaticky ukládaný stav (jednotky, aktivní téma, stav Wi-Fi)
 ├── 📄 layouts.json          # Definice souřadnic a velikostí textu pro jednotlivá témata
 ├── 📄 main.py               # Hlavní program / firmware stanice
 └── 📁 drivers/
      ├── 📄 epd2in13_V2.py   # Ovladač pro Waveshare e-Paper (rev 2.1)
      ├── 📄 ds3231.py        # Ovladač pro RTC modul hodin
      └── 📄 scd4x.py         # Ovladač pro senzor CO2 Sensirion
```

---

## ⚙️ Konfigurace souboru `.env`

Před nahráním kódu do zařízení vytvořte v kořenovém adresáři soubor `.env` a vyplňte své údaje. Hodnota `DISPLAY_REFRESH_RATE` určuje frekvenci měření a překreslování v sekundách (doporučeno 60 nebo 300).

```text
WIFI_SSID="Nazev_Vasi_Wifi"
WIFI_PASSWORD="Vase_Tajne_Heslo"
DISPLAY_REFRESH_RATE=60
```

---

## 🚀 Jak začít (Rychlý start)

1. Stáhněte si nejnovější stabilní firmware **MicroPython (.uf2)** pro Raspberry Pi Pico 2 W z oficiálních stránek [micropython.org](https://micropython.org).
2. Přepněte Pico do BOOTSEL režimu (držte tlačítko BOOTSEL při připojování USB kabelu k PC) a nahrajte `.uf2` soubor.
3. Otevřete vývojové prostředí **Thonny IDE**, přepněte interpreter na *MicroPython (Raspberry Pi Pico)*.
4. Zkopírujte složku `drivers/` a soubory `main.py`, `layouts.json` a váš upravený `.env` do paměti Pica.
5. Odpojte od PC, připojte baterii a stanice začne okamžitě fungovat.

---

## 🛡️ Ochrana e-Paper displeje (Anti-Ghosting)
Kód v `main.py` obsahuje bezpečnostní mechanismus, který počítá částečná obnovení obrazovky (*partial refresh*). Aby nedocházelo k degradaci e-paperu a vzniku "duchů", firmware automaticky po každých 20 cyklech vyvolá jeden kompletní plný refresh (*full refresh*), který displej stoprocentně vyčistí.

