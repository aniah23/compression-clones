import struct

W, H = 320, 240
rows = []
for y in range(H - 1, -1, -1):
    row = bytearray()
    for x in range(W):
        r = x * 255 // W
        g = y * 255 // H
        b = (x + y) * 255 // (W + H)
        if (x // 40 + y // 40) % 2 == 0:
            r, g, b = 255 - r, 255 - g, 255 - b
        row += bytes((b, g, r))
    rows.append(bytes(row))

pixels = b"".join(rows)
header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
dib = struct.pack("<IiiHHIIiiII", 40, W, H, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
open("image.bmp", "wb").write(header + dib + pixels)
print("image.bmp créé")