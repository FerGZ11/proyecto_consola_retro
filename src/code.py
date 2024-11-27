import board
import digitalio
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import usb_hid

# Configuración del teclado HID
keyboard = Keyboard(usb_hid.devices)

# Pines de entrada para los botones
botones = [
    {"pin": board.GP6, "tecla": Keycode.TAB},   
    {"pin": board.GP7, "tecla": Keycode.SPACE},  
    {"pin": board.GP10, "tecla": Keycode.W},  
    {"pin": board.GP12, "tecla": Keycode.C},  
    {"pin": board.GP13, "tecla": Keycode.D},  
    {"pin": board.GP14, "tecla": Keycode.A},  
    {"pin": board.GP15, "tecla": Keycode.S},  
    {"pin": board.GP27, "tecla": Keycode.BACKSPACE},  
    {"pin": board.GP26, "tecla": Keycode.ENTER},  
    {"pin": board.GP21, "tecla": Keycode.KEYPAD_EIGHT},  
    {"pin": board.GP19, "tecla": Keycode.ESCAPE},  
    {"pin": board.GP18, "tecla": Keycode.KEYPAD_SIX},  
    {"pin": board.GP17, "tecla": Keycode.KEYPAD_FOUR},  
    {"pin": board.GP16, "tecla": Keycode.KEYPAD_TWO},  
]


# Configuración de los pines como entradas con pull-up
for boton in botones:
    boton["objeto"] = digitalio.DigitalInOut(boton["pin"])
    boton["objeto"].switch_to_input(pull=digitalio.Pull.UP)

# Loop principal
while True:
    for boton in botones:
        if not boton["objeto"].value:  # Si el botón está presionado
            keyboard.press(boton["tecla"])
        else:
            keyboard.release(boton["tecla"])
