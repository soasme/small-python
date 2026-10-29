"""Sound effects, synthesized when the game starts, so it ships no audio
files. Each is 16-bit mono PCM at RATE, the bytes raylib's load_sound takes."""
from .motion import PI, sine
from .pipes import Random

RATE = 22050


def pcm(samples):
    data = bytearray()
    for value in samples:
        data += int(max(-1.0, min(1.0, value)) * 32767).to_bytes(2, "little", signed=True)
    return bytes(data)


def chirp(start, end, seconds, volume):
    """A tone gliding from start to end hertz and fading out: a flap."""
    count, phase = int(RATE * seconds), 0.0
    for i in range(count):
        t = i / count
        phase += 2 * PI * (start + (end - start) * t) / RATE
        wave = sine(phase)
        # A touch of square wave makes it brighter than a pure sine.
        yield volume * min(1.0, i / 80) * (1 - t) ** 2 * (0.75 * wave + (0.25 if wave > 0 else -0.25))


def crash(seconds, volume):
    """Muffled noise over a falling thump: hitting a pipe or the ground."""
    count, phase, noise, muffled = int(RATE * seconds), 0.0, Random(99), 0.0
    for i in range(count):
        t = i / count
        muffled += (noise.between(-1000, 1000) / 1000 - muffled) * 0.3
        phase += 2 * PI * (150 - 100 * t) / RATE
        yield volume * ((1 - t) ** 3 * 1.6 * muffled + (1 - t) ** 2 * sine(phase))


FLAP = pcm(chirp(380, 920, 0.11, 0.45))
HIT = pcm(crash(0.32, 0.55))
