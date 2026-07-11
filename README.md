# PicoAir-ePaper
[WIP] Pi Pico based device with ePaper display to show temperature, humidity, ppm, time and pressure.

---

# 🍃 PicoAir ePaper Station

Moderní, energeticky úsporná meteostanice a monitor kvality vzduchu v interiéru postavená na mikrokontroléru **Raspberry Pi Pico W**. Stanice měří teplotu, vlhkost, koncentraci CO₂ a atmosférický tlak. Naměřená data zobrazuje na elegantním e-ink (e-paper) displeji a zároveň je v reálném čase odesílá přes Wi-Fi do databáze **InfluxDB** pro vizualizaci v **Grafaně**.

---

## ✨ Hlavní vlastnosti
- **Komplexní měření:** Sledování klíčových parametrů vzduchu (Teplota, Vlhkost, CO₂ v PPM, Tlak v hPa).
- **Sdílená I2C sběrnice:** Efektivní paralelní zapojení více senzorů na piny GP18/GP19.
- **e-Paper Displej:** Nízká spotřeba, perfektní čitelnost na slunci a nativní softwarová rotace obrazu na šířku.
- **Wi-Fi a NTP synchronizace:** Automatické nastavení přesného času z internetu s vestavěnou detekcí a přepínáním letního/zimního času (DST).
- **Direct InfluxDB logování:** Odesílání dat přímo z Pica do databáze pomocí HTTP Line Protocolu bez nutnosti mezistupňů.
- **Úsporný režim:** Kompletní odpojování a hluboký spánek Wi-Fi modulu i displeje mezi měřeními pro šetření baterie.

---

## 🛠️ Hardwarové komponenty
1. **[Raspberry Pi Pico W](https://rpishop.cz/554053/raspberry-pi-pico-2-w/)** (mikrokontrolér s Wi-Fi) [209 CZK]
2. **[Sensirion SCD41](https://www.laskakit.cz/laskakit-scd41-senzor-co2--teploty-a-vlhkosti-vzduchu/)** (fotoakustický senzor CO₂, teploty a vlhkosti) [888 CZK]
3. **[Bosch BMP180](https://www.gme.cz/v/1513747/modul-meteocidlo-s-bmp180)** (senzor barometrického tlaku a teploty) [39 CZK]
4. **[Waveshare e-Paper Displej](https://rpishop.cz/pico-karty/3653-waveshare-213-e-paper-displej-pro-raspberry-pi-pico.html)** (2.13" / 2.9" nebo kompatibilní SPI e-ink) [419 CZK]
5. **[TP4056 Napájecí Modul](https://www.laskakit.cz/nabijecka-li-ion-clanku-tp4056-usb-c/)** Li-Ion / Li-Po baterie + mechanický vypínač (volitelně)

---

## 💾 Software & Firmware
Pro provoz této stanice je vyžadován MicroPython s podporou síťových funkcí. 
- **Doporučený firmware:** [MicroPython pro Raspberry Pi Pico 2 W / Pico W](https://micropython.org/download/RPI_PICO2_W/) (.uf2 soubor)
- **Vývojové prostředí:** VS Codium / VS Code s rozšířením *MicroPico*, případně Thonny IDE.

---

## 🔌 Schéma zapojení (Wiring)

Všechny senzory sdílí jednu hardwarovou sběrnici **I2C1**.

### I2C Senzory (SCD41 & BMP180)
Senzory zapojte paralelně k sobě na následující piny:
| Senzor Pin | Raspberry Pi Pico W Pin | Popis |
| :--- | :--- | :--- |
| **3.3V / VCC** | 3.3V (Pin 36) | Napájení (BMP180 připojte na 3.3V pin, nikoliv VCC!) |
| **GND** | GND | Společná zem |
| **SDA** | GP18 (Pin 24) | Datová linka I2C1 |
| **SCL** | GP19 (Pin 25) | Hodinová linka I2C1 |

### e-Paper Displej (SPI)
| Displej Pin | Raspberry Pi Pico W Pin | Popis |
| :--- | :--- | :--- |
| **BUSY** | GP4 (Pin 6) | Input s PULL_DOWN |
| **RST** | GP1 (Pin 2) | Reset displeje |
| **DC** | GP0 (Pin 1) | Data/Command selection |
| **CS** | GP5 (Pin 7) | Chip Select |
| **SCLK** | GP2 (Pin 4) | SPI Clock |
| **DIN / MOSI** | GP3 (Pin 5) | SPI Master Out |
| **VCC** | 3.3V | Napájení |
| **GND** | GND | Zem |

---

## ⚙️ Softwarová konfigurace (`.env`)

Pro správný běh stanice vytvořte v kořenovém adresáři soubor `.env` (Pico si konfiguraci načte automaticky):

```env
WIFI_SSID="Nazev_Tvoji_Wifi"
WIFI_PASSWORD="Heslo_K_Wifi"
MQTT_ENABLED=1
MQTT_BROKER="IP_Adresa_Tveho_Serveru"
MQTT_LOCATION="Pokoj"
REFRESH_RATE=300
DARK_MODE=0
UNITS="C"
NTP_ADDRESS="time.windows.com"
UTC_TIMEZONE=1
TEXT_TEMPERATURE="Teplota"
TEXT_HUMIDITY="Vlhkost"
TEXT_PPM="PPM"
TEXT_PRESSURE="Tlak"
```

---

## 🖨️ 3D Tisk (OpenSCAD)

Pouzdro je kompletně navrženo v programu **OpenSCAD**.

* **Konstrukce zámků:** V rozích krabičky jsou připraveny otvory s tiskovou tolerancí pro malé magnety z e-cigaret (SYX pody), které drží obě půlky u sebe bez šroubů.
* **Termální management:** Krabička obsahuje vnitřní přepážku, která izoluje senzor SCD41 od tepla generovaného procesorem Pico 2 W.
