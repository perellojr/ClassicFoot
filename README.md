# ClassicFoot

Manager de futebol retrô inspirado no Elifoot 2, com foco em gameplay rápido, visual DOS e progressão de carreira.

## O que o jogo tem hoje

- 32 clubes em 4 divisões (8 por divisão)
- criação de treinador e início aleatório na 4ª divisão
- liga completa com promoção/rebaixamento, premiação e bônus por vitória
- copa mata-mata com ida/volta em todas as fases (incluindo final em 2 jogos)
- sorteio visual da copa por fase (times saindo da lista e confrontos sendo montados)
- motor de jogo ao vivo com:
  - tempo correndo minuto a minuto
  - lances capitais
  - intervalo com substituições
  - pênaltis exibidos lance a lance quando necessário
- mercado de jogadores por leilão (manual + IA), histórico e venda de atletas
- mercado de treinadores (demissões, contratações, propostas e desemprego)
- finanças (folha, patrocínio mensal, estádio, empréstimo em parcelas, renda de jogo)
- treino por rodada (até 5 jogadores)
- histórico de carreira + recordes globais
- save/load
- launcher desktop (`launcher_gui.py`) com aparência terminal

## Requisitos

- Python 3.11+
- dependências em `requirements.txt`

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como executar

Modo terminal:

```bash
python3 main.py
```

Modo janela própria (sem terminal externo):

```bash
python3 launcher_gui.py
```

Tema retrô MSDOS:

```bash
CLASSICFOOT_THEME=msdos python3 main.py
```

Velocidade de cada tempo (segundos):

```bash
CLASSICFOOT_HALF_DURATION_SECONDS=20 python3 main.py
```

## Build app (macOS / Windows)

Instale o empacotador:

```bash
pip install pyinstaller
```

Build manual:

```bash
pyinstaller --noconfirm --windowed --name ClassicFoot launcher_gui.py
```

Build por script:

- macOS: `./build_mac.sh`
- Windows: `build_windows.bat`

Saídas:

- macOS: `dist/ClassicFoot.app`
- Windows: `dist/ClassicFoot/ClassicFoot.exe`

No macOS, abra o `.app` diretamente (não via `.pkg`).  
Se bloquear no Gatekeeper: clique direito no app > `Abrir`.

## Verificação rápida

```bash
python3 -m py_compile data.py main.py season.py engine.py ui.py term.py manager_market.py models.py transfers.py save.py launcher_gui.py
```

## Estrutura do projeto

- `main.py`: loop principal da carreira
- `ui.py`: telas e navegação
- `term.py`: renderização e estilos ANSI/box
- `engine.py`: simulação de partidas
- `season.py`: calendário, copa e regras de temporada
- `transfers.py`: leilões e transferências
- `manager_market.py`: mercado de treinadores
- `data.py`: times, jogadores e dados iniciais
- `models.py`: dataclasses e entidades
- `save.py`: persistência

## Observações

- Save padrão: `classicfoot_save.pkl`
- Pastas de build locais (`build/`, `dist/`) não são versionadas
