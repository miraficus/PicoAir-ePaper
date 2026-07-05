import time
from machine import Pin, SPI, ADC
import framebuf
import network
import socket
import struct

print("[START] Spouštím kompletně vyčištěný program v nekonečné smyčce...")

class MojeMQTT:
    def __init__(self, client_id, server, port=1883):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.sock = None

    def connect(self):
        # 1. Otevřeme čistý TCP socket na Dell
        self.sock = socket.socket()
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock.connect(addr)
        
        # 2. NATVRDO SESTAVENÝ VALIDNÍ MQTT v3.1.1 CONNECT PAKET
        # Žádné dynamické struct.pack, čisté bajty, které Mosquitto vyžaduje.
        id_bytes = self.client_id.encode('utf-8')
        id_len = len(id_bytes)
        
        # Variabilní hlavička pro MQTT 3.1.1 (Protokol: MQTT, Verze: 4, Clean Session, Keepalive 60s)
        var_header = b"\x00\x04MQTT\x04\x02\x00\x3c"
        
        # Payload (Délka ID + samotné ID)
        payload = bytes([id_len >> 8, id_len & 0xFF]) + id_bytes
        
        # Celková délka balíčku
        remaining_len = len(var_header) + len(payload)
        
        # Fixní hlavička (0x10 = CONNECT)
        packet = b"\x10" + bytes([remaining_len]) + var_header + payload
        
        # Odešleme balíček do sítě
        self.sock.write(packet)
        
        # Přečteme odpověď od brokera (CONNACK má vždy 4 bajty)
        res = self.sock.read(4)
        if not res or res[0] != 0x20 or res[3] != 0:
            raise Exception("Broker odmítl spojení (Kód: {})".format(res[3] if res else "Žádná data"))

    def publish(self, topic, msg):
        topic_bytes = topic.encode('utf-8')
        msg_bytes = msg.encode('utf-8')
        
        # Payload pro PUBLISH (Délka tématu + téma + zpráva)
        t_len = len(topic_bytes)
        payload = bytes([t_len >> 8, t_len & 0xFF]) + topic_bytes + msg_bytes
        
        # Fixní hlavička (0x30 = PUBLISH)
        packet = b"\x30" + bytes([len(payload)]) + payload
        self.sock.write(packet)

    def disconnect(self):
        try:
            self.sock.write(b"\xe0\x00") # 0xE0 = DISCONNECT
        except:
            pass
        self.sock.close()

    def publish(self, topic, msg, retain=False, qos=0):
        if isinstance(topic, str):
            topic = topic.encode()
        if isinstance(msg, str):
            msg = msg.encode()
        pkt = bytearray(b"\x30\0")
        if retain:
            pkt[0] |= 1
        if qos:
            pkt[0] |= qos << 1
        pkt.extend(struct.pack("!H", len(topic)))
        pkt.extend(topic)
        pkt.extend(msg)
        pkt[1] = len(pkt) - 2
        self.sock.write(pkt)

    def disconnect(self):
        self.sock.write(b"\xe0\0")
        self.sock.close()


def load_env_config():
    config = {
        "DARK_MODE": "0",
        "UNITS": "C",
        "REFRESH_RATE": "60",
        "TEXT_TEMPERATURE": "Teplota:",
        "TEXT_HUMIDITY": "Vlhkost:",
        "TEXT_PPM": "PPM:",
        "TEXT_PRESSURE": "Tlak:",
        "WIFI_SSID": "",
        "WIFI_PASSWORD": "",
        "NTP_ADDRESS": "pool.ntp.org",
        "UTC_TIMEZONE": "1",
        "MQTT_ENABLED": "0",
        "MQTT_BROKER": "",
        "MQTT_PORT": "1883",
        "MQTT_LOCATION": "pokoj"
    }
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return config

# Načteme konfiguraci do globálních proměnných
env = load_env_config()

DARK_MODE = int(env["DARK_MODE"])
if DARK_MODE == 1:
    COLOR_BG = 0  
    COLOR_FG = 1  
else:
    COLOR_BG = 1  
    COLOR_FG = 0  

USER_UNITS = env["UNITS"].upper()

# Načtení lokalizovaných textů
TXT_TEMP = env["TEXT_TEMPERATURE"] + ":" if not env["TEXT_TEMPERATURE"].endswith(":") else env["TEXT_TEMPERATURE"]
TXT_HUMI = env["TEXT_HUMIDITY"] + ":" if not env["TEXT_HUMIDITY"].endswith(":") else env["TEXT_HUMIDITY"]
TXT_PPM  = env["TEXT_PPM"] + ":" if not env["TEXT_PPM"].endswith(":") else env["TEXT_PPM"]
TXT_PRESSURE = env["TEXT_PRESSURE"] + ":" if not env["TEXT_PRESSURE"].endswith(":") else env["TEXT_PRESSURE"]

try:
    REFRESH_RATE = int(env["REFRESH_RATE"])
except (KeyError, ValueError):
    REFRESH_RATE = 60

if REFRESH_RATE < 20:
    REFRESH_RATE = 20

# Načtení MQTT konfigurace
MQTT_ENABLED = int(env.get("MQTT_ENABLED", "0"))
MQTT_BROKER = env.get("MQTT_BROKER", "")
MQTT_PORT = int(env.get("MQTT_PORT", "1883"))
MQTT_LOCATION = env.get("MQTT_LOCATION", "unknown")

# Proměnné pro uchování synchronizovaného času
base_timestamp = 0
base_ticks = 0
time_synchronized = False

def connect_wifi_and_sync_time():
    global base_timestamp, base_ticks, time_synchronized
    ssid = env["WIFI_SSID"]
    password = env["WIFI_PASSWORD"]
    ntp_server = env["NTP_ADDRESS"]
    
    if not ssid:
        print("[WIFI] V .env chybí název Wi-Fi, spouštím bez internetu.")
        return

    # 1. GENERÁLNÍ PAUZA PRO STABILIZACI PO ZAPNUTÍ (Klíčové pro Pico 2 W)
    print("[WIFI] Čekám na stabilizaci napájení...")
    time.sleep(2)

    wlan = network.WLAN(network.STA_IF)
    
    # 2. TVRDÝ RESET S DELŠÍMI PAUZAMI
    print("[WIFI] Resetuji Wi-Fi modul...")
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)  # Necháme firmware čipu plně nastartovat
    
    print("[WIFI] Připojuji se k: {}".format(ssid))
    wlan.connect(ssid, password)
    
    max_wait = 20
    while max_wait > 0 and not wlan.isconnected():
        max_wait -= 1
        time.sleep(1)
        print(".")
        
    if wlan.isconnected():
        print("\n[WIFI] Úspěšně připojeno! IP:", wlan.ifconfig()[0])
        print("[NTP] Stahuji čas z: {}".format(ntp_server))
        
        try:
            NTP_QUERY = bytearray(48)
            NTP_QUERY[0] = 0x1B
            addr = socket.getaddrinfo(ntp_server, 123)[0][-1]
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(5)
            s.sendto(NTP_QUERY, addr)
            msg, address = s.recvfrom(48)
            s.close()
            
            val = struct.unpack("!I", msg[40:44])[0]
            NTP_DELTA = 2208988800
            timestamp_utc = val - NTP_DELTA
            
            try:
                base_tz = int(env.get("UTC_TIMEZONE", 1))
            except ValueError:
                base_tz = 1

            tm = time.localtime(timestamp_utc)
            year, month, day, hour = tm[0], tm[1], tm[2], tm[3]
            
            mar_sunday = 31 - (time.localtime(time.mktime((year, 3, 31, 1, 0, 0, 0, 0)))[6])
            oct_sunday = 31 - (time.localtime(time.mktime((year, 10, 31, 1, 0, 0, 0, 0)))[6])
            
            is_dst = False
            if 3 < month < 10:
                is_dst = True
            elif month == 3:
                if day > mar_sunday or (day == mar_sunday and hour >= 1):
                    is_dst = True
            elif month == 10:
                if day < oct_sunday or (day == oct_sunday and hour < 1):
                    is_dst = True

            final_tz = base_tz + (1 if is_dst else 0)
            TIMEZONE_OFFSET = final_tz * 3600
            
            base_timestamp = timestamp_utc + TIMEZONE_OFFSET
            base_ticks = time.ticks_ms()
            time_synchronized = True
            
            print("[NTP] Synchronizováno. Datum: {}.{}.{}, Automatický DST: {}".format(day, month, year, "ANO (Letní)" if is_dst else "NE (Zimní)"))
        except Exception as e:
            print("[NTP] Chyba synchronizace času:", e)      

    else:
        print("\n[WIFI] Nepodařilo se připojit k Wi-Fi.")

    return wlan

def get_current_time_str():
    if not time_synchronized:
        return "--:--"
    elapsed_ms = time.ticks_diff(time.ticks_ms(), base_ticks)
    current_timestamp = base_timestamp + (elapsed_ms // 1000)
    local_time = time.localtime(current_timestamp)
    hours = "{:02d}".format(local_time[3])
    minutes = "{:02d}".format(local_time[4])
    return "{}:{}".format(hours, minutes)


class EPD_Landscape_Fix:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.buffer_size = 4000 

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        time.sleep_ms(delaytime)

    def send_command(self, command):
        self.digital_write(self.dc, 0)
        self.digital_write(self.cs, 0)
        self.spi.write(bytearray([command]))
        self.digital_write(self.cs, 1)

    def send_data(self, data):
        self.digital_write(self.dc, 1)
        self.digital_write(self.cs, 0)
        self.spi.write(bytearray([data]))
        self.digital_write(self.cs, 1)

    def wait_until_idle(self):
        while(self.digital_read(self.busy) == 1):
            self.delay_ms(50)

    def init(self):
        self.reset()
        self.wait_until_idle()
        self.send_command(0x12) 
        self.wait_until_idle()
        self.send_command(0x01) 
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_command(0x11) 
        self.send_data(0x03) 
        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x0F) 
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xF9) 
        self.send_data(0x00)
        self.send_command(0x3C) 
        self.send_data(0x05)
        self.send_command(0x18) 
        self.send_data(0x80)
        self.set_cursor(0, 0)
        self.wait_until_idle()

    def reset(self):
        self.digital_write(self.rst, 1)
        self.delay_ms(200)
        self.digital_write(self.rst, 0)
        self.delay_ms(10)
        self.digital_write(self.rst, 1)
        self.delay_ms(200)

    def set_cursor(self, x, y):
        self.send_command(0x4E) 
        self.send_data(x & 0xFF)
        self.send_command(0x4F) 
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    def display_frame(self):
        self.send_command(0x22)
        self.send_data(0xF7) 
        self.send_command(0x20)
        self.wait_until_idle()

    def set_frame_memory(self, image):
        self.set_cursor(0, 0)
        self.send_command(0x24) 
        self.digital_write(self.dc, 1)
        self.digital_write(self.cs, 0)
        self.spi.write(image)
        self.digital_write(self.cs, 1)

    def clear_frame_memory(self, color):
        self.set_cursor(0, 0)
        self.send_command(0x24)
        self.digital_write(self.dc, 1)
        self.digital_write(self.cs, 0)
        self.spi.write(bytes([color] * self.buffer_size))
        self.digital_write(self.cs, 1)

    def sleep(self):
        self.send_command(0x10)
        self.send_data(0x01)

# === KONFIGURACE HARDWARU ===
sck_pin = Pin(2)
mosi_pin = Pin(3)
cs_pin = Pin(5, Pin.OUT)
dc_pin = Pin(0, Pin.OUT)
rst_pin = Pin(1, Pin.OUT)
busy_pin = Pin(4, Pin.IN, Pin.PULL_DOWN) 

print("[1] Inicializuji SPI...")
spi = SPI(0, baudrate=2000000, polarity=0, phase=0, sck=sck_pin, mosi=mosi_pin)

print("[2] Vytvářím objekt displeje...")
epd = EPD_Landscape_Fix(spi, cs_pin, dc_pin, rst_pin, busy_pin)

from machine import ADC
adc_temp = ADC(4)

def get_cpu_temp():
    raw = adc_temp.read_u16()
    voltage = raw * 3.3 / 65535
    temperature_c = 27 - (voltage - 0.706) / 0.001721
    if USER_UNITS == "F":
        temperature_f = (temperature_c * 9 / 5) + 32
        return round(temperature_f, 1)
    else:
        return round(temperature_c, 1)

WIDTH_LANDSCAPE = 256
HEIGHT_LANDSCAPE = 122

draw_buf = bytearray(WIDTH_LANDSCAPE * HEIGHT_LANDSCAPE // 8)
fb_landscape = framebuf.FrameBuffer(draw_buf, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE, framebuf.MONO_HLSB)

DISP_WIDTH = 128
DISP_HEIGHT = 250
display_buf = bytearray(DISP_WIDTH * DISP_HEIGHT // 8)
fb_display = framebuf.FrameBuffer(display_buf, DISP_WIDTH, DISP_HEIGHT, framebuf.MONO_HLSB)

def text_large(text, start_x, start_y, color=0):
    current_x = start_x
    char_buf = bytearray(8 * 8 // 8)
    char_fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.MONO_HLSB)
    for char in text:
        if color == 1:
            char_fb.fill(0)
            char_fb.text(char, 0, 0, 1)
        else:
            char_fb.fill(1)
            char_fb.text(char, 0, 0, 0)
        for x in range(8):
            for y in range(8):
                if char_fb.pixel(x, y) == color:
                    target_x = current_x + (x * 2)
                    target_y = start_y + (y * 2)
                    fb_landscape.pixel(target_x, target_y, color)
                    fb_landscape.pixel(target_x + 1, target_y, color)
                    fb_landscape.pixel(target_x, target_y + 1, color)
                    fb_landscape.pixel(target_x + 1, target_y + 1, color)
        if char == " ":
            current_x += 8
        else:
            current_x += 14

# === HLAVNÍ SMYČKA PROGRAMU ===
while True:
    print("\n--- Spouštím novou aktualizaci stanice ---")
    
    # 1. NEJDŘÍVE VYKRESLÍME DISPLEJ (Zatím bez Wi-Fi)
    print("[3] Volám epd.init()...")
    epd.init()

    print("[4] Mažu displej...")
    epd.clear_frame_memory(0xFF)
    epd.display_frame()

    fb_landscape.fill(COLOR_BG)
    fb_display.fill(1)

    fb_landscape.rect(0, 0, 250, 121, COLOR_FG)
    fb_landscape.rect(1, 1, 248, 119, COLOR_FG)
    fb_landscape.rect(2, 2, 246, 117, COLOR_FG)

    # Čas bude z minulé smyčky, nebo se ukáže --:-- pokud je to úplně první start
    current_time_str = get_current_time_str()
    fb_landscape.fill_rect(3, 3, 244, 16, COLOR_FG)
    fb_landscape.text("PicoAir Stanice", 15, 6, COLOR_BG)
    fb_landscape.text(current_time_str, 200, 6, COLOR_BG)

    cpu_temperature = get_cpu_temp()
    temp_value_str = "{}".format(cpu_temperature)
    temp_unit_str = " {}".format(USER_UNITS)

    text_large(TXT_TEMP, 15, 27, COLOR_FG)
    text_large(temp_value_str, 135, 27, COLOR_FG)

    degree_x = 135 + (len(temp_value_str) * 14)
    fb_landscape.rect(degree_x + 2, 27, 4, 4, COLOR_FG)
    text_large(temp_unit_str, degree_x + 4, 27, COLOR_FG)

    text_large(TXT_HUMI, 15, 50, COLOR_FG)
    text_large("-- %", 135, 50, COLOR_FG) 

    text_large(TXT_PPM, 15, 73, COLOR_FG)
    text_large("----", 135, 73, COLOR_FG)

    text_large(TXT_PRESSURE, 15, 94, COLOR_FG)
    text_large("---- hPa", 135, 94, COLOR_FG)    

    print("Přetáčím pixely do nativní orientace...")
    for x in range(WIDTH_LANDSCAPE):
        for y in range(HEIGHT_LANDSCAPE):
            pixel = fb_landscape.pixel(x, y)
            new_x = (DISP_WIDTH - 1 - y) - 7
            new_y = x
            if 0 <= new_x < DISP_WIDTH:
                fb_display.pixel(new_x, new_y, pixel)

    print("[5] Posílám otočená data na displej...")
    epd.set_frame_memory(display_buf)
    epd.display_frame()

    print("[6] Ukládám displej ke spánku.")
    epd.sleep()
    
    # 2. TEPRVE TEĎ, KDYŽ DISPLEJ SPÍ, ZAPNEME SÍŤ
    # Spojí se s Wi-Fi a synchronizuje NTP čas
    connect_wifi_and_sync_time()
    
    # 3. OKAMŽITĚ ODEŠLEME DATA PŘES MQTT (Wi-Fi je čerstvě připojená)
    if MQTT_ENABLED == 1 and MQTT_BROKER:
        wlan = network.WLAN(network.STA_IF)
        if wlan and wlan.isconnected():
            print("[INFLUX] Odesílám data přímo do databáze...")
            try:
                # InfluxDB v1 naslouchá na portu 8086
                url_ip = MQTT_BROKER
                port = 8086
                
                # Sestavení zprávy v protokolu Influx Line Protocol
                # Struktura: mereni,tag=hodnota pole=hodnota
                payload = "pocasi,lokace={} teplota={:.1f}\n".format(MQTT_LOCATION, cpu_temperature)
                
                # Vytvoříme klasické HTTP POST spojení
                s = socket.socket()
                addr = socket.getaddrinfo(url_ip, port)[0][-1]
                s.connect(addr)
                
                # HTTP Hlavička pro InfluxDB zápis do databáze 'meteostanice'
                http_req = (
                    "POST /write?db=meteostanice HTTP/1.1\r\n"
                    "Host: {}:{}\r\n"
                    "Content-Length: {}\r\n"
                    "Content-Type: text/plain\r\n"
                    "\r\n"
                    "{}"
                ).format(url_ip, port, len(payload), payload)
                
                s.write(http_req.encode('utf-8'))
                
                # Přečteme odpověď (Influx při úspěchu vrací HTTP/1.1 204 No Content)
                response = s.read(64).decode('utf-8')
                s.close()
                
                if "204" in response:
                    print("[INFLUX] Data úspěšně zapsána do InfluxDB!")
                else:
                    print("[INFLUX] Server odpověděl jinak:", response.split("\r\n")[0])
                    
            except Exception as e:
                print("[INFLUX] Selhalo odeslání do InfluxDB:", e)
        else:
            print("[INFLUX] Wi-Fi není připojena, data neodeslána.")
            
    # 4. KOMPLETNÍ VYPNUTÍ WI-FI PŘED SPÁNKEM
    if wlan:
        wlan.active(False)
    print("[SYSTEM] Wi-Fi modul kompletně uspán.")
    
    print("[ČEKÁNÍ] Hotovo. Za {} sekund proběhne další měření...".format(REFRESH_RATE))
    time.sleep(REFRESH_RATE)