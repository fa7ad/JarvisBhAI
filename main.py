#!/usr/bin/env python3

"""
Record audio from microphone to detect hotword "jarvis"
"""

import os
import time
import wave
import struct
import tempfile

from datetime import datetime

import wit
import pyaudio
import pvporcupine

from gtts import gTTS
from logmmse import logmmse_from_file
from mpyg321.mpyg321 import MPyg321Player

from responder import Responder


KEYWORDS = ["jarvis", "bumblebee"]

rp = Responder()
pa = pyaudio.PyAudio()
pl = MPyg321Player()
ai = wit.Wit(os.getenv('WITAI_TOKEN'))
porcupine = pvporcupine.create(keywords=KEYWORDS)

sample_rate = porcupine.sample_rate
frames_per_buffer = porcupine.frame_length
DURATION = 4.5

audio_stream = pa.open(
    rate=sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=frames_per_buffer,
)


def get_command_recording():
    _, file_name = tempfile.mkstemp(".wav", prefix="input_command")
    wave_file = wave.open(file_name, "wb")
    wave_file.setnchannels(1)
    wave_file.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(sample_rate)
    nframes = int(sample_rate / frames_per_buffer * DURATION)
    for _ in range(nframes):
        audio = audio_stream.read(frames_per_buffer)
        wave_file.writeframes(audio)
    wave_file.close()
    logmmse_from_file(file_name, file_name)
    return file_name


def log(text):
    print("[%s] %s" % (str(datetime.now()), text))


while True:
    pcm = audio_stream.read(porcupine.frame_length)
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

    result = porcupine.process(pcm)
    if result >= 0:
        log("Hotword Detected: %s" % KEYWORDS[result])
        in_fname = get_command_recording()
        _, out_fname = tempfile.mkstemp(".mp3", "tts_out")
        aud_file = open(in_fname, "rb")
        ai_response = rp.get_response("not_found", None)
        try:
            resp = ai.speech(aud_file, {"Content-Type": "audio/wav"})
            log("Utterance: %s" % resp["text"])
            intent = resp["intents"][0]["name"]
            log("Intent: %s" % intent)
            ai_response = rp.get_response(intent, resp["traits"])
        except Exception as error:
            print(error)
        finally:
            aud_file.close()
        os.unlink(in_fname)
        log("Response: %s" % ai_response)
        gtitties = gTTS(ai_response, lang="bn")
        gtitties.save(out_fname)
        log("DEBUG (TTS out): %s" % out_fname)
        pl.play_song(out_fname)
        time.sleep(0.2)
        os.unlink(out_fname)
