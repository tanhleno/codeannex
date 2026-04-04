import pytest
import io
from pathlib import Path
from pdfminer.high_level import extract_text
from codeannex.pdf_builder import ModernAnnexPDF
from codeannex.config import PDFConfig
from codeannex.fonts import register_best_font, init_sprites

class TestPDFLayout:
    def should_have_consistent_page_numbering(self):
        """Verifica se o formato 'Página X' é consistente em todo o PDF."""
        output = io.BytesIO()
        mono_font, is_ttf, ttf_path = register_best_font()
        init_sprites(is_ttf, ttf_path)
        
        pdf = ModernAnnexPDF(output, Path("."), mono_font, None)
        pdf.draw_cover()
        pdf.start_new_page()
        pdf.c.save()
        
        text = extract_text(io.BytesIO(output.getvalue()))
        # O formato agora é apenas o número
        assert "1" in text
        assert "2" in text
        assert "Página" not in text

    def should_show_correct_part_labels_for_multipage_files(self, tmp_path):
        """Verifica se arquivos que ocupam várias páginas mostram '(parte 1/n)', '(parte 2/n)', etc."""
        large_file = tmp_path / "large.py"
        large_file.write_text("\n".join([f"print('line {i}')" for i in range(200)]))
        
        mono_font, is_ttf, ttf_path = register_best_font()
        init_sprites(is_ttf, ttf_path)
        
        # 1. Simulação para obter total_parts
        pdf_sim = ModernAnnexPDF(io.BytesIO(), tmp_path, mono_font, None)
        pdf_sim.is_simulation = True
        pdf_sim.render_text_file(large_file)
        
        # 2. Geração real
        output = io.BytesIO()
        pdf_real = ModernAnnexPDF(output, tmp_path, mono_font, None)
        pdf_real.summary_data = pdf_sim.summary_data
        pdf_real.render_text_file(large_file)
        pdf_real.c.save()
        
        text = extract_text(io.BytesIO(output.getvalue()))
        assert "(parte 1/" in text
        assert "(parte 2/" in text

    def should_render_project_name_in_footer_when_configured(self):
        """Verifica se o nome do projeto aparece no rodapé quando show_project_name é True."""
        output = io.BytesIO()
        config = PDFConfig(project_name="Custom Project", show_project_name=True)
        mono_font, _, _ = register_best_font()
        
        pdf = ModernAnnexPDF(output, Path("."), mono_font, None, config)
        pdf.start_new_page()
        pdf.c.save()
        
        text = extract_text(io.BytesIO(output.getvalue()))
        assert "Projeto: Custom Project" in text

    def should_render_clickable_repo_link_on_cover(self):
        """Verifica se a URL do repositório é incluída como link na capa."""
        output = io.BytesIO()
        config = PDFConfig(repo_url="https://github.com/user/project", project_name="MyProject")
        mono_font, _, _ = register_best_font()
        
        pdf = ModernAnnexPDF(output, Path("."), mono_font, None, config)
        pdf.draw_cover()
        pdf.c.save()
        
        content = output.getvalue()
        # No PDF, links são armazenados em objetos /URI
        assert b"https://github.com/user/project" in content
        assert b"MyProject" in content
