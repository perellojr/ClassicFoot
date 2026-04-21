# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sobre o Projeto

ClassicFoot é um jogo de gerenciamento de futebol retrô inspirado no Elifoot 2, escrito em Python 3.11+. Possui 32 clubes em 4 divisões, motor de partidas com distribuição de Poisson, mercado de jogadores/treinadores, Copa e sistema financeiro completo. Roda em terminal ou como app desktop (Tkinter).

## Comandos Essenciais

```bash
# Instalar dependências
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Rodar o jogo
python3 main.py                                        # modo terminal
python3 launcher_gui.py                                # janela desktop (Tkinter)
CLASSICFOOT_THEME=msdos python3 main.py               # tema DOS retrô
CLASSICFOOT_SEED=12345 python3 main.py                # simulação determinística

# Rodar todos os testes
python3 -m unittest discover -s tests -p "test_*.py" -v

# Rodar um único arquivo de testes
python3 -m unittest tests.test_engine -v

# Rodar um único teste específico
python3 -m unittest tests.test_engine.TestMatchEngine.test_red_card -v

# Checagem de sintaxe (compilação)
python3 -m py_compile data.py engine.py gameplay.py main.py season.py term.py \
  manager_market.py models.py rivalries.py transfers.py save.py launcher_gui.py ui/*.py

# Type checking (mypy, leniente)
python3 -m mypy models.py engine.py season.py save.py transfers.py manager_market.py main.py ui/

# Stress test de 40 temporadas (CI)
python3 -m unittest tests.test_long_simulation -v

# Regenerar data/teams.json após edições manuais
python3 scripts/build_teams_json.py
```

## Variáveis de Ambiente

| Variável | Uso |
|---|---|
| `CLASSICFOOT_THEME` | Tema visual (ex: `msdos`) |
| `CLASSICFOOT_SEED` | Semente RNG para reprodutibilidade |
| `CLASSICFOOT_HALF_DURATION_SECONDS` | Duração de cada tempo em segundos |
| `CLASSICFOOT_COLS` | Forçar largura do terminal |
| `CLASSICFOOT_EMBEDDED` | Sinaliza modo launcher desktop |

## Arquitetura em Camadas

### Camada de Dados — `models.py`
Dataclasses centrais: `Player`, `Team`, `Coach`, `MatchResult`, `CupTie`, `CareerState`. Enums: `Position`, `Formation`, `Postura` com modificadores táticos. Toda a lógica de OVR e tickets vive aqui.

### Motor de Simulação — `engine.py`
Simulação de partida via Poisson (sem NumPy). Seleção de escalação por formação/OVR, pênaltis, substituições, penalidades de cartão. Cálculo de renda por público e preço de ingresso.

### Sistema de Temporada — `season.py`
Geração de campeonato round-robin (2 turnos por divisão) e chaves da Copa (5 fases, todas com jogo de ida e volta, incluindo a final). Classificação com critérios de desempate, promoção/rebaixamento, patrocínios mensais e folha salarial.

### Mercados — `transfers.py` e `manager_market.py`
- `transfers.py`: Leilão de jogadores com IA de lances, renovação de contratos, restrições de elenco mínimo.
- `manager_market.py`: Demissão automática por pressão, pool de técnicos livres, cooldown anti-retaliação.

### Camada de UI — `ui/` e `term.py`
`term.py` fornece primitivos ANSI (cores, box-drawing, tabelas). O pacote `ui/` compõe as telas do jogo por domínio: menus, dashboard, copa, standings, finanças, táticas, partida ao vivo, histórico e transferências. Não há framework de UI — tudo é renderizado via `print` com códigos ANSI.

### Loop Principal — `main.py`
Orquestra a carreira: simula rodadas, aplica treinamento, dispara leilões imediatos de contrato e processa o mercado de técnicos. Contém rivalidades clássicas (Fla-Flu, Corinthians-Palmeiras, etc.).

### Persistência — `save.py`
Serialização via `pickle` em `~/.classicfoot/save.pkl` com backup automático (`.bak.pkl`). Migrações de schema (v1→v3) usam `getattr(obj, "field", default)` para compatibilidade com saves antigos.

### Camada de Aplicação — `application/`
- `events.py`: Log estruturado de eventos da carreira (`CareerEvent`).
- `orchestrator.py`: `CareerOrchestrator` separa callbacks de UI da lógica de jogo via adapters.

### Configuração — `config/`
- `economy.py`: Tabelas de prêmios, patrocínio base por divisão, multiplicadores.
- `runtime.py`: `apply_random_seed_from_env()` para simulações reprodutíveis.

## Decisões de Design Importantes

- **OVR único (0-99)** direciona toda a performance — não há atributos separados.
- **Poisson sem NumPy** mantém zero dependências pesadas para simulação.
- **Pickle completo** — o estado inteiro é serializado (não diffs incrementais).
- **Copa: final com 2 jogos** — não é partida única; essa é uma regra oficial documentada em `SIMULATION_RULES.md`.
- **Preços de ingresso centralizados** em `models.py` (não duplicar em `season.py` ou `ui.py`).
- **Schema v3** com retrocompatibilidade via `getattr` — ao adicionar campos a dataclasses, sempre fornecer `default` ou `default_factory`.

## Fluxo de Dados (Game Loop)

```
main.py
  └─ CareerOrchestrator
      ├─ data.py → 32 equipes de data/teams.json
      ├─ season.py → fixtures da liga + Copa + tabela
      └─ Por rodada:
          ├─ engine.py → simulate_match() → MatchResult
          ├─ transfers.py → leilão imediato de contratos
          ├─ manager_market.py → demissão/contratação de técnicos
          ├─ season.py → pagar salários, patrocínio mensal
          └─ save.py → ~/.classicfoot/save.pkl
```

## Estrutura de Testes

Os testes ficam em `tests/` e usam `unittest`. `tests/helpers.py` expõe `make_player()` e `make_team()` para criação rápida de fixtures. O CI (`.github/workflows/ci.yml`) roda: compilação, mypy e `unittest discover`.

Ao adicionar uma feature:
1. Estender dataclass em `models.py` (com `default` para compatibilidade de save).
2. Implementar lógica no módulo correto (`engine.py`, `season.py`, etc.).
3. Adicionar telas no módulo correspondente em `ui/` se necessário.
4. Escrever testes em `tests/`.
5. Atualizar `SIMULATION_RULES.md` se a regra do jogo mudar.
