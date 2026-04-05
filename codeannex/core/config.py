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

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ico", ".gif", ".webp", ".bmp", ".svg"}
BINARY_EXTENSIONS = {".pdf", ".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".whl"}

@dataclass
class PDFConfig:
    project_name: str | None = None
    margin_left: float = _DEFAULT_MARGIN_LEFT
    margin_right: float = _DEFAULT_MARGIN_RIGHT
    margin_top: float = _DEFAULT_MARGIN_TOP
    margin_bottom: float = _DEFAULT_MARGIN_BOTTOM
    page_width: float = PAGE_W
    page_height: float = PAGE_H
    start_page_num: int = 1
    show_project_name: bool = False
    normal_font: str = NORMAL_FONT
    bold_font: str = BOLD_FONT
    mono_font: str | None = None
    emoji_font: str | None = None
    emoji_description: bool = False
    repo_url: str | None = None
    branch_name: str | None = None
    commit_sha: str | None = None
    page_number_size: int = 8

    title_font: str | None = None
    title_size: int = 28
    title_color: str = "#1e1e2e"
    subtitle_font: str | None = None
    subtitle_size: int = 18
    subtitle_color: str | None = None
    normal_text_size: int = 10
    normal_text_color: str = "#4c4f69"
    page_number_format: str = "{n}"
    show_page_numbers: bool = True
    cover_title: str = "TECHNICAL ANNEX"
    cover_subtitle: str = "Source Code Documentation"
    primary_color: str = "#1e66f5"
    
    code_font_size: int = CODE_FONT_SIZE
    code_bg_color: str = "#1e1e2e"
    page_bg_color: str = "#ffffff"
    
    summary_title: str = "Summary / File Index"
    repo_label: str = "Repository: "
    project_label: str = "Project: "
    file_part_format: str = "(part {current}/{total})"

    def get_code_x(self) -> float: return self.margin_left + GUTTER_W
    def get_code_w(self) -> float: return self.page_width - self.get_code_x() - self.margin_right
