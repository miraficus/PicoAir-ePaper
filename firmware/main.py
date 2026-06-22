import time
from machine import Pin, SPI
import framebuf

print("[START] Spouštím integrovaný program...")

# === INTEGROVANÁ KNIHOVNA ===
EPD_WIDTH       = 128
EPD_HEIGHT      = 250

class EPD_Direct:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

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
        print("Čekám na BUSY pin... (aktuální hodnota:", self.digital_read(self.busy), ")")
        while(self.digital_read(self.busy) == 1):
            self.delay_ms(100)

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
        self.send_data(0x03) # X increment, Y increment
        
        self.send_command(0x44) # Set Ram X-address Start/End position
        self.send_data(0x00)
        self.send_data(0x0F) # 0x0F = 15 -> (15+1)*8 = 128 pixelů
        
        self.send_command(0x45) # Set Ram Y-address Start/End position
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0xF9) # 0xF9 = 249 -> 250 pixelů
        self.send_data(0x00)
        
        self.send_command(0x3C) # Border Waveform
        self.send_data(0x05)
        
        self.send_command(0x18) # Read built-in temperature sensor
        self.send_data(0x80)
        
        self.send_command(0x4E) # Set RAM x address counter to 0
        self.send_data(0x00)
        
        self.send_command(0x4F) # Set RAM y address counter to 0
        self.send_data(0x00)
        self.send_data(0x00)
        self.wait_until_idle()

    def reset(self):
        self.digital_write(self.rst, 1)
        self.delay_ms(200)
        self.digital_write(self.rst, 0)
        self.delay_ms(10)
        self.digital_write(self.rst, 1)
        self.delay_ms(200)

    def display_frame(self):
        # Spustí aktualizaci displeje pro novější typy čipů
        self.send_command(0x22)
        self.send_data(0xF7) # Kompletní update (všech vrstev)
        self.send_command(0x20) # Aktivace
        self.wait_until_idle()

    def set_frame_memory(self, image, x, y, image_width, image_height):
        self.send_command(0x24)
        for i in range(0, len(image)):
            self.send_data(image[i])

    def clear_frame_memory(self, color):
        self.send_command(0x24)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(color)

    def sleep(self):
        self.send_command(0x10)
        self.send_data(0x01)

# === SAMOTNÝ MAIN KÓD ===

# Konfigurace pinů (přesně podle tvého zapojení)
sck_pin = Pin(2)
mosi_pin = Pin(3)
cs_pin = Pin(5, Pin.OUT)
dc_pin = Pin(0, Pin.OUT)
rst_pin = Pin(1, Pin.OUT)
busy_pin = Pin(4, Pin.IN, Pin.PULL_DOWN) 

print("[1] Inicializuji hardwarové SPI...")
# Snížili jsme baudrate na 2 000 000 (2 MHz) pro maximální stabilitu
# a ujistili se, že phase=0 a polarity=0
spi = SPI(0, baudrate=2000000, polarity=0, phase=0, sck=sck_pin, mosi=mosi_pin)

print("[2] Vytvářím objekt EPD_Direct...")
epd = EPD_Direct(spi, cs_pin, dc_pin, rst_pin, busy_pin)

print("[3] Volám epd.init()...")
epd.init()

print("[4] Inicializace hotova. Mažu displej...")
epd.clear_frame_memory(0xFF)
epd.display_frame()

# Nastavení rozměrů pro buffer (šířka musí být 128)
WIDTH = 128
HEIGHT = 250

buf = bytearray(WIDTH * HEIGHT // 8)
fb = framebuf.FrameBuffer(buf, WIDTH, HEIGHT, framebuf.MONO_HLSB)

# Vyplníme displej bílou barvou
fb.fill(1)

# Nakreslíme text a rámeček
fb.text("Ahoj!", 10, 20, 0)
fb.text("Pico 2W", 10, 40, 0)
# Rámeček vykreslíme raději jen do šířky 122, ať je centrovaný na viditelnou část
fb.rect(5, 5, 112, 240, 0) 

print("[5] Vykresluji text...")
# Teď už velikost bufferu přesně sedí na matematiku ovladače
epd.set_frame_memory(buf, 0, 0, WIDTH, HEIGHT)
epd.display_frame()

print("[6] Ukládám displej ke spánku.")
epd.sleep()
print("[KONEC] Vše proběhlo úspěšně!")