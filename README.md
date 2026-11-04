# 🔊 Creative Stage V1 (MF8360) — Audio Lag Firmware Fix

Unofficial firmware modification for the **Creative Stage V1 (MF8360)** soundbar, based on the original Creative V01 firmware.

The purpose of this project is to reduce audio activation latency by modifying the silence-gate parameters, preventing the beginning of audio playback from being cut off while retaining the original noise threshold.

> ⚠️ **Disclaimer:** This is an unofficial firmware modification. The generated binary has been verified against its expected SHA-256 hash, but successful operation and audio performance must be validated on the physical soundbar. Use at your own risk.

## 📑 Table of contents

- [Overview](#-overview)
- [Firmware information](#-firmware-information)
- [Audio parameters](#audio-parameters)
- [Binary modifications](#-binary-modifications)
- [Requirements](#-requirements)
- [Build instructions](#build-instructions)
- [Firmware verification](#-firmware-verification)
- [USB preparation](#-usb-preparation)
- [Firmware installation](#-firmware-installation)
- [Expected behaviour](#expected-behaviour)
- [Post-update testing](#-post-update-testing)
- [References](#-references)
- [Disclaimer](#disclaimer)

---

## 🔍 Overview

The Creative Stage V1 uses a silence-gate mechanism that mutes the audio output after a period of silence.

The original firmware can introduce an audible delay when playback resumes, sometimes cutting off the beginning of speech or audio.

This modification changes three parameters:

| Parameter | Purpose |
|---|---|
| `THRESHOLD` | Audio level required to activate the output |
| `ATTACK` | Number of signal frames required before unmuting |
| `HOLD` | Time before the output is muted after silence |

The custom firmware keeps the original threshold, reduces the attack time to one frame and increases the hold time to approximately 70 seconds.

### Project status

<badge color="success">Binary generated and verified</badge> <badge color="warning">Hardware validation pending</badge>

The modified firmware has been generated and its SHA-256 hash matches the expected result. Physical installation and audio performance testing remain to be completed.

---

## 🧬 Firmware information

| Property | Value |
|---|---|
| Manufacturer | Creative Technology |
| Product | Creative Stage V1 |
| Model | MF8360 |
| Base firmware | Official Creative V01 |
| Firmware file | `upgrade_Dragon_SDK.bin` |
| Firmware size | 1,044,512 bytes |
| Architecture | Xtensa |
| Patching language | Python 3 |
| External dependencies | None |
| Bootloader | Original, not intentionally modified |

### Firmware package structure

The firmware update package uses the following directory structure:

```text
system/
├── upgrade_Dragon_SDK.bin
└── upgrade.txt
```

Contents of `upgrade.txt`:

```text
upgrade_Dragon_SDK.bin
```

### Firmware SHA-256 hashes

Three firmware images were identified during the investigation:

| Firmware image | SHA-256 |
|---|---|
| 🏭 Official Creative V01 | `e18d9b58d4f3ce8dbc590386a91b41fecfc33a8c038e6e0b24ee28971c81ad5c` |
| ⚠️ Alternative YouTube No-Lag | `d7f683718deb70b698a532692040bf6c322301adb0729fe565efdc60a393017c` |
| 🛠️ Custom modified firmware | `53ba88ae2047a7d602bea8cc5d4355280620e4bd2ae3cfad561750fd6bd57f76` |

**Important:** The patching script requires the original Creative V01 firmware. It validates the file size and expected byte sequences before applying modifications. The alternative YouTube firmware must not be used as input.

---

## ⚙️ Audio parameters

The script uses the following configuration:

```python
THRESHOLD    = 40
ATTACK       = 1
HOLD_SECONDS = 70

FRAMES_PER_SEC = 294
```

### Parameter comparison

| Parameter | Official V01 | Alternative No-Lag | Custom |
|---|---:|---:|---:|
| Threshold | 40 | 10 | **40** |
| Attack | 38 frames | 9 frames | **1 frame** |
| Hold | 1,038 frames | 2,776 frames | **20,580 frames** |
| Attack time | ~129.25 ms | ~30.61 ms | **~3.40 ms** |
| Hold time | ~3.53 s | ~9.44 s | **70 s** |

Calculations use 294 frames per second:

- 1 frame = 3.40 ms.
- 9 frames = 30.61 ms.
- 38 frames = 129.25 ms.
- 20,580 frames = 70 seconds.

> ℹ️ Some published comparison figures report approximately 34 ms for 9 frames and 7 ms for 1 frame. These values do not match the 294 FPS conversion used by this script.

### 🎚️ Threshold — 40

Controls the audio level required to activate the sound output.

- Lower values increase sensitivity.
- Higher values can cause quiet audio to be ignored.
- The custom firmware retains the original value of 40.
- The alternative firmware uses 10 and has been reported to produce persistent background hiss.

### ⚡ Attack — 1 frame

Controls how many signal frames are required before the audio output is unmuted.

| Firmware | Attack |
|---|---:|
| Official V01 | 38 frames |
| Alternative No-Lag | 9 frames |
| Custom | **1 frame** |

The objective is to minimise the delay before audio becomes audible.

### ⏱️ Hold — 70 seconds

Controls how long the device waits after silence before activating the mute state.

| Firmware | Hold time |
|---|---:|
| Official V01 | ~3.5 seconds |
| Alternative No-Lag | ~9.4 seconds |
| Custom | **70 seconds** |

The longer hold time is intended to reduce repeated mute/unmute cycles during quiet passages.

---

## 🔬 Binary modifications

The Python script modifies specific Xtensa instruction sequences in the original firmware image.

### Modified instruction locations

| Function | File offset | Original bytes |
|---|---:|---|
| Threshold — main L | `0x0BEDED` | `2C 8E` |
| Threshold — main R | `0x0BEDF8` | `2C 82` |
| Threshold — ADPCM L | `0x0BDA56` | `B2 A0 28` |
| Threshold — ADPCM R | `0x0BDA62` | `2C 8D` |
| Attack — main | `0x0BEE42` | `2C 69` |
| Attack — ADPCM | `0x0BDA9D` | `2C 65` |
| Hold — main | `0x0BEEB4` | `B2 A4 0E` |
| Hold — ADPCM | `0x0BDB0C` | `72 A4 0E` |

The script checks these original byte sequences before replacing them. If a sequence does not match, execution is aborted to prevent patching an incompatible or already modified firmware image.

### 🧠 Hold implementation

The original firmware stores the hold counter using a 12-bit immediate instruction (`movi`).

The maximum positive immediate value is 2,047. Since the custom hold value is 20,580, the script replaces both original instructions with `l32r` instructions referencing a shared 32-bit literal.

| Property | Value |
|---|---|
| Literal address | `0x580BC918` |
| Firmware file offset | `0x000BC918` |
| Storage format | 32-bit little-endian |
| Hold value | 20,580 |

The script verifies that the literal storage location is initially zero before writing the new value.

### 🔐 Firmware checksums

After applying the modifications, the script recalculates two 32-bit little-endian word-sum checksums.

| Checksum | Storage offset | Calculation range |
|---|---:|---|
| Application checksum | `0x0FF014` | `0x30000` – `0xFF010` |
| Image checksum | `0x0FF010` | `0x00000` – `0xFF010` |

### 📊 Modification footprint

The generated firmware differs from the original in exactly **20 bytes**:

- 12 bytes associated with instruction and parameter modifications.
- 8 bytes associated with checksum recalculation.

The original bootloader is not intentionally modified.

---

## 🐍 Requirements

- Python 3.
- Official Creative Stage V01 firmware image.
- Linux, macOS or Windows.

No external Python packages are required.

### Repository structure

The working directory should contain:

```text
creative-stage-v1-audio-lag-firmware-fix/
├── script.py
└── og_crefw_upgrade_Dragon_SDK.bin
```

The original firmware filename used by the script is:

```text
og_crefw_upgrade_Dragon_SDK.bin
```

---

## 🛠️ Build instructions

### 1. Configure the patch

Edit the configuration section in `script.py` if necessary:

```python
THRESHOLD    = 40
ATTACK       = 1
HOLD_SECONDS = 70
INPUT        = "og_crefw_upgrade_Dragon_SDK.bin"
```

### 2. Generate the modified firmware

Run:

```bash
python3 script.py
```

Expected output:

```text
OK. threshold=40 attack=1 hold=20580 frames (~70s)
Changed 20 bytes: [...]
Wrote out/system/  -> copy the whole 'system' folder to a FAT32 USB (<32GB).
```

### 3. Generated files

The script creates the following directory:

```text
out/
└── system/
    ├── upgrade_Dragon_SDK.bin
    └── upgrade.txt
```

This is the complete firmware package required for the USB update.

---

## ✅ Firmware verification

The generated firmware must match both the expected file size and SHA-256 hash.

### Verify file size

```bash
stat -c '%n %s bytes' out/system/upgrade_Dragon_SDK.bin
```

Expected result:

```text
out/system/upgrade_Dragon_SDK.bin 1044512 bytes
```

### Verify SHA-256

```bash
sha256sum out/system/upgrade_Dragon_SDK.bin
```

Expected result:

```text
53ba88ae2047a7d602bea8cc5d4355280620e4bd2ae3cfad561750fd6bd57f76  out/system/upgrade_Dragon_SDK.bin
```

<badge color="success">SHA-256 verified</badge>

The generated firmware matches the expected hash and file size.

This verifies binary reproducibility. It does not guarantee successful installation or correct operation on the soundbar.

---

## 💾 USB preparation

Use a USB flash drive with the following characteristics:

- FAT32 filesystem.
- Capacity below 32 GB.
- Firmware package located in the root directory.

The USB drive must contain this exact structure:

```text
USB/
└── system/
    ├── upgrade_Dragon_SDK.bin
    └── upgrade.txt
```

Copy the entire `system` directory from `out/` to the root of the USB drive.

Do not rename the firmware file or the directory.

---

## 🔄 Firmware installation

The update is performed through the USB port located on the side of the soundbar.

**No button combination or special button sequence is required.** The soundbar is powered on normally after connecting the USB drive.

### ⚠️ Before starting

- Verify the USB filesystem is FAT32.
- Check the firmware file and directory structure.
- Make sure the soundbar is switched off.
- Disconnect the soundbar from mains power.
- Do not interrupt the update once it starts.

### 🚀 Update procedure

**1. Switch off and unplug the soundbar**

Make sure the soundbar is completely switched off and disconnected from the power supply.

**2. Connect the USB drive**

Insert the prepared USB flash drive into the USB port located on the side of the soundbar.

**3. Reconnect mains power**

Plug the soundbar back into the power supply.

**4. Switch on the soundbar normally**

Turn on the soundbar using its normal power-on procedure.

No special button combination is needed.

**5. Wait for the update to start**

The soundbar display will show:

<badge color="info">UP</badge> **UP — Firmware update in progress**

This indicates that the firmware update is running.

> ⛔ Do not switch off, unplug or operate the soundbar while `UP` is displayed. Wait for the update to finish.

**6. Wait for the completion indicator**

When the update has finished, the display will show:

<badge color="success">SU</badge> **SU — Update completed**

**7. Disconnect the soundbar and USB drive**

Once `SU` appears:

- Unplug the soundbar from mains power.
- Remove the USB flash drive from the side USB port.

**8. Restart the soundbar**

Reconnect the soundbar to mains power and switch it on normally.

The soundbar should now boot using the updated firmware.

---

## 📊 Expected behaviour

| Behaviour | Official V01 | Alternative No-Lag | Custom |
|---|---|---|---|
| Initial audio delay | Present | Reduced | Expected to be minimised |
| First syllable cut | Possible | Mostly fixed | Expected to be avoided |
| Background hiss | After ~3.5 s of silence | Reported as constant | Expected after ~70 s of silence |
| Quiet audio passages | Muted after ~3.5 s | More sensitive | Retained for longer |
| Bootloader | Original | Original | Original |
| Threshold | 40 | 10 | 40 |

These are expected or previously reported behaviours. They are not measured results from a completed test of the custom firmware.

---

## 🧪 Post-update testing

After installing the firmware, perform the following tests:

- [ ] Confirm the soundbar boots normally.
- [ ] Test audio activation after several minutes of silence.
- [ ] Check whether the beginning of speech is still cut off.
- [ ] Test low-volume audio and quiet passages.
- [ ] Check for background hiss after 70 seconds of silence.
- [ ] Test repeated playback start/stop cycles.
- [ ] Test Bluetooth, optical and other available audio inputs.
- [ ] Confirm normal operation after a power cycle.

Record the results to establish whether the modification delivers the expected improvement.

---

## 📚 References

- 📝 Original technical article: https://blog.wasd.fi/en/posts/2025/10/creative-stage-v1-audio-lag-firmware-fix/
- 🏭 Creative Stage product support: https://support.creative.com/Products/ProductDetails.aspx?catID=4&subCatID=848&prodID=23279&prodName=Creative%20Stage

---

## ⚠️ Disclaimer

This project is an unofficial modification of Creative firmware. It is not affiliated with, endorsed by or supported by Creative Technology.

Use the modification at your own risk. Incorrect firmware, an interrupted update or an incompatible device revision may render the soundbar unusable.

Always retain an untouched backup of the original official firmware.

Do not redistribute Creative's original firmware or modified firmware binaries unless their redistribution terms permit it. The patching script and instructions allow users to generate their own modified image.

---

**Project status:** Binary modification generated and SHA-256 verified. Firmware installation procedure documented. Physical audio performance validation pending.
