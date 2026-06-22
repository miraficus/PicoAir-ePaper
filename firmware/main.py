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

# === SOFTWAROVÉ KRESLENÍ NA ŠÍŘKU ===
WIDTH_LANDSCAPE = 256  # ZMĚNA z 250 na 256 kvůli dělitelnosti 8
HEIGHT_LANDSCAPE = 122 # Viditelná výška

# Kreslící buffer na šířku (teď už bude mít správný počet bajtů)
draw_buf = bytearray(WIDTH_LANDSCAPE * HEIGHT_LANDSCAPE // 8)
fb_landscape = framebuf.FrameBuffer(draw_buf, WIDTH_LANDSCAPE, HEIGHT_LANDSCAPE, framebuf.MONO_HLSB)
fb_landscape.fill(1) # Vyplnit bílou

# Tady píšeme horizontálně (omezení rámečku na 240 nechej, ať je to hezky centrované)
fb_landscape.text("Waveshare 2.13 v2.1", 10, 15, 0)
fb_landscape.text("Konecne na sirku!", 10, 40, 0)
fb_landscape.text("Pico 2W jede bomby.", 10, 65, 0)
fb_landscape.rect(0, 0, 250, 120, 0)

# Cílový buffer na výšku (128x250 = přesně 4000 bajtů)
DISP_WIDTH = 128
DISP_HEIGHT = 250
display_buf = bytearray(DISP_WIDTH * DISP_HEIGHT // 8)
fb_display = framebuf.FrameBuffer(display_buf, DISP_WIDTH, DISP_HEIGHT, framebuf.MONO_HLSB)
fb_display.fill(1)

print("Přetáčím pixely do nativní orientace...")
for x in range(WIDTH_LANDSCAPE):
    for y in range(HEIGHT_LANDSCAPE):
        pixel = fb_landscape.pixel(x, y)
        
        # OPRAVA: Odečetli jsme 4 pixely (offset), abychom obraz posunuli 
        # směrem dolů od uříznutého okraje a vycentrovali ho
        new_x = (DISP_WIDTH - 1 - y) - 7
        new_y = x
        
        # Kontrola, aby zapisovaný pixel neskočil mimo rozsah 0 až 127
        if 0 <= new_x < DISP_WIDTH:
            fb_display.pixel(new_x, new_y, pixel)

print("[5] Posílám otočená data na displej...")
epd.set_frame_memory(display_buf)
epd.display_frame()

print("[6] Ukládám displej ke spánku.")
epd.sleep()
print("[KONEC] Vše proběhlo úspěšně!")