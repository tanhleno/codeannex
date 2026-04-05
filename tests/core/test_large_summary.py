import pytest
import io
from pathlib import Path
from codeannex.core.pdf_builder import ModernAnnexPDF
from codeannex.renderer.fonts import register_best_font, init_sprites

class TestLargeSummary:
    def should_calculate_correct_page_numbers_with_multi_page_summary(self, tmp_path):
        """Garante que os números de página estão corretos mesmo quando o sumário tem várias páginas."""
        # 1. Criar muitos arquivos para forçar um sumário longo
        # Cada linha do sumário tem ~6mm. Uma página A4 tem ~297mm.
        # Com margens, cabem ~40 itens por página. 200 itens = ~5 páginas de sumário.
        included = []
        for i in range(200):
            f = tmp_path / f"file_{i:03d}.py"
            f.write_text(f"print({i})")
            included.append((f, "text"))
        
        mono_font, is_ttf, ttf_path = register_best_font()
        init_sprites(is_ttf, ttf_path)
        
        # 2. Passo de Simulação (Simula a geração completa)
        pdf_sim = ModernAnnexPDF(io.BytesIO(), tmp_path, mono_font, None)
        pdf_sim.is_simulation = True
        pdf_sim.build(included)
        
        # O sumário deve ter ocupado várias páginas.
        # Vamos ver em qual página o primeiro arquivo (file_000.py) começou.
        first_file_page = pdf_sim.summary_data.get("file_000.py")
        
        # 3. Validações
        # Capa (1) + Sumário (N páginas). O primeiro arquivo deve começar pelo menos na página 3 ou 4.
        assert first_file_page > 2, f"O primeiro arquivo deve começar após o sumário (Página atual: {first_file_page})"
        
        # Verificar se o último arquivo tem uma página maior que o primeiro
        last_file_page = pdf_sim.summary_data.get("file_199.py")
        assert last_file_page >= first_file_page
        
        # 4. Verificar se todos os arquivos estão no summary_data
        assert len(pdf_sim.summary_data) >= 200
