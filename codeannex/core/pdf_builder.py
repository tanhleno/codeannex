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
    GUTTER_W,
    COLOR_GUTTER_BG,
    PDFConfig,
)
from ..renderer.fonts import get_digit_sprites
from ..renderer.highlight import get_token_color
from ..renderer.text_utils import (
    sanitize_text, get_safe_string_width,
    draw_text_with_fallback, draw_centred_text_with_fallback,
    get_contrast_color,
)


def _make_bookmark_key(display_name: str) -> str:
    return re.sub(r"[/()\s]", lambda m: "_" if m.group() in "/ \t" else "", display_name)


class ModernAnnexPDF:
    def __init__(self, output_path_or_buffer, project_root: Path,
                 mono_font: str, emoji_font: str | None, config: PDFConfig | None = None):
        self.config       = config or PDFConfig()
        self.c            = canvas.Canvas(output_path_or_buffer, pagesize=(self.config.page_width, self.config.page_height))
        self.project_root = project_root
        
        # Priority: 1. Config (from args), 2. Parameter, 3. Default
        self.mono_font    = self.config.mono_font or mono_font
        self.emoji_font   = self.config.emoji_font or emoji_font
        
        # Ensure we sync config back if params were used
        if not self.config.mono_font: self.config.mono_font = self.mono_font
        if not self.config.emoji_font: self.config.emoji_font = self.emoji_font

        self.page_num     = self.config.start_page_num
        self._first_page  = True
        self.y            = 0
        self.summary_data: dict         = {}
        self._registered_bookmarks: set = set()
        self.is_simulation              = False

        project_name = self.config.project_name or self.project_root.name
        self.c.setTitle(f"Source code: {project_name}")

    def _dtf(self, x, y, text, font, size, color=None):
        draw_text_with_fallback(self.c, x, y, text, font, size, self.emoji_font, color,
                                emoji_description=self.config.emoji_description)

    def _dctf(self, x, y, text, font, size, color=None):
        draw_centred_text_with_fallback(self.c, x, y, text, font, size, self.emoji_font, color,
                                        emoji_description=self.config.emoji_description)

    def _gsw(self, text, font, size) -> float:
        return get_safe_string_width(text, font, size, self.emoji_font,
                                     emoji_description=self.config.emoji_description)

    def start_new_page(self):
        if not self._first_page:
            self.c.showPage()
            self.page_num += 1
        self._first_page = False
        self.y = self.config.page_height - self.config.margin_top
        if not self.is_simulation:
            self.c.setFillColor(colors.HexColor(self.config.page_bg_color))
            self.c.rect(0, 0, self.config.page_width, self.config.page_height, fill=1, stroke=0)
            self._draw_page_info()

    def _draw_page_info(self):
        if not self.config.show_page_numbers: return
        self.c.setFont(self.config.normal_font, self.config.page_number_size)
        self.c.setFillColor(colors.HexColor(self.config.normal_text_color))
        page_label = self.config.page_number_format.replace("{n}", str(self.page_num))
        self.c.drawRightString(self.config.page_width - self.config.margin_right, 10*mm, page_label)
        if self.config.show_project_name:
            self._dtf(self.config.margin_left, 10*mm, f"{self.config.project_label}{self.config.project_name or self.project_root.name}",
                      self.config.normal_font, 8, colors.HexColor(self.config.normal_text_color))

    def _check_space(self, needed_h: float):
        if self.y - needed_h < self.config.margin_bottom: self.start_new_page()

    def _draw_file_header(self, rel_path: str, continuation: str = ""):
        h = 8 * mm
        self._check_space(h + 15*mm)
        if not self.is_simulation:
            label = f"{rel_path} {continuation}".rstrip()
            self.c.setFillColor(colors.HexColor(self.config.primary_color))
            self.c.roundRect(self.config.margin_left, self.y - h,
                             self.config.page_width - self.config.margin_left - self.config.margin_right, h, 2*mm, fill=1, stroke=0)
            self.c.rect(self.config.margin_left, self.y - h,
                        self.config.page_width - self.config.margin_left - self.config.margin_right, 2*mm, fill=1, stroke=0)
            header_text_color = get_contrast_color(self.config.primary_color)
            self._dtf(self.config.margin_left + 4*mm, self.y - h + 2.5*mm, label, self.config.normal_font, 9, header_text_color)
        self.y -= h

    def _register_bookmark(self, display_name: str, bookmark_key: str):
        if self.is_simulation: self.summary_data.setdefault(bookmark_key, self.page_num)
        else:
            if bookmark_key not in self._registered_bookmarks:
                self._registered_bookmarks.add(bookmark_key)
                self.c.bookmarkPage(bookmark_key)
                self.c.addOutlineEntry(display_name, bookmark_key, level=0)

    def draw_cover(self):
        self.start_new_page()
        if not self.is_simulation:
            mid_x = self.config.page_width / 2
            
            # 1. Main Title
            title_font = self.config.title_font or self.config.normal_font
            self._dctf(mid_x, self.config.page_height * 0.65, self.config.cover_title.upper(),
                       title_font, self.config.title_size, colors.HexColor(self.config.title_color))
            
            # 2. Subtitle
            subtitle_font = self.config.subtitle_font or self.config.normal_font
            subtitle_color = self.config.subtitle_color or self.config.title_color
            self._dctf(mid_x, self.config.page_height * 0.58, self.config.cover_subtitle,
                       subtitle_font, self.config.subtitle_size, colors.HexColor(subtitle_color))

            project_name = self.config.project_name or self.project_root.name
            text_color = colors.HexColor(self.config.normal_text_color)
            curr_y = self.config.page_height * 0.45
            
            if project_name:
                label = self.config.repo_label
                name = project_name
                
                # Calculate widths for precise alignment
                label_w = self._gsw(label, self.config.normal_font, 14)
                name_w  = self._gsw(name, self.config.normal_font, 14)
                total_w = label_w + name_w
                
                start_x = mid_x - total_w / 2
                
                # 1. Draw the label (Plain text color)
                self._dtf(start_x, curr_y, label, self.config.normal_font, 14, text_color)
                
                # 2. Draw the name (Primary color if linked, else normal)
                name_x = start_x + label_w
                final_name_color = colors.HexColor(self.config.primary_color) if self.config.repo_url else text_color
                self._dtf(name_x, curr_y, name, self.config.normal_font, 14, final_name_color)
                
                # 3. Apply link only to the name area
                if self.config.repo_url:
                    self.c.linkURL(self.config.repo_url, (name_x, curr_y - 2, name_x + name_w, curr_y + 12), relative=0, thickness=0, border=None)
                
                curr_y -= 8*mm
            
            # 4. Technical Metadata (Branch | Commit)
            tech_items = []
            if self.config.branch_name:
                tech_items.append(f"Branch: {self.config.branch_name}")
            if self.config.commit_sha:
                tech_items.append(f"Commit: {self.config.commit_sha}")
            
            if tech_items:
                tech_str = "  |  ".join(tech_items)
                self._dctf(mid_x, curr_y, tech_str, self.config.normal_font, 10, colors.HexColor("#6c7086"))
                curr_y -= 12*mm

    def draw_summary_page(self, files: list):
        self.start_new_page()
        title_font = self.config.title_font or self.config.normal_font
        if not self.is_simulation:
            self._dtf(self.config.margin_left, self.y, self.config.summary_title,
                      title_font, 16, colors.HexColor(self.config.title_color))
        self.y -= 12*mm
        nested_tree: dict = {"_files": []}
        
        # To avoid double entries for SVG (Image + Code)
        processed_paths = set()
        unique_files = []
        for fpath, ftype in files:
            if fpath not in processed_paths:
                unique_files.append((fpath, ftype))
                processed_paths.add(fpath)

        for fpath, ftype in unique_files:
            rel = fpath.relative_to(self.project_root)
            curr = nested_tree
            for part in rel.parts[:-1]: curr = curr.setdefault(part, {"_files": []})
            curr["_files"].append((rel.name, _make_bookmark_key(rel.as_posix())))
        self._draw_recursive_summary(nested_tree, 0, [], [])
        self.y = 0

    def _draw_recursive_summary(self, node: dict, depth: int, path_parts: list, is_last_list: list):
        subdirs = sorted([k for k in node.keys() if k != "_files"], key=str.lower)
        files_in_node = node.get("_files", [])
        all_entries = [(d, "dir") for d in subdirs] + [(f, "file") for f in files_in_node]
        indent_step, text_color = 5*mm, colors.HexColor(self.config.normal_text_color)
        for i, (item, type) in enumerate(all_entries):
            is_last = (i == len(all_entries) - 1)
            self._check_space(8*mm)
            if not self.is_simulation:
                base_x = self.config.margin_left
                for d_idx, p_last in enumerate(is_last_list):
                    if not p_last: self._dtf(base_x + d_idx * indent_step, self.y, "│", self.mono_font, 10, colors.HexColor(self.config.primary_color))
                curr_x = base_x + depth * indent_step
                self._dtf(curr_x, self.y, "└─" if is_last else "├─", self.mono_font, 10, colors.HexColor(self.config.primary_color))
                icon_x = curr_x + 4*mm
                self._dtf(icon_x, self.y, "▶" if type == "dir" else "•", self.config.normal_font, 10, colors.HexColor(self.config.primary_color))
                text_x = icon_x + 5*mm
                if type == "dir": self._dtf(text_x, self.y, f"{item}/", self.config.normal_font, 10, colors.HexColor(self.config.primary_color))
                else:
                    display_name, bookmark_key = item
                    page_str = str(self.summary_data.get(bookmark_key, 0))
                    self._dtf(text_x, self.y, display_name, self.config.normal_font, 10, text_color)
                    dot_w, name_w, page_w = self._gsw(".", self.config.normal_font, 10), self._gsw(display_name, self.config.normal_font, 10), self._gsw(page_str, self.config.normal_font, 10)
                    avail = self.config.page_width - text_x - self.config.margin_right - name_w - page_w - 5
                    if avail > 0: self._dtf(text_x + name_w + 2.5, self.y, "." * int(avail / dot_w), self.config.normal_font, 10, text_color)
                    self._dtf(self.config.page_width - self.config.margin_right - page_w, self.y, page_str, self.config.normal_font, 10, text_color)
                    self.c.linkRect("", bookmark_key, (text_x, self.y - 2, self.config.page_width - self.config.margin_right, self.y + 10), Border=[0, 0, 0])
            self.y -= 6*mm
            if type == "dir": self._draw_recursive_summary(node[item], depth + 1, path_parts + [item], is_last_list + [is_last])

    def render_text_file(self, fpath: Path):
        rel = fpath.relative_to(self.project_root).as_posix()
        display_name, bookmark_key = rel, _make_bookmark_key(rel)
        try: content = fpath.read_text(encoding="utf-8", errors="replace")
        except: return
        self._check_space(25*mm)
        self._register_bookmark(display_name, bookmark_key)
        bookmark_parts, total_parts = f"{bookmark_key}__parts", self.summary_data.get(f"{bookmark_key}__parts", None)
        header_suffix = self.config.file_part_format.replace("{current}", "1").replace("{total}", str(total_parts)) if total_parts else ""
        self._draw_file_header(display_name, continuation=header_suffix)
        try:
            ext = fpath.suffix.lower()
            if ext == ".svg":
                from pygments.lexers import XmlLexer
                lexer = XmlLexer(stripnl=False)
            elif fpath.name in [".gitignore", "LICENSE", "README"]:
                lexer = TextLexer(stripnl=False)
            else:
                lexer = get_lexer_for_filename(str(fpath), stripnl=False)
        except ClassNotFound:
            if not self.is_simulation: print(f"ℹ️  Highlighting fallback: No lexer for '{fpath.name}'. Using plain text.")
            lexer = TextLexer(stripnl=False)
        self._render_tokens_to_lines(lexer.get_tokens(content or " "), display_name, bookmark_parts, total_parts)
        self.y -= 4*mm

    def _render_tokens_to_lines(self, tokens, display_name, bookmark_parts, total_parts):
        lines: list = [[]]
        for ttype, value in tokens:
            color, parts = get_token_color(ttype), value.split("\n")
            for i, part in enumerate(parts):
                if i > 0: lines.append([])
                if part: lines[-1].append((part, color))
        max_w, line_idx, page_part, line_h = self.config.get_code_w() - 4*mm, 1, 1, self.config.code_font_size * 1.4
        for original_line in lines:
            v_lines = self._wrap_line(original_line, max_w)
            for i, v_line in enumerate(v_lines):
                if self.y - line_h < self.config.margin_bottom:
                    page_part += 1
                    self._draw_continuation_header(display_name, page_part, total_parts)
                if not self.is_simulation: self._draw_code_line(v_line, line_idx if i == 0 else None, line_h)
                self.y -= line_h
            line_idx += 1
        if self.is_simulation and page_part > 1: self.summary_data[bookmark_parts] = page_part

    def _wrap_line(self, original_line, max_w):
        v_lines, curr_v_line, curr_width = [], [], 0.0
        for text, color in original_line:
            text = sanitize_text(text.replace("\r", "").replace("\t", "    "))
            for part in re.split(r"( +)", text):
                if not part: continue
                pw = self._get_text_w(part)
                if curr_width + pw <= max_w: curr_v_line.append((part, color)); curr_width += pw
                else:
                    if curr_width > 0: v_lines.append(curr_v_line); curr_v_line, curr_width = [], 0.0
                    buf = ""
                    for ch in part:
                        cw = self._get_text_w(buf + ch)
                        if cw > max_w and buf: v_lines.append([(buf, color)]); buf = ch
                        else: buf += ch
                    if buf: curr_v_line.append((buf, color)); curr_width = self._get_text_w(buf)
        if curr_v_line: v_lines.append(curr_v_line)
        return v_lines or [[]]

    def _get_text_w(self, t):
        if self.is_simulation:
            try: return pdfmetrics.stringWidth(t, self.mono_font, self.config.code_font_size)
            except: return len(t) * (self.config.code_font_size * 0.6)
        return self._gsw(t, self.mono_font, self.config.code_font_size)

    def _draw_continuation_header(self, display_name, page_part, total_parts):
        suffix_str = self.config.file_part_format.replace("{current}", str(page_part))
        suffix_str = suffix_str.replace("{total}", str(total_parts)) if total_parts else suffix_str.replace("/{total}", "").replace("/{total", "")
        self._draw_file_header(display_name, continuation=suffix_str)

    def _draw_code_line(self, v_line, line_num, line_h):
        base_y, block_w = self.y - line_h, self.config.page_width - self.config.margin_left - self.config.margin_right
        self.c.setFillColor(colors.HexColor(self.config.code_bg_color))
        self.c.rect(self.config.margin_left, base_y, block_w, line_h, fill=1, stroke=0)
        self.c.setFillColor(COLOR_GUTTER_BG)
        self.c.rect(self.config.margin_left, base_y, GUTTER_W, line_h, fill=1, stroke=0)
        if line_num is not None:
            num_str = str(line_num)
            num_char_w = pdfmetrics.stringWidth("0", self.mono_font, self.config.code_font_size)
            box_hw = self.config.code_font_size * 0.9
            start_x = self.config.margin_left + GUTTER_W - 2.5*mm - len(num_str) * num_char_w
            for char in num_str:
                self.c.drawImage(get_digit_sprites()[char], start_x + (num_char_w - box_hw) / 2.0, (self.y - self.config.code_font_size - 1.5) - box_hw * 0.1, width=box_hw, height=box_hw, mask="auto")
                start_x += num_char_w
        code_x = self.config.get_code_x() + 2*mm
        for chunk, color in v_line:
            code_x = draw_text_with_fallback(self.c, code_x, self.y - self.config.code_font_size - 1, chunk, self.mono_font, self.config.code_font_size, self.emoji_font, color, emoji_description=self.config.emoji_description)

    def render_image_file(self, fpath: Path):
        rel = fpath.relative_to(self.project_root).as_posix()
        self._check_space(40*mm); self._register_bookmark(rel, _make_bookmark_key(rel)); self._draw_file_header(rel)
        self._draw_image(fpath)

    def _draw_image(self, fpath):
        is_svg, max_w, max_h = fpath.suffix.lower() == ".svg", self.config.page_width - self.config.margin_left - self.config.margin_right - 10*mm, self.y - self.config.margin_bottom - 10*mm
        img, png_data, img_w, img_h = None, None, 0, 0
        if is_svg:
            try:
                import cairosvg
                png_data = cairosvg.svg2png(url=str(fpath), scale=2.0); img = PilImage.open(io.BytesIO(png_data)); img_w, img_h = img.size
            except: pass
        else:
            try: img = PilImage.open(fpath); img_w, img_h = img.size
            except: pass
        if img_w > 0 and img_h > 0:
            scale = min(max_w / img_w, max_h / img_h, 1.0)
            draw_w, draw_h, padding = img_w * scale, img_h * scale, 5*mm
            draw_y, block_bottom, block_w = self.y - draw_h - padding, self.y - draw_h - 2*padding, self.config.page_width - self.config.margin_left - self.config.margin_right
            if not self.is_simulation:
                self.c.setFillColor(colors.HexColor("#ffffff")); self.c.rect(self.config.margin_left, block_bottom, block_w, self.y - block_bottom, fill=1, stroke=0)
                self.c.setStrokeColor(colors.HexColor("#e6e9ef")); self.c.setLineWidth(1.0); self.c.rect(self.config.margin_left, block_bottom, block_w, self.y - block_bottom, fill=0, stroke=1)
                draw_x = self.config.margin_left + (block_w - draw_w) / 2
                if img is None and png_data: img = PilImage.open(io.BytesIO(png_data))
                if img: self.c.drawImage(ImageReader(img), draw_x, draw_y, draw_w, draw_h, preserveAspectRatio=True, mask="auto")
            self.y = block_bottom - 4*mm
        else:
            if not self.is_simulation:
                self.c.setFont(self.config.normal_font, 9); self.c.setFillColor(colors.HexColor("#f38ba8")); self.c.drawString(self.config.margin_left, self.y - 10*mm, "[Error rendering image. Try: pip install cairosvg]")
                if fpath.suffix.lower() == ".svg": self.c.drawString(self.config.margin_left, self.y - 14*mm, "(Linux: sudo apt install libcairo2 | Windows: install Cairo binaries)")
            self.y -= 15*mm

    def build(self, files: list):
        self.draw_cover(); self.draw_summary_page(files)
        for i, (fpath, ftype) in enumerate(files):
            if not self.is_simulation: print(f"\r\033[K[{i+1}/{len(files)}] Processing: {fpath.name}", end="")
            if ftype == "text": self.render_text_file(fpath)
            elif ftype == "image": self.render_image_file(fpath)
        if not self.is_simulation: print(); self.c.save()
