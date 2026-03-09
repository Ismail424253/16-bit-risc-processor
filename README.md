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
# 16-bit RISC Processor — FPGA Implementation

<div align="center">

![FPGA](https://img.shields.io/badge/FPGA-Tang%20Nano%209K-orange)
![HDL](https://img.shields.io/badge/HDL-Verilog-blueviolet)
![Toolchain](https://img.shields.io/badge/Toolchain-Gowin%20IDE-blue)

**Hardware implementation of the 16-bit pipelined RISC processor on a Sipeed Tang Nano 9K FPGA.**  
Fully compatible with the Python simulator — same ISA, same opcode encoding.

</div>

---

The RTL version of the processor. Written in Verilog, synthesized with Gowin IDE, running on a Tang Nano 9K. Has a live HDMI debug display that shows the pipeline state every clock cycle.

> Python simulator docs: [README.md](README.md)

---

## Table of Contents

- [Hardware](#hardware)
- [Architecture](#architecture)
- [Modules](#modules)
- [Instruction Set](#instruction-set)
- [HDMI Debug Display](#hdmi-debug-display)
- [Build & Programming](#build--programming)
- [Project Structure](#project-structure)

---

## Hardware

| | |
|-|-|
| Board | Sipeed Tang Nano 9K |
| FPGA | Gowin GW1NR-LV9QN88PC6/I5 |
| Clock | 27 MHz → 125 MHz via PLL (for HDMI) |
| Debug output | HDMI (720p @ 60Hz) |
| Programming | Gowin Programmer, SRAM mode |

---

## Architecture

Same 5-stage pipeline as the Python simulator:

```
   ┌──────┐  IF/ID  ┌──────┐  ID/EX  ┌──────┐  EX/MEM  ┌──────┐  MEM/WB  ┌──────┐
   │  IF  │ ──────► │  ID  │ ──────► │  EX  │ ───────► │ MEM  │ ───────► │  WB  │
   └──────┘         └──────┘         └──────┘           └──────┘          └──────┘
                        │                ▲                   │
                  hazard_detect     forwarding             dmem
                        │             unit
                    stall/flush
```

### Hazard handling

| Hazard | How it's handled | Penalty |
|--------|-----------------|---------|
| Load-use | Freeze PC + IF/ID, bubble into ID/EX | 1 cycle |
| Branch taken / Jump | Resolved in EX, flush IF and IF/ID | 2 cycles |
| Other RAW hazards | Forward from EX/MEM or MEM/WB | 0 cycles |

---

## Modules

### Top level

| Module | File | Description |
|--------|------|-------------|
| `tangnano9k_top` | `tangnano9k_top.v` | Connects PLL, HDMI, and CPU |
| `cpu_top` | `cpu_top.v` | CPU wrapper — all pipeline stages wired here |

### Pipeline registers

| Module | File |
|--------|------|
| `if_id_register` | `pipeline_registers.v` |
| `id_ex_register` | `pipeline_registers.v` |
| `ex_mem_register` | `pipeline_registers.v` |
| `mem_wb_register` | `pipeline_registers.v` |

### Functional units

| Module | File | Description |
|--------|------|-------------|
| `control_unit` | `control_unit.v` | Opcode → control signals |
| `alu` | `alu.v` | 16-bit arithmetic/logic unit |
| `register_file` | `register_file.v` | 8 × 16-bit registers (R0 = 0 hardwired) |
| `instruction_memory` | `instruction_memory.v` | ROM, loaded from `program.hex` |
| `data_memory` | `data_memory.v` | Synchronous RAM |
| `forwarding_unit` | `forwarding_unit.v` | EX/MEM and MEM/WB forwarding mux control |
| `hazard_detection_unit` | `hazard_detection_unit.v` | Load-use stall detection |

### Debug / Display

| Module | File | Description |
|--------|------|-------------|
| `debug_hud` | `debug_hud.v` | Renders pipeline state as text on screen |
| `hdmi_top` | `hdmi_top.v` | HDMI signal generator (TMDS encoding) |
| `font_min` | `font_min.v` | Bitmap font ROM |
| `gowin_rpll` | `gowin_rpll/` | 27 MHz → 125 MHz PLL (Gowin IP) |

---

## Instruction Set

Defined in `defines.vh`, matches `processor_backend.py` exactly:

```verilog
`define OP_LW   4'h0   // I: lw  rt, imm(rs)
`define OP_SW   4'h1   // I: sw  rt, imm(rs)
`define OP_ADD  4'h2   // R: add rd, rs, rt
`define OP_SUB  4'h3   // R: sub rd, rs, rt
`define OP_AND  4'h4   // R: and rd, rs, rt
`define OP_OR   4'h5   // R: or  rd, rs, rt
`define OP_SLT  4'h6   // R: slt rd, rs, rt
`define OP_SLL  4'h7   // R: sll rd, rt, shamt
`define OP_SRL  4'h8   // R: srl rd, rt, shamt
`define OP_ADDI 4'h9   // I: addi rt, rs, imm
`define OP_BEQ  4'hA   // I: beq rs, rt, label
`define OP_BNE  4'hB   // I: bne rs, rt, label
`define OP_J    4'hC   // J: j   label
`define OP_JAL  4'hD   // J: jal label  (R7 = PC+1)
`define OP_JR   4'hE   // J: jr  rs
`define OP_NOP  4'hF   // nop
```

### Encoding

```
R-type: [15:12] opcode | [11:9] rs | [8:6] rt | [5:3] rd | [2:0] shamt
I-type: [15:12] opcode | [11:9] rs | [8:6] rt | [5:0] imm (6-bit signed)
J-type: [15:12] opcode | [11:0] address
```

> **SLL/SRL:** shifts `rt`, `rs` is unused.  
> **JR:** target register is in `rs` field (bits `[11:9]`).

### Control signals (`control_unit.v`)

| Signal | Width | Meaning |
|--------|-------|---------|
| `reg_write` | 1 | Write to register file |
| `mem_write` | 1 | Write to data memory (SW) |
| `mem_read` | 1 | Read from data memory (LW) |
| `mem_to_reg` | 2 | WB source: `00`=ALU, `01`=Mem, `10`=PC+1 |
| `reg_dst` | 2 | Destination reg: `00`=rt, `01`=rd, `10`=R7 |
| `alu_src` | 1 | ALU operand B: `0`=register, `1`=immediate |
| `branch` | 1 | Branch instruction |
| `jump` | 1 | J/JAL instruction |
| `jump_reg` | 1 | JR instruction |
| `alu_control` | 4 | ALU operation (matches opcode for R-type) |

---

## HDMI Debug Display

The FPGA outputs a 720p 60Hz HDMI signal showing the processor's live state every cycle:

```
┌──────────────────────────────────────────────────┐
│  PC: 0x0012        Cycle: 00134                  │
├──────────────────────────────────────────────────┤
│  IF: add r3,r1,r2   ID: lw r1,0(r0)             │
│  EX: addi r2,r0,5   MEM: ---    WB: sub r4...   │
├──────────────────────────────────────────────────┤
│  REGISTER FILE      │  DATA MEMORY              │
│  R0: 0x0000         │  [0x00]: 0x0042           │
│  R1: 0x0005  ← WB  │  [0x02]: 0x0100           │
└──────────────────────────────────────────────────┘
```

- Register/memory written in WB stage highlighted green
- White background, black text

### Clocking

```
27 MHz (crystal) → Gowin RPLL → 125 MHz → HDMI (ELVDS_OBUF)
```

---

## Build & Programming

### Requirements

- Gowin IDE v1.9.x
- Gowin Programmer (bundled with IDE)

### Build steps

1. Open Gowin IDE, load the `.gprj` project file
2. Make sure all `.v` and `.vh` files from `src/` are included
3. Pin constraints: `tangnano9k_top.cst`
4. Synthesize → Place & Route → Generate Bitstream

### Programming the board

1. Connect Tang Nano 9K via USB
2. Open Gowin Programmer
3. Device: `GW1NR-LV9QN88PC6/I5`
4. Mode: **SRAM Program** (volatile — clears on power off)
5. Select the `.fs` file → Program

### Loading a program

Generate hex from the Python simulator's assembler, put it in `src/program.hex`, then re-synthesize and reprogram.

---

## Project Structure

```
birdahadene/
├── verilog/                     # All Verilog/HDL source files
│   ├── defines.vh               # Opcode constants, bit positions
│   ├── tangnano9k_top.v         # Board top-level
│   ├── tangnano9k_top.cst       # Pin constraints
│   ├── cpu_top.v                # CPU wrapper
│   ├── processor_top.v          # Processor top-level
│   ├── pipeline_registers.v     # IF/ID, ID/EX, EX/MEM, MEM/WB
│   ├── control_unit.v           # Instruction decoder
│   ├── alu.v                    # ALU
│   ├── register_file.v          # Register file
│   ├── instruction_memory.v     # Instruction ROM
│   ├── data_memory.v            # Data RAM
│   ├── forwarding_unit.v        # Forwarding mux control
│   ├── hazard_detection_unit.v  # Stall detection
│   └── program.hex              # Loaded program
├── FPGA_README.md               # This file
└── README.md                    # Python simulator docs
```

---

## Status

| | |
|-|-|
| Synthesis | ✅ Clean |
| Place & Route | ✅ OK |
| HDMI output | ✅ Working (720p@60) |
| Pipeline execution | ✅ Verified against Python simulator |
| Branch prediction | ❌ None (flush-on-taken, 2-cycle penalty) |

---

## License

MIT
