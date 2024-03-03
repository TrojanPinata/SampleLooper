import os
from machine import Pin, I2S, ADC, SDCard, SPI
import time, math, struct
import uasyncio as asyncio

# Constants and pins
LED = Pin(22, Pin.OUT)
DRUM_MUTE = Pin(8, Pin.IN, Pin.PULL_UP)
SYNTH_MUTE = Pin(9, Pin.IN, Pin.PULL_UP)
CH1_A = Pin(16)
CH1_B = Pin(17)
CH1_C = Pin(18)
CH2_A = Pin(13)
CH2_B = Pin(14)
CH2_C = Pin(15)
TEMPO_IN = ADC(Pin(26))
SYNTH_IN = ADC(Pin(27))
YEAH_BTN = Pin(10, Pin.IN, Pin.PULL_UP)
WHOO_BTN = Pin(11, Pin.IN, Pin.PULL_UP)
DRUM0_BTN = Pin(2, Pin.IN, Pin.PULL_UP)
DRUM1_BTN = Pin(3, Pin.IN, Pin.PULL_UP)
DRUM2_BTN = Pin(4, Pin.IN, Pin.PULL_UP)
DRUM3_BTN = Pin(5, Pin.IN, Pin.PULL_UP)
DRUM_BTNS = [DRUM0_BTN, DRUM1_BTN, DRUM2_BTN, DRUM3_BTN]
DRUM_LIST = ["drum0.wav", "drum1.wav", "drum2.wav", "drum3.wav"]
SAMPLE_LIST = ["yeah.wav", "whoo.wav"]
MNT = "/sd"
PATH = MNT + "/"
SPI_RX = Pin(0)
SPI_CS = Pin(1, Pin.OUT)
SPI_SCK = Pin(6)
SPI_TX = Pin(7)
BUFFER_LEN = 40000
SAMPLE_RATE = 44100
FORMAT = I2S.MONO
SAMPLE_BITS = 16
MAX_ADC = 65535 # the pico has a 12 bit ADC but the library normalizes to 16 bit

# initialize sd card on spi0
def init_SD():
   spi = SPI(1, baudrate=1_000_000, polarity=0, phase=0, bit=8, firstbit=SPI.MSB, sck=SPI_SCK, mosi=SPI_TX, miso=SPI_RX)
   sd = SDCard(spi, SPI_CS)
   os.mount(sd, MNT)
   return spi, sd

# initialize I2S channel
def init_I2S(p1, p2, p3):
   return I2S(0, sck=p1, ws=p2, sd=p3, mode=I2S.TX, bits=SAMPLE_BITS, format=FORMAT, rate=SAMPLE_RATE, ibuf=BUFFER_LEN)

# clean up - takes in SPI and I2S objects in order to kill
def destroy(spi, a):
   os.umount("/sd")
   spi.deinit()
   a.deinit()

# used for checking state of 
def check_ADC(adc):
   return adc.read_u16()

# generates a tone - yeah i stole this function, what are you going to do about it?
def make_tone(rate, bits, frequency):
   # create a buffer containing the pure tone samples
   samples_per_cycle = rate // frequency
   sample_size_in_bytes = bits // 8
   samples = bytearray(samples_per_cycle * sample_size_in_bytes)
   volume_reduction_factor = 32
   range = pow(2, bits) // 2 // volume_reduction_factor
    
   for i in range(samples_per_cycle):
      sample = range + int((range - 1) * math.sin(2 * math.pi * i / samples_per_cycle))
      struct.pack_into("<h", samples, i * sample_size_in_bytes, sample)
        
   return samples

# check for next sample
async def check_loop():
   for j in range(0, 3):
      if DRUM_BTNS[j].value():
         drum_loop = j
         break
   return drum_loop

# play drum loop
async def drums(a):
   drum_loop = 0
   swriter = asyncio.StreamWriter(a)
   wav_samples = bytearray(10000)
   wav_samples_mv = memoryview(wav_samples)
   while(True):
      drum_loop = check_loop()
      if DRUM_MUTE.value() == 0:
         #wav = open("/sd/{}".format(DRUM_LIST[drum_loop]), "rb")
         wav = open("/{}".format(DRUM_LIST[drum_loop]), "rb")
         p = wav.seek(44)
         drum_loop = check_loop()
         while(True):
            num_read = wav.readinto(wav_samples_mv)
            drum_loop = check_loop()
            if num_read == 0:
               p = wav.seek(44)
            else:
               swriter.out_buf = wav_samples_mv[:num_read]
               await swriter.drain()

# play synth sound
async def synth(a):
   while(True):
      if SYNTH_MUTE.value() == 0:
         freq = check_ADC(SYNTH_IN)/8
         samples = make_tone(SAMPLE_RATE, SAMPLE_BITS, freq)
         p = a.write(samples)

# yeah - woo
async def think(a, n):
   swriter = asyncio.StreamWriter(a)
   wav_samples = bytearray(10000)
   wav_samples_mv = memoryview(wav_samples)
   while(True):
      if YEAH_BTN.value() == 0:
         #wav = open("/sd/{}".format(SAMPLE_LIST[0]), "rb")
         wav = open("/{}".format(SAMPLE_LIST[n]), "rb")
         p = wav.seek(44)
         while(True):
            num_read = wav.readinto(wav_samples_mv)
            if num_read == 0:
               p = wav.seek(44)
            else:
               swriter.out_buf = wav_samples_mv[:num_read]
               await swriter.drain()

# start tasks - takes in I2S output object
async def gen_tasks(a):
   play_drums = asyncio.create_task(drums(a))
   #play_synth = asyncio.create_task(synth(a))
   #play_yeah = asyncio.create_task(think(a, 0))
   #play_whoo = asyncio.create_task(think(a, 1))

if __name__=="__main__":
   #spi, sd = init_SD()
   a = init_I2S(CH1_B, CH1_A, CH1_C)
   try:
      LED.value(1)
      gen_tasks(a)

   except (Exception) as e:
      LED.value(0)
      #destroy(spi, a)
      a.deinit()
