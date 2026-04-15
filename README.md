# ClassicFoot

Jogo de futebol manager em terminal, inspirado no estilo retrô do Elifoot 2.

## Principais recursos

- 32 clubes brasileiros em 4 divisões (8 times por divisão)
- carreira com criação de treinador (nome e sobrenome)
- início obrigatório em clube sorteado da 4ª divisão
- ligas com ida e volta, promoção/rebaixamento e premiação por posição
- Copa em mata-mata com ida e volta (incluindo final em 2 jogos)
- motor de partida ao vivo com eventos, intervalo e substituições
- mercado de transferências com leilões e histórico de negociações
- sistema de treinadores (demissões, ofertas, desemprego e recolocação)
- finanças do clube (salários, estádio, empréstimos, rendas e bônus por vitória)
- treino por rodada (até 5 jogadores com evolução aleatória)
- jogadores `CRAQUE` com impacto adicional no desempenho do time
- histórico de carreira e estatísticas históricas globais
- save/load da carreira
- tema visual retrô `MSDOS` opcional

## Requisitos

- Python 3.11+ (recomendado)
- dependências em `requirements.txt`

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como rodar

```bash
python3 main.py
```

Rodar com tema retrô MSDOS:

```bash
CLASSICFOOT_THEME=msdos python3 main.py
```

Opcional: ajustar duração de cada tempo (em segundos):

```bash
CLASSICFOOT_HALF_DURATION_SECONDS=20 python3 main.py
```

## Verificação rápida

```bash
python3 -m py_compile data.py main.py season.py engine.py ui.py term.py manager_market.py models.py transfers.py save.py
```

## Estrutura do projeto

- `main.py`: loop principal da carreira e fluxo de rodada
- `ui.py`: telas e menus de terminal
- `term.py`: renderização (caixas, tabela, cores e tema MSDOS)
- `engine.py`: simulação das partidas e cálculo de desempenho
- `season.py`: calendário, copa, premiações e transições de temporada
- `transfers.py`: leilões e negociações de jogadores
- `manager_market.py`: mercado de treinadores e lógica de ofertas/demissões
- `data.py`: base de times/elencos e dados iniciais
- `models.py`: entidades e dataclasses do domínio
- `save.py`: persistência de jogo salvo

## Estado atual

Projeto em evolução contínua, com foco em experiência retrô, simulação rápida e progressão de carreira.
