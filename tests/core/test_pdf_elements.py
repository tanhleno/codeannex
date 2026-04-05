import pytest
import io
from pathlib import Path
from codeannex.core.pdf_builder import ModernAnnexPDF
from codeannex.core.config import PDFConfig
from codeannex.renderer.fonts import register_best_font, init_sprites

from pdfminer.high_level import extract_text

def should_render_cover_with_all_elements():
    """Verifica se todos os elementos da capa são processados sem erro."""
    output = io.BytesIO()
    config = PDFConfig(
        project_name="CoverTest",
        repo_url="https://github.com/test/repo",
        branch_name="dev-branch",
        commit_sha="a1b2c3d",
        cover_title="FULL COVER",
        cover_subtitle="Testing all fields"
    )
    mono_font, _, _ = register_best_font()
    pdf = ModernAnnexPDF(output, Path("."), mono_font, None, config)
    
    # Executa o desenho
    pdf.draw_cover()
    pdf.c.save()
    
    text = extract_text(io.BytesIO(output.getvalue()))
    assert "FULL COVER" in text
    assert "Repository: CoverTest" in text
    assert "Branch: dev-branch" in text
    
    # Use regex to find "Commit: [any 7 hex chars]"
    import re
    assert re.search(r"Commit: [a-f0-9]{7}", text) is not None

def should_handle_image_rendering_logic(tmp_path):
    """Testa a lógica de desenho de imagem (mockando a imagem real)."""
    output = io.BytesIO()
    mono_font, _, _ = register_best_font()
    pdf = ModernAnnexPDF(output, tmp_path, mono_font, None)
    
    # Cria uma imagem dummy
    img_path = tmp_path / "test.png"
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(img_path)
    
    pdf.start_new_page()
    pdf.render_image_file(img_path)
    pdf.c.save()
    
    content = output.getvalue()
    assert len(content) > 0

def should_handle_missing_image_gracefully(tmp_path):
    """Verifica se o sistema não quebra ao tentar renderizar imagem inexistente."""
    output = io.BytesIO()
    mono_font, _, _ = register_best_font()
    pdf = ModernAnnexPDF(output, tmp_path, mono_font, None)
    
    # Path que não existe
    fake_img = tmp_path / "ghost.png"
    
    pdf.start_new_page()
    pdf.render_image_file(fake_img)
    pdf.c.save()
    
    content = output.getvalue()
    assert len(content) > 0 # PDF gerado mesmo com erro interno
