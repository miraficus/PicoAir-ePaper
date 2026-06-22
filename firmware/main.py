import time
from machine import Pin, SPI
import framebuf

print("[START] Spouštím kompletně vyčištěný program...")

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
        self.send_data(0xF7) # Tvůj funkční refresh kód pro novou revizi
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
        # Vytvoříme čisté pole o správné velikosti 4000 bajtů a pošleme ho naráz
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

print("[3] Volám epd.init()...")
epd.init()

print("[4] Inicializace hotova. Mažu displej...")
epd.clear_frame_memory(0xFF)
epd.display_frame()

from machine import ADC

# Inicializace interního senzoru teploty (u RP2350/Pico 2W je to ADC kanál 4)
adc_temp = ADC(4)

def get_cpu_temp():
    # Přečteme syrovou hodnotu z ADC (0-65535)
    raw = adc_temp.read_u16()
    # Přepočet na napětí (Pico 2W používá 3.3V referenci)
    voltage = raw * 3.3 / 65535
    # Vzorec pro teplotní senzor v RP2350:
    # Teplota = 27 - (voltage - 0.706) / 0.001721
    temperature = 27 - (voltage - 0.706) / 0.001721
    return round(temperature, 1) # Zaokrouhlíme na 1 desetinné místo

# === SOFTWAROVÉ KRESLENÍ NA ŠÍŘKU ===
WIDTH_LANDSCAPE = 256
HEIGHT_LANDSCAPE = 122

draw_buf = bytearray(WIDTH_LANDSCAPE * HEIGHT_LANDSCAPE // 8)
fb_landscape = framebuf.FrameBuffer(draw_buf, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE, framebuf.MONO_HLSB)
fb_landscape.fill(1) # Vyplnit bílou

# --- UPRAVENÁ FUNKCE PRO TEXT 2x VĚTŠÍ (S VOLBOU BARVY) ---
def text_large(text, start_x, start_y, color=0):
    temp_w = len(text) * 8
    temp_h = 8
    temp_buf = bytearray(temp_w * temp_h // 8)
    temp_fb = framebuf.FrameBuffer(temp_buf, temp_w, temp_h, framebuf.MONO_HLSB)
    
    # Pokud chceme kreslit BÍLÝ velký text (color=1), musíme mini buffer 
    # nejdříve vyplnit ČERNĚ (0). Pokud chceme ČERNÝ text, vyplníme ho BÍLĚ (1).
    if color == 1:
        temp_fb.fill(0)
        temp_fb.text(text, 0, 0, 1) # Píšeme bíle do černého okna
    else:
        temp_fb.fill(1)
        temp_fb.text(text, 0, 0, 0) # Píšeme černě do bílého okna
    
    # Překreslení do hlavního bufferu
    for x in range(temp_w):
        for y in range(temp_h):
            # Pokud se pixel v mini bufferu shoduje s barvou textu, vykreslíme ho
            if temp_fb.pixel(x, y) == color:
                target_x = start_x + (x * 2)
                target_y = start_y + (y * 2)
                
                # Vykreslíme čtvereček 2x2 zvolenou barvou
                fb_landscape.pixel(target_x, target_y, color)
                fb_landscape.pixel(target_x + 1, target_y, color)
                fb_landscape.pixel(target_x, target_y + 1, color)
                fb_landscape.pixel(target_x + 1, target_y + 1, color)

# 1. Tlustý rámeček (3 pixely do sebe)
fb_landscape.rect(0, 0, 250, 120, 0)
fb_landscape.rect(1, 1, 248, 118, 0)
fb_landscape.rect(2, 2, 246, 116, 0)

# --- INVERZNÍ HORNÍ LIŠTA (Bílý text na černém pozadí) ---
# Vykreslíme plný černý obdélník podél horního okraje (uvnitř rámečku)
# Souřadnice: X=3, Y=3, šířka=244, výška=16, barva=0 (černá)
fb_landscape.fill_rect(3, 3, 244, 16, 0)

# Napíšeme text BÍLOU barvou (1) do tohoto černého obdélníku
fb_landscape.text("PicoAir Stanice", 15, 6, 1)
fb_landscape.text("V 1.0", 200, 6, 1)

# 2. Vykreslení hodnot velkým písmem (posunuto kousek dolů, aby to nebylo nalepené na liště)
cpu_temperature = get_cpu_temp()
temp_string = "{}C".format(cpu_temperature)

text_large("Teplota:", 15, 27, 0)
text_large(temp_string, 145, 27)

text_large("Vlhkost:", 15, 50, 0)
text_large("--%", 145, 50) 

text_large("PPM:", 15, 73, 0)
text_large("----", 145, 73)

text_large("Cas:", 15, 94, 0)
text_large("--:--", 145, 94)

# === PŮVODNÍ ROTAČNÍ SMYČKA (NEMĚNIT) ===
DISP_WIDTH = 128
DISP_HEIGHT = 250
display_buf = bytearray(DISP_WIDTH * DISP_HEIGHT // 8)
fb_display = framebuf.FrameBuffer(display_buf, DISP_WIDTH, DISP_HEIGHT, framebuf.MONO_HLSB)
fb_display.fill(1)

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
print("[KONEC] Vše proběhlo úspěšně!")