from dataclasses import dataclass
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm

# ── Page (default) ───────────────────────────────
PAGE_W, PAGE_H = A4
_DEFAULT_MARGIN_LEFT    = 1.5 * cm
_DEFAULT_MARGIN_RIGHT   = 1.5 * cm
_DEFAULT_MARGIN_TOP     = 2.0 * cm
_DEFAULT_MARGIN_BOTTOM  = 2.0 * cm

# ── Code ───────────────────────────────────────
CODE_FONT_SIZE = 10
CODE_LINE_H    = CODE_FONT_SIZE * 1.4
GUTTER_W       = 14 * mm

# ── Colors ────────────────────────────────────────
COLOR_PAGE_BG   = colors.HexColor("#ffffff")
COLOR_TEXT_MAIN = colors.HexColor("#4c4f69")
COLOR_CODE_BG   = colors.HexColor("#1e1e2e")
COLOR_GUTTER_BG = colors.HexColor("#181825")
COLOR_GUTTER_FG = colors.HexColor("#bac2de")
COLOR_HEADER_BG = colors.HexColor("#313244")
COLOR_HEADER_FG = colors.HexColor("#cdd6f4")
COLOR_ACCENT    = colors.HexColor("#89b4fa")

# ── Base fonts ──────────────────────────────────
NORMAL_FONT = "Helvetica"
BOLD_FONT   = "Helvetica-Bold"

# ── Supported image extensions ───────────────
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".gif", ".webp", ".bmp", ".svg"}

# ── Binary extensions to ignore quickly ──────
BINARY_EXTENSIONS = {".pdf", ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                     ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".whl",
                     ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}


@dataclass
class PDFConfig:
    """PDF configuration for code annex."""
    project_name: str | None = None
    margin_left: float = _DEFAULT_MARGIN_LEFT
    margin_right: float = _DEFAULT_MARGIN_RIGHT
    margin_top: float = _DEFAULT_MARGIN_TOP
    margin_bottom: float = _DEFAULT_MARGIN_BOTTOM
    start_page_num: int = 1
    show_project_name: bool = False
    normal_font: str = NORMAL_FONT
    bold_font: str = BOLD_FONT
    mono_font: str | None = None  # Will be set by register_best_font
    emoji_font: str | None = None  # Will be set by register_emoji_font
    emoji_description: bool = False  # Print descriptions instead of emojis
    repo_url: str | None = None  # URL of the repository for the cover page
    page_number_size: int = 8  # Font size for page numbers

    def get_code_x(self) -> float:
        """Calculates the initial X position of the code."""
        return self.margin_left + GUTTER_W

    def get_code_w(self) -> float:
        """Calculates the available width for code."""
        return PAGE_W - self.get_code_x() - self.margin_right
