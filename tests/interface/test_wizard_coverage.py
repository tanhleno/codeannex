import pytest
from unittest.mock import patch
import argparse
from pathlib import Path
from codeannex.interface.cli import parse_args, run_interactive_wizard

class TrackedNamespace:
    """
    Um wrapper que registra quais atributos foram acessados ou modificados.
    Isso permite saber dinamicamente quais argumentos o wizard utiliza.
    """
    def __init__(self, target):
        # Usamos __dict__ diretamente para evitar recursão no setup
        self.__dict__['_target'] = target
        self.__dict__['_accessed'] = set()

    def __getattr__(self, name):
        self._accessed.add(name)
        return getattr(self._target, name)

    def __setattr__(self, name, value):
        if name in ['_target', '_accessed']:
            self.__dict__[name] = value
        else:
            self._accessed.add(name)
            setattr(self._target, name, value)

def should_wizard_cover_most_arguments():
    """
    Verifica dinamicamente a cobertura de argumentos do wizard.
    Este teste resiste a adições/remoções de argumentos no futuro.
    """
    # 1. Obter argumentos reais e preparar o rastreador
    real_args, _ = parse_args()
    real_args.dir = "." 
    tracked = TrackedNamespace(real_args)
    
    # 2. Entradas simuladas para cobrir todas as seções do wizard
    inputs = [
        "ProjectName",                        # 1. Name
        "n", "branch", "url",                 # 2. Repo (Custom)
        "y", "CTitle", "CSub", "#000", "#111", # 3. Visual Style (Custom)
        "y", "TFont", "NFont", "MFont", "12", "/p1", # 4. Typography (Custom)
        "y", "2.0", "2.0", "210", "297", "n", "1",   # 5. Layout (Custom)
        "y", "*.py", "*.tmp"                  # 6. Filters (Custom)
    ]
    
    # Patch de dependências IO
    with patch('codeannex.interface.cli.get_git_info', return_value=("url", "main", "sha")):
        with patch('codeannex.interface.cli.get_git_remotes', return_value={"origin": "url"}):
            # Adicionamos inputs extras vazios para evitar erros se o wizard crescer
            with patch('builtins.input', side_effect=inputs + [""] * 50):
                run_interactive_wizard(tracked)
    
    # 3. Cálculo de cobertura
    all_cli_args = set(vars(real_args).keys())
    covered_by_wizard = tracked._accessed
    
    # Argumentos técnicos que geralmente não pertencem ao wizard interativo
    technical_args = {
        "dir",                # Diretório base (passado antes do wizard)
        "no_input",           # Flag que desativa o próprio wizard
        "check_emoji_font",   # Ferramenta de diagnóstico (CLI Only)
        "no_git",             # Flag de desativação técnica
        "output"              # Destino do arquivo (geralmente fixo via CLI)
    }
    
    missing = (all_cli_args - covered_by_wizard) - technical_args
    ghost_args = covered_by_wizard - all_cli_args
    
    print(f"\n📊 Wizard Coverage Analysis:")
    print(f"   - Total CLI Arguments: {len(all_cli_args)}")
    print(f"   - Covered by Wizard:   {len(covered_by_wizard)}")
    print(f"   - Missing from Wizard: {len(missing)}")
    
    if ghost_args:
        print(f"   - Ghost Args (Wizard-only): {ghost_args}")
    
    if missing:
        print(f"\n💡 Tip: The following arguments are CLI-only for now:")
        for arg in sorted(list(missing)):
            print(f"      - {arg}")

    # Validação mínima: O wizard deve cobrir pelo menos 30% dos argumentos 
    # ou uma quantidade base razoável (ajustável conforme o projeto cresce)
    coverage_ratio = len(covered_by_wizard) / (len(all_cli_args) - len(technical_args))
    assert coverage_ratio > 0.4, f"Wizard coverage is too low ({coverage_ratio:.1%})"
    
    # Garantia de sanidade: O nome do projeto sempre deve ser solicitado
    assert "name" in covered_by_wizard
