"""
Theme Configuration for Processor Simulator
All color definitions, font sizes, spacing, and UI measurements are centralized here.
Modify values in this file to change the entire application appearance.
"""

# ============================================================================
# RENK AYARLARI (COLOR SETTINGS)
# ============================================================================

# -------------------- Ana Arka Plan Renkleri --------------------
# Ana pencere ve gradient renkler
BG_MAIN = '#F5F5F0'           # Ana pencere arka planı, uygulama genelindeki temel arka plan rengi
BG_GRAD_A = '#F0F0E8'         # Gradient'in orta tonunu, arka plan geçişlerinde kullanılır
BG_GRAD_B = '#E8E8E0'         # Gradient'in üst tonunu, arka plan geçişlerinde kullanılır

# -------------------- Yüzey Renkleri (Surface Colors) --------------------
# Paneller, kartlar ve widget'lar için
SURFACE_1 = '#F8F8F3'         # Sol panel (Assembly Code), sağ panel (Registers, Memory) arka planlarını
SURFACE_2 = '#F0F0EA'         # Tablolar (Register File, Data Memory, Instruction Memory), kart arka planlarını, buton yüzeylerini
SURFACE_3 = '#E8E8E0'         # Kenarlıklar, başlık çubukları, tablo header'larının arka planlarını

# -------------------- Kenarlık Renkleri (Border Colors) --------------------
BORDER_1 = '#D0D0C8'          # Panel ayırıcıları, tablo dış kenarlıkları, ana bölüm ayırıcılarını
BORDER_2 = '#B8B8B0'          # İç kenarlıklar, tablo hücre ayırıcıları, disabled durumlarındaki kenarlıkları

# -------------------- Metin Renkleri (Text Colors) --------------------
TEXT_PRIMARY = '#2C2C28'      # Tablolardaki değerler, buton yazıları, ana içerik metinlerinin rengini
TEXT_SECONDARY = '#5A5A54'    # Etiketler (labels), açıklama yazıları, yardımcı metinlerin rengini
TEXT_MUTED = '#ABABA5'        # Yorumlar, devre dışı butonlar, pasif öğelerin metin rengini

# -------------------- Vurgu Renkleri (Accent Colors) --------------------
ACCENT_600 = '#3B4FEE'        # Hover durumundaki butonlar, aktif öğelerin koyu mavi vurgusunu
ACCENT_500 = '#4C6BF3'        # PC (Program Counter) vurgusu, seçili öğeler, aktif durumların rengini
ACCENT_400 = '#679AF8'        # Syntax highlighting'de opcode'lar, açık mavi vurguları

# -------------------- Durum Renkleri (Status Colors) --------------------
SUCCESS_500 = '#18A650'       # Forward Counter kartı, başarılı işlemler, register highlight'ların yeşil rengini
SUCCESS_600 = '#02A13D'       # Yeşil butonların hover durumundaki koyu yeşil rengini
DANGER_500 = '#DE0517'        # Flush Counter kartı, hata mesajları, hazard uyarı başlığının kırmızı rengini
DANGER_600 = '#B6091D'        # Kırmızı butonların hover durumundaki koyu kırmızı rengini
WARNING_500 = '#F59E0B'       # Stall Counter kartı, uyarı mesajları, bubble durumlarının turuncu rengini
WARNING_600 = '#D97706'       # Turuncu butonların hover durumundaki koyu turuncu rengini

# -------------------- Pipeline Aşama Renkleri (Pipeline Stage Colors) --------------------
STAGE_IF = '#4C6BF3'          # IF (Instruction Fetch) stage widget'ının kenarlık ve başlık rengini
STAGE_ID = '#679AF8'          # ID (Instruction Decode) stage widget'ının kenarlık ve başlık rengini
STAGE_EX = '#18A650'          # EX (Execute) stage widget'ının kenarlık ve başlık rengini
STAGE_MEM = '#F59E0B'         # MEM (Memory Access) stage widget'ının kenarlık ve başlık rengini
STAGE_WB = '#8B5CF6'          # WB (Write Back) stage widget'ının kenarlık ve başlık rengini

# -------------------- Yarı Saydam Renkler (RGBA Colors) --------------------
# Pipeline stage widget'larında ve overlay'lerde kullanılır
# Format: (R, G, B, alpha) - alpha 0.0 (tamamen saydam) ile 1.0 (tamamen opak) arası
RGBA_SURFACE_LIGHT = (240, 240, 234, 0.5)      # Pipeline stage instruction içeriğinin arka plan şeffaflığını
RGBA_SURFACE_MEDIUM = (232, 232, 224, 0.6)     # Pipeline stage'lerin varsayılan arka plan şeffaflığını
RGBA_SURFACE_DARK = (232, 232, 224, 0.8)       # Aktif pipeline stage'lerin (instruction varsa) arka plan şeffaflığını
RGBA_SURFACE_TRANSPARENT = (232, 232, 224, 0.4) # Boş pipeline stage'lerin arka plan şeffaflığını

# -------------------- Popup Renkleri (Popup Colors) --------------------
POPUP_BG = '#F8F8F3'          # Hazard detay popup penceresinin arka plan rengini
POPUP_BORDER = '#D0D0C8'      # Hazard detay popup penceresinin kenarlık rengini
POPUP_TEXT = '#2C2C28'        # Popup'taki başlık ve ana metin rengini
POPUP_CYCLE_COLOR = '#DE0517' # Popup'ta gösterilen cycle numarasının vurgu rengini
POPUP_DETAIL_COLOR = '#4C6BF3' # Popup'taki hazard açıklama metninin rengini


# ============================================================================
# YAZI BOYUTLARI (FONT SIZES)
# ============================================================================

# -------------------- Ana Başlıklar (Main Headers) --------------------
FONT_TITLE_LARGE = 24         # Ana pencere başlığı, en büyük başlık yazı boyutunu (px cinsinden)
FONT_TITLE_MEDIUM = 18        # Bölüm başlıkları (örn: "Registers", "Memory"), orta başlık yazı boyutunu
FONT_TITLE_SMALL = 16         # Alt bölüm başlıkları, küçük başlık yazı boyutunu

# -------------------- Panel Başlıkları --------------------
FONT_PANEL_HEADER = 14        # Panel başlık çubuklarındaki yazı boyutunu (örn: "Assembly Code Editor")
FONT_SECTION_HEADER = 13      # Section başlıklarındaki yazı boyutunu (örn: "Register File", "Data Memory")

# -------------------- İçerik Metinleri (Content Text) --------------------
FONT_BODY_LARGE = 12          # Ana içerik metinleri, buton yazıları, büyük body text boyutunu
FONT_BODY_MEDIUM = 11         # Tablo içerikleri, etiketler, orta body text boyutunu
FONT_BODY_SMALL = 10          # Küçük açıklamalar, yardımcı metinler, küçük body text boyutunu
FONT_BODY_TINY = 9            # Çok küçük notlar, alt yazılar, en küçük okunabilir text boyutunu

# -------------------- Özel Yazı Tipleri --------------------
FONT_CODE = 11                # Assembly code editor'daki kod yazı boyutunu
FONT_MONOSPACE = 10           # Tablolardaki hex/binary değerlerin monospace yazı boyutunu
FONT_COUNTER = 28             # Counter kartlarındaki büyük sayıların yazı boyutunu (Stall, Forward, Flush)
FONT_COUNTER_LABEL = 11       # Counter kartlarındaki etiket yazılarının boyutunu

# -------------------- Buton Yazı Boyutları --------------------
FONT_BUTTON_LARGE = 12        # Büyük butonların (Load, Run, Step) yazı boyutunu
FONT_BUTTON_MEDIUM = 11       # Orta butonların yazı boyutunu
FONT_BUTTON_SMALL = 10        # Küçük butonların yazı boyutunu

# -------------------- Pipeline Stage Yazı Boyutları --------------------
FONT_STAGE_TITLE = 12         # Pipeline stage başlıklarının (IF, ID, EX, MEM, WB) yazı boyutunu
FONT_STAGE_CONTENT = 10       # Pipeline stage içindeki instruction detaylarının yazı boyutunu


# ============================================================================
# KUTU BOYUTLARI (BOX/WIDGET SIZES)
# ============================================================================

# -------------------- Ana Pencere Boyutları --------------------
WINDOW_MIN_WIDTH = 1400       # Ana pencerenin minimum genişliğini (px cinsinden)
WINDOW_MIN_HEIGHT = 900       # Ana pencerenin minimum yüksekliğini (px cinsinden)

# -------------------- Panel Genişlikleri --------------------
LEFT_PANEL_MIN_WIDTH = 400    # Sol panel (Assembly Code Editor) minimum genişliğini
LEFT_PANEL_MAX_WIDTH = 600    # Sol panel (Assembly Code Editor) maksimum genişliğini
RIGHT_PANEL_MIN_WIDTH = 350   # Sağ panel (Registers & Memory) minimum genişliğini

# -------------------- Tablo Boyutları --------------------
TABLE_ROW_HEIGHT = 28         # Tablo satır yüksekliğini (Register File, Memory tablolarında)
TABLE_HEADER_HEIGHT = 32      # Tablo başlık satırı yüksekliğini
TABLE_MIN_WIDTH = 300         # Tabloların minimum genişliğini
TABLE_CELL_MIN_WIDTH = 80     # Tablo hücresinin minimum genişliğini

# -------------------- Buton Boyutları --------------------
BUTTON_HEIGHT_LARGE = 40      # Büyük butonların (Load, Run) yüksekliğini
BUTTON_HEIGHT_MEDIUM = 32     # Orta butonların (Step, Reset) yüksekliğini
BUTTON_HEIGHT_SMALL = 28      # Küçük butonların yüksekliğini
BUTTON_MIN_WIDTH = 100        # Butonların minimum genişliğini
BUTTON_ICON_SIZE = 16         # Buton icon'larının boyutunu (px cinsinden)

# -------------------- Counter Card Boyutları --------------------
COUNTER_CARD_WIDTH = 140      # Counter kartlarının (Stall, Forward, Flush) genişliğini
COUNTER_CARD_HEIGHT = 90      # Counter kartlarının yüksekliğini

# -------------------- Pipeline Stage Widget Boyutları --------------------
STAGE_WIDGET_MIN_WIDTH = 180  # Pipeline stage widget'larının minimum genişliğini
STAGE_WIDGET_HEIGHT = 120     # Pipeline stage widget'larının yüksekliğini
STAGE_HEADER_HEIGHT = 30      # Pipeline stage başlık bölümünün yüksekliğini

# -------------------- Scrollbar Boyutları --------------------
SCROLLBAR_WIDTH = 12          # Dikey scrollbar'ların genişliğini
SCROLLBAR_HEIGHT = 12         # Yatay scrollbar'ların yüksekliğini

# -------------------- Input/TextEdit Boyutları --------------------
INPUT_HEIGHT = 32             # Tek satırlık input alanlarının yüksekliğini
TEXTEDIT_MIN_HEIGHT = 200     # Çok satırlı text alanlarının (code editor) minimum yüksekliğini

# -------------------- Popup Boyutları --------------------
POPUP_MIN_WIDTH = 350         # Hazard popup penceresinin minimum genişliğini
POPUP_MAX_WIDTH = 500         # Hazard popup penceresinin maksimum genişliğini
POPUP_MIN_HEIGHT = 150        # Hazard popup penceresinin minimum yüksekliğini


# ============================================================================
# PADDING VE MARGIN DEĞERLERI (SPACING)
# ============================================================================

# -------------------- Container Padding'ler --------------------
PADDING_WINDOW = 16           # Ana pencere içindeki genel padding'i (tüm kenarlardan boşluk)
PADDING_PANEL = 12            # Panel içindeki genel padding'i (sol/sağ panellerin iç boşluğu)
PADDING_SECTION = 10          # Section'ların (Register File, Memory vb.) padding'ini
PADDING_CARD = 12             # Kartların (Counter cards) içindeki padding'i

# -------------------- Widget Padding'ler --------------------
PADDING_BUTTON = 8            # Butonların içindeki padding'i (yazı ile kenar arası boşluk)
PADDING_TABLE_CELL = 6        # Tablo hücrelerinin içindeki padding'i
PADDING_STAGE = 8             # Pipeline stage widget'larının içindeki padding'i
PADDING_POPUP = 15            # Popup pencerelerinin içindeki padding'i

# -------------------- Margin Değerleri --------------------
MARGIN_SECTION = 10           # Section'lar arası dikey boşluğu
MARGIN_WIDGET = 8             # Widget'lar arası genel boşluğu
MARGIN_BUTTON = 6             # Butonlar arası boşluğu
MARGIN_COUNTER = 8            # Counter kartları arası boşluğu

# -------------------- Spacing (Layout İçi Boşluklar) --------------------
SPACING_HORIZONTAL = 12       # Yatay layout'larda öğeler arası boşluğu
SPACING_VERTICAL = 10         # Dikey layout'larda öğeler arası boşluğu
SPACING_TIGHT = 4             # Sıkı layout'larda kullanılan minimal boşluğu
SPACING_LOOSE = 16            # Gevşek layout'larda kullanılan geniş boşluğu


# ============================================================================
# KENARLIK VE ÇERÇEVE AYARLARI (BORDER SETTINGS)
# ============================================================================

# -------------------- Border Kalınlıkları --------------------
BORDER_WIDTH_THIN = 1         # İnce kenarlıkların kalınlığını (tablo hücreleri, ayırıcılar)
BORDER_WIDTH_MEDIUM = 2       # Orta kenarlıkların kalınlığını (paneller, kartlar)
BORDER_WIDTH_THICK = 3        # Kalın kenarlıkların kalınlığını (aktif/vurgulu öğeler)

# -------------------- Border Radius (Köşe Yuvarlaklığı) --------------------
BORDER_RADIUS_SMALL = 4       # Küçük köşe yuvarlaklığını (butonlar, input'lar)
BORDER_RADIUS_MEDIUM = 6      # Orta köşe yuvarlaklığını (kartlar, paneller)
BORDER_RADIUS_LARGE = 8       # Büyük köşe yuvarlaklığını (modal'lar, popup'lar)
BORDER_RADIUS_ROUND = 12      # Çok yuvarlak köşelerin yuvarlaklığını (özel öğeler)


# ============================================================================
# DİĞER UI ÖLÇÜLERİ (OTHER UI MEASUREMENTS)
# ============================================================================

# -------------------- Icon Boyutları --------------------
ICON_SIZE_SMALL = 14          # Küçük icon'ların boyutunu (inline icon'lar)
ICON_SIZE_MEDIUM = 18         # Orta icon'ların boyutunu (buton icon'ları)
ICON_SIZE_LARGE = 24          # Büyük icon'ların boyutunu (başlık icon'ları)

# -------------------- Line Height (Satır Yüksekliği) --------------------
LINE_HEIGHT_TIGHT = 1.2       # Sıkı line-height oranını (başlıklar)
LINE_HEIGHT_NORMAL = 1.5      # Normal line-height oranını (body text)
LINE_HEIGHT_RELAXED = 1.8     # Gevşek line-height oranını (uzun metinler)

# -------------------- Shadow/Elevation --------------------
SHADOW_OFFSET = 2             # Gölge offset değerini (px cinsinden)
SHADOW_BLUR = 8               # Gölge blur değerini (px cinsinden)
SHADOW_OPACITY = 0.1          # Gölge opaklığını (0.0 - 1.0 arası)

# -------------------- Animation Timing --------------------
ANIMATION_FAST = 150          # Hızlı animasyon süresini (ms cinsinden)
ANIMATION_NORMAL = 250        # Normal animasyon süresini (ms cinsinden)
ANIMATION_SLOW = 400          # Yavaş animasyon süresini (ms cinsinden)


# ============================================================================
# HELPER FONKSIYONLAR (HELPER FUNCTIONS)
# ============================================================================

def rgba_string(rgba_tuple):
    """
    RGBA tuple'ını CSS rgba() string formatına çevirir
    KULLANIM: Pipeline stage'lerde ve overlay'lerde yarı saydam renkler için
    Örnek: rgba_string((240, 240, 234, 0.5)) -> "rgba(240, 240, 234, 0.5)"
    """
    return f"rgba({rgba_tuple[0]}, {rgba_tuple[1]}, {rgba_tuple[2]}, {rgba_tuple[3]})"


def get_shadow_style():
    """
    Standart gölge style string'i döndürür
    KULLANIM: Kartlar, popup'lar ve elevated öğeler için gölge efekti
    """
    return f"{SHADOW_OFFSET}px {SHADOW_OFFSET}px {SHADOW_BLUR}px rgba(0,0,0,{SHADOW_OPACITY})"


def get_padding_style(all_sides=None, horizontal=None, vertical=None, top=None, right=None, bottom=None, left=None):
    """
    Padding değerlerini CSS style string'ine çevirir
    KULLANIM: Widget ve layout'larda dinamik padding tanımlamak için
    
    Parametreler:
        all_sides: Tüm kenarlar için aynı padding
        horizontal: Yatay (left, right) padding
        vertical: Dikey (top, bottom) padding
        top, right, bottom, left: Her kenar için ayrı padding
    """
    if all_sides is not None:
        return f"padding: {all_sides}px;"
    elif horizontal is not None or vertical is not None:
        v = vertical if vertical is not None else 0
        h = horizontal if horizontal is not None else 0
        return f"padding: {v}px {h}px;"
    else:
        t = top if top is not None else 0
        r = right if right is not None else 0
        b = bottom if bottom is not None else 0
        l = left if left is not None else 0
        return f"padding: {t}px {r}px {b}px {l}px;"


def get_margin_style(all_sides=None, horizontal=None, vertical=None, top=None, right=None, bottom=None, left=None):
    """
    Margin değerlerini CSS style string'ine çevirir
    KULLANIM: Widget'lar arası boşlukları dinamik olarak ayarlamak için
    
    Parametreler all_sides için get_padding_style ile aynı
    """
    if all_sides is not None:
        return f"margin: {all_sides}px;"
    elif horizontal is not None or vertical is not None:
        v = vertical if vertical is not None else 0
        h = horizontal if horizontal is not None else 0
        return f"margin: {v}px {h}px;"
    else:
        t = top if top is not None else 0
        r = right if right is not None else 0
        b = bottom if bottom is not None else 0
        l = left if left is not None else 0
        return f"margin: {t}px {r}px {b}px {l}px;"


# ============================================================================
# GERİYE UYUMLULUK SÖZLÜĞÜ (BACKWARD COMPATIBILITY DICTIONARY)
# ============================================================================
# Mevcut kodun çalışmasını sağlamak için eski COLORS sözlüğü korunmuştur

COLORS = {
    'bg_0': BG_MAIN,
    'bg_grad_a': BG_GRAD_A,
    'bg_grad_b': BG_GRAD_B,
    'surface_1': SURFACE_1,
    'surface_2': SURFACE_2,
    'surface_3': SURFACE_3,
    'border_1': BORDER_1,
    'border_2': BORDER_2,
    'text_primary': TEXT_PRIMARY,
    'text_secondary': TEXT_SECONDARY,
    'text_muted': TEXT_MUTED,
    'accent_600': ACCENT_600,
    'accent_500': ACCENT_500,
    'accent_400': ACCENT_400,
    'success_500': SUCCESS_500,
    'success_600': SUCCESS_600,
    'danger_500': DANGER_500,
    'danger_600': DANGER_600,
    'warning_500': WARNING_500,
    'warning_600': WARNING_600,
    'stage_if': STAGE_IF,
    'stage_id': STAGE_ID,
    'stage_ex': STAGE_EX,
    'stage_mem': STAGE_MEM,
    'stage_wb': STAGE_WB,
    # Kısa isimler (geriye uyumluluk için)
    'surface': SURFACE_1,
    'surface_light': SURFACE_2,
    'border': BORDER_1,
    'primary': ACCENT_500,
    'primary_hover': ACCENT_600,
    'success': SUCCESS_500,
    'error': DANGER_500,
    'warning': WARNING_500,
    'info': ACCENT_400,
    'accent': ACCENT_500,
}

