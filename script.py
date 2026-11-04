
#!/usr/bin/env python3
# Rebuild a Creative Stage v1 (MF8360) firmware with custom silence-gate parameters.
# Input : official "MF8360 Creative Stage FW upgrader V01" upgrade_Dragon_SDK.bin
# Output: ./out/system/{upgrade_Dragon_SDK.bin, upgrade.txt}
import os

# ============================== KNOBS ==============================
THRESHOLD    = 40     # silence level. Keep ~40. Lower -> risk hiss; higher -> cuts quiet audio. (<=95)
ATTACK       = 1      # signal frames before un-mute. 1..3. Lower = faster wake.
HOLD_SECONDS = 70     # silence seconds before mute. ~294 frames/s; max ~223 s (16-bit counter).
INPUT        = "og_crefw_upgrade_Dragon_SDK.bin"   # path to the OFFICIAL image
# ==================================================================

BASE      = 0x58000000
LIT_ADDR  = 0x580bc918   # free 4-aligned padding slot (between two functions) for a >2047 hold value
FRAMES_PER_SEC = 294

def enc_movin(reg, imm):                 # movi.n aReg, imm (0..95) -> 2 bytes
    assert 0 <= imm <= 95, "movi.n immediate out of range"
    return bytes([((imm >> 4) & 0x7) << 4 | 0x0c, ((imm & 0x0f) << 4) | reg])

def enc_movi(reg, imm):                  # movi aReg, imm12 (-2048..2047) -> 3 bytes
    assert -2048 <= imm <= 2047, "movi immediate out of range"
    i = imm & 0x0fff
    return bytes([(reg << 4) | 0x02, (0xa << 4) | ((i >> 8) & 0x0f), i & 0xff])

def enc_l32r(reg, pc, target):           # l32r aReg, target (target below pc, 4-aligned) -> 3 bytes
    off = target - ((pc + 3) & ~3)
    assert off < 0 and off % 4 == 0 and off >= -0x40000, "l32r target out of range"
    imm16 = (off >> 2) & 0xffff
    return bytes([(reg << 4) | 0x01, imm16 & 0xff, (imm16 >> 8) & 0xff])

def build(stock, thr, attack, hold):
    assert 0 <= thr <= 95, "THRESHOLD must be 0..95"
    assert 1 <= attack <= 95, "ATTACK must be small (1..3 recommended)"
    assert 1 <= hold <= 65535, "HOLD frames must be 1..65535"
    d = bytearray(stock)
    def put(off, old, new, name):
        if d[off:off+len(old)] != old:
            raise SystemExit(f"Base mismatch @0x{off:x} ({name}). "
                             f"This is not the official V01 image (or already patched).")
        d[off:off+len(new)] = new
    # THRESHOLD — 4 sites: main-path L/R and adpcm-path L/R
    put(0x0beded, bytes([0x2c,0x8e]),      enc_movin(14, thr), "threshold main L")
    put(0x0bedf8, bytes([0x2c,0x82]),      enc_movin(2,  thr), "threshold main R")
    put(0x0bda56, bytes([0xb2,0xa0,0x28]), enc_movi(11,  thr), "threshold adpcm L")
    put(0x0bda62, bytes([0x2c,0x8d]),      enc_movin(13, thr), "threshold adpcm R")
    # ATTACK — 2 sites
    put(0x0bee42, bytes([0x2c,0x69]),      enc_movin(9, attack), "attack main")
    put(0x0bda9d, bytes([0x2c,0x65]),      enc_movin(5, attack), "attack adpcm")
    # HOLD — 2 sites (movi if it fits, else l32r + shared literal)
    for off, reg, pc in [(0x0beeb4, 11, 0x580beeb4), (0x0bdb0c, 7, 0x580bdb0c)]:
        old = bytes([(reg << 4) | 0x02, 0xa4, 0x0e])          # original: movi aReg, 0x40e (1038)
        put(off, old, enc_movi(reg, hold) if hold <= 2047 else enc_l32r(reg, pc, LIT_ADDR), "hold")
    if hold > 2047:
        lo = LIT_ADDR - BASE
        if d[lo:lo+4] != b"\x00\x00\x00\x00":
            raise SystemExit("Literal slot not free — unexpected base image.")
        d[lo:lo+4] = hold.to_bytes(4, "little")
    # Recompute the two affected checksums (32-bit little-endian word sums)
    def wsum(s, e):
        x = 0
        for p in range(s, e, 4):
            x = (x + int.from_bytes(d[p:p+4], "little")) & 0xffffffff
        return x
    d[0xff014:0xff018] = wsum(0x30000, 0xff010).to_bytes(4, "little")  # "app" region
    d[0xff010:0xff014] = wsum(0x00000, 0xff010).to_bytes(4, "little")  # "all" region
    return bytes(d)

def main():
    stock = open(INPUT, "rb").read()
    if len(stock) != 1044512:
        raise SystemExit(f"Unexpected size {len(stock)} (expected 1044512). Wrong file?")
    hold = max(1, min(65535, round(HOLD_SECONDS * FRAMES_PER_SEC)))
    out = build(stock, THRESHOLD, ATTACK, hold)
    os.makedirs("out/system", exist_ok=True)
    open("out/system/upgrade_Dragon_SDK.bin", "wb").write(out)
    open("out/system/upgrade.txt", "w").write("upgrade_Dragon_SDK.bin")
    changed = [hex(i) for i in range(len(out)) if out[i] != stock[i]]
    print(f"OK. threshold={THRESHOLD} attack={ATTACK} hold={hold} frames (~{hold/FRAMES_PER_SEC:.0f}s)")
    print(f"Changed {len(changed)} bytes: {changed}")
    print("Wrote out/system/  -> copy the whole 'system' folder to a FAT32 USB (<32GB).")

if __name__ == "__main__":
    main()

