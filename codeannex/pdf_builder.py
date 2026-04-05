import io
import re
from pathlib import Path

from PIL import Image as PilImage
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.util import ClassNotFound
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from .config import (
    PAGE_W, PAGE_H, GUTTER_W,
    CODE_FONT_SIZE, CODE_LINE_H,
    COLOR_PAGE_BG, COLOR_TEXT_MAIN, COLOR_CODE_BG, COLOR_GUTTER_BG,
    COLOR_HEADER_BG, COLOR_HEADER_FG, COLOR_ACCENT,
    PDFConfig,
)
from .fonts import get_digit_sprites
from .highlight import get_token_color
from .text_utils import (
    sanitize_text, get_safe_string_width,
    draw_text_with_fallback, draw_centred_text_with_fallback,
    get_contrast_color,
)


def _make_bookmark_key(display_name: str) -> str:
    return re.sub(r"[/()\s]", lambda m: "_" if m.group() in "/ \t" else "", display_name)


class ModernAnnexPDF:
    def __init__(self, output_path_or_buffer, project_root: Path,
                 mono_font: str, emoji_font: str | None, config: PDFConfig | None = None):
        self.c            = canvas.Canvas(output_path_or_buffer, pagesize=(PAGE_W, PAGE_H))
        self.project_root = project_root
        self.mono_font    = mono_font
        self.emoji_font   = emoji_font
        self.config       = config or PDFConfig()
        # Use config fonts if specified
        if self.config.mono_font:
            self.mono_font = self.config.mono_font
        if self.config.emoji_font:
            self.emoji_font = self.config.emoji_font
        self.page_num     = self.config.start_page_num
        self._first_page  = True
        self.y            = 0
        self.summary_data: dict         = {}
        self._registered_bookmarks: set = set()
        self.is_simulation              = False

        # Define the project name
        project_name = self.config.project_name or self.project_root.name
        self.c.setTitle(f"Source code: {project_name}")

    # ── Atalhos de desenho ───────────────────────
    def _dtf(self, x, y, text, font, size, color=None):
        draw_text_with_fallback(self.c, x, y, text, font, size, self.emoji_font, color,
                                emoji_description=self.config.emoji_description)

    def _dctf(self, x, y, text, font, size, color=None):
        draw_centred_text_with_fallback(self.c, x, y, text, font, size, self.emoji_font, color,
                                        emoji_description=self.config.emoji_description)

    def _gsw(self, text, font, size) -> float:
        return get_safe_string_width(text, font, size, self.emoji_font,
                                     emoji_description=self.config.emoji_description)

    # ── Paginação ────────────────────────────────
    def start_new_page(self):
        if not self._first_page:
            self.c.showPage()
            self.page_num += 1
        
        self._first_page = False
        self.y = PAGE_H - self.config.margin_top
        if not self.is_simulation:
            self.c.setFillColor(colors.HexColor(self.config.page_bg_color))
            self.c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
            self._draw_page_info()

    def _draw_page_info(self):
        if not self.config.show_page_numbers:
            return

        self.c.setFont(self.config.normal_font, self.config.page_number_size)
        self.c.setFillColor(colors.HexColor(self.config.normal_text_color))
        
        page_label = self.config.page_number_format.replace("{n}", str(self.page_num))
        self.c.drawRightString(PAGE_W - self.config.margin_right, 10*mm, page_label)
        
        if self.config.show_project_name:
            self._dtf(self.config.margin_left, 10*mm, f"{self.config.project_label}{self.config.project_name or self.project_root.name}",
                      self.config.normal_font, 8, colors.HexColor(self.config.normal_text_color))

    def _check_space(self, needed_h: float):
        if self.y - needed_h < self.config.margin_bottom:
            self.start_new_page()

    # ── Elementos comuns ─────────────────────────
    def _draw_file_header(self, rel_path: str, continuation: str = ""):
        h = 8 * mm
        self._check_space(h + 15*mm)
        if not self.is_simulation:
            label = f"{rel_path} {continuation}".rstrip()
            self.c.setFillColor(colors.HexColor(self.config.primary_color))
            self.c.roundRect(self.config.margin_left, self.y - h,
                             PAGE_W - self.config.margin_left - self.config.margin_right, h, 2*mm, fill=1, stroke=0)
            self.c.rect(self.config.margin_left, self.y - h,
                        PAGE_W - self.config.margin_left - self.config.margin_right, 2*mm, fill=1, stroke=0)
            # Dynamic contrast: White for dark backgrounds, Black for light backgrounds
            header_text_color = get_contrast_color(self.config.primary_color)
            self._dtf(self.config.margin_left + 4*mm, self.y - h + 2.5*mm, label, self.config.bold_font, 9, header_text_color)
        self.y -= h

    def _register_bookmark(self, display_name: str, bookmark_key: str):
        if self.is_simulation:
            self.summary_data.setdefault(bookmark_key, self.page_num)
        else:
            if bookmark_key not in self._registered_bookmarks:
                self._registered_bookmarks.add(bookmark_key)
                self.c.bookmarkPage(bookmark_key)
                self.c.addOutlineEntry(display_name, bookmark_key, level=0)

    # ── Capa ─────────────────────────────────────
    def draw_cover(self):
        self.start_new_page()
        if not self.is_simulation:
            mid_x = PAGE_W / 2
            
            # Use configured title font and size
            title_font = self.config.title_font or self.config.bold_font
            self._dctf(mid_x, PAGE_H * 0.60, self.config.cover_title,
                       title_font, self.config.title_size, colors.HexColor(self.config.title_color))
            
            # Use configured subtitle font and size
            subtitle_font = self.config.subtitle_font or self.config.normal_font
            subtitle_color = self.config.subtitle_color or self.config.title_color
            self._dctf(mid_x, PAGE_H * 0.53, self.config.cover_subtitle,
                       subtitle_font, self.config.subtitle_size, colors.HexColor(subtitle_color))
            
            self.c.setStrokeColor(colors.HexColor(self.config.primary_color))
            self.c.setLineWidth(1)
            self.c.line(mid_x - 40*mm, PAGE_H * 0.5, mid_x + 40*mm, PAGE_H * 0.5)
            
            project_name = self.config.project_name or self.project_root.name
            text_color = colors.HexColor(self.config.normal_text_color)
            if self.config.repo_url:
                # Desenha o rótulo e depois o link
                label_prefix = self.config.repo_label
                prefix_w = self._gsw(label_prefix, self.config.normal_font, 12)
                name_w = self._gsw(project_name, self.config.normal_font, 12)
                total_w = prefix_w + name_w
                
                start_x = mid_x - total_w / 2
                self._dtf(start_x, PAGE_H * 0.45, label_prefix, self.config.normal_font, 12, text_color)
                
                # O link em si (nome do projeto)
                link_x = start_x + prefix_w
                self._dtf(link_x, PAGE_H * 0.45, project_name, self.config.normal_font, 12, colors.HexColor(self.config.primary_color))
                
                # Adicionar área clicável para o link
                self.c.linkURL(self.config.repo_url, 
                               (link_x, PAGE_H * 0.45 - 2, link_x + name_w, PAGE_H * 0.45 + 10),
                               relative=0, thickness=0, border=None)
            else:
                self._dctf(mid_x, PAGE_H * 0.45, f"{self.config.repo_label}{project_name}",
                           self.config.normal_font, 12, text_color)

    # ── Sumário ──────────────────────────────────
    def draw_summary_page(self, files: list):
        self.start_new_page()
        # Use configured title style for consistency
        title_font = self.config.title_font or self.config.bold_font
        if not self.is_simulation:
            self._dtf(self.config.margin_left, self.y, self.config.summary_title,
                      title_font, 16, colors.HexColor(self.config.title_color))
        self.y -= 12*mm

        # Build nested tree
        nested_tree: dict = {"_files": []}
        for fpath, ftype in files:
            rel = fpath.relative_to(self.project_root)
            curr = nested_tree
            for part in rel.parts[:-1]:
                curr = curr.setdefault(part, {"_files": []})
            curr["_files"].append((rel.name, _make_bookmark_key(rel.as_posix())))

        def draw_recursive(node: dict, depth: int, path_parts: list, is_last_list: list):
            subdirs = sorted([k for k in node.keys() if k != "_files"], key=str.lower)
            files_in_node = node.get("_files", [])
            all_entries = [(d, "dir") for d in subdirs] + [(f, "file") for f in files_in_node]
            
            indent_step = 5*mm  # Compact step
            text_color = colors.HexColor(self.config.normal_text_color)
            
            for i, (item, type) in enumerate(all_entries):
                is_last = (i == len(all_entries) - 1)
                self._check_space(8*mm)
                
                if not self.is_simulation:
                    base_x = self.config.margin_left
                    
                    # 1. Draw vertical lines for parent levels
                    for d_idx, parent_is_last in enumerate(is_last_list):
                        if not parent_is_last:
                            line_x = base_x + d_idx * indent_step
                            self._dtf(line_x, self.y, "│", self.mono_font, 10, colors.HexColor(self.config.primary_color))
                    
                    # 2. Draw current connector
                    curr_x = base_x + depth * indent_step
                    connector = "└─" if is_last else "├─"
                    self._dtf(curr_x, self.y, connector, self.mono_font, 10, colors.HexColor(self.config.primary_color))
                    
                    # 3. Draw Icon (Primary Color)
                    icon_x = curr_x + 4*mm
                    icon = "▶" if type == "dir" else "•"
                    self._dtf(icon_x, self.y, icon, self.config.normal_font, 10, colors.HexColor(self.config.primary_color))
                    
                    # 4. Draw Label (Increased offset for better spacing)
                    text_x = icon_x + 5*mm
                    if type == "dir":
                        self._dtf(text_x, self.y, f"{item}/", self.config.bold_font, 10, colors.HexColor(self.config.primary_color))
                    else:
                        display_name, bookmark_key = item
                        page_str = str(self.summary_data.get(bookmark_key, 0))
                        self._dtf(text_x, self.y, display_name, self.config.normal_font, 10, text_color)
                        
                        # Dots and Page
                        dot_w  = self._gsw(".", self.config.normal_font, 10)
                        name_w = self._gsw(display_name, self.config.normal_font, 10)
                        page_w = self._gsw(page_str, self.config.normal_font, 10)
                        avail  = PAGE_W - text_x - self.config.margin_right - name_w - page_w - 5
                        
                        if avail > 0:
                            self._dtf(text_x + name_w + 2.5, self.y, "." * int(avail / dot_w), self.config.normal_font, 10, text_color)
                        self._dtf(PAGE_W - self.config.margin_right - page_w, self.y, page_str, self.config.normal_font, 10, text_color)
                        
                        self.c.linkRect("", bookmark_key, (text_x, self.y - 2, PAGE_W - self.config.margin_right, self.y + 10), Border=[0, 0, 0])

                self.y -= 6*mm
                if type == "dir":
                    draw_recursive(node[item], depth + 1, path_parts + [item], is_last_list + [is_last])

        draw_recursive(nested_tree, 0, [], [])
        self.y = 0

    # ── Arquivo de texto ─────────────────────────
    def render_text_file(self, fpath: Path, label_suffix=""):
        rel           = fpath.relative_to(self.project_root).as_posix()
        display_name  = rel + label_suffix
        bookmark_key  = _make_bookmark_key(rel)   # chave sem sufixo — igual à do sumário

        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        self._check_space(25*mm)
        self._register_bookmark(display_name, bookmark_key)
        
        bookmark_parts  = f"{bookmark_key}__parts"
        total_parts     = self.summary_data.get(bookmark_parts, None)
        
        header_suffix = ""
        if total_parts:
            header_suffix = self.config.file_part_format.replace("{current}", "1").replace("{total}", str(total_parts))
        self._draw_file_header(display_name, continuation=header_suffix)

        try:
            lexer = get_lexer_for_filename(str(fpath), stripnl=False)
        except ClassNotFound:
            lexer = TextLexer(stripnl=False)

        # Tokenizar e montar linhas
        lines: list = [[]]
        for ttype, value in lexer.get_tokens(content or " "):
            color = get_token_color(ttype)
            parts = value.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    lines.append([])
                if part:
                    lines[-1].append((part, color))

        max_w  = self.config.get_code_w() - 4*mm

        def text_w(t: str) -> float:
            # During simulation, uses fast approximation to avoid checking each character
            if self.is_simulation:
                try:
                    return pdfmetrics.stringWidth(t, self.mono_font, self.config.code_font_size)
                except Exception:
                    return len(t) * (self.config.code_font_size * 0.6)  # Heurística: ~60% da altura
            return get_safe_string_width(t, self.mono_font, self.config.code_font_size, self.emoji_font,
                                         emoji_description=self.config.emoji_description)

        def wrap_segment(part: str, color, curr_width: float,
                         curr_v_line: list, v_lines: list) -> tuple[list, float]:
            """Adiciona `part` à linha atual, quebrando por largura real quando necessário."""
            pw = text_w(part)
            if curr_width + pw <= max_w:
                curr_v_line.append((part, color))
                return curr_v_line, curr_width + pw

            # Não cabe — tenta quebrar codepoint a codepoint
            if curr_width > 0:
                v_lines.append(curr_v_line)
                curr_v_line, curr_width = [], 0.0

            buf = ""
            for ch in part:
                cw = text_w(buf + ch)
                if cw > max_w and buf:
                    v_lines.append([(buf, color)])
                    buf = ch
                else:
                    buf += ch
            if buf:
                curr_v_line.append((buf, color))
                curr_width = text_w(buf)

            return curr_v_line, curr_width

        line_idx        = 1
        page_part       = 1
        line_h          = self.config.code_font_size * 1.4

        for original_line in lines:
            v_lines: list    = []
            curr_v_line: list = []
            curr_width        = 0.0

            for text, color in original_line:
                text = sanitize_text(text.replace("\r", "").replace("\t", "    "))
                for part in re.split(r"( +)", text):
                    if not part:
                        continue
                    curr_v_line, curr_width = wrap_segment(
                        part, color, curr_width, curr_v_line, v_lines
                    )

            if curr_v_line:
                v_lines.append(curr_v_line)
            if not v_lines:
                v_lines.append([])

            for i, v_line in enumerate(v_lines):
                if self.y - line_h < self.config.margin_bottom:
                    page_part += 1
                    suffix_str = self.config.file_part_format.replace("{current}", str(page_part))
                    if total_parts:
                        suffix_str = suffix_str.replace("{total}", str(total_parts))
                    else:
                        suffix_str = suffix_str.replace("/{total}", "").replace("/{total", "") # Cleanup if total missing
                    
                    self._draw_file_header(display_name, continuation=suffix_str)

                if not self.is_simulation:
                    base_y  = self.y - line_h
                    block_w = PAGE_W - self.config.margin_left - self.config.margin_right
                    self.c.setFillColor(colors.HexColor(self.config.code_bg_color))
                    self.c.rect(self.config.margin_left, base_y, block_w, line_h, fill=1, stroke=0)
                    self.c.setFillColor(COLOR_GUTTER_BG)
                    self.c.rect(self.config.margin_left, base_y, GUTTER_W, line_h, fill=1, stroke=0)

                    if i == 0:
                        num_str    = str(line_idx)
                        num_char_w = pdfmetrics.stringWidth("0", self.mono_font, self.config.code_font_size)
                        box_hw     = self.config.code_font_size * 0.8
                        start_x    = self.config.margin_left + GUTTER_W - 2*mm - len(num_str) * num_char_w
                        for char in num_str:
                            self.c.drawImage(
                                get_digit_sprites()[char],
                                start_x + (num_char_w - box_hw) / 2.0,
                                (self.y - self.config.code_font_size - 1) - box_hw * 0.2,
                                width=box_hw, height=box_hw, mask="auto",
                            )
                            start_x += num_char_w

                    code_x = self.config.get_code_x() + 2*mm
                    for chunk, color in v_line:
                        code_x = draw_text_with_fallback(
                            self.c, code_x, self.y - self.config.code_font_size - 1,
                            chunk, self.mono_font, self.config.code_font_size, self.emoji_font, color,
                            emoji_description=self.config.emoji_description,
                        )

                self.y -= line_h
            line_idx += 1

        if self.is_simulation and page_part > 1:
            self.summary_data[bookmark_parts] = page_part

        self.y -= 4*mm

    # ── Arquivo de imagem ────────────────────────
    def render_image_file(self, fpath: Path, label_suffix=""):
        rel           = fpath.relative_to(self.project_root).as_posix()
        display_name  = rel + label_suffix
        bookmark_key  = _make_bookmark_key(rel)   # chave sem sufixo — igual à do sumário

        self._check_space(40*mm)
        self._register_bookmark(display_name, bookmark_key)
        self._draw_file_header(display_name)

        is_svg  = fpath.suffix.lower() == ".svg"
        max_w   = PAGE_W - self.config.margin_left - self.config.margin_right - 10*mm
        max_h   = self.y - self.config.margin_bottom - 10*mm
        img, png_data, drawing = None, None, None
        img_w = img_h = 0

        if is_svg:
            try:
                import cairosvg
                png_data = cairosvg.svg2png(url=str(fpath), scale=2.0)
                img = PilImage.open(io.BytesIO(png_data))
                img_w, img_h = img.size
            except ImportError:
                try:
                    from svglib.svglib import svg2rlg
                    drawing = svg2rlg(str(fpath))
                    if drawing:
                        img_w, img_h = drawing.width, drawing.height
                except Exception:
                    pass
        else:
            try:
                img = PilImage.open(fpath)
                img_w, img_h = img.size
            except Exception:
                pass

        if img_w > 0 and img_h > 0:
            scale  = min(max_w / img_w, max_h / img_h, 1.0)
            draw_w = img_w * scale
            draw_h = img_h * scale
            padding      = 5*mm
            block_top    = self.y
            draw_y       = block_top - draw_h - padding
            block_bottom = draw_y - padding
            block_w      = PAGE_W - self.config.margin_left - self.config.margin_right

            if not self.is_simulation:
                self.c.setFillColor(colors.HexColor("#ffffff"))
                self.c.rect(self.config.margin_left, block_bottom, block_w, block_top - block_bottom,
                            fill=1, stroke=0)
                self.c.setStrokeColor(colors.HexColor("#e6e9ef"))
                self.c.setLineWidth(0.5)
                self.c.rect(self.config.margin_left, block_bottom, block_w, block_top - block_bottom,
                            fill=0, stroke=1)

                draw_x = self.config.margin_left + (block_w - draw_w) / 2
                if is_svg and png_data is None and drawing is not None:
                    from reportlab.graphics import renderPDF
                    drawing.width  *= scale
                    drawing.height *= scale
                    drawing.transform = (scale, 0, 0, scale, 0, 0)
                    renderPDF.draw(drawing, self.c, draw_x, draw_y)
                else:
                    if img is None:
                        img = PilImage.open(io.BytesIO(png_data)) if png_data else PilImage.open(fpath)
                    self.c.drawImage(ImageReader(img), draw_x, draw_y, draw_w, draw_h,
                                     preserveAspectRatio=True, mask="auto")

            self.y = block_bottom - 4*mm
        else:
            if not self.is_simulation:
                self.c.setFont(self.config.normal_font, 9)
                self.c.setFillColor(colors.HexColor("#f38ba8"))
                self.c.drawString(self.config.margin_left, self.y - 10*mm,
                                  "[Error or missing library to render image]")
            self.y -= 15*mm

    # ── Main build ──────────────────────────
    def build(self, files: list):
        self.draw_cover()
        self.draw_summary_page(files)
        for i, (fpath, ftype) in enumerate(files):
            if not self.is_simulation:
                print(f"\r\033[K[{i+1}/{len(files)}] Processing: {fpath.name}", end="")
            svg_suffix = " (Code)" if ftype == "text" else " (Image)"
            suffix = svg_suffix if fpath.suffix.lower() == ".svg" else ""
            if ftype == "text":
                self.render_text_file(fpath, label_suffix=suffix)
            elif ftype == "image":
                self.render_image_file(fpath, label_suffix=suffix)
        if not self.is_simulation:
            print()
            self.c.save()
