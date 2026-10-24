import wave, struct, math, random
w = wave.open("son.wav", "wb")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
for i in range(22050 * 5):
    v = int(8000 * math.sin(2 * math.pi * 440 * i / 22050) + random.randint(-800, 800))
    w.writeframes(struct.pack("<h", v))
w.close()