"""Notification musicale : do central doux, fichier PCM 48 kHz / 24 bits stéréo."""
from pathlib import Path

SOUND = Path(__file__).resolve().parent / 'sons' / 'do-doux.wav'


def play_notification():
    import logging
    import winsound
    try:
        winsound.PlaySound(str(SOUND), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except RuntimeError:
        # Le retour visuel reste disponible si la sortie audio ne l'est pas.
        logging.warning('Le son de notification ne peut pas être joué.')


def generate():
    import math
    import wave
    rate, duration = 48_000, 0.28
    frequency = 261.6255653005986  # Do central, accordage la = 440 Hz.
    frames = bytearray()
    for index in range(round(rate * duration)):
        t = index / rate
        attack = min(1.0, t / 0.03)
        release = min(1.0, (duration-t) / 0.14)
        envelope = math.sin(math.pi*attack/2)**2 * math.sin(math.pi*release/2)**2
        envelope *= math.exp(-1.5*t/duration)
        phase = 2*math.pi*frequency*t
        tone = math.sin(phase) + 0.08*math.sin(2*phase) + 0.015*math.sin(3*phase)
        value = round(0.14 * envelope * tone * ((1 << 23)-1))
        sample = value.to_bytes(3, 'little', signed=True)
        frames.extend(sample * 2)
    SOUND.parent.mkdir(exist_ok=True)
    with wave.open(str(SOUND), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(3)
        wav.setframerate(rate)
        wav.writeframes(frames)


if __name__ == '__main__':
    generate()
