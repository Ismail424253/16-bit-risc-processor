# 16-bit RISC Processor Simulator

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![GUI](https://img.shields.io/badge/GUI-PySide6-informational)

**16-bit RISC processor simulator with a 5-stage pipeline, hazard detection, and data forwarding.**  
Computer Organization Course — 2025/2026 Fall Semester

</div>

---

A MIPS-inspired 16-bit processor built from scratch. Has its own assembly language, assembler, and a PySide6 GUI where you can step through the pipeline cycle by cycle and watch everything happen in real time.

> There's also a hardware version running on a **Tang Nano 9K** FPGA with a live HDMI debug display. See [FPGA_README.md](FPGA_README.md).

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Instruction Set](#instruction-set)
- [Technical Specs](#technical-specs)
- [Project Structure](#project-structure)

---

## Features

| Feature | Description |
|---------|-------------|
| 16-bit datapath | All data and instructions are 16 bits wide |
| 8 registers | R0–R7, R0 is always 0, R7 is the link register |
| 512-byte memories | Separate instruction and data memory |
| 15 instructions + NOP | See full table below |
| Data forwarding | EX/MEM→EX and MEM/WB→EX |
| Hazard detection | Stall for load-use only; everything else forwarded |
| Step back | Full snapshot/restore — rewind to any previous cycle |
| Immediate mode | 6-bit immediate can be signed or unsigned (selectable) |

---

## Architecture

### Pipeline

```
┌──────┬──────┬──────┬──────┬──────┐
│  IF  │  ID  │  EX  │ MEM  │  WB  │
│Fetch │Decode│ ALU  │ Mem  │Write │
└──────┴──────┴──────┴──────┴──────┘
```

Pipeline registers: `IF/ID` → `ID/EX` → `EX/MEM` → `MEM/WB`

### Hazards

**Data forwarding** — no stall needed for most RAW hazards:
```asm
ADD R1, R2, R3   # result forwarded from EX/MEM
ADD R4, R1, R5   # gets R1 directly
```

**Load-use stall** — 1 cycle penalty:
```asm
LW  R1, 0(R0)    # result comes out of MEM
ADD R2, R1, R3   # R1 not ready yet → stall
```

**Branch/Jump flush** — 2-cycle penalty:
```asm
BEQ R1, R2, loop  # decided in EX stage
nop               # flushed
nop               # flushed
```

---

## Installation

Requires Python 3.8+.

```bash
pip install PySide6
python main.py
```

---

## Instruction Set

### Formats

```
R-type:  [opcode:4][rs:3][rt:3][rd:3][shamt:3]
I-type:  [opcode:4][rs:3][rt:3][immediate:6]
J-type:  [opcode:4][address:12]
```

### Instructions

| Mnemonic | Opcode | Type | Syntax | Operation |
|----------|--------|------|--------|-----------|
| `lw`   | `0x0` | I | `lw rt, imm(rs)` | `rt = mem[rs+imm]` |
| `sw`   | `0x1` | I | `sw rt, imm(rs)` | `mem[rs+imm] = rt` |
| `add`  | `0x2` | R | `add rd, rs, rt` | `rd = rs + rt` |
| `sub`  | `0x3` | R | `sub rd, rs, rt` | `rd = rs - rt` |
| `and`  | `0x4` | R | `and rd, rs, rt` | `rd = rs & rt` |
| `or`   | `0x5` | R | `or rd, rs, rt`  | `rd = rs \| rt` |
| `slt`  | `0x6` | R | `slt rd, rs, rt` | `rd = (rs < rt) ? 1 : 0` |
| `sll`  | `0x7` | R | `sll rd, rt, shamt` | `rd = rt << shamt` |
| `srl`  | `0x8` | R | `srl rd, rt, shamt` | `rd = rt >> shamt` |
| `addi` | `0x9` | I | `addi rt, rs, imm` | `rt = rs + imm` |
| `beq`  | `0xA` | I | `beq rs, rt, label` | branch if `rs == rt` |
| `bne`  | `0xB` | I | `bne rs, rt, label` | branch if `rs != rt` |
| `j`    | `0xC` | J | `j label` | `PC = label` |
| `jal`  | `0xD` | J | `jal label` | `R7 = PC+1; PC = label` |
| `jr`   | `0xE` | J | `jr rs` | `PC = rs` |
| `nop`  | `0xF` | R | `nop` | — |

> Immediate is 6-bit signed: **−32 to +31**. Out-of-range values throw an assembly error.

### Examples

```asm
# Fibonacci: fib(8)
    addi r1, r0, 0
    addi r2, r0, 1
    addi r4, r0, 8
loop:
    add  r3, r1, r2
    add  r1, r0, r2
    add  r2, r0, r3
    addi r4, r4, -1
    bne  r4, r0, loop
```

```asm
# Function call with JAL/JR
    jal  func
    ...
func:
    addi r1, r0, 42
    jr   r7
```

---

## Technical Specs

| | |
|-|-|
| Datapath | 16 bit |
| Instruction width | 16 bit |
| Registers | 8 (R0–R7) |
| Instruction memory | 512 bytes, word-aligned |
| Data memory | 512 bytes, little-endian, word-aligned |
| Immediate | 6-bit (signed or unsigned, selectable) |
| Branch resolution | EX stage (2-cycle penalty if taken) |
| Forwarding | EX/MEM→EX, MEM/WB→EX |
| Stall | Load-use only (1 cycle) |

---

## Project Structure

```
birdahadene/
├── main.py                  # Entry point
├── processor_backend.py     # Pipeline engine (Instruction, Memory, ALU, Processor...)
├── processor_frontend.py    # PySide6 GUI
├── theme.py                 # UI colors and styles
├── verify_encoding.py       # Encoding verification tool
├── README.md                # This file
└── FPGA_README.md           # Hardware implementation
```

---

## License

MIT
