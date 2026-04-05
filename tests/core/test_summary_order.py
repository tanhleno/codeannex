import pytest
import io
from pathlib import Path
from codeannex.core.pdf_builder import ModernAnnexPDF
from codeannex.io.file_utils import sort_files
from codeannex.renderer.fonts import register_best_font, init_sprites

class TestSummaryOrder:
    def should_have_increasing_page_numbers_with_subdirs_first(self, tmp_path):
        """Verifica se os números de página são crescentes com subpastas vindo antes de arquivos."""
        # Estrutura:
        # a.py (root)
        # b/c.py (subdir)
        # d.py (root)
        
        (tmp_path / "a.py").write_text("print('a')\n" * 100)
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "c.py").write_text("print('c')\n" * 100)
        (tmp_path / "d.py").write_text("print('d')\n" * 100)
        
        # A nova ordem de renderização deve ser:
        # 1. b/c.py (porque b/ é um diretório)
        # 2. a.py
        # 3. d.py
        raw_files = [tmp_path / "a.py", tmp_path / "b" / "c.py", tmp_path / "d.py"]
        sorted_paths = sort_files(raw_files, tmp_path)
        included = [(p, "text") for p in sorted_paths]
        
        # Verifica se a ordenação funcionou como pedido (subpastas primeiro)
        assert "b/c.py" in sorted_paths[0].as_posix()
        
        mono_font, is_ttf, ttf_path = register_best_font()
        init_sprites(is_ttf, ttf_path)
        
        pdf_sim = ModernAnnexPDF(io.BytesIO(), tmp_path, mono_font, None)
        pdf_sim.is_simulation = True
        pdf_sim.build(included)
        
        # Chaves de bookmark
        pages = [
            pdf_sim.summary_data.get("b_c.py"), # Primeiro
            pdf_sim.summary_data.get("a.py"),   # Segundo
            pdf_sim.summary_data.get("d.py")    # Terceiro
        ]
        
        # Verificação de ordem crescente
        assert None not in pages
        assert pages[0] < pages[1]
        assert pages[1] < pages[2]
        assert pages == sorted(pages)
