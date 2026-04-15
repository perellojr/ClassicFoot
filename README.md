# ClassicFoot

Jogo de terminal inspirado no clima de Elifoot 2, com foco em temporada rápida, tabelas, elencos e simulação leve.

## O que já existe

- 32 clubes no total
- 4 divisões com 8 clubes cada
- criação de treinador com nome e sobrenome no início da carreira
- início obrigatório em um clube da Divisão 4
- Elencos gerados com até 30 jogadores por time
- Temporada com ida e volta dentro de cada divisão
- Copa ClassicFoot em mata-mata espalhada ao longo da temporada
- Menu de terminal para escolher clube, jogar mês a mês, ver tabela, elenco e artilharia
- Promoção e rebaixamento ao fim do ano

## Como rodar

```bash
python3 main.py
```

## Como validar

```bash
python3 -m unittest discover -s tests -v
```

## Estrutura

- `main.py`: ponto de entrada
- `classicfoot/data.py`: clubes e geração de elencos
- `classicfoot/models.py`: entidades do jogo
- `classicfoot/engine.py`: simulação de liga e copa
- `classicfoot/cli.py`: interface em terminal

## Próximos passos sugeridos

- mercado de transferências
- lesões e suspensões
- evolução de jogadores por idade e desempenho
- finanças mensais e premiações
- salvar e carregar temporadas
- confrontos em duas mãos na copa
