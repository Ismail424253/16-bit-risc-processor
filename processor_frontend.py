"""
16-bit RISC Processor Simulator - Frontend
5-Stage Pipeline Architecture
Computer Architecture Course Project
Modern Dark Navy UI Theme
"""

import sys
from typing import Dict, List, Optional, Tuple
import copy
import html
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                               QTableWidget, QTableWidgetItem, QFrame,
                               QFileDialog, QMessageBox, QSlider, QTabWidget,
                               QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
                               QHeaderView, QStyledItemDelegate, QStyleOptionViewItem, QStyle,
                               QDialog, QTextBrowser, QComboBox)
from PySide6.QtCore import Qt, QTimer, Signal, QRegularExpression, QRectF
from PySide6.QtGui import QFont, QColor, QPalette, QBrush, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QTextFormat, QTextDocument

# Import backend classes
from processor_backend import (
    OPCODE_MAP, OPCODE_REVERSE, INSTRUCTION_TYPES,
    Instruction, RegisterFile, Memory, ALU, PipelineRegister, 
    HazardUnit, Processor, Assembler
)

# Import theme colors
from theme import (
    COLORS,
    RGBA_SURFACE_LIGHT,
    RGBA_SURFACE_MEDIUM,
    RGBA_SURFACE_DARK,
    RGBA_SURFACE_TRANSPARENT,
    POPUP_BG,
    POPUP_BORDER,
    POPUP_TEXT,
    POPUP_CYCLE_COLOR,
    POPUP_DETAIL_COLOR,
    rgba_string
)

# ============================================================================
# MINIMAL HAZARD POPUP
# ============================================================================

class SimpleHazardPopup(QDialog):
    """Minimal popup to show hazard details - cycle, stage, and type only."""
    def __init__(self, cycle, stage, hazard_type, hazard_class, reason, parent=None):
        super().__init__(parent)
        
        # Window settings - frameless popup style
        self.setWindowTitle("Hazard Details")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(480, 180)  # Biraz daha geniş ve yüksek
        
        # Theme styling (from theme.py) - Açık tema için uygun
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {POPUP_BG};
                border: 2px solid {POPUP_BORDER};
                border-radius: 10px;
            }}
            QLabel {{
                color: {POPUP_TEXT};
                font-size: 13px;
                background: transparent;
            }}
        """)
        
        layout = QGridLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        
        # Title labels (left column) - Açık tema için daha koyu renk
        lbl_cycle_title = QLabel("Cycle:")
        lbl_cycle_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_cycle_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        lbl_stage_title = QLabel("Pipeline Stage:")
        lbl_stage_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_stage_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        lbl_hazard_title = QLabel("Hazard Type:")
        lbl_hazard_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_hazard_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        lbl_detail_title = QLabel("Details:")
        lbl_detail_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_detail_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        # Value labels (right column) - with color highlights
        lbl_cycle_val = QLabel(f"#{cycle}")
        lbl_cycle_val.setFont(QFont("Consolas", 12, QFont.Bold))
        lbl_cycle_val.setStyleSheet(f"color: {POPUP_CYCLE_COLOR};")
        
        lbl_stage_val = QLabel(stage)
        lbl_stage_val.setFont(QFont("Consolas", 12, QFont.Bold))
        lbl_stage_val.setStyleSheet(f"color: {POPUP_CYCLE_COLOR};")
        
        # Show hazard classification without duplicate text
        # If hazard_type already contains hazard_class, just show hazard_type
        # Otherwise show: "hazard_class (hazard_type)"
        if hazard_class.lower() in hazard_type.lower():
            hazard_display = hazard_type
        else:
            hazard_display = f"{hazard_class} ({hazard_type})"
        
        lbl_hazard_val = QLabel(hazard_display)
        lbl_hazard_val.setFont(QFont("Segoe UI", 12))
        lbl_hazard_val.setStyleSheet(f"color: {COLORS['text_primary']};")
        
        lbl_detail_val = QLabel(reason)
        lbl_detail_val.setFont(QFont("Segoe UI", 11))
        lbl_detail_val.setStyleSheet(f"color: {POPUP_DETAIL_COLOR};")
        lbl_detail_val.setWordWrap(True)
        
        # Grid layout (row, column)
        layout.addWidget(lbl_cycle_title, 0, 0)
        layout.addWidget(lbl_cycle_val, 0, 1)
        
        layout.addWidget(lbl_stage_title, 1, 0)
        layout.addWidget(lbl_stage_val, 1, 1)
        
        layout.addWidget(lbl_hazard_title, 2, 0)
        layout.addWidget(lbl_hazard_val, 2, 1)
        
        layout.addWidget(lbl_detail_title, 3, 0, Qt.AlignTop)
        layout.addWidget(lbl_detail_val, 3, 1)
        
        self.setLayout(layout)
    
    def focusOutEvent(self, event):
        """Close popup when focus is lost (click outside)."""
        self.close()
        super().focusOutEvent(event)


# ============================================================================
# EXECUTION COMPLETION STATISTICS DIALOG
# ============================================================================

class ExecutionCompletionDialog(QDialog):
    """Dialog showing execution statistics when program finishes"""
    def __init__(self, processor, parent=None):
        super().__init__(parent)
        
        self.processor = processor
        
        # Window settings
        self.setWindowTitle("Program Execution Completed")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        # Calculate statistics
        total_cycles = processor.cycle_count
        retired_instructions = processor.retired_count
        stalls = processor.stall_count
        flushes = processor.flush_count
        forwards = processor.forward_count
        branch_executed = processor.branch_executed_count
        branch_taken = processor.branch_taken_count
        
        # Calculate CPI (Cycles Per Instruction)
        cpi = total_cycles / retired_instructions if retired_instructions > 0 else 0
        
        # Calculate pipeline efficiency
        # Ideal cycles = retired_instructions (if no hazards)
        # Pipeline efficiency = ideal_cycles / actual_cycles * 100
        ideal_cycles = retired_instructions
        pipeline_efficiency = (ideal_cycles / total_cycles * 100) if total_cycles > 0 else 0
        
        # Calculate branch prediction accuracy (assumed not taken)
        branch_accuracy = ((branch_executed - branch_taken) / branch_executed * 100) if branch_executed > 0 else 0
        
        # Theme styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                background: transparent;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QFrame {{
                background-color: {COLORS['surface_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Program Execution Completed")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Statistics container
        stats_frame = QFrame()
        stats_layout = QGridLayout()
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(15)
        
        # Create statistics rows
        row = 0
        
        # Section 1: Basic Statistics
        section1_title = QLabel("📊 Execution Statistics")
        section1_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section1_title.setStyleSheet(f"color: {COLORS['primary']};")
        stats_layout.addWidget(section1_title, row, 0, 1, 2)
        row += 1
        
        self._add_stat_row(stats_layout, row, "Total Cycles:", str(total_cycles), COLORS['accent'])
        row += 1
        self._add_stat_row(stats_layout, row, "Instructions (Retired):", str(retired_instructions), COLORS['accent'])
        row += 1
        self._add_stat_row(stats_layout, row, "CPI (Cycles Per Instruction):", f"{cpi:.2f}", COLORS['warning'])
        row += 1
        self._add_stat_row(stats_layout, row, "Pipeline Efficiency:", f"{pipeline_efficiency:.1f}%", COLORS['success'])
        row += 1
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet(f"background-color: {COLORS['border']};")
        stats_layout.addWidget(separator1, row, 0, 1, 2)
        row += 1
        
        # Section 2: Hazard Statistics
        section2_title = QLabel("⚠️ Hazard Statistics")
        section2_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section2_title.setStyleSheet(f"color: {COLORS['primary']};")
        stats_layout.addWidget(section2_title, row, 0, 1, 2)
        row += 1
        
        self._add_stat_row(stats_layout, row, "Pipeline Stalls:", str(stalls), COLORS['error'])
        row += 1
        self._add_stat_row(stats_layout, row, "Pipeline Flushes:", str(flushes), COLORS['warning'])
        row += 1
        self._add_stat_row(stats_layout, row, "Data Forwardings:", str(forwards), COLORS['success'])
        row += 1
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet(f"background-color: {COLORS['border']};")
        stats_layout.addWidget(separator2, row, 0, 1, 2)
        row += 1
        
        # Section 3: Branch Statistics
        section3_title = QLabel("🔀 Branch/Jump Statistics")
        section3_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section3_title.setStyleSheet(f"color: {COLORS['primary']};")
        stats_layout.addWidget(section3_title, row, 0, 1, 2)
        row += 1
        
        self._add_stat_row(stats_layout, row, "Branches/Jumps Executed:", str(branch_executed), COLORS['accent'])
        row += 1
        self._add_stat_row(stats_layout, row, "Branches/Jumps Taken:", str(branch_taken), COLORS['accent'])
        row += 1
        self._add_stat_row(stats_layout, row, "Branch Prediction Accuracy:", f"{branch_accuracy:.1f}%", COLORS['info'])
        row += 1
        
        stats_frame.setLayout(stats_layout)
        main_layout.addWidget(stats_frame)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedHeight(45)
        main_layout.addWidget(close_btn)
        
        self.setLayout(main_layout)
    
    def _add_stat_row(self, layout, row, label_text, value_text, value_color):
        """Helper to add a statistics row"""
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 12))
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        value = QLabel(value_text)
        value.setFont(QFont("Consolas", 13, QFont.Bold))
        value.setStyleSheet(f"color: {value_color};")
        value.setAlignment(Qt.AlignRight)
        
        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)


# ============================================================================
# GUI APPLICATION - MODERN DARK NAVY THEME
# ============================================================================

# UI Constants
INST_MEM_MAX_ROWS = 512  # Maximum rows to display in Instruction Memory table
# Note: All colors are now imported from theme.py - modify colors there to change the entire theme


# ----------------------------------------------------------------------------
# Syntax Highlighter for Assembly Code
# ----------------------------------------------------------------------------
class AssemblyHighlighter(QSyntaxHighlighter):
    """Advanced syntax highlighter for assembly code."""
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        def make_format(color_hex: str, bold: bool = False, italic: bool = False, light: bool = False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))
            if bold:
                fmt.setFontWeight(QFont.Bold)
            elif light:
                fmt.setFontWeight(QFont.Light)
            if italic:
                fmt.setFontItalic(True)
            fmt.setFontFamily("Consolas")
            return fmt
        
        # Comments (Gray, Italic, Light) - handled specially so nothing inside comments gets token-highlighting
        self._comment_re = QRegularExpression(r"#.*$")
        self._comment_fmt = make_format(COLORS['text_muted'], italic=True, light=True)
        
        # Labels (Orange, Bold) - Allows whitespace at start (e.g., "  loop:")
        self.rules.append((QRegularExpression(r"^\s*[A-Za-z_][\w]*:"), make_format(COLORS['warning_500'], True)))
        
        # 3. Registers (Green, Bold) - Matches $r0-$r7, $zero
        self.rules.append((QRegularExpression(r"\$r\d\b"), make_format(COLORS['success_500'], True)))
        self.rules.append((QRegularExpression(r"\$zero\b"), make_format(COLORS['success_500'], True)))
        
        # 4. Opcodes (Blue, Bold) - Dynamically from OPCODE_MAP
        # Uses re.escape to ensure safety
        if 'OPCODE_MAP' in globals():
            opcodes_list = [re.escape(op) for op in OPCODE_MAP.keys()]
            opcodes_pattern = r"\b(" + "|".join(opcodes_list) + r")\b"
            self.rules.append((QRegularExpression(opcodes_pattern, QRegularExpression.CaseInsensitiveOption),
                               make_format(COLORS['accent_400'], True)))
        
        # 5. Hex Numbers (Purple) - e.g. 0xFFFF
        self.rules.append((QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), make_format(COLORS['stage_wb'])))
        
        # 6. Decimal Numbers (Purple) - e.g. 123, -45
        self.rules.append((QRegularExpression(r"\b[-+]?\d+\b"), make_format(COLORS['stage_wb'])))
    
    def highlightBlock(self, text: str):
        """
        Apply syntax highlighting for assembly code.
        Only lines starting with # are treated as comments.
        """
        stripped = text.strip()
        
        # 1. Handle complete comments or empty lines
        if not stripped or stripped.startswith('#'):
            self.setFormat(0, len(text), self._comment_fmt)
            return

        # 2. Apply standard rules (opcodes, registers, numbers, labels)
        comment_match = self._comment_re.match(text)
        comment_start = comment_match.capturedStart() if comment_match.hasMatch() else -1

        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                # Don't highlight inside comment regions
                if comment_start != -1 and start >= comment_start:
                    continue
                if comment_start != -1 and (start + length) > comment_start:
                    continue
                self.setFormat(start, length, fmt)

        # 3. Format the comment region (# and everything after)
        if comment_start != -1:
            self.setFormat(comment_start, len(text) - comment_start, self._comment_fmt)


def format_asm_inline_html(text: str) -> str:
    """Format an assembly string with inline HTML coloring for opcodes/registers/numbers."""
    if not text:
        return ""
    
    # Only treat lines starting with # as comments
    stripped = text.strip()
    if stripped.startswith('#'):
        return f"<span style=\"color: {COLORS['text_muted']}; font-style: italic;\">{html.escape(text)}</span>"

    # Tokenize while preserving punctuation/spaces
    token_re = re.compile(r"(\$r\d\b|\$zero\b|0x[0-9a-fA-F]+\b|[-+]?\d+\b|[A-Za-z_]\w*)")
    out: List[str] = []
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            out.append(html.escape(text[pos:m.start()]))
        tok = m.group(1)
        tok_l = tok.lower()
        color = None
        weight = None
        if tok_l in OPCODE_MAP:
            color = COLORS.get('accent_400')
            weight = 600
        elif tok.startswith("$"):
            color = COLORS.get('success_500')
            weight = 600
        elif tok_l.startswith("0x") or tok.lstrip("+-").isdigit():
            color = COLORS.get('stage_wb')
        if color:
            style = f"color: {color};"
            if weight:
                style += f" font-weight: {weight};"
            out.append(f"<span style=\"{style}\">{html.escape(tok)}</span>")
        else:
            out.append(html.escape(tok))
        pos = m.end()
    if pos < len(text):
        out.append(html.escape(text[pos:]))
    return "".join(out)


class RichTextDelegate(QStyledItemDelegate):
    """Render HTML in QTableWidget cells while preserving selection/background painting."""
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # Draw the item background/selection/etc. but not the plain text
        text = opt.text
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        # Draw rich text
        doc = QTextDocument()
        doc.setDefaultFont(opt.font)
        doc.setHtml(text)
        painter.save()
        painter.translate(opt.rect.topLeft())
        doc.drawContents(painter, QRectF(0, 0, opt.rect.width(), opt.rect.height()))
        painter.restore()

class LastWrittenDelegate(QStyledItemDelegate):
    """Paint last-written register row with a neon background that wins over selection/QSS."""
    def paint(self, painter, option, index):
        is_last = (index.data(Qt.UserRole) == 1)
        if not is_last:
            super().paint(painter, option, index)
            return

        neon_bg = QColor("#00F5D4")
        neon_text = QColor("#0B1020")  # very dark navy (better contrast than pure black)

        # Hard-paint the background first so QSS/alternating/selection cannot override it.
        painter.save()
        painter.fillRect(option.rect, neon_bg)

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # Prevent any selection overlay from darkening the cell.
        opt.state &= ~QStyle.State_Selected

        opt.font.setBold(True)
        opt.backgroundBrush = QBrush(Qt.NoBrush)

        # Force readable text colors
        opt.palette.setColor(QPalette.Text, neon_text)
        opt.palette.setColor(QPalette.HighlightedText, neon_text)
        opt.palette.setColor(QPalette.Highlight, neon_bg)

        super().paint(painter, opt, index)
        painter.restore()

class StageWidget(QFrame):
    """Custom widget for pipeline stage display - Modern card style"""
    def __init__(self, stage_name: str, stage_color: str):
        super().__init__()
        self.stage_name = stage_name
        self.stage_color = stage_color
        self.instruction = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Modern colored pill/tag for stage name
        header = QHBoxLayout()
        pill = QLabel(self.stage_name)
        pill.setStyleSheet(f"""
            QLabel {{
                background-color: {self.stage_color};
                border-radius: 10px;
                padding: 5px 14px;
                color: white;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
        """)
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedWidth(60)
        header.addWidget(pill)
        header.addStretch()
        layout.addLayout(header)
        
        # Instruction content
        self.content_label = QLabel("Empty")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.content_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 12px;
                background-color: {rgba_string(RGBA_SURFACE_LIGHT)};
                border-radius: 8px;
                min-height: 90px;
            }}
        """)
        layout.addWidget(self.content_label)
        
        # Modern card styling with transparent background and colored border
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {rgba_string(RGBA_SURFACE_MEDIUM)};
                border: 2px solid {self.stage_color};
                border-radius: 12px;
            }}
        """)
        
    def set_instruction(self, pipeline_reg):
        """
        Set stage display from pipeline register.
        Handles PipelineRegister objects, raw Instruction objects, and trace dictionaries.
        """
        # Varsayılan değerler
        instruction = None
        is_bubble = False
        is_stalled = False

        # 1. Durum: Trace Dictionary (Backend'den gelen en doğru veri yapısı)
        if isinstance(pipeline_reg, dict):
            instruction = pipeline_reg.get('inst')
            is_bubble = pipeline_reg.get('bubble', False)
            is_stalled = pipeline_reg.get('stall', False)  # Stall bilgisini buradan alacağız
            
        # 2. Durum: PipelineRegister Objesi (Eski uyumluluk)
        elif hasattr(pipeline_reg, 'instruction'):
            instruction = pipeline_reg.instruction
            is_bubble = getattr(pipeline_reg, 'is_bubble', False)
            is_stalled = getattr(pipeline_reg, 'stall', False)
            
        # 3. Durum: Raw Instruction Objesi (Eski uyumluluk)
        else:
            instruction = pipeline_reg
            # Instruction objesi tek başına bubble/stall bilgisi taşımaz
        
        self.instruction = instruction
        
        # --- YENİ STALL KONTROLÜ (En öncelikli) ---
        if is_stalled:
            self.content_label.setTextFormat(Qt.RichText)
            self.content_label.setText(f"<b style='color: #DE0517; font-size: 14px;'>STALL</b><br><br><span style='color: #5A5A54;'>Waiting for data...</span>")
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(222, 5, 23, 0.1);
                    border: 2px solid #DE0517;
                    border-radius: 12px;
                }}
            """)
        # --- MEVCUT DİĞER DURUMLAR ---
        elif is_bubble:
            # Show BUBBLE for flushed/squashed instructions
            self.content_label.setTextFormat(Qt.PlainText)
            self.content_label.setText("BUBBLE")
            # Bubble state - orange/warning style
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 152, 0, 0.15);
                    border: 2px dashed #FF9800;
                    border-radius: 12px;
                }}
            """)
        elif instruction:
            # Show instruction
            self.content_label.setTextFormat(Qt.RichText)
            text = format_asm_inline_html(str(instruction))
            pc_text = f"PC: {instruction.pc}"
            self.content_label.setText(f"{text}<br><br><span style=\"color: {COLORS['text_secondary']};\">{html.escape(pc_text)}</span>")
            # Active state - more opaque background
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {rgba_string(RGBA_SURFACE_DARK)};
                    border: 2px solid {self.stage_color};
                    border-radius: 12px;
                    box-shadow: 0 4px 12px {self.stage_color}40;
                }}
            """)
        else:
            # Show Empty
            self.content_label.setTextFormat(Qt.PlainText)
            self.content_label.setText("Empty")
            # Inactive state - transparent with dashed border
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {rgba_string(RGBA_SURFACE_TRANSPARENT)};
                    border: 2px dashed {COLORS['border_2']};
                    border-radius: 12px;
                }}
            """)


from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QPainter, QTextBlock


class LineNumberArea(QWidget):
    """Widget that displays line numbers alongside the code editor."""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class AssemblyCodeEditor(QPlainTextEdit):
    """
    Assembly source editor with integrated line number area.
    Uses QPlainTextEdit for better code editing support and proper line number alignment.
    pc_line is a 0-based editor line index (block index) for the current PC instruction.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pc_line: Optional[int] = None
        
        # Create line number area
        self.line_number_area = LineNumberArea(self)
        
        # Connect signals for updating line number area
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        
        # Initial setup
        self.update_line_number_area_width(0)
    
    def line_number_area_width(self) -> int:
        """Calculate the width needed for line number area."""
        digits = max(2, len(str(max(1, self.blockCount()))))
        # Width = arrow prefix (2 chars) + space + digits + padding
        # Using font metrics for accurate width
        space = self.fontMetrics().horizontalAdvance('9') * (digits + 4) + 10
        return space
    
    def update_line_number_area_width(self, _):
        """Update the viewport margins to make room for line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """Update the line number area when the editor scrolls or content changes."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        """Handle resize to keep line number area properly positioned."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
    
    def line_number_area_paint_event(self, event):
        """Paint the line numbers in the line number area."""
        painter = QPainter(self.line_number_area)
        
        # Background color
        painter.fillRect(event.rect(), QColor(COLORS['surface_3']))
        
        # Get the first visible block
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        # Font setup - make line numbers lighter/thinner
        font = self.font()
        font.setWeight(QFont.Light)  # Make font thinner
        painter.setFont(font)
        
        digits = max(2, len(str(max(1, self.blockCount()))))
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # Determine if this is the PC line
                is_pc_line = (self.pc_line is not None and block_number == self.pc_line)
                
                # Arrow prefix
                prefix = "->" if is_pc_line else "  "
                
                # Number with proper padding
                number = f"{prefix} {block_number + 1:>{digits}d}"
                
                # Set color based on PC line
                if is_pc_line:
                    painter.setPen(QColor(COLORS['accent_500']))
                    # Draw highlight background for PC line
                    highlight_rect = event.rect()
                    highlight_rect.setTop(top)
                    highlight_rect.setBottom(bottom)
                    highlight_color = QColor(COLORS['accent_500'])
                    highlight_color.setAlpha(40)
                    painter.fillRect(highlight_rect, highlight_color)
                else:
                    painter.setPen(QColor(COLORS['text_muted']))
                
                # Draw the line number with more padding from right border
                painter.drawText(0, top, self.line_number_area.width() - 15, 
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
        
        painter.end()

    def set_pc_line(self, line_index_or_none: Optional[int]) -> None:
        self.pc_line = line_index_or_none
        self._apply_pc_highlight()
        # Also update the line number area to show the arrow
        self.line_number_area.update()
        
        # Auto-scroll to make the PC line visible
        if self.pc_line is not None and self.pc_line >= 0:
            block = self.document().findBlockByNumber(int(self.pc_line))
            if block.isValid():
                cursor = QTextCursor(block)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()

    def _apply_pc_highlight(self) -> None:
        extra_selections = []

        if self.pc_line is not None and self.pc_line >= 0:
            # IMPORTANT: Use *block-based* positioning, not QTextCursor.Down.
            # Down moves by VISUAL lines (wrapped comment lines), which breaks PC alignment.
            block = self.document().findBlockByNumber(int(self.pc_line))
            if not block.isValid():
                self.setExtraSelections([])
                return

            cursor = QTextCursor(self.document())
            cursor.setPosition(block.position())

            # Use QTextEdit.ExtraSelection (works for QPlainTextEdit too)
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(COLORS['accent_500'])
            line_color.setAlpha(100)  # Increased from 60 to 100 for more visible highlight
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = cursor
            extra_selections.append(selection)

        # This is the single source of truth for the blue full-line PC highlight.
        self.setExtraSelections(extra_selections)


class ProcessorSimulatorGUI(QMainWindow):
    """Main GUI for the processor simulator - Modern Dark Navy Theme"""
    def __init__(self):
        super().__init__()
        self.processor = Processor()
        self.assembler = Assembler()
        # PC -> editor line mapping built during assembly/parsing (0-based editor lines)
        self.pc_to_editor_line_map: List[int] = []
        # Track the last source text we assembled so we can auto-assemble on Run/Step when needed.
        self._last_assembled_source: str = ""
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self.auto_step)
        self.execution_speed = 500  # ms between steps
        self.is_running = False
        # Debounce timer for auto-reset on code change (avoids resetting on every keystroke)
        self._auto_reset_timer = QTimer()
        self._auto_reset_timer.setSingleShot(True)
        self._auto_reset_timer.timeout.connect(lambda: self.reset_processor(silent=True))
        self.has_valid_program = False  # Track if assembly succeeded
        # Hazards history (GUI-only): persist across cycles; cleared on reset/program load
        self.hazard_history: List[dict] = []
        self._last_hazard_rendered_index = 0
        # Undo history (GUI-only)
        self.state_history: List[dict] = []
        self.max_history = 500
        # Track last written memory address for persistent highlight
        self.last_mem_write_addr = None
        self.init_ui()
        self.apply_theme()
        
    def apply_theme(self):
        """Apply light theme to the application"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_0']};
            }}
            QWidget {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_2']};
                border-radius: 6px;
                padding: 8px 16px;
                color: {COLORS['text_primary']};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_3']};
                border-color: {COLORS['accent_400']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['border_1']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_1']};
                color: {COLORS['text_muted']};
            }}
            QTextEdit {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
                selection-background-color: {COLORS['accent_500']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QTableWidget {{
                background-color: {COLORS['surface_2']};
                alternate-background-color: {COLORS['surface_3']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border_1']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent_500']}40;
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_3']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {COLORS['border_2']};
                font-weight: 600;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
                background-color: {COLORS['surface_1']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['surface_2']};
                color: {COLORS['text_secondary']};
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['accent_400']};
                color: {COLORS['text_primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['surface_3']};
            }}
            QFrame {{
                border-radius: 8px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border_2']};
                height: 4px;
                background: {COLORS['surface_3']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent_500']};
                border: 2px solid {COLORS['accent_400']};
                width: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['accent_400']};
            }}
            QScrollBar:vertical {{
                background: {COLORS['surface_1']};
                width: 10px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border_2']};
                min-height: 20px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {COLORS['surface_1']};
                height: 10px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {COLORS['border_2']};
                min-width: 20px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {COLORS['text_secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QMessageBox {{
                background-color: {COLORS['surface_1']};
                color: {COLORS['text_primary']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                background-color: transparent;
            }}
            QMessageBox QPushButton {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 6px;
                padding: 8px 20px;
                color: {COLORS['text_primary']};
                font-weight: 500;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {COLORS['surface_3']};
                border-color: {COLORS['accent_400']};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {COLORS['border_1']};
            }}
        """)
        
    def init_ui(self):
        """Initialize the modern UI"""
        self.setWindowTitle("16-bit RISC Pipeline Simulator")
        self.setGeometry(50, 50, 1600, 950)
        
        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== TOP BAR =====
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_1']};
                border-bottom: 1px solid {COLORS['border_1']};
                border-radius: 0px;
            }}
        """)
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        
        title = QLabel("16-bit RISC Pipeline Simulator")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
        """)
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        main_layout.addWidget(top_bar)
        
        # ===== CONTROLS BAR =====
        controls_bar = QFrame()
        controls_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_1']};
                border-bottom: 1px solid {COLORS['border_1']};
                border-radius: 0px;
            }}
        """)
        controls_bar.setFixedHeight(100)
        controls_layout = QVBoxLayout(controls_bar)
        controls_layout.setContentsMargins(20, 10, 20, 10)
        controls_layout.setSpacing(12)
        
        # First row - buttons and speed
        first_row = QHBoxLayout()
        first_row.setSpacing(10)
        
        # Reset button (red) - always enabled so user can recover from any state
        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.clicked.connect(self.reset_processor)
        self.btn_reset.setEnabled(True)
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger_500']};
                border: none;
                color: white;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger_600']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_2']};
                color: {COLORS['text_muted']};
            }}
        """)
        first_row.addWidget(self.btn_reset)
        
        # Step Back button (Undo) — opposite icon of Step Cycle (rewind vs fast-forward)
        self.step_back_btn = QPushButton("⏪ Step Back")
        self.step_back_btn.setEnabled(False)
        self.step_back_btn.clicked.connect(self.step_back)
        first_row.addWidget(self.step_back_btn)

        # Step Cycle button
        self.btn_step_cycle = QPushButton("⏩ Step Cycle")
        self.btn_step_cycle.clicked.connect(self.step_cycle)
        self.btn_step_cycle.setEnabled(False)
        first_row.addWidget(self.btn_step_cycle)
        # Alias (per spec)
        self.step_cycle_btn = self.btn_step_cycle
        
        # Mode label removed per request (mode-lock behavior remains)
        
        # Run/Pause button (green/yellow)
        self.btn_run = QPushButton("▶️ Run")
        self.btn_run.clicked.connect(self.toggle_run)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['success_600']},
                    stop:1 {COLORS['success_500']}
                );
                border: none;
                color: white;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success_600']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_2']};
                color: {COLORS['text_muted']};
            }}
        """)
        first_row.addWidget(self.btn_run)
        
        first_row.addSpacing(20)
        
        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        first_row.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self.update_speed)
        first_row.addWidget(self.speed_slider)
        
        # Speed percentage display
        self.speed_value_label = QLabel("50%")
        self.speed_value_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px; font-weight: 600;")
        first_row.addWidget(self.speed_value_label)
        
        first_row.addStretch()
        
        # Statistics
        self.lbl_cycle = QLabel("0")
        self.lbl_cycle.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                color: {COLORS['text_primary']};
            }}
        """)
        cycle_container = self.create_stat_widget("Cycle", self.lbl_cycle)
        first_row.addWidget(cycle_container)
        
        self.lbl_pc = QLabel("0")
        self.lbl_pc.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                color: {COLORS['text_primary']};
            }}
        """)
        pc_container = self.create_stat_widget("PC", self.lbl_pc)
        first_row.addWidget(pc_container)
        
        self.lbl_instructions = QLabel("0")
        self.lbl_instructions.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                color: {COLORS['text_primary']};
            }}
        """)
        inst_container = self.create_stat_widget("Instructions", self.lbl_instructions)
        first_row.addWidget(inst_container)
        
        self.lbl_cpi = QLabel("0.00")
        self.lbl_cpi.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                color: {COLORS['text_primary']};
            }}
        """)
        cpi_container = self.create_stat_widget("CPI", self.lbl_cpi)
        first_row.addWidget(cpi_container)
        
        controls_layout.addLayout(first_row)
        
        # Second row previously showed hazard badges; moved onto the Hazards panel (right side).
        
        main_layout.addWidget(controls_bar)
        
        # ===== MAIN CONTENT AREA =====
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # LEFT PANEL - Assembly Editor
        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_1']};
                border-right: 1px solid {COLORS['border_1']};
                border-radius: 0px;
            }}
        """)
        left_panel.setFixedWidth(480)  # Assembly Code editörü için genişlik artırıldı
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(12)
        
        editor_header = QHBoxLayout()
        editor_header.setSpacing(6)
        editor_title = QLabel("Assembly Code")
        editor_title.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
        """)
        editor_header.addWidget(editor_title)
        editor_header.addStretch()

        # Load File button (loads .asm into the editor; does not assemble automatically)
        self.btn_load_file = QPushButton("📂 Load")
        self.btn_load_file.clicked.connect(self.load_file)
        self.btn_load_file.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_3']};
                border: 1px solid {COLORS['border_1']};
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_2']};
            }}
        """)
        editor_header.addWidget(self.btn_load_file)
        
        # Immediate Mode Selector (auto-assembles on Step/Run)
        editor_header.addSpacing(10)
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
        """)
        editor_header.addWidget(mode_label)
        
        self.imm_mode_combo = QComboBox()
        self.imm_mode_combo.addItems(["Signed", "Unsigned"])
        self.imm_mode_combo.setCurrentText("Signed")
        self.imm_mode_combo.currentTextChanged.connect(self.on_imm_mode_changed)
        self.imm_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_1']};
                color: {COLORS['text_primary']};
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 4px;
                min-width: 80px;
            }}
            QComboBox:hover {{
                background-color: {COLORS['surface_3']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface_2']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent_500']};
                border: 1px solid {COLORS['border_1']};
            }}
        """)
        editor_header.addWidget(self.imm_mode_combo)
        
        left_layout.addLayout(editor_header)
        
        # Code editor with line numbers
        editor_container = QWidget()
        editor_layout = QHBoxLayout(editor_container)
        editor_layout.setSpacing(0)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Shared monospace font to keep metrics identical
        code_font = QFont("Consolas", 12)
        code_font.setStyleHint(QFont.Monospace)
        code_font.setFixedPitch(True)
        
        # Code editor (assembly) with integrated line number area
        self.code_editor = AssemblyCodeEditor()
        # No line wrapping - allow horizontal scrolling for long lines
        self.code_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.code_editor.setFont(code_font)
        self.code_editor.document().setDocumentMargin(0)
        self.code_editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.code_editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Start with an empty editor
        self.code_editor.setPlainText("")
        self.code_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                padding: 5px;
                selection-background-color: {COLORS['accent_500']};
            }}
        """)
        # Syntax highlighting for assembly
        self.highlighter = AssemblyHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self._sync_step_buttons_with_state)
        # Auto-reset on code change (silent, no status messages)
        self.code_editor.textChanged.connect(self._on_code_changed)
        editor_layout.addWidget(self.code_editor)
        
        # Give the editor more vertical space; Hazards will live under Registers on the right.
        left_layout.addWidget(editor_container, 6)
        
        # Hazards panel (moved under Registers on the right panel)
        hazard_frame = QFrame()
        hazard_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['danger_500']};
                border-radius: 8px;
            }}
        """)
        hazard_frame.setMinimumHeight(240)
        hazard_layout = QVBoxLayout(hazard_frame)
        hazard_layout.setContentsMargins(10, 10, 10, 10)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        lbl_hazards = QLabel("⚠️ Hazards")
        lbl_hazards.setStyleSheet(f"color: {COLORS['danger_500']}; font-weight: bold; font-size: 13px;")
        header_row.addWidget(lbl_hazards)
        
        # Stat cards for Stall, Flush, Forward counters
        stalls, flushes, forwards = self._hazard_totals_from_history()
        self.stall_card, self.stall_label = self.create_stat_card("Stall", stalls, COLORS['warning_500'])
        self.flush_card, self.flush_label = self.create_stat_card("Flush", flushes, COLORS['danger_500'])
        self.forward_card, self.forward_label = self.create_stat_card("Forward", forwards, COLORS['success_500'])
        
        header_row.addWidget(self.stall_card)
        header_row.addWidget(self.flush_card)
        header_row.addWidget(self.forward_card)
        header_row.addStretch()

        hazard_layout.addLayout(header_row)
        self.hazard_table = QTableWidget()
        self.hazard_table.setColumnCount(4)
        self.hazard_table.setHorizontalHeaderLabels(["#", "Stage", "Hazard Type", "Status"])
        self.hazard_table.verticalHeader().setVisible(False)
        self.hazard_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.hazard_table.setSelectionMode(QTableWidget.NoSelection)  # No selection highlight
        self.hazard_table.cellDoubleClicked.connect(self.show_hazard_details)  # Double-click to show details
        self.hazard_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.hazard_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.hazard_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.hazard_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.hazard_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface_1']};
                border: none;
                gridline-color: {COLORS['border_1']};
                color: {COLORS['text_primary']};
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_3']};
                color: {COLORS['text_secondary']};
                font-weight: bold;
                border: 1px solid {COLORS['border_1']};
                padding: 4px;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
        """)
        
        # Status message
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 500;
                padding: 10px 14px;
                background-color: {COLORS['surface_1']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
            }}
        """)
        # Place status just under the code editor
        left_layout.addWidget(self.lbl_status)

        # Hazards panel content - NOW ADDED TO LEFT PANEL (below code editor)
        hazard_layout.addWidget(self.hazard_table)
        left_layout.addWidget(hazard_frame, 2)  # Add hazard panel to left panel
        
        content_layout.addWidget(left_panel)
        
        # CENTER PANEL - Pipeline Visualization
        center_panel = QFrame()
        center_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_1']};
                border-right: 1px solid {COLORS['border_1']};
                border-left: 1px solid {COLORS['border_1']};
                border-radius: 0px;
            }}
        """)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.setSpacing(20)
        
        # Pipeline stages title
        pipeline_title = QLabel("Pipeline Stages")
        pipeline_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
        """)
        center_layout.addWidget(pipeline_title)
        
        # Pipeline stages
        stages_layout = QHBoxLayout()
        stages_layout.setSpacing(12)
        
        self.stage_if = StageWidget("IF", COLORS['stage_if'])
        self.stage_id = StageWidget("ID", COLORS['stage_id'])
        self.stage_ex = StageWidget("EX", COLORS['stage_ex'])
        self.stage_mem = StageWidget("MEM", COLORS['stage_mem'])
        self.stage_wb = StageWidget("WB", COLORS['stage_wb'])
        
        stages_layout.addWidget(self.stage_if)
        stages_layout.addWidget(self.stage_id)
        stages_layout.addWidget(self.stage_ex)
        stages_layout.addWidget(self.stage_mem)
        stages_layout.addWidget(self.stage_wb)
        
        center_layout.addLayout(stages_layout)
        
        # Pipeline registers info
        registers_title = QLabel("Pipeline Registers")
        registers_title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
                margin-top: 10px;
            }}
        """)
        center_layout.addWidget(registers_title)
        
        pipe_regs_layout = QHBoxLayout()
        pipe_regs_layout.setSpacing(12)
        
        self.pipe_if_id = self.create_pipeline_register("IF/ID")
        self.pipe_id_ex = self.create_pipeline_register("ID/EX")
        self.pipe_ex_mem = self.create_pipeline_register("EX/MEM")
        self.pipe_mem_wb = self.create_pipeline_register("MEM/WB")
        
        pipe_regs_layout.addWidget(self.pipe_if_id)
        pipe_regs_layout.addWidget(self.pipe_id_ex)
        pipe_regs_layout.addWidget(self.pipe_ex_mem)
        pipe_regs_layout.addWidget(self.pipe_mem_wb)
        
        center_layout.addLayout(pipe_regs_layout)
        
        # Execution trace / console log
        # Bottom Container: Output only
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        # Nudge Cycle Output panel slightly downward for better visual balance
        bottom_layout.setContentsMargins(0, 24, 0, 0)
        bottom_layout.setSpacing(10)

        # RIGHT: Output Panel
        output_frame = QFrame()
        output_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_2']};
                border: 1px solid {COLORS['border_1']};
                border-radius: 8px;
            }}
        """)
        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(10, 10, 10, 10)
        lbl_output = QLabel("ℹ️ Cycle Output")
        lbl_output.setStyleSheet(f"color: {COLORS['accent_400']}; font-weight: bold;")
        output_layout.addWidget(lbl_output)
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setLineWrapMode(QTextEdit.NoWrap)
        output_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.output_log.setStyleSheet("border: none; background: transparent; font-family: Consolas; font-size: 11px;")
        self.output_log.setMinimumHeight(280)
        output_layout.addWidget(self.output_log)
        bottom_layout.addWidget(output_frame, 1)

        center_layout.addWidget(bottom_container, 1)
        
        content_layout.addWidget(center_panel, 1)
        
        # RIGHT PANEL - State Viewer
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_1']};
                border-left: 1px solid {COLORS['border_1']};
                border-radius: 0px;
            }}
        """)
        right_panel.setFixedWidth(450)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(10)
        
        # Tabs for Registers and Instruction Memory (on top)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        # Registers tab
        registers_widget = QWidget()
        registers_layout = QVBoxLayout(registers_widget)
        registers_layout.setContentsMargins(0, 10, 0, 0)
        
        self.register_table = QTableWidget(8, 4)
        self.register_table.setHorizontalHeaderLabels(["Reg", "Alias", "Hex", "Dec"])
        # Balanced header sizing (compact but readable)
        reg_hdr = self.register_table.horizontalHeader()
        reg_hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Reg
        reg_hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Alias
        reg_hdr.setSectionResizeMode(2, QHeaderView.Stretch)           # Hex
        reg_hdr.setSectionResizeMode(3, QHeaderView.Stretch)           # Dec
        self.register_table.setAlternatingRowColors(True)
        # Prevent selection styling from darkening our neon last-written highlight
        self.register_table.setSelectionMode(QTableWidget.NoSelection)
        # Delegate-based highlight so selection/QSS cannot override last-written neon row
        self.register_table.setItemDelegate(LastWrittenDelegate(self.register_table))
        # Compact rows + monospace items
        reg_font = QFont("Consolas", 10)
        reg_font.setStyleHint(QFont.Monospace)
        reg_font.setFixedPitch(True)
        self.register_table.setFont(reg_font)
        self.register_table.verticalHeader().setDefaultSectionSize(28)
        # Make vertical header (row numbers) readable and stable
        reg_vhdr = self.register_table.verticalHeader()
        reg_vhdr.setVisible(True)
        reg_vhdr.setFixedWidth(36)  # Match Data Memory row-number column width
        reg_vhdr.setDefaultAlignment(Qt.AlignCenter)
        reg_vhdr.setSectionResizeMode(QHeaderView.Fixed)
        
        reg_aliases = ["Zero", "Caller", "Caller", "Caller", "Caller", "Callee", "Callee", "Callee"]
        for i in range(8):
            self.register_table.setItem(i, 0, QTableWidgetItem(f"$r{i}"))
            self.register_table.setItem(i, 1, QTableWidgetItem(reg_aliases[i]))
            self.register_table.setItem(i, 2, QTableWidgetItem("0x0000"))
            self.register_table.setItem(i, 3, QTableWidgetItem("0"))
            for j in range(4):
                self.register_table.item(i, j).setFlags(Qt.ItemIsEnabled)
                self.register_table.item(i, j).setFont(reg_font)
            self.register_table.setRowHeight(i, 28)
        
        
        # Registers tab
        registers_widget = QWidget()
        registers_layout = QVBoxLayout(registers_widget)
        registers_layout.setContentsMargins(0, 10, 0, 0)
        
        self.register_table = QTableWidget(8, 4)
        self.register_table.setHorizontalHeaderLabels(["Reg", "Alias", "Hex", "Dec"])
        # Balanced header sizing (compact but readable)
        reg_hdr = self.register_table.horizontalHeader()
        reg_hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Reg
        reg_hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Alias
        reg_hdr.setSectionResizeMode(2, QHeaderView.Stretch)           # Hex
        reg_hdr.setSectionResizeMode(3, QHeaderView.Stretch)           # Dec
        self.register_table.setAlternatingRowColors(True)
        # Prevent selection styling from darkening our neon last-written highlight
        self.register_table.setSelectionMode(QTableWidget.NoSelection)
        # Delegate-based highlight so selection/QSS cannot override last-written neon row
        self.register_table.setItemDelegate(LastWrittenDelegate(self.register_table))
        # Compact rows + monospace items
        reg_font = QFont("Consolas", 10)
        reg_font.setStyleHint(QFont.Monospace)
        reg_font.setFixedPitch(True)
        self.register_table.setFont(reg_font)
        self.register_table.verticalHeader().setDefaultSectionSize(28)
        # Make vertical header (row numbers) readable and stable
        reg_vhdr = self.register_table.verticalHeader()
        reg_vhdr.setVisible(True)
        reg_vhdr.setFixedWidth(36)  # Match Data Memory row-number column width
        reg_vhdr.setDefaultAlignment(Qt.AlignCenter)
        reg_vhdr.setSectionResizeMode(QHeaderView.Fixed)
        
        reg_aliases = ["Zero", "Caller", "Caller", "Caller", "Caller", "Callee", "Callee", "Callee"]
        for i in range(8):
            self.register_table.setItem(i, 0, QTableWidgetItem(f"$r{i}"))
            self.register_table.setItem(i, 1, QTableWidgetItem(reg_aliases[i]))
            self.register_table.setItem(i, 2, QTableWidgetItem("0x0000"))
            self.register_table.setItem(i, 3, QTableWidgetItem("0"))
            for j in range(4):
                self.register_table.item(i, j).setFlags(Qt.ItemIsEnabled)
                self.register_table.item(i, j).setFont(reg_font)
            self.register_table.setRowHeight(i, 28)
        
        registers_layout.addWidget(self.register_table)
        self.tabs.addTab(registers_widget, "Registers")
        
        # Instruction Memory tab
        inst_mem_widget = QWidget()
        inst_mem_layout = QVBoxLayout(inst_mem_widget)
        inst_mem_layout.setContentsMargins(0, 10, 0, 0)
        
        # Start with 0 rows, will be set dynamically based on program size
        self.inst_memory_table = QTableWidget(0, 4)
        self.inst_memory_table.setHorizontalHeaderLabels(["PC", "Assembly", "Binary", "Hex"])
        inst_hdr = self.inst_memory_table.horizontalHeader()
        inst_hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # PC
        inst_hdr.setSectionResizeMode(1, QHeaderView.Stretch)           # Assembly
        inst_hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Binary (show full bits)
        inst_hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Hex
        # Give Assembly column enough minimum width to show full instructions
        self.inst_memory_table.setColumnWidth(1, 250)
        self.inst_memory_table.setAlternatingRowColors(True)
        # Disable selection highlighting (no green highlight on click)
        self.inst_memory_table.setSelectionMode(QTableWidget.NoSelection)
        self.inst_memory_table.setFocusPolicy(Qt.NoFocus)
        inst_font = QFont("Consolas", 10)
        inst_font.setStyleHint(QFont.Monospace)
        inst_font.setFixedPitch(True)
        self.inst_memory_table.setFont(inst_font)
        # Increase row height so assembly instructions fit comfortably
        self.inst_memory_table.verticalHeader().setDefaultSectionSize(32)
        # Match Data Memory row-number column width
        inst_vhdr = self.inst_memory_table.verticalHeader()
        inst_vhdr.setVisible(True)
        inst_vhdr.setFixedWidth(36)
        inst_vhdr.setDefaultAlignment(Qt.AlignCenter)
        inst_vhdr.setSectionResizeMode(QHeaderView.Fixed)
        # Show full binary strings (no ellipsis), keep single-line cells, allow horizontal scroll when needed
        self.inst_memory_table.setWordWrap(False)
        try:
            self.inst_memory_table.setTextElideMode(Qt.ElideNone)
        except Exception:
            pass
        self.inst_memory_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Rich-text rendering for Assembly column (color registers/numbers/opcodes)
        self.inst_memory_table.setItemDelegateForColumn(1, RichTextDelegate(self.inst_memory_table))
        
        inst_mem_layout.addWidget(self.inst_memory_table)
        self.tabs.addTab(inst_mem_widget, "Instruction Memory")
        
        # Add tabs to layout (top position)
        right_layout.addWidget(self.tabs, 3)
        
        # Data Memory section (direct display, below tabs)
        data_mem_header = QLabel("Data Memory")
        data_mem_header.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_500']};
                font-weight: bold;
                font-size: 14px;
                padding: 5px 0px;
                margin-top: -5px;
            }}
        """)
        right_layout.addWidget(data_mem_header)
        
        # Data Memory table
        self.memory_table = QTableWidget(0, 3)
        # Sütun başlıklarını "Value (Hex)" ve "Value (Dec)" yaparak verinin ne olduğunu netleştiriyoruz.
        self.memory_table.setHorizontalHeaderLabels(["Address", "Value (Hex)", "Value (Dec)"])
        self.memory_table.horizontalHeader().setStretchLastSection(True)
        self.memory_table.setAlternatingRowColors(True)
        # Prevent selection styling from darkening our neon last-written highlight
        self.memory_table.setSelectionMode(QTableWidget.NoSelection)
        # Delegate-based highlight for last-written memory address (same as registers)
        self.memory_table.setItemDelegate(LastWrittenDelegate(self.memory_table))
        # Make vertical header consistent across tables (row numbers)
        mem_vhdr = self.memory_table.verticalHeader()
        mem_vhdr.setVisible(True)
        mem_vhdr.setFixedWidth(36)
        mem_vhdr.setDefaultAlignment(Qt.AlignCenter)
        mem_vhdr.setSectionResizeMode(QHeaderView.Fixed)
        self.memory_table.verticalHeader().setDefaultSectionSize(28)
        
        right_layout.addWidget(self.memory_table, 2)
        
        content_layout.addWidget(right_panel)
        
        main_layout.addWidget(content)
        
        # Initial update
        self.update_display()
    
    def create_stat_widget(self, title: str, value_label: QLabel) -> QWidget:
        """Create a statistic display widget"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(12, 0, 12, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 10px;
                font-weight: 500;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return container
    
    def create_badge(self, text: str, color: str) -> QLabel:
        """Create a colored badge label"""
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: 1px solid {color};
                border-radius: 12px;
                padding: 5px 16px;
                color: {color};
                font-size: 11px;
                font-weight: 600;
                font-family: 'Consolas', monospace;
                min-width: 90px;
            }}
        """)
        badge.setAlignment(Qt.AlignCenter)
        return badge
    
    def create_stat_card(self, title: str, value: int, color: str) -> tuple:
        """Create a modern stat card with title and value display.
        Returns (card_widget, value_label) tuple for updating the value later."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        
        # Modern card design with colored border
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_2']};
                border: 2px solid {color};
                border-radius: 8px;
            }}
            QLabel {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        # Internal layout
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(1)
        
        # Value (large number display)
        lbl_value = QLabel(str(value))
        lbl_value.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        lbl_value.setAlignment(Qt.AlignCenter)
        lbl_value.setFont(QFont("Consolas", 14, QFont.Bold))
        
        # Title (small label below)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600; font-size: 8px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFont(QFont("Segoe UI", 8, QFont.DemiBold))
        
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_title)
        
        card.setLayout(layout)
        card.setFixedWidth(50)  # Compact width for header placement
        card.setFixedHeight(45)  # Compact height
        
        return card, lbl_value
    
    def create_pipeline_register(self, name: str) -> QFrame:
        """Create a pipeline register info widget"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_3']};
                border: 1px solid {COLORS['border_2']};
                border-radius: 10px;
                padding: 8px;
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)
        
        title = QLabel(name)
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
                font-weight: 700;
                font-family: 'Consolas', monospace;
            }}
        """)
        layout.addWidget(title)
        
        content = QLabel("--")
        content.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-family: 'Consolas', monospace;
                background-color: rgba({RGBA_SURFACE_LIGHT[0]}, {RGBA_SURFACE_LIGHT[1]}, {RGBA_SURFACE_LIGHT[2]}, 0.35);
                border: 1px solid {COLORS['border_1']};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(content)
        
        # Store content label for later updates
        setattr(container, 'content_label', content)
        container.setMinimumWidth(170)
        return container

    def create_stage_arrow(self) -> QLabel:
        """Create an arrow label between pipeline stages."""
        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        arrow.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 28px;
                font-weight: 900;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """)
        arrow.setFixedWidth(40)
        arrow.setFixedHeight(60)
        return arrow
    
    def _compute_editor_line_for_pc(self) -> Optional[int]:
        # Highlight instruction currently in pipeline (IF stage), not the next one to fetch
        pc = None
        if_id = getattr(self.processor, "if_id", None)
        if if_id and hasattr(if_id, 'instruction') and if_id.instruction:
            # Use the instruction currently in IF/ID pipeline register
            pc = if_id.instruction.pc
        else:
            # Fallback to processor PC before first cycle
            pc = getattr(self.processor, "pc", 0)
        
        if pc is not None and 0 <= pc < len(self.pc_to_editor_line_map):
            return self.pc_to_editor_line_map[pc]
        return None

    def _refresh_pc_indicator(self) -> None:
        """Refresh PC indicator in the code editor."""
        editor_line = self._compute_editor_line_for_pc() if getattr(self.processor, "instructions", None) else None
        self.code_editor.set_pc_line(editor_line)

    def highlight_current_line(self):
        """Backward-compatible wrapper: PC highlight is driven by pc_to_editor_line_map."""
        self._refresh_pc_indicator()
    
    def _on_code_changed(self):
        """Handle code editor text change - auto-reset with debounce"""
        # Restart debounce timer (300ms delay to avoid resetting on every keystroke)
        self._auto_reset_timer.start(300)
    
    def load_program(self):
        """Load and assemble the program"""
        code = self.code_editor.toPlainText()
        if not code.strip():
            self.has_valid_program = False
            self.btn_step_cycle.setEnabled(False)
            self.btn_run.setEnabled(False)
            self.step_back_btn.setEnabled(False)
            self.lbl_status.setText("Status: ⚠️ Please enter assembly code first")
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['warning_500']};
                    background-color: {COLORS['warning_500']}20;
                    border: 1px solid {COLORS['warning_500']};
                    padding: 8px;
                    border-radius: 6px;
                }}
            """)
            return
        
        try:
            # Clear any previous validation errors before attempting assembly
            self.processor.clear_validation_error()
            
            self.assembler = Assembler()
            # IMPORTANT: load_program() recreates Assembler(), so we must re-apply the UI mode here.
            # Otherwise the dropdown may show Unsigned while the assembler validates as Signed.
            if hasattr(self, "imm_mode_combo"):
                try:
                    self.assembler.set_immediate_mode(self.imm_mode_combo.currentText())
                except Exception:
                    # Fall back to legacy setter if needed
                    self.assembler.set_imm_mode(self.imm_mode_combo.currentText().lower())
            instructions = self.assembler.parse(code)
            if not instructions:
                self.has_valid_program = False
                self.btn_step_cycle.setEnabled(False)
                self.btn_run.setEnabled(False)
                self.step_back_btn.setEnabled(False)
                self.lbl_status.setText("Status: ⚠️ No valid instructions found")
                self.lbl_status.setStyleSheet(f"""
                    QLabel {{
                        color: {COLORS['warning_500']};
                        background-color: {COLORS['warning_500']}20;
                        border: 1px solid {COLORS['warning_500']};
                        padding: 8px;
                        border-radius: 6px;
                    }}
                """)
                self.pc_to_editor_line_map = []
                self.code_editor.set_pc_line(None)
                self.update_line_numbers()
                return
            
            self.processor.load_program(instructions)
            # Store PC->editor line mapping produced by the assembler (0-based editor line indices)
            self.pc_to_editor_line_map = list(getattr(self.assembler, "pc_to_editor_line_map", []))
            # Remember what we assembled (used for auto-assemble on Run/Step).
            self._last_assembled_source = code
            try:
                self.code_editor.document().setModified(False)
            except Exception:
                pass
            # Clear hazard history on new program load (so history matches the run)
            self.hazard_history.clear()
            self._last_hazard_rendered_index = 0
            if hasattr(self, 'hazard_table'):
                self.hazard_table.setRowCount(0)
            # Clear undo history on new program load
            if hasattr(self, "state_history"):
                self.state_history.clear()
            if hasattr(self, "step_back_btn"):
                self.step_back_btn.setEnabled(False)
            self.lbl_status.setText(f"Status: ✅ Loaded {len(instructions)} instructions successfully")
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['success_500']};
                    background-color: {COLORS['success_500']}20;
                    border: 1px solid {COLORS['success_500']};
                    padding: 8px;
                    border-radius: 6px;
                }}
            """)
            self.btn_step_cycle.setEnabled(True)
            self.btn_run.setEnabled(True)
            self.btn_reset.setEnabled(True)
            self.has_valid_program = True  # Mark that we have a valid program
            # PC indicator (gutter arrow + blue highlight) must use the mapping, not UI counting.
            self._refresh_pc_indicator()
            self.update_display()
            self._sync_step_buttons_with_state()
            self.add_trace_log(f"✅ Program loaded: {len(instructions)} instructions")
            # Unlock mode selector on successful load
            self._lock_imm_mode(False)
        except Exception as e:
            # Assembly/validation FAILED - set error state and disable execution buttons
            self.processor.set_validation_error(str(e))
            self.has_valid_program = False
            
            # Update button states based on error
            self.update_action_buttons_enabled_state()
            
            # Show error in status label
            self.lbl_status.setText(f"Status: ❌ Assembly Failed - {str(e)}")
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['danger_500']};
                    background-color: {COLORS['danger_500']}20;
                    border: 1px solid {COLORS['danger_500']};
                    padding: 8px;
                    border-radius: 6px;
                }}
            """)
            
            # Log error to trace
            self.add_trace_log(f"❌ Assembly error: {str(e)}", error=True)
            
            # Show error popup
            QMessageBox.critical(
                self,
                "❌ Assembly Error",
                f"<b>Program could NOT be loaded due to validation error:</b><br><br>"
                f"{str(e)}<br><br>"
                f"<b>⚠️ Program NOT loaded. Fix the error and try again.</b>",
                QMessageBox.Ok
            )
            # Keep mode selector enabled on failure so user can change mode and retry
            self._lock_imm_mode(False)

    def _ensure_program_ready_for_execution(self) -> bool:
        """
        Make Run / Step Cycle usable without manually pressing Assemble.
        - If there is no loaded program (or mapping is missing), assemble now.
        - If program is halted, assemble now (restart from the current editor text).
        - If code changed since last assemble:
          - If the processor is still at the start, re-assemble.
          - Otherwise, keep the currently running program and warn the user.
        """
        # Block execution if there's a validation error
        if self.processor.has_validation_error:
            self._set_status(f"Status: ❌ Cannot execute - {self.processor.validation_error}", level="error")
            return False
        
        code = self.code_editor.toPlainText()
        if not code.strip():
            self._set_status("Status: ⚠️ Please enter assembly code first", level="warning")
            return False

        has_program = bool(getattr(self.processor, "instructions", []))
        halted = bool(getattr(self.processor, "halted", False))
        mapping_ok = bool(self.pc_to_editor_line_map)
        code_changed = (code != (self._last_assembled_source or ""))
        at_start = (getattr(self.processor, "cycle_count", 0) == 0 and getattr(self.processor, "pc", 0) == 0)

        if (not has_program) or (not mapping_ok) or halted:
            self.load_program()
            # Return False if assembly failed (has_valid_program flag will be False)
            if not self.has_valid_program:
                self._set_status("Status: ❌ Cannot execute - assembly failed", level="error")
                return False
            return bool(getattr(self.processor, "instructions", []))

        if code_changed and at_start and (not self.is_running):
            self.load_program()
            # Return False if assembly failed
            if not self.has_valid_program:
                self._set_status("Status: ❌ Cannot execute - assembly failed", level="error")
                return False
            return bool(getattr(self.processor, "instructions", []))

        if code_changed and (not at_start):
            # Don't silently destroy the current run; user can Reset to restart from the edited code.
            self._set_status("Status: ✏️ Code changed — press Reset to restart from edited code", level="warning")
        
        # Final check: even if we have a program, ensure it's valid
        if not self.has_valid_program:
            self._set_status("Status: ❌ Cannot execute - no valid program loaded", level="error")
            return False
        
        return True
    
    def on_imm_mode_changed(self, mode_text: str):
        """Handle immediate mode change (Signed/Unsigned)"""
        mode = mode_text.lower()  # "Signed" -> "signed", "Unsigned" -> "unsigned"
        
        # Update assembler and processor modes
        if hasattr(self, 'assembler') and self.assembler:
            # Assembler expects UI strings ("Signed"/"Unsigned") for validation
            try:
                self.assembler.set_immediate_mode(mode_text)
            except Exception:
                # Backwards compatible
                self.assembler.set_imm_mode(mode)
        self.processor.set_imm_mode(mode)
        
        # Auto-reset processor when mode changes (ensures clean state)
        self.reset_processor()
        
        # Log the mode change
        self.add_trace_log(f"🔧 Mode changed to: {mode_text}")
        
        # Update status
        self._set_status(f"Status: 🔧 Mode: {mode_text} (Auto-reset)", level="info")
    
    def _lock_imm_mode(self, locked: bool):
        """Lock or unlock the immediate mode selector
        
        Args:
            locked: If True, disable mode selector; if False, enable it
        """
        if hasattr(self, 'imm_mode_combo'):
            self.imm_mode_combo.setEnabled(not locked)

    def load_file(self):
        """Load an assembly file into the code editor (UI-only)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Assembly File",
            "",
            "Assembly Files (*.asm *.s *.txt);;All Files (*)"
        )
        if not file_path:
            return

        try:
            # Try UTF-8 first, then fall back for unusual encodings.
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()

            self.code_editor.setPlainText(content)
            # Loading a file does not assemble; clear mapping + PC indicator.
            self.pc_to_editor_line_map = []
            self.code_editor.set_pc_line(None)
            self.update_line_numbers()
            self._last_assembled_source = ""
            self._set_status(f"Status: 📂 Loaded file: {os.path.basename(file_path)}", level="success")
        except Exception as e:
            self._set_status(f"Status: ❌ Failed to load file: {e}", level="error")
    
    def step_execution(self):
        """Execute one clock cycle"""
        if self.processor.halted:
            self._set_status("Status: ✅ Execution complete (HALT)", level="success")
            self.add_trace_log("✅ Program execution complete", target=getattr(self, 'output_log', None))
            self.stop_execution()
            self._sync_step_buttons_with_state()
            return
        
        try:
            continue_exec = self.processor.step()
        except Exception as e:
            # Runtime error during execution (e.g., memory access violation)
            self.processor.set_validation_error(str(e))
            self.processor.halted = True
            self.has_valid_program = False
            self.stop_execution()
            
            error_msg = f"Runtime Error: {str(e)}"
            self._set_status(f"Status: ❌ {error_msg}", level="error")
            self.add_trace_log(f"❌ {error_msg}", error=True)
            
            # Update button states based on error
            self.update_action_buttons_enabled_state()
            
            # Show error popup
            QMessageBox.critical(
                self,
                "❌ Runtime Error",
                f"<b>Execution halted due to runtime error:</b><br><br>"
                f"{str(e)}<br><br>"
                f"<b>⚠️ Fix the program and assemble again.</b>",
                QMessageBox.Ok
            )
            return

        # Hazards: keep per-cycle hazards, but also append into GUI history and render incrementally
        self._append_current_hazards_to_history()
        self.update_hazard_table()

        # Update UI after hazards so totals/badges match visible table rows
        self.update_display()
        self._sync_step_buttons_with_state()

        # Status: show that we advanced one cycle and we're still running
        if not getattr(self.processor, "halted", False):
            c = getattr(self.processor, "cycle_count", 0)
            pc = getattr(self.processor, "pc", 0)
            self._set_status(f"Status: ⏩ Cycle {c} executed (PC {pc})", level="info")
        
        # Pretty cycle trace to output panel (append-based history)
        # Highlight "Cycle N" tokens in white for readability
        if hasattr(self, 'output_log'):
            raw = self.processor.format_cycle_trace_pretty()
            escaped = (raw.replace("&", "&amp;")
                          .replace("<", "&lt;")
                          .replace(">", "&gt;"))
            cycle_color = COLORS.get('text_primary', '#FFFFFF')
            escaped = re.sub(r"(Cycle\s+\d+)",
                             rf"<span style=\"color: {cycle_color}; font-weight: 600;\">\1</span>",
                             escaped)
            self.output_log.append(f"<pre style=\"margin:0;\">{escaped}</pre>")
            # Auto-scroll to the bottom so the latest cycle is visible
            self.output_log.moveCursor(QTextCursor.End)

        if not continue_exec:
            self._set_status("Status: ✅ Execution complete", level="success")
            self.stop_execution()
            self._sync_step_buttons_with_state()
            # Show completion statistics dialog
            completion_dialog = ExecutionCompletionDialog(self.processor, self)
            completion_dialog.exec()

    def step_cycle(self):
        """Step exactly one cycle."""
        if not self._ensure_program_ready_for_execution():
            return
        # Don't step if already halted
        if self.processor.halted:
            self._set_status("Status: ⚠️ Program already halted - use Step Back or Reset", level="warning")
            return
        # Lock mode selector once execution starts
        self._lock_imm_mode(True)
        self._push_snapshot()
        self.step_execution()
        self._sync_step_buttons_with_state()

    def _push_snapshot(self):
        """Push a deep snapshot for undo (GUI-only; does not affect execution)."""
        self.state_history.append({
            "processor": self.processor.snapshot_state(),
            "hazard_history": copy.deepcopy(getattr(self, "hazard_history", [])),
            "_last_hazard_rendered_index": getattr(self, "_last_hazard_rendered_index", 0),
        })
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        if hasattr(self, "step_back_btn"):
            self.step_back_btn.setEnabled(len(self.state_history) > 0)

    def step_back(self):
        """Undo: restore processor + GUI-side hazard history to the previous snapshot."""
        if not self.state_history:
            if hasattr(self, "step_back_btn"):
                self.step_back_btn.setEnabled(False)
            return
        
        # Lock mode selector during execution operations
        self._lock_imm_mode(True)

        snap = self.state_history.pop()

        # Restore processor
        self.processor.restore_state(snap["processor"])

        # Restore GUI-side hazard history buffer and re-render table
        if hasattr(self, "hazard_history"):
            self.hazard_history = copy.deepcopy(snap.get("hazard_history", []))
        self._last_hazard_rendered_index = snap.get("_last_hazard_rendered_index", 0)
        if hasattr(self, "hazard_table"):
            self.hazard_table.setRowCount(0)
            # Re-render the history into the table from scratch
            self._last_hazard_rendered_index = 0
            self.update_hazard_table()

        # No Step Instruction feature: nothing else to restore for step-mode/PC overrides

        # Refresh all UI views (registers, memory, pipeline, hazards, etc.)
        self.update_display()
        self._sync_step_buttons_with_state()

        # Status: explicit undo + whether we can continue
        c = getattr(self.processor, "cycle_count", 0)
        pc = getattr(self.processor, "pc", 0)
        if getattr(self.processor, "halted", False):
            self._set_status(f"Status: ⏪ Step Back → Cycle {c} (PC {pc}) — still HALTED", level="warning")
        else:
            self._set_status(f"Status: ⏪ Step Back → Cycle {c} (PC {pc}) — ready", level="info")

        if hasattr(self, "step_back_btn"):
            self.step_back_btn.setEnabled(len(self.state_history) > 0)

        # Optional: add a small note in output without deleting history
        self.add_trace_log(f"← Reverted to Cycle {self.processor.cycle_count}", target=getattr(self, 'output_log', None))
    
    def toggle_run(self):
        """Toggle continuous execution"""
        if not self.is_running:
            if not self._ensure_program_ready_for_execution():
                return
            # Lock mode selector once execution starts
            self._lock_imm_mode(True)
            self.is_running = True
            self.btn_run.setText("⏸️ Pause")
            self.btn_run.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['warning_500']};
                    border: none;
                    color: white;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['warning_600']};
                }}
            """)
            self.execution_timer.start(self.execution_speed)
            self.add_trace_log("▶️ Continuous execution started")
        else:
            self.stop_execution()
    
    def stop_execution(self):
        """Stop continuous execution (paused state allows Step Cycle/Step Back)"""
        self.is_running = False
        self.execution_timer.stop()
        self.btn_run.setText("▶️ Run")
        self.btn_run.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['success_600']},
                    stop:1 {COLORS['success_500']}
                );
                border: none;
                color: white;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success_600']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_2']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.add_trace_log("⏸️ Execution paused")
        
        # Sync button states properly after stopping
        self._sync_step_buttons_with_state()
        
        # Ensure step back button state is correct
        if hasattr(self, "step_back_btn"):
            self.step_back_btn.setEnabled(len(self.state_history) > 0)
    
    def auto_step(self):
        """Auto-step for continuous execution"""
        if not self.processor.halted:
            self._push_snapshot()  # Save state for Step Back functionality
            self.step_execution()
        else:
            self.stop_execution()
    
    def reset_processor(self, silent=False):
        """Reset the processor
        
        Args:
            silent: If True, don't show status/log messages (for auto-reset on code change)
        """
        # Clear any validation errors on reset
        self.processor.clear_validation_error()
        self.processor.reset()

        # ========================================================
        # YENİ EKLENEN KISIM: Instruction Memory'yi Temizle
        # ========================================================
        self.processor.instructions = []  # İşlemci hafızasındaki komutları sil
        self.processor.instruction_count = 0
        self.has_valid_program = False    # Geçerli program olmadığını işaretle
        self.inst_memory_table.setRowCount(0) # Tabloyu görsel olarak temizle
        self._last_assembled_source = ""  # Son derlenen kodu unut
        # ========================================================

        if self.is_running:
            self.stop_execution()
        # Clear mapping + PC indicator on reset.
        self.pc_to_editor_line_map = []
        self.code_editor.set_pc_line(None)
        # Clear hazard history + hazard/output logs
        self.hazard_history.clear()
        self._last_hazard_rendered_index = 0
        # Clear last memory write highlight
        self.last_mem_write_addr = None
        if hasattr(self, 'hazard_table'):
            self.hazard_table.setRowCount(0)
        # Clear undo history
        if hasattr(self, "state_history"):
            self.state_history.clear()
        if hasattr(self, "step_back_btn"):
            self.step_back_btn.setEnabled(False)
        if hasattr(self, 'output_log'):
            self.output_log.clear()
        self.update_display()
        self._sync_step_buttons_with_state()
        
        # Show status/log messages only if not silent
        if not silent:
            self._set_status("Status: 🔄 Processor reset (Memory Cleared)", level="info")
            self.add_trace_log("🔄 Processor reset and memory cleared", target=getattr(self, 'output_log', None))
        
        # DEĞİŞİKLİK: Program silindiği için butonları disable etmemiz lazım, 
        # _sync_step_buttons_with_state() bunu has_valid_program=False olduğu için otomatik yapacaktır.
        
        # Unlock mode selector on reset
        self._lock_imm_mode(False)
    
    def update_speed(self, value):
        """Update execution speed"""
        # Invert: higher slider value = faster execution = lower delay
        self.execution_speed = 1000 - (value * 10)
        if self.is_running:
            self.execution_timer.setInterval(self.execution_speed)
        # Update speed percentage display
        if hasattr(self, 'speed_value_label'):
            self.speed_value_label.setText(f"{value}%")
    
    def add_trace_log(self, message: str, warning: bool = False, error: bool = False, target: Optional[QTextEdit] = None):
        """Add message to a specified log (hazard/output); default to output_log if not provided."""
        log_widget = target if target else getattr(self, 'output_log', None)
        if not log_widget:
            return
        if error:
            color = COLORS['danger_500']
        elif warning:
            color = COLORS['warning_500']
        else:
            color = COLORS['text_secondary']
        
        log_widget.append(f'<span style="color: {color};">{message}</span>')
        # Auto-scroll to bottom
        cursor = log_widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        log_widget.setTextCursor(cursor)

    def _set_status(self, text: str, level: str = "info"):
        """Set the status label text with consistent styling (UI-only)."""
        if not hasattr(self, "lbl_status"):
            return
        self.lbl_status.setText(text)

        level = (level or "info").lower()
        if level in ("success", "ok"):
            color = COLORS['success_600']  # Daha koyu yeşil - daha iyi kontrast
            bg = f"{COLORS['success_500']}30"  # Daha opak arka plan
            border = COLORS['success_600']
        elif level in ("warning", "warn"):
            color = COLORS['warning_600']  # Daha koyu turuncu - daha iyi kontrast
            bg = f"{COLORS['warning_500']}30"  # Daha opak arka plan
            border = COLORS['warning_600']
        elif level in ("error", "danger", "fail"):
            color = COLORS['danger_600']  # Daha koyu kırmızı - daha iyi kontrast
            bg = f"{COLORS['danger_500']}30"  # Daha opak arka plan
            border = COLORS['danger_600']
        else:
            color = COLORS['text_primary']  # Info için koyu metin
            bg = COLORS['surface_1']  # Açık arka plan
            border = COLORS['accent_400']  # Açık mavi kenarlık

        self.lbl_status.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: 500;
                padding: 10px 14px;
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 8px;
            }}
        """)
    
    def update_action_buttons_enabled_state(self):
        """Update enabled/disabled state of action buttons based on error state
        
        This is called when:
        - Assembly succeeds or fails
        - Validation error occurs during execution
        - Processor is reset
        
        Rules:
        - If has_validation_error is True, disable all execution buttons
        - Otherwise, enable based on normal state (has_valid_program, halted, etc.)
        """
        has_error = self.processor.has_validation_error
        
        if has_error:
            # Disable all execution buttons when there's a validation error
            if hasattr(self, "btn_run"):
                self.btn_run.setEnabled(False)
            if hasattr(self, "btn_step_cycle"):
                self.btn_step_cycle.setEnabled(False)
            if hasattr(self, "step_back_btn"):
                self.step_back_btn.setEnabled(False)
        else:
            # Normal state: use existing sync logic
            self._sync_step_buttons_with_state()

    def _sync_step_buttons_with_state(self):
        """Single source of truth for step button enabled state (UI-only)."""
        halted = bool(getattr(self.processor, "halted", False))
        has_program = bool(getattr(self.processor, "instructions", []))
        has_code = bool(getattr(self, "code_editor", None) and self.code_editor.toPlainText().strip())
        # If a program exists and isn't halted, we can step/run.
        # If no program exists yet but the editor has code, we allow Run/Step to auto-assemble.
        can_step = (has_program and (not halted)) or ((not has_program) and has_code)

        # Run depends on halted + program loaded (Step Back can re-enable by restoring non-halted state)
        if hasattr(self, "btn_run"):
            self.btn_run.setEnabled(can_step)

        # Step Cycle depends on halted + program loaded
        if hasattr(self, "step_cycle_btn"):
            self.step_cycle_btn.setEnabled(can_step)

    def _append_current_hazards_to_history(self):
        """Append current processor hazards into GUI-side history (no changes to hazard detection/structure)."""
        hazards = getattr(self.processor, 'current_hazards', []) or []
        cycle = getattr(self.processor, 'cycle_count', None)
        for hz in hazards:
            if isinstance(hz, dict):
                entry = dict(hz)  # do not mutate processor's dict
            else:
                # Fallback for unexpected hazard formats; keep display stable
                entry = {'stage': 'Unknown', 'type': 'Hazard', 'status': str(hz), 'reason': ''}
            # Ensure cycle is stored somewhere (do NOT change wording in status)
            if 'cycle' not in entry:
                entry['cycle'] = cycle
            self.hazard_history.append(entry)

    def _hazard_totals_from_history(self) -> Tuple[int, int, int]:
        """Compute (stalls, flushes, forwards) totals from hazard history so badges match the table."""
        stalls = flushes = forwards = 0
        for hz in self.hazard_history:
            t = f"{hz.get('type', '')} {hz.get('status', '')}".lower()
            if "forward" in t:
                forwards += 1
            if ("stall" in t) or ("load-use" in t) or ("load use" in t):
                stalls += 1
            if "flush" in t:
                flushes += 1
        return stalls, flushes, forwards

    def update_hazard_table(self):
        """Render hazards as a running history log (append-only, no per-step clearing)."""
        if not hasattr(self, 'hazard_table'):
            return

        new_items = self.hazard_history[self._last_hazard_rendered_index:]
        if not new_items:
            return

        for hazard in new_items:
            row = self.hazard_table.rowCount()
            self.hazard_table.insertRow(row)

            # Line number (1-based)
            line_number = row + 1
            item_line = QTableWidgetItem(str(line_number))
            item_line.setFont(QFont("Segoe UI", 9))
            item_line.setForeground(QColor(COLORS['text_secondary']))
            item_line.setTextAlignment(Qt.AlignCenter)

            stage = hazard.get('stage', 'Unknown')
            h_type = hazard.get('type', 'Unknown')
            # Keep existing UI cleanup behavior (does not change hazard detection)
            h_type = re.sub(r"\s*\([^)]*\)", "", str(h_type)).strip()
            status = hazard.get('status', 'Active')
            reason = hazard.get('reason', '')

            item_stage = QTableWidgetItem(str(stage))
            item_type = QTableWidgetItem(str(h_type))

            # Simplify status: Only show "Flush", "Stall", or "Forward"
            status_text = str(status)
            status_lower = status_text.lower()
            
            # Determine simple status label
            if "flush" in status_lower:
                simple_status = "Flush"
                status_color = COLORS['danger_500']
            elif "stall" in status_lower:
                simple_status = "Stall"
                status_color = COLORS['warning_500']
            elif "forward" in status_lower:
                simple_status = "Forward"
                status_color = COLORS['success_500']
            else:
                simple_status = status_text
                status_color = COLORS['text_primary']
            
            item_status = QTableWidgetItem(simple_status)
            item_status.setForeground(QColor(status_color))
            item_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
            
            # Store the full hazard dict for click-to-details feature
            item_status.setData(Qt.UserRole, hazard)

            self.hazard_table.setItem(row, 0, item_line)
            self.hazard_table.setItem(row, 1, item_stage)
            self.hazard_table.setItem(row, 2, item_type)
            self.hazard_table.setItem(row, 3, item_status)

        self._last_hazard_rendered_index = len(self.hazard_history)
        self.hazard_table.resizeRowsToContents()
        self.hazard_table.scrollToBottom()
    
    def show_hazard_details(self, row, col):
        """Show minimal popup with hazard details."""
        # Retrieve the hazard dict from the status column (column 3)
        item = self.hazard_table.item(row, 3)
        if not item:
            return
        
        hz = item.data(Qt.UserRole)
        if not hz:
            return
        
        # Extract hazard information
        cycle = hz.get('cycle', '?')
        stage = hz.get('stage', 'Unknown')
        h_type = hz.get('type', 'Unknown')
        status = hz.get('status', 'Active')
        reason = hz.get('reason', 'No additional details available')
        
        # Determine hazard classification
        status_lower = status.lower()
        h_type_lower = h_type.lower()
        
        if "forward" in status_lower or "forward" in h_type_lower:
            hazard_class = "RAW Hazard"
        elif "flush" in status_lower or "branch" in h_type_lower or "jump" in h_type_lower:
            hazard_class = "Control Hazard"
        elif "stall" in status_lower or "load-use" in h_type_lower or "load use" in h_type_lower:
            hazard_class = "RAW Hazard (Load-Use)"
        else:
            hazard_class = "Pipeline Event"
        
        # Show minimal popup
        popup = SimpleHazardPopup(cycle, stage, h_type, hazard_class, reason, self)
        popup.exec()
    
    def update_data_memory_table(self):
        """Update data memory table to show only touched (written) addresses."""
        # Get sorted list of touched word-aligned addresses
        touched = sorted(self.processor.data_memory.touched_words)
        
        # Set table row count dynamically
        self.memory_table.setRowCount(len(touched))
        
        # Update last written memory address (persistent across cycles)
        if hasattr(self.processor, 'last_mem_event') and self.processor.last_mem_event:
            if self.processor.last_mem_event.get('kind') == 'WRITE':
                self.last_mem_write_addr = self.processor.last_mem_event.get('addr')
        
        # Populate table with touched addresses only
        for row, addr in enumerate(touched):
            word_val = self.processor.data_memory.read_word(addr)
            
            # Determine if this address is the last written one (persistent highlight)
            is_last_written = (self.last_mem_write_addr is not None and addr == self.last_mem_write_addr)
            
            # Address column (byte address, hex + decimal)
            addr_item = self.memory_table.item(row, 0)
            if addr_item is None:
                addr_item = QTableWidgetItem()
                self.memory_table.setItem(row, 0, addr_item)
            addr_item.setText(f"0x{addr:04X} ({addr})")
            addr_item.setData(Qt.UserRole, 1 if is_last_written else 0)
            
            # Hex column
            hex_item = self.memory_table.item(row, 1)
            if hex_item is None:
                hex_item = QTableWidgetItem()
                self.memory_table.setItem(row, 1, hex_item)
            hex_item.setText(f"0x{word_val & 0xFFFF:04X}")
            hex_item.setData(Qt.UserRole, 1 if is_last_written else 0)
            
            # Dec column (signed 16-bit)
            dec_item = self.memory_table.item(row, 2)
            if dec_item is None:
                dec_item = QTableWidgetItem()
                self.memory_table.setItem(row, 2, dec_item)
            signed_val = self.processor.to_signed16(word_val)
            dec_item.setText(str(signed_val))
            dec_item.setData(Qt.UserRole, 1 if is_last_written else 0)
    
    def update_display(self):
        """Update all display elements"""
        # Update statistics
        self.lbl_cycle.setText(str(self.processor.cycle_count))
        self.lbl_pc.setText(str(self.processor.pc))  # Decimal format
        # Show dynamic executed instruction count (retired), like modern_simulator.py
        self.lbl_instructions.setText(str(getattr(self.processor, "retired_count", 0)))
        
        # PC indicator in the editor (gutter arrow + blue full-line highlight)
        # MUST use pc_to_editor_line_map (no UI-side counting/skipping).
        self._refresh_pc_indicator()
        
        retired = getattr(self.processor, "retired_count", 0)
        if retired > 0:
            cpi = self.processor.cycle_count / retired
            self.lbl_cpi.setText(f"{cpi:.2f}")
        else:
            self.lbl_cpi.setText("0.00")
        
        # Update pipeline stages - pass pipeline registers to show BUBBLE vs Empty
        # --- DÜZELTME BAŞLANGICI ---
        # Backend'deki trace (log) verisini kullanarak arayüzü güncelle.
        # Bu sayede Output log ile GUI birebir (BUBBLE, STALL dahil) eşleşir.
        stages = self.processor.trace_last_stages
        is_global_stall = getattr(self.processor, 'last_cycle_stall', False)

        def get_stage_data(stage_name):
            # Veriyi kopyala ki orjinali bozulmasın
            data = stages.get(stage_name, {}).copy() if stages.get(stage_name) else {}
            # Eğer backend global stall verdiyse, IF ve ID aşamalarına 'stall' bilgisini ekle
            if is_global_stall and stage_name in ['IF', 'ID']:
                data['stall'] = True
            return data

        self.stage_if.set_instruction(get_stage_data('IF'))
        self.stage_id.set_instruction(get_stage_data('ID'))
        self.stage_ex.set_instruction(stages.get('EX'))
        self.stage_mem.set_instruction(stages.get('MEM'))
        self.stage_wb.set_instruction(stages.get('WB'))
        # --- DÜZELTME BİTİŞİ ---
        
        # Update pipeline registers (detailed, multi-line)
        if self.processor.if_id.instruction:
            inst = self.processor.if_id.instruction
            pc_val = getattr(inst, "pc", 0)
            self.pipe_if_id.content_label.setText(f"PC: {pc_val}\nInst: {inst.get_hex_string()}")
        else:
            self.pipe_if_id.content_label.setText("--")
        
        if self.processor.id_ex.instruction:
            inst = self.processor.id_ex.instruction
            rs_val = self.processor.id_ex.data.get('rs_value', 0)
            rt_val = self.processor.id_ex.data.get('rt_value', 0)
            imm_val = getattr(inst, "imm", 0)
            self.pipe_id_ex.content_label.setText(
                f"RS Val: 0x{rs_val:04X}\nRT Val: 0x{rt_val:04X}\nImm: {imm_val}"
            )
        else:
            self.pipe_id_ex.content_label.setText("--")
        
        if self.processor.ex_mem.instruction:
            alu_result = self.processor.ex_mem.data.get('alu_result', 0)
            store_data = self.processor.ex_mem.data.get('store_data', 0)
            self.pipe_ex_mem.content_label.setText(
                f"ALU Res: 0x{alu_result:04X}\nStore: 0x{store_data:04X}"
            )
        else:
            self.pipe_ex_mem.content_label.setText("--")
        
        if self.processor.mem_wb.instruction:
            inst = self.processor.mem_wb.instruction
            write_data = self.processor.mem_wb.data.get('write_data', 0)
            dest_reg = 0
            if inst.opcode not in ['sw', 'beq', 'bne', 'j', 'jal', 'jr', 'nop']:
                dest_reg = inst.rt if inst.opcode in ['lw', 'addi'] else inst.rd
            self.pipe_mem_wb.content_label.setText(
                f"Write: 0x{write_data:04X}\nDest: R{dest_reg}"
            )
        else:
            self.pipe_mem_wb.content_label.setText("--")
        
        for i in range(8):
            value = self.processor.registers.read(i)
            # Add marker to last written register row (except r0)
            lw = getattr(self.processor, "last_written_register", None)
            is_last = (lw is not None and lw != 0 and i == lw)
            if is_last:
                self.register_table.item(i, 0).setText(f"▶ $r{i}")
            else:
                self.register_table.item(i, 0).setText(f"$r{i}")
            self.register_table.item(i, 2).setText(f"0x{value:04X}")
            # Display as signed 16-bit integer
            signed_value = value if value <= 32767 else value - 65536
            # Show signed 16-bit decimal (no parentheses)
            self.register_table.item(i, 3).setText(f"{signed_value}")

            # Mark each cell for delegate-based painting (wins over selection/QSS)
            for col in range(self.register_table.columnCount()):
                item = self.register_table.item(i, col)
                if item is not None:
                    item.setData(Qt.UserRole, 1 if is_last else 0)
        
        # Update instruction memory - display all instructions up to INST_MEM_MAX_ROWS
        inst_count = min(len(self.processor.instructions), INST_MEM_MAX_ROWS)
        self.inst_memory_table.setRowCount(inst_count)
        for i in range(inst_count):
            inst = self.processor.instructions[i]
            # NOTE: PC is word-indexed in this simulator; we display it as a 16-bit hex address for readability.
            pc_hex = f"0x{i & 0xFFFF:04X}"
            pc_cell = pc_hex  # Artık ok işareti yok, sadece PC adresi
            self.inst_memory_table.setItem(i, 0, QTableWidgetItem(pc_cell))
            asm_item = QTableWidgetItem()
            asm_item.setData(Qt.DisplayRole, format_asm_inline_html(str(inst)))
            self.inst_memory_table.setItem(i, 1, asm_item)
            # Group binary into 4-bit chunks: "xxxx xxxx xxxx xxxx"
            b = inst.get_binary_string()
            b_grouped = " ".join([b[j:j+4] for j in range(0, len(b), 4)])
            self.inst_memory_table.setItem(i, 2, QTableWidgetItem(b_grouped))
            self.inst_memory_table.setItem(i, 3, QTableWidgetItem(inst.get_hex_string()))
            
            # Highlight current PC
            for col in range(4):
                self.inst_memory_table.item(i, col).setBackground(QColor(COLORS['surface_2']))
                self.inst_memory_table.item(i, col).setForeground(QColor(COLORS['text_primary']))
            if i == self.processor.pc:
                for col in range(4):
                    self.inst_memory_table.item(i, col).setBackground(QColor(COLORS['accent_500']))
        
        # Update data memory - only show touched (written) addresses
        self.update_data_memory_table()
        
        # Update stat cards (stall, flush, forward counters)
        stalls, flushes, forwards = self._hazard_totals_from_history()
        if hasattr(self, 'stall_label'):
            self.stall_label.setText(str(stalls))
        if hasattr(self, 'flush_label'):
            self.flush_label.setText(str(flushes))
        if hasattr(self, 'forward_label'):
            self.forward_label.setText(str(forwards))


# ============================================================================
# MAIN
# ============================================================================

