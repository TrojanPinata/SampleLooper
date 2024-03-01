import os
import uos
from machine import Pin, I2S, ADC, SDCard, mount
import wave
import time
import math
import audio_i2s
import _thread

# Constants and pins
LED = Pin(22, Pin.OUT)
DRUM_MUTE = Pin(8, Pin.IN, Pin.PULL_DOWN)
SYNTH_MUTE = Pin(9, Pin.IN, Pin.PULL_DOWN)
CH1_A = Pin(16)
CH1_B = Pin(17)
CH1_C = Pin(18)
CH2_A = Pin(13)
CH2_B = Pin(14)
CH2_C = Pin(15)
TEMPO_IN = ADC(Pin(26))
SYNTH_IN = ADC(Pin(27))
YEAH_BTN = Pin(10, Pin.IN, Pin.PULL_DOWN)
WHOO_BTN = Pin(11, Pin.IN, Pin.PULL_DOWN)
DRUM0_BTN = Pin(2, Pin.IN, Pin.PULL_DOWN)
DRUM1_BTN = Pin(3, Pin.IN, Pin.PULL_DOWN)
DRUM2_BTN = Pin(4, Pin.IN, Pin.PULL_DOWN)
DRUM3_BTN = Pin(5, Pin.IN, Pin.PULL_DOWN)
DRUM_BTNS = [DRUM0_BTN, DRUM1_BTN, DRUM2_BTN, DRUM3_BTN]
DRUM_LIST = ["drum0.wav", "drum1.wav", "drum2.wav", "drum3.wav"]
SAMPLE_LIST = ["yeah.wav", "whoo.wav"]
MODIFIER = 80
LMODIFIER = 80

# open sample file
def play_sample(filename):
   tempo = (TEMPO_IN/1024)
   with open(("/sd/" + filename), 'rb') as f:
      w = wave.open(f)
      a = audio_i2s.AudioOut()
      adjusted_speed = (1 + tempo)
      a.play(w, speed=adjusted_speed)
      return a

# run drum loop
def drums():
   drum_loop = 0
   a = None
   while(True):
      if a != None:
         while(a.playing()):
            for j in range(0, 3):
               if DRUM_BTNS[j].value():
                  drum_loop = j
                  break

      if DRUM_MUTE.value() == 0:
         a = play_sample(DRUM_LIST(drum_loop))

# Function to generate sine wave
def generate_sine_wave(freq, duration_ms):
   sample_rate = 44100  # Sample rate for audio playback
   num_samples = int(sample_rate * duration_ms / 1000)
   sin_wave = bytearray(num_samples)
   for i in range(num_samples):
      sin_wave[i] = 127 + int(126 * math.sin(2 * math.pi * freq * i / sample_rate))
   return sin_wave

# Function to play sine wave accompaniment
def play_sine_wave(freq, duration_ms):
   sin_wave = generate_sine_wave(freq, duration_ms)
   a = audio_i2s.AudioOut(sample_rate=44100, bits=16, buffer_size=512)
   a.play(sin_wave)
   while a.playing():
      time.sleep_ms(100)

# run synth loop
def synth():
   return 1


if __name__=="__main__":
   sd = SDCard()
   mount(sd, "/sd")

   drum_list = ["drum0.wav", "drum1.wav", "drum2.wav", "drum3.wav"]
   yw_list = ["yeah.wav", "whoo.wav"]
   drum_buttons = [DRUM0_BTN, DRUM1_BTN, DRUM2_BTN, DRUM3_BTN]


   # start synth thread
   synth_thread = _thread.start_new_thread(synth, ())

   # led on to signify thread split successfully
   LED.on()

   # start drum loop
   drums()