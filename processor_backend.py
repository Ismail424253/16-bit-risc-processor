"""
16-bit RISC Processor Simulator - Backend
5-Stage Pipeline Architecture
Computer Architecture Course Project
"""

from typing import Dict, List, Optional, Tuple
import copy
import re

# Opcode mapping based on specification
OPCODE_MAP = {
    'lw': 0b0000,
    'sw': 0b0001,
    'add': 0b0010,
    'sub': 0b0011,
    'and': 0b0100,
    'or': 0b0101,
    'slt': 0b0110,
    'sll': 0b0111,
    'srl': 0b1000,
    'addi': 0b1001,
    'beq': 0b1010,
    'bne': 0b1011,
    'j': 0b1100,
    'jal': 0b1101,
    'jr': 0b1110,
    'nop': 0b1111  # Special case
}

# Reverse mapping for decoding
OPCODE_REVERSE = {v: k for k, v in OPCODE_MAP.items()}

# Instruction types
INSTRUCTION_TYPES = {
    # R-Type: opcode, rs, rt, rd, shamt
    'add': 'R', 'sub': 'R', 'and': 'R', 'or': 'R', 'slt': 'R', 
    'sll': 'R', 'srl': 'R',
    # I-Type: opcode, rs, rt, immediate
    'lw': 'I', 'sw': 'I', 'addi': 'I', 'beq': 'I', 'bne': 'I',
    # J-Type: opcode, target
    'j': 'J', 'jal': 'J', 'jr': 'J',
    'nop': 'R'
}

class Instruction:
    """Represents a single instruction with binary encoding"""
    def __init__(self, opcode: str, rd: int = 0, rs: int = 0, rt: int = 0, 
                 imm: int = 0, shamt: int = 0, address: int = 0, label: str = None):
        self.opcode = opcode
        self.rd = rd  # destination register (3 bits)
        self.rs = rs  # source register 1 (3 bits)
        self.rt = rt  # source register 2 (3 bits)
        self.imm = imm  # immediate value (6 bits for I-Type)
        self.shamt = shamt  # shift amount (3 bits)
        self.address = address  # jump address (12 bits for J-Type)
        self.label = label  # label name for branches/jumps (for display only)
        self.pc = 0  # program counter when fetched
        self.binary = self.encode()  # 16-bit binary encoding
    
    def encode(self) -> int:
        """Encode instruction to 16-bit binary format"""
        opcode_bits = OPCODE_MAP.get(self.opcode, 0) & 0xF  # 4 bits
        inst_type = INSTRUCTION_TYPES.get(self.opcode, 'R')
        
        if inst_type == 'R':
            # R-Type: [opcode-4][rs-3][rt-3][rd-3][shamt-3] = 16 bits
            binary = (opcode_bits << 12) | \
                     ((self.rs & 0x7) << 9) | \
                     ((self.rt & 0x7) << 6) | \
                     ((self.rd & 0x7) << 3) | \
                     (self.shamt & 0x7)
        elif inst_type == 'I':
            # I-Type: [opcode-4][rs-3][rt-3][immediate-6] = 16 bits
            binary = (opcode_bits << 12) | \
                     ((self.rs & 0x7) << 9) | \
                     ((self.rt & 0x7) << 6) | \
                     (self.imm & 0x3F)  # 6-bit immediate
        elif inst_type == 'J':
            # J-Type: [opcode-4][target-12] = 16 bits
            if self.opcode == 'jr':
                # jr uses rs field in lower bits
                binary = (opcode_bits << 12) | ((self.rs & 0x7) << 9)
            else:
                binary = (opcode_bits << 12) | (self.address & 0xFFF)
        else:
            binary = 0
        
        return binary & 0xFFFF
    
    @staticmethod
    def decode(binary: int) -> 'Instruction':
        """Decode 16-bit binary to instruction"""
        opcode_bits = (binary >> 12) & 0xF
        opcode = OPCODE_REVERSE.get(opcode_bits, 'nop')
        inst_type = INSTRUCTION_TYPES.get(opcode, 'R')
        
        if inst_type == 'R':
            rs = (binary >> 9) & 0x7
            rt = (binary >> 6) & 0x7
            rd = (binary >> 3) & 0x7
            shamt = binary & 0x7
            return Instruction(opcode, rd=rd, rs=rs, rt=rt, shamt=shamt)
        elif inst_type == 'I':
            rs = (binary >> 9) & 0x7
            rt = (binary >> 6) & 0x7
            imm = binary & 0x3F
            # Sign extend 6-bit immediate to 16-bit
            if imm & 0x20:  # if bit 5 is set
                imm = imm | 0xFFC0
            return Instruction(opcode, rs=rs, rt=rt, imm=imm)
        elif inst_type == 'J':
            if opcode == 'jr':
                rs = (binary >> 9) & 0x7
                return Instruction(opcode, rs=rs)
            else:
                address = binary & 0xFFF
                return Instruction(opcode, address=address)
        
        return Instruction('nop')
    
    def get_binary_string(self) -> str:
        """Get formatted binary string representation"""
        return f"{self.binary:016b}"
    
    def get_hex_string(self) -> str:
        """Get hexadecimal string representation"""
        return f"0x{self.binary:04X}"
        
    def __str__(self):
        """String representation with register names"""
        if self.opcode in ['add', 'sub', 'and', 'or', 'slt']:
            return f"{self.opcode} $r{self.rd}, $r{self.rs}, $r{self.rt}"
        elif self.opcode in ['sll', 'srl']:
            return f"{self.opcode} $r{self.rd}, $r{self.rt}, {self.shamt}"
        elif self.opcode == 'addi':
            # Convert 6-bit unsigned to signed for display
            imm_val = self.imm if self.imm < 32 else self.imm - 64
            return f"{self.opcode} $r{self.rt}, $r{self.rs}, {imm_val}"
        elif self.opcode in ['lw', 'sw']:
            imm_val = self.imm if self.imm < 32 else self.imm - 64
            return f"{self.opcode} $r{self.rt}, {imm_val}($r{self.rs})"
        elif self.opcode in ['beq', 'bne']:
            # Eğer etiket varsa onu göster, yoksa sayısal offset'i göster
            if self.label:
                target = self.label
            else:
                target = self.imm if self.imm < 32 else self.imm - 64
            return f"{self.opcode} $r{self.rs}, $r{self.rt}, {target}"
        elif self.opcode in ['j', 'jal']:
            # Eğer etiket varsa onu göster, yoksa adresi göster
            target = self.label if self.label else self.address
            return f"{self.opcode} {target}"
        elif self.opcode == 'jr':
            return f"{self.opcode} $r{self.rs}"
        elif self.opcode == 'nop':
            return "nop"
        return "unknown"
    
    def get_detailed_string(self) -> str:
        """Get detailed string with binary and hex representation"""
        return f"{str(self):30s} | Binary: {self.get_binary_string()} | Hex: {self.get_hex_string()}"


class RegisterFile:
    """8 general-purpose 16-bit registers"""
    def __init__(self):
        self.registers = [0] * 8  # R0-R7
        
    def read(self, reg_num: int) -> int:
        if 0 <= reg_num < 8:
            return self.registers[reg_num] & 0xFFFF
        return 0
    
    def write(self, reg_num: int, value: int):
        if 0 < reg_num < 8:  # R0 is typically read-only (always 0)
            self.registers[reg_num] = value & 0xFFFF
            
    def reset(self):
        self.registers = [0] * 8


class Memory:
    """Memory module (512 bytes)"""
    def __init__(self, size: int = 512):
        self.size = size
        self.data = [0] * size
        self.touched_words = set()  # Track word-aligned addresses that have been written
        
    def read_word(self, address: int) -> int:
        """Read 16-bit word (little endian)
        
        Auto-aligns address to even boundary (word-aligned).
        
        Raises:
            ValueError: If address is out of bounds
        """
        # Auto-align to word boundary (floor division)
        address = (address // 2) * 2
        
        if address < 0 or address > self.size - 2:
            raise ValueError(
                f"Memory address out of range: {address}. Valid byte range: 0..{self.size-2}"
            )
        
        low = self.data[address]
        high = self.data[address + 1]
        return (high << 8) | low
    
    def write_word(self, address: int, value: int):
        """Write 16-bit word (little endian)
        
        Auto-aligns address to even boundary (word-aligned).
        
        Raises:
            ValueError: If address is out of bounds
        """
        # Auto-align to word boundary (floor division)
        address = (address // 2) * 2
        
        if address < 0 or address > self.size - 2:
            raise ValueError(
                f"Memory address out of range: {address}. Valid byte range: 0..{self.size-2}"
            )
        
        self.data[address] = value & 0xFF
        self.data[address + 1] = (value >> 8) & 0xFF
        # Track touched word-aligned address (auto-aligned to even)
        self.touched_words.add(address)
            
    def reset(self):
        self.data = [0] * self.size
        self.touched_words.clear()


class ALU:
    """Arithmetic Logic Unit"""
    @staticmethod
    def execute(operation: str, operand1: int, operand2: int) -> int:
        operand1 = operand1 & 0xFFFF
        operand2 = operand2 & 0xFFFF
        
        # Convert to signed for operations that need it
        def to_signed(val):
            if val & 0x8000:
                return val - 0x10000
            return val
        
        if operation == 'add' or operation == 'addi':
            result = operand1 + operand2
        elif operation == 'sub':
            result = operand1 - operand2
        elif operation == 'and':
            result = operand1 & operand2
        elif operation == 'or':
            result = operand1 | operand2
        elif operation == 'slt':
            result = 1 if to_signed(operand1) < to_signed(operand2) else 0
        elif operation == 'sll':
            result = operand1 << operand2
        elif operation == 'srl':
            result = operand1 >> operand2
        else:
            result = 0
            
        return result & 0xFFFF


class PipelineRegister:
    """Register between pipeline stages"""
    def __init__(self):
        self.instruction = None
        self.data = {}
        self.stall = False
        self.flush = False
        self.is_bubble = False  # True when this is a flushed/squashed instruction (bubble)
        
    def reset(self):
        self.instruction = None
        self.data = {}
        self.stall = False
        self.flush = False
        self.is_bubble = False


class HazardUnit:
    """Detects and resolves hazards"""
    def __init__(self):
        self.data_hazards = []
        self.control_hazards = []
        self.stall_needed = False
        self.forward_ex_ex = False
        self.forward_mem_ex = False
        
    def detect_data_hazard(self, id_ex: PipelineRegister, ex_mem: PipelineRegister, 
                          mem_wb: PipelineRegister, current_inst: Optional[Instruction]) -> Tuple[bool, List[Dict]]:
        """
        Detect RAW (Read After Write) data hazards.
        
        FIX: Only report STALLS here. 
        Forwarding is reported by Processor.execute() when it actually happens.
        This prevents double-counting in the UI.
        """
        hazards: List[Dict] = []
        stall = False
        
        if not current_inst:
            return False, hazards
        
        # === 1. Check for load-use hazard (need to stall) ===
        # Only ID/EX stage LW can cause a load-use stall
        if id_ex.instruction and not id_ex.flush and id_ex.instruction.opcode == 'lw':
            lw_dest = id_ex.instruction.rt  # LW writes to rt
            if current_inst.opcode != 'nop' and lw_dest != 0:
                # Check if current instruction needs lw_dest as a source operand
                needs_rs = hasattr(current_inst, 'rs') and current_inst.rs == lw_dest
                
                # RT is a source operand for: R-type (add, sub, and, or, slt), shifts (sll, srl), branches, SW
                needs_rt = (hasattr(current_inst, 'rt') and current_inst.rt == lw_dest and 
                           current_inst.opcode in ['add', 'sub', 'and', 'or', 'slt', 'sll', 'srl', 'beq', 'bne', 'sw'])
                
                if needs_rs or needs_rt:
                    which_operand = []
                    if needs_rs:
                        which_operand.append("rs")
                    if needs_rt:
                        which_operand.append("rt")
                    operand_str = "/".join(which_operand)
                    stall = True
                    hazards.append({
                        'stage': 'ID/EX',
                        'type': 'Data Hazard (Load-Use)',
                        'status': 'Stall',
                        'reason': f"Need $r{lw_dest} for {operand_str} (lw in EX)"
                    })
        
        # Forwarding detection logic removed from here because Processor.execute 
        # already logs forwarding events. This prevents duplicate entries in the UI.
        
        return stall, hazards
    
    def detect_control_hazard(self, instruction: Optional[Instruction]) -> Optional[Dict]:
        """
        Control hazards are handled in EX when the branch/jump decision is known.
        We do NOT report speculative control hazards here (matches modern_simulator.py behavior).
        """
        return None


class Processor:
    """16-bit RISC Processor with 5-stage pipeline"""
    def __init__(self):
        self.pc = 0  # Program Counter
        self.registers = RegisterFile()
        self.instruction_memory = Memory(512)
        self.data_memory = Memory(512)
        self.alu = ALU()
        self.hazard_unit = HazardUnit()
        
        # Pipeline registers
        self.if_id = PipelineRegister()
        self.id_ex = PipelineRegister()
        self.ex_mem = PipelineRegister()
        self.mem_wb = PipelineRegister()
        
        # Pipeline stage contents (for visualization)
        self.stage_if = None
        self.stage_id = None
        self.stage_ex = None
        self.stage_mem = None
        self.stage_wb = None
        
        self.instructions = []
        self.cycle_count = 0
        self.instruction_count = 0
        # Dynamic (retired) instruction count (excludes NOP and flushed instructions)
        self.retired_count = 0
        self.stall_count = 0
        self.flush_count = 0
        self.forward_count = 0
        self.halted = False

        # Dynamic branch/jump stats (counted when reaching EX stage)
        self.branch_executed_count = 0
        self.branch_taken_count = 0
        
        # For hazard visualization
        self.current_hazards = []
        
        # Last per-instruction effects (for trace/UI)
        self.last_wb_event = None   # {"reg":int,"value":int}
        # {"type":"LW"/"SW","addr":int,"value":int} (also carries 'kind' for existing trace)
        self.last_mem_event = None
        
        # Trace-only bookkeeping (does not affect execution)
        self.last_cycle_stall = False
        self.last_cycle_flush = False
        self.last_reg_write_delta = None  # {'reg': int, 'old': int, 'new': int}
        self.trace_last_stages = {'IF': None, 'ID': None, 'EX': None, 'MEM': None, 'WB': None}
        
        # Validation error state (for strict validation with fail-fast)
        self.validation_error: Optional[str] = None
        self.has_validation_error: bool = False
        
        # Immediate mode: "signed" (default) or "unsigned"
        # Controls how 6-bit immediates are extended in ADDI, LW, SW
        # Branches (beq/bne) always remain signed
        self.imm_mode = "signed"
        
        # Track last written register for UI highlighting
        self.last_written_register = -1
    
    def set_imm_mode(self, mode: str):
        """Set immediate interpretation mode: 'signed' or 'unsigned'"""
        if mode not in ["signed", "unsigned"]:
            raise ValueError(f"Invalid immediate mode: {mode}. Must be 'signed' or 'unsigned'.")
        self.imm_mode = mode
    
    def extend_imm6(self, imm6: int, *, signed: bool) -> int:
        """Extend 6-bit immediate to 16-bit
        
        Args:
            imm6: 6-bit immediate value (0-63)
            signed: If True, sign-extend; if False, zero-extend
        
        Returns:
            16-bit extended value
        """
        imm6 &= 0x3F  # Ensure 6-bit
        if signed and (imm6 & 0x20):  # Check sign bit (bit 5)
            return imm6 | 0xFFC0  # Sign extend to 16-bit
        return imm6  # Zero extend (just use as-is)
    
    def set_validation_error(self, message: str):
        """Set validation error state and store error message
        
        This is called when:
        - Assembly fails (invalid immediate, out of range branch offset, etc.)
        - Runtime error occurs (memory access out of bounds, etc.)
        
        Args:
            message: Detailed error message describing what went wrong
        """
        self.validation_error = message
        self.has_validation_error = True
    
    def clear_validation_error(self):
        """Clear validation error state
        
        This is called when:
        - Starting a new assembly (before parse)
        - Resetting the processor
        """
        self.validation_error = None
        self.has_validation_error = False
        
    def load_program(self, instructions: List[Instruction]):
        """Load instructions into instruction memory"""
        self.instructions = instructions
        self.instruction_count = len(instructions)
        self.reset()
        
        # Print loaded program
        print("\n" + "="*80)
        print("PROGRAM LOADED INTO INSTRUCTION MEMORY")
        print("="*80)
        print(f"Total Instructions: {len(instructions)}\n")
        for i, inst in enumerate(instructions):
            print(f"  [{i:3d}] {str(inst):40s} | {inst.get_binary_string()} | {inst.get_hex_string()}")
        print("="*80 + "\n")
        
    def reset(self):
        """Reset processor state"""
        self.pc = 0
        self.registers.reset()
        self.data_memory.reset()
        
        # Reset Pipeline Registers
        self.if_id.reset()
        self.id_ex.reset()
        self.ex_mem.reset()
        self.mem_wb.reset()
        
        # CRITICAL FIX: Reset Stage Visualization Variables
        # This ensures the GUI cards clear out and show "Empty"
        self.stage_if = None
        self.stage_id = None
        self.stage_ex = None
        self.stage_mem = None
        self.stage_wb = None
        
        self.cycle_count = 0
        self.stall_count = 0
        self.flush_count = 0
        self.forward_count = 0
        self.retired_count = 0
        self.branch_executed_count = 0
        self.branch_taken_count = 0
        self.halted = False
        self.current_hazards = []
        self.last_wb_event = None
        self.last_mem_event = None
        self.last_cycle_stall = False
        self.last_cycle_flush = False
        self.last_reg_write_delta = None
        self.trace_last_stages = {'IF': None, 'ID': None, 'EX': None, 'MEM': None, 'WB': None}
        self.last_written_register = -1
        
        # CRITICAL FIX: Reset drain_cycles attribute (for pipeline drain logic)
        # Without this, second program run would immediately halt!
        if hasattr(self, 'drain_cycles'):
            delattr(self, 'drain_cycles')

    def snapshot_state(self) -> dict:
        """
        Return a deep snapshot of the current processor state.
        Instruction memory / program list is treated as read-only and excluded.
        """
        snap: dict = {}

        # Core control state
        snap["pc"] = self.pc
        snap["cycle_count"] = self.cycle_count
        snap["halted"] = self.halted

        # Architectural state
        snap["registers"] = copy.deepcopy(self.registers)
        snap["data_memory"] = copy.deepcopy(self.data_memory)

        # Pipeline registers + stage visualization
        snap["if_id"] = copy.deepcopy(self.if_id)
        snap["id_ex"] = copy.deepcopy(self.id_ex)
        snap["ex_mem"] = copy.deepcopy(self.ex_mem)
        snap["mem_wb"] = copy.deepcopy(self.mem_wb)

        snap["stage_if"] = copy.deepcopy(self.stage_if)
        snap["stage_id"] = copy.deepcopy(self.stage_id)
        snap["stage_ex"] = copy.deepcopy(self.stage_ex)
        snap["stage_mem"] = copy.deepcopy(self.stage_mem)
        snap["stage_wb"] = copy.deepcopy(self.stage_wb)

        # Hazards / metrics
        snap["current_hazards"] = copy.deepcopy(self.current_hazards)
        snap["last_written_register"] = self.last_written_register
        snap["forward_count"] = self.forward_count
        snap["stall_count"] = self.stall_count
        snap["flush_count"] = self.flush_count
        snap["retired_count"] = self.retired_count
        snap["branch_executed_count"] = self.branch_executed_count
        snap["branch_taken_count"] = self.branch_taken_count

        # Last events (used by trace output)
        snap["instruction_count"] = self.instruction_count
        snap["last_wb_event"] = copy.deepcopy(getattr(self, "last_wb_event", None))
        snap["last_mem_event"] = copy.deepcopy(getattr(self, "last_mem_event", None))

        # Trace-only bookkeeping (does not affect execution, but affects UI/output)
        snap["last_cycle_stall"] = getattr(self, "last_cycle_stall", False)
        snap["last_cycle_flush"] = getattr(self, "last_cycle_flush", False)
        snap["last_reg_write_delta"] = copy.deepcopy(getattr(self, "last_reg_write_delta", None))
        snap["trace_last_stages"] = copy.deepcopy(getattr(self, "trace_last_stages", None))

        # HazardUnit internal flags (safe to snapshot for exact restore)
        snap["hazard_unit"] = copy.deepcopy(getattr(self, "hazard_unit", None))

        # --- DÜZELTME: Pipeline drain durumunu kaydet ---
        # Bu sayede Step Back yaptığımızda drain_cycles değeri doğru geri yüklenir
        if hasattr(self, 'drain_cycles'):
            snap["drain_cycles"] = self.drain_cycles

        return snap

    def restore_state(self, snap: dict) -> None:
        """Restore processor state from snapshot."""
        # Core control state
        self.pc = snap["pc"]
        self.cycle_count = snap["cycle_count"]
        self.halted = snap["halted"]

        # Architectural state
        self.registers = copy.deepcopy(snap["registers"])
        self.data_memory = copy.deepcopy(snap["data_memory"])

        # Pipeline registers + stage visualization
        self.if_id = copy.deepcopy(snap["if_id"])
        self.id_ex = copy.deepcopy(snap["id_ex"])
        self.ex_mem = copy.deepcopy(snap["ex_mem"])
        self.mem_wb = copy.deepcopy(snap["mem_wb"])

        self.stage_if = copy.deepcopy(snap["stage_if"])
        self.stage_id = copy.deepcopy(snap["stage_id"])
        self.stage_ex = copy.deepcopy(snap["stage_ex"])
        self.stage_mem = copy.deepcopy(snap["stage_mem"])
        self.stage_wb = copy.deepcopy(snap["stage_wb"])

        # Hazards / metrics
        self.current_hazards = copy.deepcopy(snap["current_hazards"])
        self.last_written_register = snap["last_written_register"]
        self.forward_count = snap["forward_count"]
        self.stall_count = snap["stall_count"]
        self.flush_count = snap["flush_count"]
        self.retired_count = snap.get("retired_count", 0)
        self.branch_executed_count = snap.get("branch_executed_count", 0)
        self.branch_taken_count = snap.get("branch_taken_count", 0)

        # Last events (used by trace output)
        self.instruction_count = snap.get("instruction_count", self.instruction_count)
        self.last_wb_event = copy.deepcopy(snap.get("last_wb_event", None))
        self.last_mem_event = copy.deepcopy(snap.get("last_mem_event", None))

        # Trace-only bookkeeping
        self.last_cycle_stall = snap.get("last_cycle_stall", False)
        self.last_cycle_flush = snap.get("last_cycle_flush", False)
        self.last_reg_write_delta = copy.deepcopy(snap.get("last_reg_write_delta", None))
        self.trace_last_stages = copy.deepcopy(snap.get("trace_last_stages", None))

        # HazardUnit internal flags
        if "hazard_unit" in snap:
            self.hazard_unit = copy.deepcopy(snap["hazard_unit"])

        # --- DÜZELTME: Pipeline drain durumunu geri yükle veya sil ---
        # Eğer snapshot'ta drain_cycles varsa, o değeri geri yükle
        # Yoksa ve şu an işlemcide varsa (gelecekten geçmişe döndüysek), sil
        if "drain_cycles" in snap:
            self.drain_cycles = snap["drain_cycles"]
        elif hasattr(self, 'drain_cycles'):
            # Eğer snapshot'ta drain yoksa ama şu an işlemcide varsa (yani gelecekten geçmişe döndüysek)
            # bu özelliği silmemiz gerekir.
            delattr(self, 'drain_cycles')
        
    def fetch(self):
        """IF Stage: Instruction Fetch"""
        if self.halted or self.pc >= len(self.instructions):
            self.stage_if = None
            return None
        
        # IMPORTANT: clone the instruction object so .pc is stable per in-flight instance
        instruction = copy.copy(self.instructions[self.pc])
        instruction.pc = self.pc
        self.stage_if = instruction
        return instruction
    
    def decode(self, instruction: Optional[Instruction]):
        """ID Stage: Instruction Decode"""
        if not instruction or instruction.opcode == 'nop':
            self.stage_id = None
            return None, 0, 0
        
        self.stage_id = instruction
        
        # Read registers
        rs_value = self.registers.read(instruction.rs)
        rt_value = self.registers.read(instruction.rt)
        
        return instruction, rs_value, rt_value
    
    def execute(self, instruction: Optional[Instruction], rs_value: int, rt_value: int):
        """EX Stage: Execute - Uses CURRENT (stable) pipeline registers for forwarding"""
        if not instruction or instruction.opcode == 'nop':
            self.stage_ex = None
            return None, 0
        
        self.stage_ex = instruction
        
        # Forwarding logic - Standard MIPS forwarding with proper priority
        # Priority: EX/MEM (Distance 1) > MEM/WB (Distance 2) > Register File
        # CRITICAL: Uses CURRENT self.ex_mem and self.mem_wb (not next_* versions)
        
        # Determine destination registers for forwarding sources
        ex_mem_dest = -1
        mem_wb_dest = -1
        
        if self.ex_mem.instruction and 'alu_result' in self.ex_mem.data:
            ex_mem_dest = self.ex_mem.instruction.rd if self.ex_mem.instruction.opcode not in ['lw', 'addi'] else self.ex_mem.instruction.rt
        
        if self.mem_wb.instruction and 'write_data' in self.mem_wb.data:
            mem_wb_dest = self.mem_wb.instruction.rd if self.mem_wb.instruction.opcode not in ['lw', 'addi'] else self.mem_wb.instruction.rt
        
        # Determine forwarding paths
        
        # Forward RS operand (with priority: EX/MEM > MEM/WB)
        if ex_mem_dest != -1 and ex_mem_dest != 0 and instruction.rs == ex_mem_dest:
            # Forward from EX/MEM (Distance 1 - most recent)
            old_rs = rs_value
            rs_value = self.ex_mem.data['alu_result']
            self.forward_count += 1
            # Add to current_hazards for GUI
            self.current_hazards.append({
                "stage": "EX",
                "type": "Data Hazard (Forwarding)",
                "status": "Forward",
                "reason": f"Forward $r{instruction.rs} to rs (from EX/MEM)"
            })
        elif mem_wb_dest != -1 and mem_wb_dest != 0 and instruction.rs == mem_wb_dest:
            # Forward from MEM/WB (Distance 2) only if EX/MEM doesn't match
            old_rs = rs_value
            rs_value = self.mem_wb.data['write_data']
            self.forward_count += 1
            # Add to current_hazards for GUI
            self.current_hazards.append({
                "stage": "EX",
                "type": "Data Hazard (Forwarding)",
                "status": "Forward",
                "reason": f"Forward $r{instruction.rs} to rs (from MEM/WB)"
            })
        
        # Forward RT operand (with priority: EX/MEM > MEM/WB)
        # rt is used as source in: R-type (add, sub, and, or, slt, sll, srl), beq, bne, sw
        rt_is_source = instruction.opcode in ['add', 'sub', 'and', 'or', 'slt', 'sll', 'srl', 'beq', 'bne', 'sw']
        
        if rt_is_source:
            if ex_mem_dest != -1 and ex_mem_dest != 0 and instruction.rt == ex_mem_dest:
                # Forward from EX/MEM (Distance 1 - most recent)
                old_rt = rt_value
                rt_value = self.ex_mem.data['alu_result']
                self.forward_count += 1
                # Add to current_hazards for GUI
                self.current_hazards.append({
                    "stage": "EX",
                    "type": "Data Hazard (Forwarding)",
                    "status": "Forward",
                    "reason": f"Forward $r{instruction.rt} to rt (from EX/MEM)"
                })
            elif mem_wb_dest != -1 and mem_wb_dest != 0 and instruction.rt == mem_wb_dest:
                # Forward from MEM/WB (Distance 2) only if EX/MEM doesn't match
                old_rt = rt_value
                rt_value = self.mem_wb.data['write_data']
                self.forward_count += 1
                # Add to current_hazards for GUI
                self.current_hazards.append({
                    "stage": "EX",
                    "type": "Data Hazard (Forwarding)",
                    "status": "Forward",
                    "reason": f"Forward $r{instruction.rt} to rt (from MEM/WB)"
                })
        
        alu_result = 0
        
        # ALU operations
        if instruction.opcode in ['add', 'sub', 'and', 'or', 'slt']:
            alu_result = self.alu.execute(instruction.opcode, rs_value, rt_value)
        elif instruction.opcode == 'addi':
            # Extend 6-bit immediate based on current mode
            # For ADDI, respect processor's immediate mode
            use_signed = (self.imm_mode == "signed")
            imm = self.extend_imm6(instruction.imm, signed=use_signed)
            alu_result = self.alu.execute('add', rs_value, imm)
        elif instruction.opcode == 'sll':
            alu_result = self.alu.execute('sll', rt_value, instruction.shamt)
        elif instruction.opcode == 'srl':
            alu_result = self.alu.execute('srl', rt_value, instruction.shamt)
        elif instruction.opcode in ['lw', 'sw']:
            # Calculate memory address with extended immediate
            # For LW/SW, respect processor's immediate mode
            use_signed = (self.imm_mode == "signed")
            imm = self.extend_imm6(instruction.imm, signed=use_signed)
            alu_result = (rs_value + imm) & 0xFFFF
        elif instruction.opcode in ['beq', 'bne']:
            # Branch decision
            alu_result = 1 if rs_value == rt_value else 0
        
        # For sw, we need to pass rt_value (with forwarding applied) to MEM stage
        if instruction.opcode == 'sw':
            return instruction, alu_result, rt_value
            
        return instruction, alu_result
    
    def memory_access(self, instruction: Optional[Instruction], alu_result: int):
        """MEM Stage: Memory Access"""
        if not instruction or instruction.opcode == 'nop':
            self.stage_mem = None
            self.last_mem_event = None
            return None, 0
        
        self.stage_mem = instruction
        
        mem_data = alu_result
        
        if instruction.opcode == 'lw':
            mem_data = self.data_memory.read_word(alu_result)
            self.last_mem_event = {
                'type': 'LW',
                'kind': 'READ',
                'addr': alu_result & 0xFFFF,
                'value': mem_data & 0xFFFF
            }
            # Attach to instruction for retirement summary
            setattr(instruction, '_trace_mem_event', dict(self.last_mem_event))
        elif instruction.opcode == 'sw':
            # Get store data from EX/MEM register (already forwarded in EX stage)
            store_data = self.ex_mem.data.get('store_data', 0)
            self.data_memory.write_word(alu_result, store_data)
            self.last_mem_event = {
                'type': 'SW',
                'kind': 'WRITE',
                'addr': alu_result & 0xFFFF,
                'value': store_data & 0xFFFF
            }
            # Attach to instruction for retirement summary
            setattr(instruction, '_trace_mem_event', dict(self.last_mem_event))
        else:
            self.last_mem_event = None
            
        return instruction, mem_data
    
    def writeback(self, instruction: Optional[Instruction], write_data: int):
        """WB Stage: Write Back"""
        if not instruction or instruction.opcode == 'nop':
            self.stage_wb = None
            # CHANGED: Don't clear last_written_register - keep highlight persistent!
            # self.last_written_register = -1  # ← Removed
            self.last_reg_write_delta = None
            self.last_wb_event = None
            return
        
        self.stage_wb = instruction
        self.last_reg_write_delta = None
        self.last_wb_event = None
        
        if instruction.opcode in ['add', 'sub', 'and', 'or', 'slt', 'sll', 'srl']:
            old_val = self.registers.read(instruction.rd)
            self.registers.write(instruction.rd, write_data)
            self.last_written_register = instruction.rd
            new_val = self.registers.read(instruction.rd)
            self.last_reg_write_delta = {'reg': instruction.rd, 'old': old_val, 'new': new_val}
            self.last_wb_event = {'reg': instruction.rd, 'value': write_data & 0xFFFF}
            setattr(instruction, '_trace_wb_event', dict(self.last_wb_event))
        elif instruction.opcode in ['addi', 'lw']:
            old_val = self.registers.read(instruction.rt)
            self.registers.write(instruction.rt, write_data)
            self.last_written_register = instruction.rt
            new_val = self.registers.read(instruction.rt)
            self.last_reg_write_delta = {'reg': instruction.rt, 'old': old_val, 'new': new_val}
            self.last_wb_event = {'reg': instruction.rt, 'value': write_data & 0xFFFF}
            setattr(instruction, '_trace_wb_event', dict(self.last_wb_event))
        elif instruction.opcode == 'jal':
            # Store return address in R7
            old_val = self.registers.read(7)
            self.registers.write(7, instruction.pc + 1)
            self.last_written_register = 7
            new_val = self.registers.read(7)
            self.last_reg_write_delta = {'reg': 7, 'old': old_val, 'new': new_val}
            self.last_wb_event = {'reg': 7, 'value': (instruction.pc + 1) & 0xFFFF}
            setattr(instruction, '_trace_wb_event', dict(self.last_wb_event))
        else:
            # CHANGED: Don't clear last_written_register for non-writing instructions
            # Keep the highlight on the last written register until a new one is written
            # self.last_written_register = -1  # ← Removed
            self.last_reg_write_delta = None
            self.last_wb_event = None

        # Ensure last_mem_event reflects this instruction's effects (if any)
        if instruction.opcode != 'nop':
            inst_mem = getattr(instruction, '_trace_mem_event', None)
            if inst_mem:
                self.last_mem_event = inst_mem
    
    def to_signed16(self, x: int) -> int:
        x &= 0xFFFF
        return x if x < 0x8000 else x - 0x10000

    def format_cycle_compact(self) -> str:
        """Balanced compact cycle output (2–3 lines + separator)."""
        def fmt_inst(inst: Optional[Instruction]) -> str:
            return "NOP" if not inst or inst.opcode == 'nop' else str(inst)

        # Line 1 — Header
        cycle = self.cycle_count
        pc_val = self.pc & 0xFFFF
        line1 = f"C{cycle}  PC=0x{pc_val:04X} ({self.to_signed16(pc_val)})"

        # Line 2 — Pipeline stages
        line2 = (
            f"IF: {fmt_inst(self.stage_if)} | "
            f"ID: {fmt_inst(self.stage_id)} | "
            f"EX: {fmt_inst(self.stage_ex)} | "
            f"MEM: {fmt_inst(self.stage_mem)} | "
            f"WB: {fmt_inst(self.stage_wb)}"
        )

        # Line 3 — Events (only if any exist)
        events: List[str] = []

        # RW
        if self.last_written_register != -1:
            reg = self.last_written_register
            val = self.registers.read(reg)
            events.append(f"RW: r{reg}<-0x{val & 0xFFFF:04X} ({self.to_signed16(val)})")

        # MEM (based on current MEM/WB register contents for this cycle)
        mw_inst = self.mem_wb.instruction
        mw_data = self.mem_wb.data or {}
        addr = mw_data.get('alu_result', None)
        if mw_inst and mw_inst.opcode in ['lw', 'sw'] and addr is not None:
            if mw_inst.opcode == 'lw':
                val = mw_data.get('write_data', None)
                if val is not None:
                    events.append(
                        f"MEM: R[0x{addr & 0xFFFF:04X} ({self.to_signed16(addr)})] = "
                        f"0x{val & 0xFFFF:04X} ({self.to_signed16(val)})"
                    )
            elif mw_inst.opcode == 'sw':
                sval = mw_data.get('store_data', None)
                if sval is not None:
                    events.append(
                        f"MEM: W[0x{addr & 0xFFFF:04X} ({self.to_signed16(addr)})] = "
                        f"0x{sval & 0xFFFF:04X} ({self.to_signed16(sval)})"
                    )

        # HZ (unchanged hazard text)
        if self.current_hazards:
            parts: List[str] = []
            for hz in self.current_hazards:
                if isinstance(hz, dict):
                    status = hz.get('status', '')
                    reason = hz.get('reason', '')
                    token = status
                    if reason:
                        token = f"{status} | {reason}"
                    parts.append(token.strip())
                else:
                    parts.append(str(hz).strip())

            if len(parts) > 2:
                parts = parts[:2] + ["..."]
            hz_text = "; ".join(parts) if parts else "-"
            events.append(f"HZ: {hz_text}")

        lines = [line1, line2]
        if events:
            lines.append(" | ".join(events))
        lines.append("────────────────────────")
        return "\n".join(lines)

    def format_cycle_trace_pretty(self) -> str:
        """Pretty, structured pipeline trace for the current cycle (formatting only)."""

        
        def fmt_hex_dec(x: int) -> str:
            x &= 0xFFFF
            return f"0x{x:04X} ({self.to_signed16(x)})"

        def fmt_stage_inst(stage_data, stage_name: str) -> str:
            """Format stage instruction with proper Empty/BUBBLE/STALL handling.
            
            Args:
                stage_data: Either dict {'inst', 'bubble', 'empty'} or legacy Instruction|None
                stage_name: Stage name ('IF', 'ID', 'EX', 'MEM', 'WB')
            
            Returns:
                Formatted string: instruction, "Empty", "BUBBLE", or "STALL"
            """
            # Handle stall condition first (affects IF and ID stages)
            if self.last_cycle_stall and stage_name in ['IF', 'ID']:
                return "STALL"
            
            # New dict format
            if isinstance(stage_data, dict):
                inst = stage_data.get('inst')
                is_bubble = stage_data.get('bubble', False)
                is_empty = stage_data.get('empty', False)
                

                
                if is_bubble:
                    return "BUBBLE"
                if is_empty or inst is None:
                    return "Empty"
                # Valid instruction
                return str(inst)
            
            # Legacy format (backwards compatibility)
            if stage_data is None:
                return "Empty"
            if hasattr(stage_data, 'opcode') and stage_data.opcode == 'nop':
                return "BUBBLE"
            return str(stage_data)

        cycle = self.cycle_count
        pc_val = self.pc & 0xFFFF

        # Get WB instruction for summary
        wb_data = self.trace_last_stages.get('WB') if isinstance(self.trace_last_stages, dict) else None
        if isinstance(wb_data, dict):
            wb_inst = wb_data.get('inst')
        else:
            wb_inst = wb_data
        
        if not wb_inst or (hasattr(wb_inst, "opcode") and wb_inst.opcode == "nop"):
            wb_str = "NOP"
        else:
            wb_str = str(wb_inst)

        stall_str = "YES" if self.last_cycle_stall else "NO"
        flush_str = "YES" if self.last_cycle_flush else "NO"
        hz_count = len(self.current_hazards) if self.current_hazards else 0

        lines: List[str] = []
        lines.append("════════════════════════════════════════════")
        lines.append(f"Pipeline Status — Cycle {cycle}   PC: {fmt_hex_dec(pc_val)}")
        lines.append(f"Summary: WB={wb_str} | Stall={stall_str} | Flush={flush_str} | Hazards={hz_count}")
        lines.append("════════════════════════════════════════════")

        # Register delta
        if self.last_reg_write_delta:
            r = self.last_reg_write_delta['reg']
            oldv = self.last_reg_write_delta['old']
            newv = self.last_reg_write_delta['new']
            lines.append(f"Register Changes: r{r}: {fmt_hex_dec(oldv)} → {fmt_hex_dec(newv)}")

        # Memory event
        if self.last_mem_event:
            kind = self.last_mem_event.get('kind')
            addr = self.last_mem_event.get('addr', 0)
            val = self.last_mem_event.get('value', 0)
            if kind == 'READ':
                lines.append(f"Memory: READ  [{fmt_hex_dec(addr)}] = {fmt_hex_dec(val)}")
            elif kind == 'WRITE':
                lines.append(f"Memory: WRITE [{fmt_hex_dec(addr)}] = {fmt_hex_dec(val)}")

        # Per-stage trace lines (always 5)
        snap = self.trace_last_stages if isinstance(self.trace_last_stages, dict) else {}
        s_if = fmt_stage_inst(snap.get('IF'), 'IF')
        s_id = fmt_stage_inst(snap.get('ID'), 'ID')
        s_ex = fmt_stage_inst(snap.get('EX'), 'EX')
        s_mem = fmt_stage_inst(snap.get('MEM'), 'MEM')
        s_wb = fmt_stage_inst(snap.get('WB'), 'WB')

        tag = f"[PC:{pc_val:04X}][C:{cycle}]"
        lines.append(f"{tag} IF  : {s_if}")
        lines.append(f"{tag} ID  : {s_id}")
        lines.append(f"{tag} EX  : {s_ex}")
        lines.append(f"{tag} MEM : {s_mem}")
        lines.append(f"{tag} WB  : {s_wb}")

        # Hazards section (unchanged hazard text)
        if self.current_hazards:
            lines.append("Hazards:")
            for hz in self.current_hazards:
                if isinstance(hz, dict):
                    status = hz.get('status', '')
                    reason = hz.get('reason', '')
                    lines.append(f"  - {status} | {reason}".rstrip())
                else:
                    lines.append(f"  - {str(hz)}")
        else:
            lines.append("Hazards: None")

        lines.append("------------------------------------------------------------")
        return "\n".join(lines)

    def step(self) -> bool:
        """Execute one clock cycle - Shadow Register Implementation"""
        if self.halted:
            return False
        
        self.cycle_count += 1
        self.current_hazards = []
        self.last_cycle_stall = False
        self.last_cycle_flush = False
        self.last_reg_write_delta = None
        self.last_wb_event = None
        self.last_mem_event = None
        # Snapshot pipeline latches for trace (start-of-cycle view)
        # Each stage stores: {'inst': Instruction|None, 'bubble': bool, 'empty': bool}
        def make_stage_snapshot(latch: PipelineRegister) -> dict:
            """Create a stage snapshot with bubble/empty state"""
            inst = latch.instruction if not latch.flush else None
            is_bubble = getattr(latch, 'is_bubble', False) or latch.flush
            is_empty = (inst is None) and not is_bubble
            result = {'inst': inst, 'bubble': is_bubble, 'empty': is_empty}
            # DEBUG: Print snapshot creation
            if self.cycle_count == 1:
                print(f"      [TRACE] Snapshot: inst={inst}, flush={latch.flush}, is_bubble_attr={getattr(latch, 'is_bubble', False)} -> bubble={is_bubble}, empty={is_empty}")
            return result
        
        self.trace_last_stages = {
            'IF': {'inst': None, 'bubble': False, 'empty': True},  # IF will be set later during fetch
            'ID': make_stage_snapshot(self.if_id),
            'EX': make_stage_snapshot(self.id_ex),
            'MEM': make_stage_snapshot(self.ex_mem),
            'WB': make_stage_snapshot(self.mem_wb),
        }
        
        # Print cycle header
        print("\n" + "="*80)
        print(f"CYCLE {self.cycle_count} - PC: {self.pc}")
        print("="*80)
        
        # ========================================================================
        # STEP 1: CREATE SHADOW (NEXT) REGISTERS
        # All stages read from CURRENT registers and write to NEXT registers
        # ========================================================================
        
        # Initialize next-state pipeline registers (shadow registers)
        next_if_id = PipelineRegister()
        next_id_ex = PipelineRegister()
        next_ex_mem = PipelineRegister()
        next_mem_wb = PipelineRegister()
        next_pc = self.pc
        
        # Branch/Jump flag: Prevents IF stage from incrementing PC if branch taken
        branch_taken_flag = False
        
        # ========================================================================
        # STEP 2: HAZARD DETECTION (using CURRENT state)
        # ========================================================================
        
        current_inst = self.if_id.instruction if not self.if_id.flush else None
        stall, data_hazards = self.hazard_unit.detect_data_hazard(
            self.id_ex, self.ex_mem, self.mem_wb, current_inst
        )
        self.last_cycle_stall = bool(stall)
        
        if data_hazards:
            self.current_hazards.extend(data_hazards)
            for hz in data_hazards:
                print(f"[!] HAZARD DETECTED: {hz}")
        
        # Control hazards are recorded ONLY when the branch/jump is actually TAKEN in EX.
        # (matches modern_simulator.py: no speculative "maybe flush" hazards)
        
        # ========================================================================
        # STEP 3: EXECUTE PIPELINE STAGES
        # Each stage reads from CURRENT (self.*) and writes to NEXT (next_*)
        # ========================================================================
        
        print("\nPIPELINE STAGES:")
        print("-" * 80)
        
        # ------------------------------------------------------------------------
        # WB STAGE: Read from CURRENT mem_wb, Write to Registers
        # ------------------------------------------------------------------------
        if self.mem_wb.instruction and not self.mem_wb.flush:
            write_data = self.mem_wb.data.get('write_data', 0)
            print(f"[WB]  {self.mem_wb.instruction} | Write Data: 0x{write_data:04X}")
            self.writeback(self.mem_wb.instruction, write_data)
            # Dynamic instruction retirement count (exclude NOPs)
            if self.mem_wb.instruction.opcode != 'nop':
                self.retired_count += 1
        else:
            if self.mem_wb.flush:
                print("[WB]  (flushed)")
            else:
                print("[WB]  (empty)")
        
        # ------------------------------------------------------------------------
        # MEM STAGE: Read from CURRENT ex_mem, Write to NEXT mem_wb
        # ------------------------------------------------------------------------
        if self.ex_mem.instruction:
            alu_res = self.ex_mem.data.get('alu_result', 0)
            print(f"[MEM] {self.ex_mem.instruction} | ALU Result: 0x{alu_res:04X}", end="")
            inst, mem_data = self.memory_access(self.ex_mem.instruction, alu_res)
            
            if self.ex_mem.instruction.opcode == 'lw':
                print(f" | Loaded: 0x{mem_data:04X}")
            elif self.ex_mem.instruction.opcode == 'sw':
                print(f" | Stored to addr: 0x{alu_res:04X}")
            else:
                print()
            
            # Write to NEXT mem_wb
            next_mem_wb.instruction = inst
            next_mem_wb.data = {'write_data': mem_data, 'alu_result': alu_res}
            next_mem_wb.is_bubble = self.ex_mem.is_bubble  # Propagate bubble state
            # Add store value for UI/logging only (does not affect execution)
            if self.ex_mem.instruction.opcode == 'sw':
                next_mem_wb.data['store_data'] = self.ex_mem.data.get('store_data', 0)
        else:
            print("[MEM] (empty)")
            next_mem_wb.instruction = None
            next_mem_wb.data = {}
            next_mem_wb.is_bubble = self.ex_mem.is_bubble if hasattr(self.ex_mem, 'is_bubble') else False
        
        # ------------------------------------------------------------------------
        # EX STAGE: Read from CURRENT id_ex, Write to NEXT ex_mem
        # CRITICAL: Forwarding uses CURRENT (stable) ex_mem and mem_wb
        # NOTE: stall only applies to IF/ID; ID/EX should still execute
        # ------------------------------------------------------------------------
        if self.id_ex.instruction and not self.id_ex.flush:
            rs_val = self.id_ex.data.get('rs_value', 0)
            rt_val = self.id_ex.data.get('rt_value', 0)
            print(f"[EX]  {self.id_ex.instruction} | RS: 0x{rs_val:04X}, RT: 0x{rt_val:04X}", end="")
            
            # Execute with forwarding (uses CURRENT self.ex_mem and self.mem_wb)
            exec_result = self.execute(self.id_ex.instruction, rs_val, rt_val)
            
            # Handle return value (sw returns 3 values, others return 2)
            if len(exec_result) == 3:
                inst, alu_result, store_data = exec_result
                print(f" -> ALU: 0x{alu_result:04X}, Store: 0x{store_data:04X}")
                next_ex_mem.data = {'alu_result': alu_result, 'store_data': store_data}
            else:
                inst, alu_result = exec_result
                print(f" -> ALU: 0x{alu_result:04X}")
                next_ex_mem.data = {'alu_result': alu_result}
            
            # Write to NEXT ex_mem
            next_ex_mem.instruction = inst
            next_ex_mem.is_bubble = self.id_ex.is_bubble  # Propagate bubble state
            
            # ------------------------------------------------------------------------
            # BRANCH/JUMP LOGIC: Update next_pc and set flush flags
            # ------------------------------------------------------------------------
            if inst and inst.opcode in ['beq', 'bne', 'j', 'jal', 'jr']:
                # Dynamic branch/jump count (instruction reached EX and is not flushed)
                self.branch_executed_count += 1
                branch_taken = False
                
                if inst.opcode == 'beq' and alu_result == 1:
                    # Branch TAKEN: registers are equal
                    branch_taken = True
                    offset = inst.imm
                    if offset & 0x20:  # Sign extend 6-bit immediate
                        offset = offset | 0xFFC0
                    if offset & 0x8000:  # Convert to signed
                        offset = offset - 0x10000
                    next_pc = (inst.pc + 1 + offset) & 0x1FF
                    print(f"      -> BRANCH TAKEN: PC {self.pc} -> {next_pc}")
                    
                elif inst.opcode == 'beq' and alu_result == 0:
                    print(f"      -> BRANCH NOT TAKEN (beq failed)")
                    
                elif inst.opcode == 'bne' and alu_result == 0:
                    # Branch TAKEN: registers are not equal
                    branch_taken = True
                    offset = inst.imm
                    if offset & 0x20:
                        offset = offset | 0xFFC0
                    if offset & 0x8000:
                        offset = offset - 0x10000
                    next_pc = (inst.pc + 1 + offset) & 0x1FF
                    print(f"      -> BRANCH TAKEN: PC {self.pc} -> {next_pc}")
                    
                elif inst.opcode == 'bne' and alu_result == 1:
                    print(f"      -> BRANCH NOT TAKEN (bne failed)")
                    
                elif inst.opcode == 'j':
                    branch_taken = True
                    next_pc = inst.address & 0x1FF
                    print(f"      -> JUMP: PC {self.pc} -> {next_pc}")
                    print(f"      -> [DEBUG] Jump target address: {inst.address}")
                    
                elif inst.opcode == 'jal':
                    branch_taken = True
                    next_pc = inst.address & 0x1FF
                    print(f"      -> JUMP AND LINK: PC {self.pc} -> {next_pc}, Return addr saved in $r7")
                    
                elif inst.opcode == 'jr':
                    branch_taken = True
                    next_pc = self.registers.read(inst.rs) & 0x1FF
                    print(f"      -> JUMP REGISTER: PC {self.pc} -> {next_pc}")
                
                # Set flush flags in NEXT registers and branch flag
                if branch_taken:
                    next_if_id.flush = True
                    next_if_id.is_bubble = True  # Mark as bubble for UI display
                    next_id_ex.flush = True
                    next_id_ex.is_bubble = True  # Mark as bubble for UI display
                    self.flush_count += 1
                    self.branch_taken_count += 1
                    # Record a real control hazard event (taken branch/jump)
                    hz_type = "Control Hazard (Branch Taken)" if inst.opcode in ["beq", "bne"] else "Control Hazard (Jump Taken)"
                    self.current_hazards.append({
                        "stage": "EX",
                        "type": hz_type,
                        "status": "Flush IF/ID + ID/EX",
                        "reason": f"{inst.opcode.upper()} taken → PC={next_pc}"
                    })
                    # CRITICAL: Set flag to prevent IF stage from incrementing PC
                    branch_taken_flag = True
                    print(f"      -> [FLUSH] Setting next_if_id.flush = True, is_bubble = True")
                    print(f"      -> [FLUSH] Setting next_id_ex.flush = True, is_bubble = True")
                    print(f"      -> [FLUSH] Setting branch_taken_flag = True")
                    print(f"      -> [FLUSH] next_pc set to: {next_pc}")
                    
                    # ========================================================
                    # 🔥 [DEĞİŞİKLİK 1] ID AŞAMASINI ANINDA BUBBLE YAP
                    # ========================================================
                    # Görsel olarak o anki ID aşamasındaki komutu gizleyip BUBBLE göster
                    if isinstance(self.trace_last_stages, dict):
                        self.trace_last_stages['ID']['bubble'] = True
                        # İsteğe bağlı: Komutu tamamen gizlemek için:
                        # self.trace_last_stages['ID']['inst'] = None
                    # ========================================================
        else:
            print("[EX]  (empty)")
            next_ex_mem.instruction = None
            next_ex_mem.data = {}
            next_ex_mem.is_bubble = self.id_ex.is_bubble if hasattr(self.id_ex, 'is_bubble') else False
        
        # ------------------------------------------------------------------------
        # ID STAGE: Read from CURRENT if_id, Write to NEXT id_ex
        # ------------------------------------------------------------------------
        # CRITICAL: Check if next_id_ex was already marked for flush by EX stage (branch/jump)
        # If EX already set next_id_ex.flush/is_bubble, don't overwrite it!
        if next_id_ex.flush or next_id_ex.is_bubble:
            # EX stage already flushed next_id_ex (branch taken in this cycle)
            # Don't overwrite - ID's instruction will be squashed
            print("[ID]  (squashed by EX branch/jump in same cycle - bubble inserted)")
        elif self.if_id.instruction and not stall and not self.if_id.flush:
            inst, rs_val, rt_val = self.decode(self.if_id.instruction)
            print(f"[ID]  {self.if_id.instruction} | Decoded RS: 0x{rs_val:04X}, RT: 0x{rt_val:04X}")
            
            # Write to NEXT id_ex (valid instruction, not a bubble)
            next_id_ex.instruction = inst
            next_id_ex.data = {'rs_value': rs_val, 'rt_value': rt_val}
            next_id_ex.is_bubble = False  # Clear bubble flag for valid instruction
        else:
            if stall:
                print("[ID]  (stalled - bubble inserted)")
                self.stall_count += 1
                # Insert bubble (nop) in NEXT id_ex
                next_id_ex.instruction = Instruction('nop')
                next_id_ex.data = {}
                next_id_ex.is_bubble = True  # Mark stall bubble
                
                # --- YENİ EKLENEN KISIM ---
                next_id_ex.stall = True   # ID aşamasının duraksadığını işaretle
                next_if_id.stall = True   # IF aşamasının duraksadığını işaretle
                # --------------------------
                
                # Keep CURRENT if_id when stalled (IF will also stall)
                next_if_id.instruction = self.if_id.instruction
                next_if_id.data = self.if_id.data.copy() if self.if_id.data else {}
                next_if_id.flush = self.if_id.flush
                next_if_id.is_bubble = self.if_id.is_bubble  # Preserve bubble state
            elif self.if_id.flush:
                print("[ID]  (flushed)")
                next_id_ex.instruction = None
                next_id_ex.data = {}
                next_id_ex.is_bubble = True  # Mark flush bubble
            else:
                print("[ID]  (empty)")
                next_id_ex.instruction = None
                next_id_ex.data = {}
                next_id_ex.is_bubble = False  # Empty, not a bubble
        
        # ------------------------------------------------------------------------
        # IF STAGE: Fetch from memory, Write to NEXT if_id
        # CRITICAL: Don't fetch if stalled, flushed, or if next_if_id already set by ID
        # ------------------------------------------------------------------------
        print(f"[IF]  Checking: stall={stall}, self.if_id.flush={self.if_id.flush}, next_if_id.flush={next_if_id.flush}")
        
        if stall:
            # Stall: Don't fetch, ID already preserved if_id in next_if_id
            print("[IF]  (stalled)")
        elif self.if_id.flush:
            # Flush affects IF/ID (ID stage). IF stage should still be able to fetch
            # the next instruction using the updated PC in the *same* cycle.
            print("[IF]  (flushed - continuing fetch from updated PC)")
            if next_if_id.instruction:
                print("[IF]  (instruction already in next_if_id from ID stall)")
            else:
                next_if_id.flush = False
                next_if_id.is_bubble = False  # Clear bubble flag, fetching valid instruction
                inst = self.fetch()
                if inst:
                    print(f"[IF]  Fetching instruction at PC={self.pc}: {inst}")
                    next_pc += 1
                    print(f"      -> [DEBUG] PC incremented: {self.pc} -> {next_pc}")
                else:
                    print("[IF]  (no more instructions)")
                next_if_id.instruction = inst
                
                # ========================================================
                # 🔥 [DEĞİŞİKLİK 2c] IF AŞAMASINI TRACE'E YAZARKEN MÜDAHALE ET
                # ========================================================
                if isinstance(self.trace_last_stages, dict):
                    self.trace_last_stages['IF'] = {
                        'inst': inst,
                        # Eğer bu cycle'da branch alındıysa (EX aşamasında), 
                        # şu an çektiğimiz komut (yanlış yol) görsel olarak BUBBLE olsun.
                        'bubble': branch_taken_flag,
                        'empty': (inst is None)
                    }
                # ========================================================
        elif next_if_id.instruction:
            # ID stage already set next_if_id (stall condition in previous check)
            print("[IF]  (instruction already in next_if_id from ID stall)")
        elif next_if_id.flush:
            # IMPORTANT (Control hazard penalty correctness):
            # When EX takes a branch/jump, we already redirected next_pc and marked younger
            # wrong-path instructions for squash (IF/ID + ID/EX). IF must NOT be skipped here.
            # If IF is skipped, each taken control transfer costs an extra dead cycle (3-cycle
            # penalty instead of the standard 2-cycle penalty for "branch resolved in EX").
            # Standard EX-resolved branch behavior: allow IF to fetch the *sequential* instruction
            # (which is now known to be wrong-path), keep next_if_id.flush=True so it will be
            # squashed, and rely on next_pc (already redirected to the target) for next cycle.
            print("[IF]  (flush set by EX - fetching wrong-path (will be squashed))")

            inst = self.fetch()
            if inst:
                print(f"[IF]  Fetching instruction at PC={self.pc}: {inst}")
            else:
                print("[IF]  (no more instructions)")

            # Keep flush=True and is_bubble=True (set by EX) so UI shows "BUBBLE"
            # and this wrong-path instruction doesn't enter ID next cycle.
            next_if_id.instruction = inst
            # next_if_id.flush and next_if_id.is_bubble remain True from EX stage (line 1115-1116)
            
            # ========================================================
            # 🔥 [DEĞİŞİKLİK 2a] IF AŞAMASINI TRACE'E YAZARKEN MÜDAHALE ET
            # ========================================================
            if isinstance(self.trace_last_stages, dict):
                self.trace_last_stages['IF'] = {
                    'inst': inst,
                    # Eğer bu cycle'da branch alındıysa (EX aşamasında), 
                    # şu an çektiğimiz komut (yanlış yol) görsel olarak BUBBLE olsun.
                    'bubble': branch_taken_flag or next_if_id.is_bubble,
                    'empty': False
                }
            # ========================================================
        else:
            # Normal fetch
            inst = self.fetch()
            if inst:
                print(f"[IF]  Fetching instruction at PC={self.pc}: {inst}")
                # CRITICAL: Only increment PC if no branch/jump was taken in EX stage
                if not branch_taken_flag:
                    next_pc += 1  # Increment PC for next cycle
                    print(f"      -> [DEBUG] PC incremented: {self.pc} -> {next_pc}")
                else:
                    print(f"      -> PC not incremented (branch/jump target already set)")
                    print(f"      -> [DEBUG] branch_taken_flag detected, PC stays at {next_pc}")
            else:
                print("[IF]  (no more instructions)")
            
            # Write to NEXT if_id
            next_if_id.instruction = inst
            next_if_id.is_bubble = False  # Clear bubble flag for normal fetch
            
            # ========================================================
            # 🔥 [DEĞİŞİKLİK 2b] IF AŞAMASINI TRACE'E YAZARKEN MÜDAHALE ET
            # ========================================================
            if isinstance(self.trace_last_stages, dict):
                self.trace_last_stages['IF'] = {
                    'inst': inst,
                    # Eğer bu cycle'da branch alındıysa (EX aşamasında), 
                    # şu an çektiğimiz komut (yanlış yol) görsel olarak BUBBLE olsun.
                    'bubble': branch_taken_flag or next_if_id.is_bubble,
                    'empty': (inst is None)
                }
            # ========================================================
        
        # Save flush flag for trace reporting
        self.last_cycle_flush = bool(branch_taken_flag)

        # ========================================================================
        # STEP 4: SYNCHRONOUS UPDATE - Clock Edge Simulation
        # Update ALL pipeline registers and PC simultaneously
        # ========================================================================
        
        self.if_id = next_if_id
        self.id_ex = next_id_ex
        self.ex_mem = next_ex_mem
        self.mem_wb = next_mem_wb
        self.pc = next_pc
        
        # ========================================================================
        # STEP 5: PRINT STATUS
        # ========================================================================
        
        # Print register state if changed
        if self.last_written_register != -1:
            print(f"\nREGISTER UPDATE:")
            print(f"   $r{self.last_written_register} = 0x{self.registers.read(self.last_written_register):04X} ({self.registers.read(self.last_written_register)})")
        
        # Print summary
        print(f"\nCYCLE SUMMARY:")
        print(f"   Total Cycles: {self.cycle_count} | Stalls: {self.stall_count} | Flushes: {self.flush_count} | Forwards: {self.forward_count}")
        
        # Check if done - Pipeline Drain Logic
        # Start drain ONLY when: 
        # 1. PC is past last instruction AND
        # 2. IF/ID is empty (no instruction was fetched this cycle - truly at end)
        # This prevents early drain when PC temporarily goes past end but branch brings it back
        if self.pc >= len(self.instructions) and not next_if_id.instruction:
            if not hasattr(self, 'drain_cycles'):
                self.drain_cycles = 0
                print(f"   [PIPELINE DRAIN] Started - waiting for pipeline to empty")
            else:
                self.drain_cycles += 1
                print(f"   [PIPELINE DRAIN] Cycle {self.drain_cycles}/3")
        
        # Halt after pipeline has drained (3 cycles for last instruction to complete WB)
        if hasattr(self, 'drain_cycles') and self.drain_cycles >= 3:
            self.halted = True
            print("\n" + "="*80)
            print("PROGRAM EXECUTION COMPLETE")
            print("="*80)
            print(f"\nFINAL STATISTICS:")
            print(f"   Total Cycles: {self.cycle_count}")
            print(f"   Instructions (retired): {self.retired_count}")
            print(f"   CPI: {self.cycle_count / self.retired_count if self.retired_count > 0 else 0:.2f}")
            print(f"   Stalls: {self.stall_count}")
            print(f"   Flushes: {self.flush_count}")
            print(f"   Forwards: {self.forward_count}")
            print(f"   Branch/Jumps executed: {self.branch_executed_count}")
            print(f"   Taken branches/jumps: {self.branch_taken_count}")
            print("\nFINAL REGISTER STATE:")
            for i in range(8):
                val = self.registers.read(i)
                alias = ["Zero", "Caller", "Caller", "Caller", "Caller", "Callee", "Callee", "Callee"][i]
                print(f"   $r{i} ({alias:6s}): 0x{val:04X} ({val:5d})")
            
        return not self.halted


# ============================================================================
# ASSEMBLER
# ============================================================================

class Assembler:
    """Converts assembly code to instructions"""
    def __init__(self):
        self.labels = {}
        # Populated after parse(): pc_to_editor_line_map[pc] = 0-based editor line index
        self.pc_to_editor_line_map: List[int] = []
        # Immediate mode selected by UI: "Signed" (default) or "Unsigned"
        # This affects immediates used by addi/lw/sw only.
        # IMPORTANT: Branch offsets (beq/bne) remain SIGNED always.
        self.immediate_mode = "Signed"
        # Backwards-compat internal form (some older code paths check this)
        self.imm_mode = "signed"
    
    def set_imm_mode(self, mode: str):
        """Backward-compatible setter: accepts 'signed'/'unsigned'."""
        mode_l = (mode or "").strip().lower()
        if mode_l == "signed":
            self.set_immediate_mode("Signed")
            return
        if mode_l == "unsigned":
            self.set_immediate_mode("Unsigned")
            return
        raise ValueError(f"Invalid immediate mode: {mode}. Must be 'signed' or 'unsigned'.")

    def set_immediate_mode(self, mode_str: str):
        """Set immediate mode using UI strings: 'Signed' or 'Unsigned'."""
        raw = (mode_str or "").strip()
        if raw.lower() == "signed":
            self.immediate_mode = "Signed"
            self.imm_mode = "signed"
            return
        if raw.lower() == "unsigned":
            self.immediate_mode = "Unsigned"
            self.imm_mode = "unsigned"
            return
        raise ValueError(f"Invalid immediate mode: {mode_str}. Must be 'Signed' or 'Unsigned'.")
        
    def parse(self, code: str) -> List[Instruction]:
        """Parse assembly code into instructions"""
        lines = code.split('\n')
        instructions = []
        pc_to_editor_line_map: List[int] = []
        
        # First pass: collect labels and count instruction addresses correctly
        # We must ignore any lines that are NOT valid instructions
        current_addr = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split off comment if any
            if '#' in line:
                line = line.split('#')[0].strip()
            if not line:
                continue

            # Check for label
            if ':' in line:
                label_parts = line.split(':', 1)
                label = label_parts[0].strip()
                self.labels[label] = current_addr
                line = label_parts[1].strip()
                # If only label on line, don't increment PC
                if not line:
                    continue
            
            # Verify if it's a real opcode
            parts = line.replace(',', ' ').split()
            if parts and parts[0].lower() in OPCODE_MAP:
                current_addr += 1
        
        # Second pass: parse instructions
        current_pc = 0
        for line_idx, raw in enumerate(lines):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
                
            # Remove comment suffix
            if '#' in line:
                line = line.split('#')[0].strip()
            if not line:
                continue

            # Skip separator-only header lines like "=====" or "-----" or "_____"
            # (UI line wraps must NOT affect parsing; only actual newline-separated lines count.)
            if set(line) <= {"=", "-", "_"}:
                continue

            # Remove label if present
            if ':' in line:
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue

            # Only treat real opcode lines as candidate instructions (avoid parsing headers like "=====")
            parts = line.replace(',', ' ').split()
            if not parts or parts[0].lower() not in OPCODE_MAP:
                continue
            
            try:
                inst = self.parse_instruction(line, current_pc)
                if inst:
                    instructions.append(inst)
                    pc_to_editor_line_map.append(line_idx)
                    current_pc += 1
            except Exception as e:
                # STRICT validation: re-raise errors instead of silently continuing
                # This ensures invalid programs are rejected immediately
                raise ValueError(f"Line {line_idx + 1}: {line}\n{str(e)}")
        
        # ✅ AUTO-FIX: Add a trailing NOP to catch END labels that point past the last instruction
        # This prevents "pc >= len(instructions)" halts when branching to labels after code
        # Only add NOP if the last instruction is NOT already a NOP
        if instructions and instructions[-1].opcode != 'nop':
            instructions.append(Instruction('nop'))
            pc_to_editor_line_map.append(len(lines) - 1)  # Map to last line (cosmetic)
                
        # Expose mapping without changing parse() return type (UI consumes this)
        self.pc_to_editor_line_map = pc_to_editor_line_map
        return instructions
    
    def parse_instruction(self, line: str, current_pc: int = 0) -> Optional[Instruction]:
        """Parse a single instruction"""
        parts = line.replace(',', ' ').split()
        if not parts:
            return None
        
        opcode = parts[0].lower()
        
        if opcode == 'nop':
            return Instruction('nop')
        
        # R-type: add, sub, and, or, slt
        if opcode in ['add', 'sub', 'and', 'or', 'slt']:
            rd = self.parse_register(parts[1])
            rs = self.parse_register(parts[2])
            rt = self.parse_register(parts[3])
            return Instruction(opcode, rd=rd, rs=rs, rt=rt)
        
        # Shift: sll, srl
        elif opcode in ['sll', 'srl']:
            rd = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            shamt = int(parts[3])
            # Validate shift amount (3-bit: 0-7)
            if shamt < 0 or shamt > 7:
                raise ValueError(
                    f"Shift amount {shamt} is OUT OF RANGE!\n"
                    f"Valid range: 0 to 7 (3-bit unsigned)\n"
                    f"Instruction: {opcode} {parts[1]},{parts[2]},{parts[3]}"
                )
            return Instruction(opcode, rd=rd, rt=rt, shamt=shamt)
        
        # I-type: addi
        elif opcode == 'addi':
            rt = self.parse_register(parts[1])
            rs = self.parse_register(parts[2])
            # Mode-aware immediate parsing (Signed: -32..31, Unsigned: 0..63)
            imm = self.parse_immediate(parts[3])
            return Instruction(opcode, rt=rt, rs=rs, imm=imm)
        
        # Load/Store: lw, sw
        elif opcode in ['lw', 'sw']:
            rt = self.parse_register(parts[1])
            # Parse offset(rs) format
            offset_part = parts[2]
            if '(' in offset_part:
                offset_str = offset_part.split('(')[0]
                rs = self.parse_register(offset_part.split('(')[1].rstrip(')'))
                # Mode-aware offset parsing (Signed: -32..31, Unsigned: 0..63)
                offset = self.parse_immediate(offset_str)
            else:
                offset = 0
                rs = self.parse_register(offset_part)
            return Instruction(opcode, rt=rt, rs=rs, imm=offset)
        
        # Branch: beq, bne
        elif opcode in ['beq', 'bne']:
            rs = self.parse_register(parts[1])
            rt = self.parse_register(parts[2])
            label_name = None  # Track if we have a label
            
            # Check if it's a label or immediate
            if parts[3] in self.labels:
                # Calculate relative offset: target - (PC + 1)
                label_name = parts[3]  # Save the label name
                target_addr = self.labels[parts[3]]
                offset = target_addr - (current_pc + 1)
                # Branch offsets are ALWAYS signed (-32..31), regardless of mode.
                if offset < -32 or offset > 31:
                    raise ValueError(
                        f"Branch offset {offset} is OUT OF RANGE. "
                        f"Valid range: -32 to +31 (6-bit signed). "
                        f"Label '{parts[3]}' too far."
                    )
                imm = offset & 0x3F  # Convert to 6-bit
            else:
                # Numeric branch offsets are ALWAYS signed (-32..31), regardless of mode.
                imm = self.parse_immediate_signed_6(parts[3])
            return Instruction(opcode, rs=rs, rt=rt, imm=imm, label=label_name)
        
        # Jump: j, jal
        elif opcode in ['j', 'jal']:
            label_name = None  # Track if we have a label
            if parts[1] in self.labels:
                label_name = parts[1]  # Save the label name
                address = self.labels[parts[1]]
            else:
                address = int(parts[1])
            return Instruction(opcode, address=address, label=label_name)
        
        # Jump register: jr
        elif opcode == 'jr':
            rs = self.parse_register(parts[1])
            return Instruction(opcode, rs=rs)
        
        return None
    
    def parse_register(self, reg_str: str) -> int:
        """Parse register name to number (supports R0-R7, $r0-$r7, $0-$7)"""
        reg_str = reg_str.lower().strip()
        
        # Remove $ and r prefixes
        reg_str = reg_str.replace('$r', '').replace('$', '').replace('r', '')
        
        # Handle special register names
        reg_map = {
            '0': 0, 'zero': 0,
            '1': 1, '2': 2, '3': 3, '4': 4, 
            '5': 5, '6': 6, '7': 7
        }
        
        if reg_str in reg_map:
            return reg_map[reg_str]
        
        try:
            return int(reg_str) & 0x7  # Ensure 3-bit register
        except:
            return 0
    
    def parse_immediate(self, imm_str: str) -> int:
        """Parse immediate value based on selected immediate mode (6-bit).

        - Signed mode:   -32..+31  (6-bit signed, two's complement)
        - Unsigned mode:  0..63    (6-bit unsigned)

        NOTE: Branch offsets are handled separately and are ALWAYS signed.
        """
        mode = (getattr(self, "immediate_mode", "Signed") or "Signed").strip().lower()
        if mode == "unsigned":
            return self.parse_immediate_unsigned_6(imm_str)
        return self.parse_immediate_signed_6(imm_str)

    def parse_immediate_signed_6(self, imm_str: str) -> int:
        """Parse 6-bit signed immediate [-32..31], return encoded imm6 (val & 0x3F)."""
        if imm_str.startswith('0x'):
            val = int(imm_str, 16)
        elif imm_str.startswith('0b'):
            val = int(imm_str, 2)
        else:
            val = int(imm_str)

        if val < -32 or val > 31:
            raise ValueError(
                f"Immediate value {val} is OUT OF RANGE. "
                f"Valid range: -32 to +31 (6-bit signed)."
            )
        return val & 0x3F

    def parse_immediate_unsigned_6(self, imm_str: str) -> int:
        """Parse 6-bit unsigned immediate [0..63], return encoded imm6 (val & 0x3F)."""
        if imm_str.startswith('0x'):
            val = int(imm_str, 16)
        elif imm_str.startswith('0b'):
            val = int(imm_str, 2)
        else:
            val = int(imm_str)

        if val < 0 or val > 63:
            raise ValueError(
                f"Immediate value {val} is OUT OF RANGE. "
                f"Valid range: 0 to 63 (6-bit unsigned)."
            )
        return val & 0x3F
    
    def parse_immediate_unsigned(self, imm_str: str) -> int:
        """Parse immediate value (6-bit unsigned: 0 to 63)
        
        Raises:
            ValueError: If value is negative or out of valid range [0, 63]
        """
        if imm_str.startswith('0x'):
            val = int(imm_str, 16)
        elif imm_str.startswith('0b'):
            val = int(imm_str, 2)
        else:
            val = int(imm_str)
        
        # Strict validation for unsigned: range must be 0-63
        if val < 0 or val > 63:
            raise ValueError(
                f"Unsigned immediate out of range: {val}. Allowed: 0..63"
            )
        
        return val & 0x3F


