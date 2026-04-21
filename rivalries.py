"""Rivalidades dinâmicas e contexto de confrontos clássicos."""
from season import Season, sort_standings

# Confrontos clássicos históricos (por ID dos clubes).
CLASSIC_PAIRS = {
    frozenset((1, 5)),   # Fla-Flu
    frozenset((1, 15)),  # Fla-Vasco
    frozenset((1, 6)),   # Fla-Botafogo
    frozenset((4, 2)),   # Corinthians-Palmeiras
    frozenset((4, 9)),   # Corinthians-São Paulo
    frozenset((2, 9)),   # Palmeiras-São Paulo
    frozenset((8, 7)),   # Grêmio-Inter
    frozenset((3, 10)),  # Atlético-MG-Cruzeiro
    frozenset((14, 19)), # Bahia-Vitória
    frozenset((11, 23)), # Fortaleza-Ceará
    frozenset((13, 25)), # Athletico-Coritiba
    frozenset((26, 18)), # Goiás-Atlético-GO
}


def _ensure_rivalry_fields(team) -> None:
    if not hasattr(team, "rivalry_points") or not isinstance(getattr(team, "rivalry_points"), dict):
        team.rivalry_points = {}
    if not hasattr(team, "dynamic_rivals") or not isinstance(getattr(team, "dynamic_rivals"), list):
        team.dynamic_rivals = []


def is_classic(home_team, away_team) -> bool:
    if frozenset((home_team.id, away_team.id)) in CLASSIC_PAIRS:
        return True
    home_rivals = set(getattr(home_team, "dynamic_rivals", []) or [])
    away_rivals = set(getattr(away_team, "dynamic_rivals", []) or [])
    return (away_team.id in home_rivals) or (home_team.id in away_rivals)


def is_state_rivalry(home_team, away_team) -> bool:
    """Rivalidade intermediária: clubes do mesmo estado."""
    hs = str(getattr(home_team, "state", "")).strip().upper()
    as_ = str(getattr(away_team, "state", "")).strip().upper()
    return bool(home_team.id != away_team.id and hs and hs == as_)


def register_dynamic_rivalry(team_a, team_b, delta: float) -> None:
    if delta <= 0:
        return
    _ensure_rivalry_fields(team_a)
    _ensure_rivalry_fields(team_b)

    for source, target in ((team_a, team_b), (team_b, team_a)):
        old_score = float(source.rivalry_points.get(target.id, 0.0))
        source.rivalry_points[target.id] = round(min(30.0, old_score + delta), 2)
        if source.rivalry_points[target.id] >= 8.0 and target.id not in source.dynamic_rivals:
            source.dynamic_rivals.append(target.id)


def league_rivalry_context(season: Season, home, away, round_num: int) -> dict:
    division_teams = [club for club in season.all_teams if club.division == home.division]
    ranked = sort_standings(division_teams)
    position_by_id = {club.id: idx + 1 for idx, club in enumerate(ranked)}
    pos_home = int(position_by_id.get(home.id, len(ranked)))
    pos_away = int(position_by_id.get(away.id, len(ranked)))

    # Divisão com 8 clubes: 14 rodadas de liga (ida e volta).
    is_late_round = round_num >= 10
    title_clash = is_late_round and pos_home <= 2 and pos_away <= 2
    promotion_clash = is_late_round and home.division > 1 and pos_home <= 3 and pos_away <= 3
    return {
        "league_title_clash": title_clash,
        "league_promotion_clash": promotion_clash,
    }
