# Regras de Simulação (v1)

Este documento define as regras oficiais da simulação do ClassicFoot v1.

## 1) Estrutura da Temporada

- 32 clubes em 4 divisões (8 por divisão).
- Liga em pontos corridos (ida e volta por divisão).
- Copa nacional em mata-mata:
  - 1ª Fase (32 -> 16), Oitavas (16 -> 8), Quartas (8 -> 4), Semi (4 -> 2), Final (2 -> campeão).
  - Todas as fases em ida e volta (incluindo final).
  - Empate no agregado decide nos pênaltis.

## 2) Criação da Carreira

- O treinador é criado com nome e sobrenome.
- O clube inicial do jogador é sorteado na 4ª divisão.
- O time inicial não é escolhido manualmente.

## 3) Motor de Partida

- Simulação em dois tempos (0–45 e 46–90).
- Exibição ao vivo de placares e lances capitais.
- Intervalo com substituições do time do jogador (máximo 5).
- Escalação:
  - 11 titulares.
  - até 12 reservas.
  - exatamente 1 goleiro em campo.
- Cartão vermelho remove o jogador da partida.
- Goleiro expulso: substituição automática se houver goleiro no banco.

## 4) Força do Time e Tática

- A métrica base de jogador é o OVR.
- A força da equipe combina:
  - OVR dos 11 usados,
  - formação,
  - postura tática (defensivo/equilibrado/ofensivo),
  - bônus do treinador.
- Postura ofensiva aumenta criação ofensiva e risco defensivo.
- Postura defensiva reduz risco defensivo e volume ofensivo.
- Tática `BEST XI` escolhe 1 goleiro + 10 melhores OVR válidos.

## 5) Estatísticas e Artilharia

- Global: considera gols/jogos da temporada inteira (Liga + Copa).
- Ranking por divisão: considera somente jogos de Liga.
- Ranking da Copa: considera somente jogos de Copa.

## 6) Mercado de Jogadores (Leilão)

- Leilões automáticos surgem por contratos expirando.
- Leilões manuais podem ser criados pela tela de venda.
- Clube com caixa negativo não participa de leilão.
- Limites de elenco:
  - mínimo para venda/listagem: 16 jogadores,
  - máximo de elenco: 45 jogadores.
- IA disputa leilões entre clubes não bloqueados.
- O time do jogador só oferta por lance manual (não via IA).

## 7) Contratos

- Renovação pode ser aceita ou recusada por probabilidade (baseada na proposta salarial).
- Se recusar renovação:
  - renovação automática forçada com aumento salarial e novo prazo.
- Contratos expiram por rodada.

## 8) Mercado de Treinadores

- Demissões por pressão de desempenho (posição, sequência, aproveitamento).
- Proteções:
  - não recontratar imediatamente o técnico recém-demitido no mesmo clube,
  - cooldown de demissão após troca,
  - processamento de mercado de técnicos focado nas rodadas de Liga.
- Treinador do jogador pode:
  - ser demitido por desempenho,
  - receber propostas compatíveis com reputação e momento.

## 9) Finanças

- Componentes principais:
  - folha salarial,
  - patrocínio mensal,
  - renda de bilheteria,
  - manutenção do estádio,
  - empréstimos e parcelas.
- Patrocínio mensal usa divisão + prestígio + torcida, com piso ligado à folha.
- Bônus por vitória de Liga:
  - vitória em casa: bônus adicional sobre a renda,
  - vitória fora: bônus maior.
- Empréstimo:
  - pagamento em 12x,
  - opção de quitação antecipada com juros reduzidos.

## 10) Progressão de Torcida e Divisão

- Subir de divisão tende a aumentar torcida/prestígio.
- Permanecer tende a crescimento leve.
- Cair de divisão tende a reduzir engajamento/prestígio.
- Clássicos e jogos decisivos da Copa tendem a elevar lotação.

## 11) Recordes e Histórico

- Mantém histórico de:
  - campeões da liga/copa,
  - técnicos campeões (critérios definidos),
  - artilharia e ataques acumulados,
  - maiores públicos/rendas e maior goleada.
- Compatibilidade com saves antigos via normalização/migração dos campos.

## 12) Regras de Interface

- Layout retro em caixas ANSI (modo terminal e launcher desktop).
- Campos longos são truncados com `...` para evitar quebra visual.
- Atualizações de rodada priorizam classificação/copa + artilheiros.

---

## Escopo v1 (congelamento)

As regras acima são o baseline oficial da v1. Mudanças estruturais devem atualizar este documento junto com o changelog.
