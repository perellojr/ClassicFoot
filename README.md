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

Simulação reproduzível (seed fixa):

```bash
CLASSICFOOT_SEED=12345 python3 main.py
```

## Build app (macOS / Windows)

Build por script (recomendado):

```bash
# macOS
./build_mac.sh

# Windows
build_windows.bat
```

Saídas:

- macOS: `dist/ClassicFoot.app`
- Windows: `dist/ClassicFoot/ClassicFoot.exe`

No macOS, abra o `.app` diretamente (não via `.pkg`).  
Se bloquear no Gatekeeper: clique direito no app > `Abrir`.

## Publicar uma release

Crie e envie uma tag semântica — o CI cuida do build e publica automaticamente:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Isso dispara o workflow `.github/workflows/release.yml`, que:

1. Builda `ClassicFoot-mac.zip` e `ClassicFoot-windows.zip` em paralelo
2. Cria um GitHub Release com changelog automático
3. Publica no itch.io (se os secrets `BUTLER_CREDENTIALS` e `ITCH_USERNAME` estiverem configurados em `Settings → Secrets → Actions`)

## Testes automatizados

Executar suíte completa:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Escopo atual dos testes:

- estrutura dos dados e criação de temporada
- engine e resultado de partida (incluindo metadados de escalação usada)
- mercado de transferências (lances, bloqueio de IA, elenco mínimo)
- mercado de treinadores (anti-reprocesso na rodada e anti-recontratação imediata)
- fluxo principal (sorteio da copa e bloqueio do time do jogador no leilão IA)
- save/load round-trip completo (JSON)
- rivalidades dinâmicas
- estresse de simulação com 40 temporadas completas

Rodar somente o teste de estresse (40 temporadas):

```bash
python3 -m unittest tests.test_long_simulation -v
```

## CI (GitHub Actions)

O projeto possui dois workflows:

**`ci.yml`** — validação contínua em `push`/`pull_request`:

- lint com `ruff`
- `py_compile` de todos os módulos
- `mypy` (type checking)
- suíte `unittest` com coverage (Ubuntu + macOS)

**`release.yml`** — build e publicação ao criar uma tag `v*.*.*`:

- build macOS + Windows em paralelo via PyInstaller
- GitHub Release com changelog automático
- upload para itch.io (opcional, via secrets)

## Estrutura do projeto

- `main.py`: loop principal da carreira
- `gameplay.py`: execução ao vivo de rodadas (lineups, tempos, substituições, pênaltis)
- `rivalries.py`: rivalidades clássicas e dinâmicas
- `ui/`: telas e navegação (pacote, substitui o antigo `ui.py`)
- `term.py`: renderização e estilos ANSI/box
- `engine.py`: simulação de partidas
- `season.py`: calendário, copa e regras de temporada
- `transfers.py`: leilões e transferências
- `manager_market.py`: mercado de treinadores
- `data.py`: times, jogadores e dados iniciais
- `models.py`: dataclasses e entidades
- `save.py`: persistência (JSON, com fallback automático para saves antigos em pickle)
- `application/`: camada de aplicação
  - `events.py`: registro central de eventos/notificações da carreira
  - `history.py`: histórico de temporada e estatísticas mundiais
  - `orchestrator.py`: orquestração do ciclo de carreira/temporada
- `config/`: parâmetros de runtime e economia
  - `economy.py`: premiações, patrocínio e constantes financeiras
  - `runtime.py`: seed opcional e flags de execução
- `.github/workflows/ci.yml`: pipeline de validação contínua
- `.github/workflows/release.yml`: build e publicação de releases

## Regras oficiais da simulação

- Consulte [SIMULATION_RULES.md](/Users/cperello/Documents/Dev/Pessoal/ClassicFoot/SIMULATION_RULES.md) para o baseline oficial da v1.

## Observações

- Save padrão: `~/.classicfoot/save.json` (saves antigos em `.pkl` são migrados automaticamente)
- Pastas de build locais (`build/`, `dist/`) não são versionadas
