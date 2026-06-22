import time
from machine import Pin, SPI
import framebuf

print("[START] Spouštím kompletně vyčištěný program v nekonečné smyčce...")

def load_env_config():
    # Výchozí hodnoty v češtině pro případ, že .env soubor selže
    config = {
        "DARK_MODE": "0",
        "UNITS": "C",
        "TEXT_TEMPERATURE": "Teplota:",
        "TEXT_HUMIDITY": "Vlhkost:",
        "TEXT_PPM": "PPM:",
        "TEXT_TIME": "Cas:"
    }
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
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

# Načtení lokalizovaných textů (přidáme dvojtečku na konec, pokud ji tam nemáš)
TXT_TEMP = env["TEXT_TEMPERATURE"] + ":" if not env["TEXT_TEMPERATURE"].endswith(":") else env["TEXT_TEMPERATURE"]
TXT_HUMI = env["TEXT_HUMIDITY"] + ":" if not env["TEXT_HUMIDITY"].endswith(":") else env["TEXT_HUMIDITY"]
TXT_PPM  = env["TEXT_PPM"] + ":" if not env["TEXT_PPM"].endswith(":") else env["TEXT_PPM"]
TXT_TIME = env["TEXT_TIME"] + ":" if not env["TEXT_TIME"].endswith(":") else env["TEXT_TIME"]

class EPD_Landscape_Fix:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        # Hardwarové fixní rozměry čipu SSD1680
        self.buffer_size = 4000 # 128 * 250 // 8

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
        
        self.send_command(0x12) # SWRESET
        self.wait_until_idle()
        
        self.send_command(0x01) # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)
        
        self.send_command(0x11) # Data entry mode
        self.send_data(0x03) # X inc, Y inc
        
        self.send_command(0x44) # Set Ram X-address Start/End
        self.send_data(0x00)
        self.send_data(0x0F) # 128 pixelů
        
        self.send_command(0x45) # Set Ram Y-address Start/End
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xF9) # 250 pixelů
        self.send_data(0x00)
        
        self.send_command(0x3C) # Border Waveform
        self.send_data(0x05)
        
        self.send_command(0x18) # Temperature sensor
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
        self.send_command(0x4E) # RAM x address counter
        self.send_data(x & 0xFF)
        self.send_command(0x4F) # RAM y address counter
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    def display_frame(self):
        self.send_command(0x22)
        self.send_data(0xF7) 
        self.send_command(0x20)
        self.wait_until_idle()

    def set_frame_memory(self, image):
        self.set_cursor(0, 0)
        self.send_command(0x24) # Zápis do RAM
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
# Inicializace interního senzoru teploty
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

# === SOFTWAROVÉ KRESLENÍ NA ŠÍŘKU ===
WIDTH_LANDSCAPE = 256
HEIGHT_LANDSCAPE = 122

draw_buf = bytearray(WIDTH_LANDSCAPE * HEIGHT_LANDSCAPE // 8)
fb_landscape = framebuf.FrameBuffer(draw_buf, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE, framebuf.MONO_HLSB)

DISP_WIDTH = 128
DISP_HEIGHT = 250
display_buf = bytearray(DISP_WIDTH * DISP_HEIGHT // 8)
fb_display = framebuf.FrameBuffer(display_buf, DISP_WIDTH, DISP_HEIGHT, framebuf.MONO_HLSB)

# --- FUNKCE PRO ZVĚTŠENÝ TEXT ---
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
            current_x += 16  # Opraveno na tvých požadovaných 11 pro menší mezery!

# === HLAVNÍ SMYČKA PROGRAMU ===
while True:
    print("\n--- Spouštím novou aktualizaci stanice ---")
    
    print("[3] Volám epd.init()...")
    epd.init()

    print("[4] Mažu displej...")
    epd.clear_frame_memory(0xFF)
    epd.display_frame()

    # Vyčistíme lokální buffery na výchozí barvy
    fb_landscape.fill(COLOR_BG)
    fb_display.fill(1)

    # 1. Tlustý rámeček
    fb_landscape.rect(0, 0, 250, 121, COLOR_FG)
    fb_landscape.rect(1, 1, 248, 119, COLOR_FG)
    fb_landscape.rect(2, 2, 246, 117, COLOR_FG)

    # --- INVERZNÍ HORNÍ LIŠTA ---
    fb_landscape.fill_rect(3, 3, 244, 16, COLOR_FG)
    fb_landscape.text("PicoAir Stanice", 15, 6, COLOR_BG)
    fb_landscape.text("V 1.0", 200, 6, COLOR_BG)

    # 2. Vykreslení hodnot velkým písmem z .env
    cpu_temperature = get_cpu_temp()
    temp_value_str = "{}".format(cpu_temperature)
    temp_unit_str = " {}".format(USER_UNITS)

    # TEPLOTA
    text_large(TXT_TEMP, 15, 27, COLOR_FG)
    text_large(temp_value_str, 145, 27, COLOR_FG)

    # Přepočet pozice kroužku (násobíme 11 kvůli upraveným mezerám)
    degree_x = 145 + (len(temp_value_str) * 16)
    fb_landscape.rect(degree_x + 2, 27, 4, 4, COLOR_FG)
    text_large(temp_unit_str, degree_x + 4, 27, COLOR_FG)

    # VLHKOST
    text_large(TXT_HUMI, 15, 50, COLOR_FG)
    text_large("-- %", 145, 50, COLOR_FG) 

    # PPM
    text_large(TXT_PPM, 15, 73, COLOR_FG)
    text_large("----", 145, 73, COLOR_FG)

    # ČAS
    text_large(TXT_TIME, 15, 94, COLOR_FG)
    text_large("--:--", 145, 94, COLOR_FG)

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
    
    print("[ČEKÁNÍ] Hotovo. Za 60 sekund proběhne další měření...")
    time.sleep(60)