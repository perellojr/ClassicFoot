"""
ClassicFoot - Construtor de times (gerador do data/teams.json).

Não importar diretamente no jogo — use data.py.
Para regenerar data/teams.json após alterar dados:

    python scripts/build_teams_json.py
"""
from models import Player, Team, Coach, Formation, Postura, Position as P

_pid = 0
def _p(name, pos, age, nat, ovr, *_ignored):
    """Cria um Player. Args extras (atributos individuais legados) são ignorados."""
    global _pid
    _pid += 1
    return Player(id=_pid, name=name, position=pos, age=age, nationality=nat, overall=float(ovr))

GK, DEF, MID, ATK = P.GK, P.DEF, P.MID, P.ATK
BR = "Brasileiro"
GENERIC_FIRST_NAMES = [
    "Pedro", "Paulinho", "Roberto", "Carlos", "João", "Lucas", "Mateus",
    "Rafael", "Bruno", "André", "Felipe", "Diego", "Renan", "Marcos",
]
GENERIC_LAST_NAMES = [
    "Augusto", "Silva", "Souza", "Santos", "Oliveira", "Rocha", "Lima",
    "Moura", "Pereira", "Costa", "Fernandes", "Ribeiro", "Teixeira", "Alves",
]


def _generic_team(
    team_id, name, short_name, city, state, stadium, division, prestige,
    coach_name, primary_color, secondary_color, base_ovr
):
    team = Team(
        id=team_id, name=name, short_name=short_name,
        city=city, state=state,
        stadium=stadium, division=division, prestige=prestige,
        coach=Coach(coach_name, BR, tactical=max(66, prestige), motivation=max(68, prestige), experience=max(64, prestige - 2)),
        primary_color=primary_color, secondary_color=secondary_color,
    )
    team.players = [
        _p(f"Goleiro {short_name} 1",  GK, 29, BR, base_ovr + 3, 48, 58, 20, 48, 66, 70, 54, base_ovr + 6),
        _p(f"Goleiro {short_name} 2",  GK, 22, BR, base_ovr - 4, 46, 52, 18, 44, 60, 62, 48, base_ovr - 1),
        _p(f"Zagueiro {short_name} 1", DEF, 29, BR, base_ovr + 1, 66, 66, 22, 58, 72, 72, 66, 12),
        _p(f"Zagueiro {short_name} 2", DEF, 27, BR, base_ovr,     68, 64, 22, 56, 70, 70, 62, 12),
        _p(f"Lateral {short_name} 1",  DEF, 26, BR, base_ovr - 1, 74, 66, 26, 60, 66, 64, 54, 10),
        _p(f"Lateral {short_name} 2",  DEF, 24, BR, base_ovr - 2, 72, 64, 24, 58, 64, 62, 52, 10),
        _p(f"Volante {short_name} 1",  MID, 28, BR, base_ovr + 1, 68, 70, 52, 70, 72, 66, 56, 10),
        _p(f"Volante {short_name} 2",  MID, 25, BR, base_ovr - 1, 68, 68, 50, 68, 68, 64, 54, 10),
        _p(f"Meia {short_name} 1",     MID, 27, BR, base_ovr + 2, 72, 72, 58, 72, 66, 60, 52, 10),
        _p(f"Meia {short_name} 2",     MID, 23, BR, base_ovr,     74, 70, 56, 70, 64, 58, 50, 10),
        _p(f"Meia {short_name} 3",     MID, 21, BR, base_ovr - 2, 72, 68, 52, 68, 62, 56, 48, 10),
        _p(f"Ponta {short_name} 1",    ATK, 26, BR, base_ovr + 2, 80, 72, 70, 58, 64, 50, 56, 10),
        _p(f"Ponta {short_name} 2",    ATK, 24, BR, base_ovr,     78, 70, 68, 56, 62, 48, 54, 10),
        _p(f"Centroavante {short_name} 1", ATK, 28, BR, base_ovr + 3, 74, 70, 74, 54, 72, 54, 68, 10),
        _p(f"Centroavante {short_name} 2", ATK, 22, BR, base_ovr - 1, 76, 68, 66, 52, 66, 48, 60, 10),
        _p(f"Reserva {short_name} 1",  MID, 24, BR, base_ovr - 3, 68, 64, 48, 64, 60, 54, 46, 10),
        _p(f"Reserva {short_name} 2",  DEF, 23, BR, base_ovr - 3, 66, 62, 20, 54, 62, 60, 52, 10),
    ]
    return team


def _name_nat(spec):
    if isinstance(spec, tuple):
        return spec[0], spec[1]
    return spec, BR


def _build_named_roster(base_ovr, goalkeepers, defenders, midfielders, attackers):
    players = []

    gk_ages = [33, 28, 23, 20]
    def_ages = [31, 29, 28, 27, 26, 24, 23, 21, 20]
    mid_ages = [32, 30, 28, 27, 25, 24, 22, 21, 20]
    atk_ages = [33, 30, 28, 26, 24, 23, 21, 20]

    for idx, spec in enumerate(goalkeepers):
        name, nat = _name_nat(spec)
        ovr = max(62, base_ovr + 4 - (idx * 2))
        players.append(_p(
            name, GK, gk_ages[min(idx, len(gk_ages) - 1)], nat,
            ovr, 48, 58, 20, 48, 66, 70, 54, ovr + 3
        ))

    for idx, spec in enumerate(defenders):
        name, nat = _name_nat(spec)
        ovr = max(60, base_ovr + 3 - idx)
        pace = 75 if idx >= 4 else 69
        players.append(_p(
            name, DEF, def_ages[min(idx, len(def_ages) - 1)], nat,
            ovr, pace, 68, 24, 60, 72, 72, 64, 10
        ))

    for idx, spec in enumerate(midfielders):
        name, nat = _name_nat(spec)
        ovr = max(60, base_ovr + 3 - idx)
        players.append(_p(
            name, MID, mid_ages[min(idx, len(mid_ages) - 1)], nat,
            ovr, 72, 72, 58, 72, 68, 62, 54, 10
        ))

    for idx, spec in enumerate(attackers):
        name, nat = _name_nat(spec)
        ovr = max(60, base_ovr + 4 - idx)
        players.append(_p(
            name, ATK, atk_ages[min(idx, len(atk_ages) - 1)], nat,
            ovr, 80, 72, 72, 58, 70, 52, 62, 10
        ))

    return players


def _named_team(
    team_id, name, short_name, city, state, stadium, division, prestige,
    coach_name, primary_color, secondary_color, base_ovr,
    goalkeepers, defenders, midfielders, attackers
):
    team = Team(
        id=team_id, name=name, short_name=short_name,
        city=city, state=state,
        stadium=stadium, division=division, prestige=prestige,
        coach=Coach(coach_name, BR, tactical=max(66, prestige), motivation=max(68, prestige), experience=max(64, prestige - 2)),
        primary_color=primary_color, secondary_color=secondary_color,
    )
    team.players = _build_named_roster(base_ovr, goalkeepers, defenders, midfielders, attackers)
    return team


def create_all_teams():
    teams = []

    # =========================================================
    # DIVISÃO 1
    # =========================================================

    # --- FLAMENGO ---
    flamengo = Team(
        id=1, name="Flamengo", short_name="FLA",
        city="Rio de Janeiro", state="RJ",
        stadium="Maracanã", division=1, prestige=97,
        coach=Coach("Leonardo Jardim", "Português", tactical=84, motivation=85, experience=84),
        primary_color="red", secondary_color="black"
    )
    flamengo.players = [
        _p("Rossi",             GK,  28, "Argentino",  86, 52, 64, 30, 55, 74, 82, 58, 87),
        _p("Santos",            GK,  23, BR,           72, 54, 60, 25, 52, 70, 72, 55, 73),
        _p("Léo Pereira",       DEF, 28, BR,           84, 72, 74, 38, 65, 86, 84, 80, 14),
        _p("Fabrício Bruno",    DEF, 28, BR,           82, 64, 73, 32, 67, 82, 84, 78, 12),
        _p("Léo Ortiz",         DEF, 28, BR,           81, 70, 74, 33, 68, 83, 82, 76, 12),
        _p("Ayrton Lucas",      DEF, 27, BR,           78, 82, 72, 42, 70, 74, 72, 62, 11),
        _p("Guillermo Varela",  DEF, 31, "Uruguaio",   76, 80, 72, 36, 68, 74, 74, 60, 10),
        _p("David Luiz",        DEF, 37, BR,           76, 56, 80, 34, 76, 72, 78, 80, 12),
        _p("Gerson",            MID, 27, BR,           87, 74, 85, 62, 82, 84, 76, 68, 10),
        _p("De La Cruz",        MID, 28, "Uruguaio",   85, 76, 86, 65, 84, 76, 72, 62, 10),
        _p("Arrascaeta",        MID, 30, "Uruguaio",   88, 80, 90, 72, 86, 74, 66, 58, 10),
        _p("Pulgar",            MID, 30, "Chileno",    77, 70, 76, 64, 78, 80, 74, 70, 10),
        _p("Allan",             MID, 32, BR,           74, 72, 72, 52, 72, 82, 76, 64, 10),
        _p("Matheus Gonçalves", MID, 20, BR,           75, 82, 76, 62, 74, 70, 62, 55, 10),
        _p("Pedro",             ATK, 27, BR,           89, 74, 84, 88, 72, 84, 76, 86, 10),
        _p("Bruno Henrique",    ATK, 33, BR,           80, 84, 78, 74, 68, 78, 62, 64, 10),
        _p("Éverton Cebolinha", ATK, 28, BR,           81, 88, 80, 76, 72, 76, 58, 62, 10),
        _p("Plata",             ATK, 25, "Equatoriano", 83, 90, 82, 76, 70, 72, 55, 60, 10),
        _p("Wesley",            ATK, 22, BR,           78, 86, 76, 72, 65, 72, 58, 60, 10),
        _p("Wallace Yan",       ATK, 21, BR,           72, 80, 72, 66, 60, 68, 52, 58, 10),
        _p("Carlinhos",         ATK, 24, BR,           71, 78, 70, 65, 60, 66, 50, 56, 10),
        _p("Carlos Alcaraz",    MID, 22, "Argentino",  76, 78, 78, 60, 76, 74, 68, 58, 10),
    ]

    # --- PALMEIRAS ---
    palmeiras = Team(
        id=2, name="Palmeiras", short_name="PAL",
        city="São Paulo", state="SP",
        stadium="Allianz Parque", division=1, prestige=95,
        coach=Coach("Abel Ferreira", "Português", tactical=90, motivation=86, experience=82),
        primary_color="green", secondary_color="white"
    )
    palmeiras.players = [
        _p("Weverton",          GK,  36, BR,           88, 56, 70, 28, 60, 78, 84, 62, 89),
        _p("Marcelo Lomba",     GK,  36, BR,           72, 50, 60, 22, 55, 70, 72, 58, 73),
        _p("Gustavo Gómez",     DEF, 31, "Paraguaio",  85, 70, 76, 36, 72, 86, 86, 82, 12),
        _p("Murilo",            DEF, 27, BR,           83, 74, 74, 32, 68, 82, 84, 78, 12),
        _p("Piquerez",          DEF, 27, "Uruguaio",   81, 82, 74, 42, 72, 76, 76, 66, 11),
        _p("Marcos Rocha",      DEF, 35, BR,           76, 76, 72, 34, 66, 74, 72, 58, 10),
        _p("Mayke",             DEF, 31, BR,           75, 78, 70, 36, 65, 74, 70, 56, 10),
        _p("Michel",            DEF, 21, BR,           73, 72, 70, 30, 64, 72, 72, 60, 10),
        _p("Raphael Veiga",     MID, 29, BR,           88, 78, 86, 82, 82, 76, 68, 60, 10),
        _p("Richard Ríos",      MID, 24, "Colombiano", 83, 80, 80, 62, 80, 82, 74, 64, 10),
        _p("Zé Rafael",         MID, 32, BR,           79, 72, 76, 58, 78, 82, 76, 66, 10),
        _p("Aníbal Moreno",     MID, 27, "Argentino",  79, 74, 78, 60, 78, 82, 76, 65, 10),
        _p("Gabriel Menino",    MID, 24, BR,           77, 78, 76, 62, 76, 78, 72, 60, 10),
        _p("Maurício",          MID, 23, BR,           77, 80, 76, 65, 76, 74, 66, 58, 10),
        _p("Estêvão",           ATK, 18, BR,           86, 88, 86, 78, 78, 70, 58, 62, 10),
        _p("Flaco López",       ATK, 25, "Argentino",  85, 76, 80, 84, 68, 80, 74, 78, 10),
        _p("Dudu",              ATK, 32, BR,           82, 84, 80, 75, 72, 74, 60, 64, 10),
        _p("Rony",              ATK, 28, BR,           77, 86, 74, 72, 66, 74, 58, 62, 10),
        _p("Lázaro",            ATK, 23, BR,           74, 82, 74, 68, 64, 68, 54, 58, 10),
        _p("Facundo Torres",    ATK, 25, "Uruguaio",   80, 84, 80, 74, 70, 70, 56, 60, 10),
        _p("Felipe Anderson",   ATK, 31, BR,           79, 84, 78, 72, 72, 72, 58, 60, 10),
    ]

    # --- ATLÉTICO MINEIRO ---
    atletico_mg = Team(
        id=3, name="Atlético Mineiro", short_name="CAM",
        city="Belo Horizonte", state="MG",
        stadium="Arena MRV", division=1, prestige=90,
        coach=Coach("Eduardo Domínguez", "Argentino", tactical=84, motivation=82, experience=82),
        primary_color="black", secondary_color="white"
    )
    atletico_mg.players = [
        _p("Everson",           GK,  34, BR,           85, 52, 66, 28, 56, 76, 82, 60, 86),
        _p("Guilherme",         GK,  24, BR,           72, 54, 60, 22, 52, 68, 70, 55, 73),
        _p("Guilherme Arana",   DEF, 27, BR,           84, 84, 78, 44, 72, 78, 76, 66, 11),
        _p("Júnior Alonso",     DEF, 31, "Paraguaio",  81, 66, 72, 30, 68, 84, 84, 78, 12),
        _p("Mauricio Lemos",    DEF, 27, "Uruguaio",   80, 70, 72, 30, 66, 82, 82, 76, 12),
        _p("Rubens",            DEF, 26, BR,           77, 82, 72, 40, 68, 74, 72, 62, 10),
        _p("Mariano",           DEF, 30, BR,           74, 76, 70, 34, 64, 72, 70, 58, 10),
        _p("Lyanco",            DEF, 27, BR,           76, 70, 72, 30, 66, 80, 80, 72, 12),
        _p("Alisson",           MID, 31, BR,           84, 76, 80, 70, 78, 80, 72, 66, 10),
        _p("Otávio",            MID, 28, BR,           79, 74, 78, 62, 78, 78, 72, 64, 10),
        _p("Alan Franco",       MID, 27, "Equatoriano", 78, 72, 74, 58, 76, 82, 76, 66, 10),
        _p("Fausto Vera",       MID, 26, "Argentino",  77, 72, 74, 60, 74, 80, 74, 62, 10),
        _p("Igor Gomes",        MID, 26, BR,           75, 74, 74, 58, 74, 74, 68, 60, 10),
        _p("Battaglia",         MID, 30, "Argentino",  75, 68, 74, 58, 76, 80, 76, 64, 10),
        _p("Hulk",              ATK, 38, BR,           83, 72, 80, 80, 68, 84, 70, 74, 10),
        _p("Paulinho",          ATK, 23, BR,           87, 86, 82, 84, 70, 82, 62, 76, 10),
        _p("Deyverson",         ATK, 33, BR,           79, 80, 72, 76, 62, 80, 64, 72, 10),
        _p("Vargas",            ATK, 35, "Chileno",    80, 82, 78, 74, 70, 74, 60, 66, 10),
        _p("Cadu",              ATK, 21, BR,           73, 82, 72, 68, 62, 68, 54, 60, 10),
        _p("Alan Kardec",       ATK, 36, BR,           72, 70, 68, 70, 60, 72, 62, 68, 10),
        _p("Wanderson",         ATK, 30, BR,           74, 82, 72, 68, 64, 68, 56, 60, 10),
    ]

    # --- CORINTHIANS ---
    corinthians = Team(
        id=4, name="Corinthians", short_name="COR",
        city="São Paulo", state="SP",
        stadium="Neo Química Arena", division=1, prestige=91,
        coach=Coach("Fernando Diniz", BR, tactical=82, motivation=79, experience=84),
        primary_color="white", secondary_color="black"
    )
    corinthians.players = [
        _p("Hugo Souza",        GK,  24, BR,           83, 58, 66, 28, 58, 74, 80, 60, 84),
        _p("Matheus Donelli",   GK,  22, BR,           74, 55, 62, 24, 54, 68, 72, 56, 75),
        _p("Félix Torres",      DEF, 27, "Equatoriano", 83, 72, 76, 34, 68, 84, 84, 80, 12),
        _p("Cacá",              DEF, 25, BR,           79, 74, 74, 32, 66, 82, 82, 76, 12),
        _p("Matheuzinho",       DEF, 24, BR,           77, 82, 72, 38, 66, 74, 70, 58, 10),
        _p("Hugo",              DEF, 27, BR,           76, 78, 70, 36, 65, 76, 72, 60, 10),
        _p("Fagner",            DEF, 35, BR,           73, 74, 70, 34, 64, 72, 70, 55, 10),
        _p("João Pedro Tchoca", DEF, 23, BR,           75, 70, 72, 32, 66, 78, 78, 72, 12),
        _p("Rodrigo Garro",     MID, 26, "Argentino",  84, 78, 86, 74, 84, 72, 66, 60, 10),
        _p("Breno Bidon",       MID, 20, BR,           80, 76, 78, 64, 78, 78, 70, 62, 10),
        _p("Charles",           MID, 29, BR,           79, 74, 76, 62, 76, 82, 76, 64, 10),
        _p("Raniele",           MID, 27, BR,           78, 72, 74, 60, 76, 80, 74, 64, 10),
        _p("André Carrillo",    MID, 33, "Peruano",    77, 82, 76, 68, 72, 72, 64, 58, 10),
        _p("Alex Santana",      MID, 30, BR,           75, 72, 72, 58, 74, 78, 72, 62, 10),
        _p("Yuri Alberto",      ATK, 23, BR,           83, 80, 78, 82, 66, 78, 62, 72, 10),
        _p("Wesley",            ATK, 24, BR,           79, 84, 76, 74, 66, 74, 58, 62, 10),
        _p("Romero",            ATK, 34, "Paraguaio",  76, 82, 74, 70, 66, 72, 58, 62, 10),
        _p("Gustavo Mosquito",  ATK, 27, BR,           74, 84, 72, 68, 62, 68, 54, 58, 10),
        _p("Talles Magno",      ATK, 23, BR,           73, 82, 72, 66, 62, 66, 52, 57, 10),
        _p("Pedro Raul",        ATK, 26, BR,           76, 70, 70, 74, 58, 76, 60, 72, 10),
    ]

    # --- FLUMINENSE ---
    fluminense = Team(
        id=5, name="Fluminense", short_name="FLU",
        city="Rio de Janeiro", state="RJ",
        stadium="Maracanã", division=1, prestige=84,
        coach=Coach("Renato Gaúcho", BR, tactical=80, motivation=82, experience=88),
        primary_color="green", secondary_color="white"
    )
    fluminense.players = [
        _p("Fábio",             GK,  43, BR,           83, 48, 68, 25, 60, 70, 80, 58, 84),
        _p("Vitor Eudes",       GK,  21, BR,           70, 52, 58, 22, 50, 66, 68, 52, 71),
        _p("Marcelo",           DEF, 36, BR,           81, 80, 80, 44, 76, 72, 72, 64, 10),
        _p("Nino",              DEF, 27, BR,           79, 68, 74, 32, 68, 82, 82, 76, 12),
        _p("Thiago Santos",     DEF, 31, BR,           78, 68, 72, 30, 68, 80, 80, 74, 12),
        _p("Manoel",            DEF, 34, BR,           74, 66, 70, 28, 66, 78, 76, 70, 12),
        _p("Samuel Xavier",     DEF, 32, BR,           76, 78, 70, 36, 64, 74, 70, 56, 10),
        _p("Diogo Barbosa",     DEF, 30, BR,           75, 80, 70, 38, 66, 72, 70, 58, 10),
        _p("Jhon Arias",        MID, 26, "Colombiano", 85, 86, 82, 72, 76, 74, 62, 58, 10),
        _p("Ganso",             MID, 34, BR,           82, 60, 88, 68, 88, 66, 62, 52, 10),
        _p("Martinelli",        MID, 23, BR,           80, 74, 78, 64, 78, 76, 70, 62, 10),
        _p("Alexsander",        MID, 20, BR,           78, 76, 76, 60, 76, 74, 66, 58, 10),
        _p("Renato Augusto",    MID, 36, BR,           79, 66, 84, 66, 84, 68, 64, 56, 10),
        _p("Lima",              MID, 27, BR,           77, 74, 74, 62, 74, 76, 70, 60, 10),
        _p("German Cano",       ATK, 36, "Argentino",  84, 70, 78, 84, 64, 78, 68, 82, 10),
        _p("Keno",              ATK, 33, BR,           76, 86, 74, 70, 64, 70, 56, 60, 10),
        _p("Serna",             ATK, 25, "Colombiano", 77, 84, 76, 72, 68, 68, 54, 60, 10),
        _p("Bernal",            ATK, 22, "Colombiano", 74, 82, 74, 68, 66, 66, 52, 58, 10),
        _p("Lelê",              ATK, 22, BR,           72, 80, 72, 66, 62, 66, 50, 56, 10),
    ]

    # --- BOTAFOGO ---
    botafogo = Team(
        id=6, name="Botafogo", short_name="BOT",
        city="Rio de Janeiro", state="RJ",
        stadium="Estádio Nilton Santos", division=1, prestige=87,
        coach=Coach("Franclim Carvalho", BR, tactical=78, motivation=78, experience=68),
        primary_color="black", secondary_color="white"
    )
    botafogo.players = [
        _p("John",              GK,  26, BR,           85, 54, 66, 28, 56, 76, 82, 60, 86),
        _p("Gatito Fernández",  GK,  36, "Paraguaio",  75, 50, 62, 24, 52, 72, 74, 56, 76),
        _p("Alexander Barboza", DEF, 28, "Uruguaio",   81, 70, 74, 32, 68, 84, 84, 78, 12),
        _p("Lucas Halter",      DEF, 26, BR,           78, 72, 72, 30, 66, 80, 80, 74, 12),
        _p("Bastos",            DEF, 32, "Angolano",   79, 72, 72, 32, 66, 82, 80, 74, 12),
        _p("Marçal",            DEF, 34, BR,           78, 80, 72, 40, 68, 72, 72, 62, 10),
        _p("Cuiabano",          DEF, 23, BR,           77, 82, 70, 38, 66, 72, 70, 58, 10),
        _p("Damián Suárez",     DEF, 36, "Uruguaio",   74, 74, 70, 34, 64, 72, 70, 56, 10),
        _p("Thiago Almada",     MID, 23, "Argentino",  86, 82, 86, 72, 82, 74, 66, 58, 10),
        _p("Savarino",          MID, 27, "Venezuelano", 84, 84, 82, 70, 78, 72, 62, 58, 10),
        _p("Marlon Freitas",    MID, 28, BR,           81, 78, 78, 66, 78, 80, 72, 64, 10),
        _p("Gregore",           MID, 29, BR,           78, 74, 74, 58, 74, 82, 76, 64, 10),
        _p("Eduardo",           MID, 27, "Croata",     76, 76, 76, 64, 76, 72, 68, 58, 10),
        _p("Tiquinho Soares",   ATK, 33, BR,           84, 76, 78, 82, 66, 80, 68, 78, 10),
        _p("Igor Jesus",        ATK, 23, BR,           81, 82, 76, 78, 66, 78, 62, 72, 10),
        _p("Luiz Henrique",     ATK, 23, BR,           83, 88, 80, 76, 68, 72, 58, 64, 10),
        _p("Júnior Santos",     ATK, 25, BR,           79, 84, 76, 74, 64, 72, 56, 62, 10),
        _p("Jeffinho",          ATK, 25, BR,           77, 84, 74, 70, 62, 68, 52, 58, 10),
        _p("Matheus Nascimento", ATK, 21, BR,          74, 82, 72, 68, 60, 70, 54, 62, 10),
    ]

    # =========================================================
    # DIVISÃO 2
    # =========================================================

    # --- INTERNACIONAL ---
    internacional = Team(
        id=7, name="Internacional", short_name="INT",
        city="Porto Alegre", state="RS",
        stadium="Beira-Rio", division=2, prestige=82,
        coach=Coach("Roger Machado", BR, tactical=79, motivation=78, experience=80),
        primary_color="red", secondary_color="white"
    )
    internacional.players = [
        _p("Rochet",            GK,  31, "Uruguaio",   84, 52, 64, 26, 54, 74, 80, 58, 85),
        _p("Anthoni",           GK,  21, BR,           72, 52, 60, 22, 50, 66, 68, 52, 73),
        _p("Vitão",             DEF, 25, BR,           81, 72, 74, 32, 68, 82, 84, 78, 12),
        _p("Mercado",           DEF, 37, "Argentino",  77, 66, 72, 30, 68, 80, 78, 72, 12),
        _p("Fernando",          DEF, 34, BR,           79, 68, 72, 32, 66, 82, 82, 76, 12),
        _p("Bustos",            DEF, 28, "Colombiano", 77, 80, 72, 38, 66, 74, 72, 60, 10),
        _p("Renê",              DEF, 34, BR,           75, 78, 70, 36, 64, 72, 70, 56, 10),
        _p("Clayton Sampaio",   DEF, 23, BR,           72, 72, 68, 28, 62, 72, 70, 58, 10),
        _p("Alan Patrick",      MID, 30, BR,           83, 72, 82, 72, 82, 72, 66, 60, 10),
        _p("Maurício",          MID, 21, BR,           81, 78, 78, 66, 76, 76, 68, 60, 10),
        _p("Bruno Gomes",       MID, 27, BR,           77, 74, 74, 60, 74, 78, 72, 62, 10),
        _p("Rômulo",            MID, 27, BR,           76, 72, 72, 58, 72, 78, 70, 60, 10),
        _p("Gabriel Tabata",    MID, 26, BR,           80, 82, 78, 68, 74, 70, 62, 58, 10),
        _p("Enner Valencia",    ATK, 35, "Equatoriano", 83, 78, 76, 80, 66, 78, 66, 72, 10),
        _p("Rafael Borré",      ATK, 29, "Colombiano", 83, 80, 76, 80, 64, 78, 60, 70, 10),
        _p("Wanderson",         ATK, 30, BR,           76, 82, 72, 70, 64, 68, 54, 60, 10),
        _p("Alario",            ATK, 32, "Argentino",  75, 72, 70, 72, 60, 74, 58, 68, 10),
        _p("Gustavo Prado",     ATK, 22, BR,           73, 78, 70, 66, 60, 66, 52, 60, 10),
        _p("Wesley Moraes",     ATK, 28, BR,           74, 76, 68, 68, 60, 76, 58, 66, 10),
    ]

    # --- GRÊMIO ---
    gremio = Team(
        id=8, name="Grêmio", short_name="GRE",
        city="Porto Alegre", state="RS",
        stadium="Arena do Grêmio", division=2, prestige=83,
        coach=Coach("Luís Castro", "Português", tactical=82, motivation=80, experience=84),
        primary_color="blue", secondary_color="black"
    )
    gremio.players = [
        _p("Marchesín",         GK,  36, "Argentino",  83, 50, 64, 26, 54, 72, 80, 56, 84),
        _p("Caíque",            GK,  25, BR,           72, 52, 60, 22, 50, 66, 68, 52, 73),
        _p("Kannemann",         DEF, 33, "Argentino",  83, 68, 74, 32, 68, 84, 84, 80, 12),
        _p("Geromel",           DEF, 37, BR,           79, 58, 74, 28, 68, 80, 78, 78, 12),
        _p("Reinaldo",          DEF, 34, BR,           78, 80, 72, 40, 68, 72, 72, 62, 10),
        _p("João Pedro",        DEF, 23, BR,           75, 72, 72, 32, 64, 76, 76, 70, 12),
        _p("Natã",              DEF, 24, BR,           73, 74, 70, 30, 62, 74, 72, 62, 10),
        _p("Rodrigo Ely",       DEF, 31, BR,           74, 68, 70, 28, 64, 76, 74, 68, 12),
        _p("Cristaldo",         MID, 29, "Argentino",  84, 76, 84, 74, 82, 72, 66, 58, 10),
        _p("Villasanti",        MID, 27, "Paraguaio",  82, 74, 78, 62, 78, 82, 74, 64, 10),
        _p("Pepê",              MID, 27, BR,           81, 84, 78, 68, 74, 74, 64, 58, 10),
        _p("Du Queiroz",        MID, 25, BR,           77, 76, 74, 60, 74, 76, 70, 60, 10),
        _p("Dodi",              MID, 30, BR,           78, 72, 74, 60, 76, 80, 72, 62, 10),
        _p("Diego Costa",       ATK, 30, BR,           83, 76, 78, 80, 64, 80, 64, 72, 10),
        _p("Braithwaite",       ATK, 33, "Dinamarquês", 80, 80, 76, 76, 66, 76, 64, 72, 10),
        _p("Soteldo",           ATK, 27, "Venezuelano", 82, 88, 84, 74, 72, 66, 54, 56, 10),
        _p("Everton Galdino",   ATK, 28, BR,           80, 84, 76, 74, 64, 70, 56, 62, 10),
        _p("JP Galvão",         ATK, 22, BR,           74, 80, 72, 66, 60, 66, 50, 58, 10),
        _p("André Henrique",    ATK, 25, BR,           73, 78, 70, 66, 60, 68, 52, 60, 10),
    ]

    # --- SÃO PAULO ---
    sao_paulo = Team(
        id=9, name="São Paulo FC", short_name="SPF",
        city="São Paulo", state="SP",
        stadium="MorumBIS", division=2, prestige=80,
        coach=Coach("Luis Zubeldía", "Argentino", tactical=80, motivation=78, experience=76),
        primary_color="red", secondary_color="white"
    )
    sao_paulo.players = [
        _p("Rafael",            GK,  34, BR,           84, 52, 66, 26, 58, 74, 80, 58, 85),
        _p("Young",             GK,  24, BR,           71, 52, 60, 22, 50, 66, 68, 52, 72),
        _p("Arboleda",          DEF, 31, "Equatoriano", 83, 70, 74, 32, 68, 84, 84, 80, 12),
        _p("Sabino",            DEF, 27, BR,           78, 70, 72, 30, 66, 80, 80, 74, 12),
        _p("Moreira",           DEF, 24, "Paraguaio",  76, 72, 70, 28, 64, 76, 76, 68, 12),
        _p("Welington",         DEF, 23, BR,           77, 84, 72, 40, 68, 72, 70, 58, 10),
        _p("Igor Vinicius",     DEF, 27, BR,           75, 80, 70, 36, 64, 72, 70, 56, 10),
        _p("Ferraresi",         DEF, 25, "Venezuelano", 74, 70, 70, 28, 64, 76, 74, 68, 12),
        _p("Calleri",           ATK, 31, "Argentino",  85, 74, 78, 84, 64, 80, 68, 78, 10),
        _p("Lucas Moura",       ATK, 32, BR,           83, 82, 82, 76, 74, 70, 60, 62, 10),
        _p("Luciano",           ATK, 30, BR,           81, 80, 78, 76, 66, 74, 58, 66, 10),
        _p("Pablo Maia",        MID, 23, BR,           81, 76, 78, 62, 78, 78, 72, 62, 10),
        _p("Alisson",           MID, 30, BR,           79, 74, 76, 62, 76, 78, 72, 62, 10),
        _p("Wellington Rato",   MID, 30, BR,           79, 82, 76, 68, 72, 72, 62, 58, 10),
        _p("Galoppo",           MID, 25, "Argentino",  80, 76, 78, 66, 78, 74, 66, 58, 10),
        _p("Bobadilla",         MID, 27, "Paraguaio",  77, 74, 74, 60, 74, 78, 70, 62, 10),
        _p("Lucas",             MID, 26, BR,           76, 72, 72, 58, 72, 74, 68, 60, 10),
        _p("Ferreira",          ATK, 27, BR,           77, 82, 74, 70, 66, 68, 54, 58, 10),
        _p("André Anderson",    ATK, 26, BR,           74, 80, 72, 66, 62, 66, 52, 56, 10),
        _p("William",           ATK, 27, BR,           75, 82, 72, 70, 62, 68, 54, 58, 10),
    ]

    # --- CRUZEIRO ---
    cruzeiro = Team(
        id=10, name="Cruzeiro", short_name="CRU",
        city="Belo Horizonte", state="MG",
        stadium="Mineirão", division=2, prestige=80,
        coach=Coach("Artur Jorge", "Português", tactical=81, motivation=79, experience=78),
        primary_color="blue", secondary_color="white"
    )
    cruzeiro.players = [
        _p("Cássio",            GK,  37, BR,           86, 50, 66, 26, 58, 74, 82, 58, 87),
        _p("Anderson",          GK,  24, BR,           72, 52, 60, 22, 50, 66, 68, 52, 73),
        _p("Zé Ivaldo",         DEF, 28, BR,           81, 70, 74, 32, 68, 82, 82, 78, 12),
        _p("Marlon",            DEF, 28, BR,           78, 72, 72, 30, 66, 80, 78, 72, 12),
        _p("Villalba",          DEF, 28, "Colombiano", 76, 72, 70, 30, 64, 76, 74, 64, 10),
        _p("William",           DEF, 29, BR,           74, 74, 70, 32, 64, 74, 72, 58, 10),
        _p("Kaiki Bruno",       DEF, 22, BR,           77, 82, 72, 38, 66, 72, 70, 56, 10),
        _p("Lucas Villalba",    DEF, 24, "Colombiano", 74, 76, 68, 30, 62, 72, 70, 58, 10),
        _p("Matheus Pereira",   MID, 28, BR,           86, 82, 86, 78, 84, 72, 64, 56, 10),
        _p("Lucas Silva",       MID, 31, BR,           79, 70, 76, 60, 78, 80, 74, 64, 10),
        _p("Walace",            MID, 29, BR,           81, 74, 76, 62, 76, 84, 76, 66, 10),
        _p("Matheus Henrique",  MID, 26, BR,           80, 76, 78, 64, 78, 76, 68, 60, 10),
        _p("Christian",         MID, 26, BR,           78, 76, 74, 62, 74, 74, 66, 58, 10),
        _p("Newton",            MID, 27, BR,           75, 72, 72, 56, 72, 76, 70, 60, 10),
        _p("Kaio Jorge",        ATK, 23, BR,           81, 80, 76, 78, 64, 74, 58, 70, 10),
        _p("Arthur Gomes",      ATK, 27, BR,           79, 82, 74, 74, 64, 70, 56, 62, 10),
        _p("Lautaro Díaz",      ATK, 29, "Argentino",  80, 78, 74, 76, 62, 76, 58, 68, 10),
        _p("Rafa Silva",        ATK, 31, BR,           78, 82, 74, 72, 64, 68, 54, 60, 10),
        _p("Gabriel Veron",     ATK, 22, BR,           75, 82, 72, 68, 62, 66, 52, 58, 10),
    ]

    # --- FORTALEZA ---
    fortaleza = Team(
        id=11, name="Fortaleza", short_name="FOR",
        city="Fortaleza", state="CE",
        stadium="Arena Castelão", division=2, prestige=77,
        coach=Coach("Juan Pablo Vojvoda", "Argentino", tactical=84, motivation=82, experience=78),
        primary_color="red", secondary_color="blue"
    )
    fortaleza.players = [
        _p("João Ricardo",      GK,  34, BR,           85, 52, 66, 26, 56, 74, 80, 58, 86),
        _p("Santos",            GK,  25, BR,           72, 52, 60, 22, 50, 66, 68, 52, 73),
        _p("Titi",              DEF, 31, BR,           83, 68, 74, 32, 68, 84, 84, 80, 12),
        _p("Brítez",            DEF, 30, "Paraguaio",  81, 72, 72, 30, 66, 82, 82, 74, 12),
        _p("Tinga",             DEF, 30, BR,           80, 80, 72, 38, 66, 76, 76, 66, 10),
        _p("Bruno Pacheco",     DEF, 29, BR,           79, 80, 72, 38, 66, 74, 72, 60, 10),
        _p("Mateusão",          DEF, 25, BR,           76, 72, 70, 30, 64, 76, 76, 68, 12),
        _p("Zé Welison",        MID, 28, BR,           78, 72, 74, 58, 74, 82, 76, 64, 10),
        _p("Caio Alexandre",    MID, 26, BR,           80, 76, 76, 62, 76, 78, 72, 62, 10),
        _p("Hércules",          MID, 24, BR,           79, 74, 74, 62, 74, 78, 70, 60, 10),
        _p("Pochettino",        MID, 27, "Uruguaio",   81, 78, 80, 68, 78, 72, 66, 58, 10),
        _p("Kervin Andrade",    MID, 23, "Venezuelano", 77, 76, 74, 62, 74, 72, 64, 56, 10),
        _p("Yago Pikachu",      ATK, 30, BR,           77, 84, 72, 68, 64, 68, 54, 58, 10),
        _p("Moisés",            ATK, 29, BR,           82, 84, 78, 74, 68, 72, 58, 62, 10),
        _p("Lucero",            ATK, 28, "Argentino",  84, 76, 78, 82, 64, 80, 64, 76, 10),
        _p("Renato Kayzer",     ATK, 28, BR,           80, 78, 74, 76, 62, 78, 58, 68, 10),
        _p("Breno Lopes",       ATK, 28, BR,           78, 82, 74, 72, 62, 68, 54, 60, 10),
        _p("Pedro Rocha",       ATK, 27, BR,           76, 80, 72, 70, 62, 68, 52, 60, 10),
    ]

    # --- RED BULL BRAGANTINO ---
    bragantino = Team(
        id=12, name="RB Bragantino", short_name="RBB",
        city="Bragança Paulista", state="SP",
        stadium="Nabi Abi Chedid", division=2, prestige=75,
        coach=Coach("Fernando Seabra", BR, tactical=77, motivation=76, experience=74),
        primary_color="red", secondary_color="white"
    )
    bragantino.players = [
        _p("Cleiton",           GK,  27, BR,           83, 54, 66, 26, 56, 74, 80, 58, 84),
        _p("Lucão",             GK,  23, BR,           70, 52, 58, 22, 50, 64, 66, 50, 71),
        _p("Luan Cândido",      DEF, 24, BR,           81, 82, 74, 40, 70, 74, 74, 62, 10),
        _p("Pedro Henrique",    DEF, 26, BR,           79, 70, 72, 30, 66, 80, 80, 74, 12),
        _p("Natan",             DEF, 24, BR,           79, 72, 72, 30, 66, 80, 78, 72, 12),
        _p("Juninho Capixaba",  DEF, 28, BR,           78, 82, 70, 38, 66, 72, 70, 58, 10),
        _p("Andrés Hurtado",    DEF, 25, "Colombiano", 76, 74, 70, 30, 64, 74, 72, 62, 10),
        _p("Lucas Evangelista", MID, 28, "Italo-Bras.", 81, 76, 80, 68, 78, 74, 68, 58, 10),
        _p("Eric Ramires",      MID, 27, BR,           80, 76, 78, 66, 76, 76, 70, 60, 10),
        _p("Raul",              MID, 27, BR,           79, 74, 76, 62, 76, 78, 72, 60, 10),
        _p("Jhon Jhon",         MID, 25, BR,           80, 82, 78, 68, 74, 72, 62, 58, 10),
        _p("Matheus Fernandes", MID, 27, BR,           77, 72, 74, 60, 74, 78, 70, 60, 10),
        _p("Hyoran",            MID, 30, BR,           76, 74, 72, 60, 72, 72, 64, 56, 10),
        _p("Thiago Borbas",     ATK, 24, "Uruguaio",   80, 78, 74, 76, 62, 76, 58, 68, 10),
        _p("Lincoln",           ATK, 24, BR,           75, 84, 74, 70, 62, 66, 50, 58, 10),
        _p("Helinho",           ATK, 27, BR,           77, 82, 74, 72, 62, 66, 52, 60, 10),
        _p("Vitinho",           ATK, 29, BR,           78, 84, 74, 72, 64, 68, 54, 58, 10),
        _p("Eduardo Sasha",     ATK, 32, BR,           76, 76, 70, 72, 60, 72, 56, 64, 10),
        _p("Guilherme Lopes",   ATK, 21, BR,           73, 80, 72, 66, 60, 64, 50, 56, 10),
    ]

    # =========================================================
    # DIVISÃO 3
    # =========================================================

    # --- ATHLETICO PARANAENSE ---
    athletico_pr = Team(
        id=13, name="Athletico Paranaense", short_name="CAP",
        city="Curitiba", state="PR",
        stadium="Ligga Arena", division=3, prestige=75,
        coach=Coach("Odair Hellmann", BR, tactical=78, motivation=76, experience=82),
        primary_color="red", secondary_color="black"
    )
    athletico_pr.players = [
        _p("Léo Linck",         GK,  22, BR,           79, 52, 62, 24, 52, 70, 76, 56, 80),
        _p("Mycael",            GK,  22, BR,           73, 52, 60, 22, 50, 66, 70, 52, 74),
        _p("Erick",             DEF, 27, BR,           79, 80, 72, 38, 66, 74, 72, 60, 10),
        _p("Kaique Rocha",      DEF, 22, BR,           78, 70, 72, 30, 64, 78, 78, 72, 12),
        _p("Matheus Felipe",    DEF, 23, BR,           77, 72, 72, 28, 64, 76, 76, 68, 12),
        _p("Lucas Fasson",      DEF, 25, BR,           74, 78, 68, 32, 62, 70, 68, 56, 10),
        _p("Leo Godoy",         DEF, 29, "Paraguaio",  75, 76, 70, 32, 64, 72, 70, 58, 10),
        _p("Esquivel",          DEF, 25, "Hondurenho", 76, 82, 70, 36, 64, 70, 68, 54, 10),
        _p("Fernandinho",       MID, 39, BR,           80, 66, 80, 62, 80, 76, 78, 64, 10),
        _p("Canobbio",          MID, 27, "Uruguaio",   79, 82, 78, 68, 72, 72, 62, 56, 10),
        _p("Erick Flores",      MID, 27, "Hondurenho", 77, 76, 74, 62, 72, 74, 66, 58, 10),
        _p("Christian",         MID, 25, "Argentino",  76, 72, 74, 60, 72, 76, 68, 60, 10),
        _p("Zapelli",           MID, 24, "Argentino",  75, 74, 74, 60, 72, 72, 64, 56, 10),
        _p("Terans",            ATK, 27, "Cubano",     80, 82, 78, 72, 70, 70, 56, 60, 10),
        _p("Pablo",             ATK, 35, BR,           79, 72, 72, 76, 60, 76, 58, 70, 10),
        _p("Mastriani",         ATK, 31, "Uruguaio",   75, 74, 68, 72, 58, 72, 60, 68, 10),
        _p("Rômulo",            ATK, 27, BR,           77, 80, 72, 70, 62, 68, 54, 60, 10),
        _p("Vitor Bueno",       ATK, 29, BR,           74, 76, 72, 66, 64, 64, 52, 56, 10),
        _p("Cuello",            ATK, 25, "Argentino",  76, 82, 74, 70, 64, 66, 52, 58, 10),
    ]

    # --- BAHIA ---
    bahia = Team(
        id=14, name="Bahia", short_name="BAH",
        city="Salvador", state="BA",
        stadium="Arena Fonte Nova", division=3, prestige=73,
        coach=Coach("Rogério Ceni", BR, tactical=80, motivation=80, experience=82),
        primary_color="blue", secondary_color="red"
    )
    bahia.players = [
        _p("Marcos Felipe",     GK,  27, BR,           81, 54, 64, 26, 54, 72, 78, 58, 82),
        _p("Adriel",            GK,  21, BR,           69, 52, 58, 20, 48, 62, 66, 50, 70),
        _p("Gabriel Xavier",    DEF, 25, BR,           79, 72, 72, 30, 66, 80, 78, 72, 12),
        _p("Rezende",           DEF, 28, BR,           78, 70, 72, 28, 64, 80, 78, 72, 12),
        _p("Romão",             DEF, 27, BR,           77, 72, 70, 28, 64, 76, 74, 68, 12),
        _p("Gilberto",          DEF, 33, BR,           76, 78, 68, 34, 62, 72, 70, 56, 10),
        _p("Acevedo",           DEF, 26, "Paraguaio",  77, 76, 72, 32, 64, 74, 74, 64, 10),
        _p("Everton Ribeiro",   MID, 35, BR,           83, 74, 84, 70, 82, 68, 64, 56, 10),
        _p("Cauly",             MID, 28, BR,           83, 78, 82, 72, 80, 70, 64, 58, 10),
        _p("Jean Lucas",        MID, 25, BR,           79, 74, 76, 62, 76, 78, 70, 62, 10),
        _p("Thaciano",          MID, 28, BR,           78, 76, 74, 64, 72, 72, 64, 58, 10),
        _p("Nico Acevedo",      MID, 24, "Venezuelano", 77, 72, 74, 60, 74, 74, 66, 58, 10),
        _p("Biel",              ATK, 24, BR,           76, 84, 74, 68, 62, 66, 52, 56, 10),
        _p("Everaldo",          ATK, 31, BR,           80, 80, 74, 74, 62, 72, 56, 64, 10),
        _p("Ademir",            ATK, 28, BR,           77, 84, 72, 70, 60, 68, 52, 58, 10),
        _p("Luciano Juba",      ATK, 26, BR,           78, 82, 74, 72, 62, 66, 52, 58, 10),
        _p("Willian José",      ATK, 33, BR,           79, 72, 70, 76, 60, 76, 58, 68, 10),
        _p("Caio Dantas",       ATK, 23, BR,           72, 78, 70, 66, 58, 64, 50, 58, 10),
    ]

    # --- VASCO DA GAMA ---
    vasco = Team(
        id=15, name="Vasco da Gama", short_name="VAS",
        city="Rio de Janeiro", state="RJ",
        stadium="São Januário", division=3, prestige=75,
        coach=Coach("Fábio Carille", BR, tactical=76, motivation=75, experience=80),
        primary_color="white", secondary_color="black"
    )
    vasco.players = [
        _p("Léo Jardim",        GK,  30, BR,           81, 52, 64, 24, 54, 72, 78, 58, 82),
        _p("Daniel Fuzato",     GK,  26, BR,           77, 52, 62, 22, 52, 68, 74, 56, 78),
        _p("João Victor",       DEF, 27, BR,           78, 72, 72, 30, 66, 78, 78, 72, 12),
        _p("Léo",               DEF, 30, BR,           78, 76, 70, 36, 64, 74, 72, 62, 10),
        _p("Maicon",            DEF, 35, BR,           76, 70, 72, 28, 66, 78, 76, 70, 12),
        _p("Puma Rodríguez",    DEF, 28, "Uruguaio",   80, 84, 72, 38, 66, 72, 70, 58, 10),
        _p("Lucas Piton",       DEF, 25, BR,           79, 84, 72, 38, 68, 72, 70, 58, 10),
        _p("Paulo Henrique",    DEF, 28, BR,           77, 74, 70, 30, 64, 74, 72, 62, 10),
        _p("Payet",             MID, 38, "Francês",    81, 66, 88, 68, 88, 62, 62, 52, 10),
        _p("Sforza",            MID, 23, "Suíço",      78, 74, 78, 62, 76, 74, 68, 58, 10),
        _p("Hugo Moura",        MID, 25, BR,           75, 72, 72, 58, 72, 76, 68, 60, 10),
        _p("De Lucca",          MID, 27, BR,           74, 72, 72, 56, 72, 72, 66, 58, 10),
        _p("Mateus Carvalho",   MID, 26, BR,           76, 74, 74, 60, 74, 74, 66, 58, 10),
        _p("Vegetti",           ATK, 36, "Argentino",  84, 70, 74, 82, 62, 80, 66, 78, 10),
        _p("Emerson Rodríguez", ATK, 23, "Colombiano", 78, 82, 76, 72, 64, 68, 54, 58, 10),
        _p("Jean David",        ATK, 30, "Canadense",  77, 80, 74, 72, 64, 68, 54, 60, 10),
        _p("Adson",             ATK, 24, BR,           75, 82, 72, 68, 62, 64, 50, 56, 10),
        _p("Rayan",             ATK, 18, BR,           74, 82, 72, 66, 60, 64, 50, 56, 10),
        _p("Rossi",             ATK, 22, "Argentino",  73, 78, 70, 66, 60, 64, 50, 58, 10),
    ]

    # --- JUVENTUDE ---
    juventude = Team(
        id=16, name="Juventude", short_name="JUV",
        city="Caxias do Sul", state="RS",
        stadium="Alfredo Jaconi", division=3, prestige=62,
        coach=Coach("Maurício Barbieri", BR, tactical=72, motivation=73, experience=74),
        primary_color="green", secondary_color="white"
    )
    juventude.players = [
        _p("Gabriel",           GK,  29, BR,           79, 52, 62, 24, 52, 70, 76, 56, 80),
        _p("César",             GK,  33, BR,           71, 50, 58, 20, 50, 68, 68, 52, 72),
        _p("Rodrigo Sam",       DEF, 28, BR,           77, 68, 72, 28, 64, 78, 78, 72, 12),
        _p("Danilo Boza",       DEF, 27, BR,           76, 72, 70, 28, 62, 76, 74, 66, 12),
        _p("Diego Nascimento",  DEF, 28, BR,           75, 70, 68, 26, 62, 74, 72, 64, 12),
        _p("William",           DEF, 31, BR,           74, 78, 68, 32, 62, 70, 68, 56, 10),
        _p("Ewerton",           DEF, 26, BR,           75, 76, 68, 30, 62, 72, 70, 58, 10),
        _p("Jean Irmer",        MID, 30, BR,           74, 72, 72, 56, 72, 72, 66, 58, 10),
        _p("Caíque",            MID, 27, BR,           74, 72, 70, 56, 70, 72, 65, 58, 10),
        _p("Bruninho",          MID, 23, BR,           75, 74, 72, 58, 72, 72, 64, 56, 10),
        _p("Mandaca",           MID, 28, "Guineense",  76, 76, 74, 60, 72, 74, 66, 58, 10),
        _p("Jadson",            MID, 36, BR,           73, 62, 76, 60, 76, 64, 60, 52, 10),
        _p("Gilberto",          ATK, 31, BR,           78, 80, 72, 72, 62, 68, 54, 62, 10),
        _p("Erick Farias",      ATK, 27, BR,           77, 80, 72, 70, 60, 66, 52, 58, 10),
        _p("Lucas Barbosa",     ATK, 24, BR,           76, 80, 70, 68, 60, 64, 50, 56, 10),
        _p("Edinho",            ATK, 29, BR,           74, 76, 68, 68, 58, 66, 52, 58, 10),
        _p("Marcelinho",        ATK, 33, BR,           75, 72, 72, 68, 62, 64, 52, 58, 10),
        _p("Dentinho",          ATK, 36, BR,           73, 74, 68, 66, 58, 62, 50, 56, 10),
    ]

    # --- CUIABÁ ---
    cuiaba = Team(
        id=17, name="Cuiabá", short_name="CUI",
        city="Cuiabá", state="MT",
        stadium="Arena Pantanal", division=3, prestige=60,
        coach=Coach("Eduardo Barros", BR, tactical=72, motivation=71, experience=68),
        primary_color="yellow", secondary_color="green"
    )
    cuiaba.players = [
        _p("Walter",            GK,  37, BR,           77, 48, 60, 22, 50, 68, 74, 54, 78),
        _p("João Carlos",       GK,  23, BR,           69, 50, 56, 20, 48, 62, 66, 50, 70),
        _p("Marllon",           DEF, 29, BR,           76, 68, 70, 26, 62, 76, 74, 68, 12),
        _p("Alan Ross",         DEF, 26, BR,           74, 70, 68, 24, 60, 72, 70, 62, 12),
        _p("Beltrame",          DEF, 28, BR,           75, 72, 68, 26, 62, 72, 70, 60, 10),
        _p("São Júnior",        DEF, 30, BR,           73, 74, 66, 26, 60, 70, 68, 56, 10),
        _p("Rikelmy",           DEF, 22, BR,           72, 72, 66, 24, 58, 68, 66, 54, 10),
        _p("Filipe Augusto",    MID, 31, BR,           79, 70, 76, 64, 76, 72, 66, 58, 10),
        _p("Lucas Mineiro",     MID, 27, BR,           77, 72, 74, 58, 72, 74, 68, 60, 10),
        _p("Raylan",            MID, 23, BR,           75, 76, 72, 58, 70, 70, 62, 54, 10),
        _p("Max",               MID, 28, BR,           73, 70, 70, 54, 68, 72, 64, 56, 10),
        _p("Denilson",          MID, 27, BR,           72, 70, 68, 52, 66, 70, 62, 54, 10),
        _p("Jonathan Cafú",     ATK, 30, BR,           75, 80, 70, 68, 60, 66, 52, 56, 10),
        _p("Isidro Pitta",      ATK, 26, "Paraguaio",  76, 74, 68, 72, 56, 72, 58, 66, 10),
        _p("Elton",             ATK, 30, BR,           75, 72, 68, 70, 56, 70, 56, 62, 10),
        _p("Clayson",           ATK, 30, BR,           76, 80, 70, 70, 60, 64, 50, 54, 10),
        _p("André Luís",        ATK, 23, BR,           73, 78, 68, 66, 56, 64, 48, 54, 10),
        _p("Deyverson",         ATK, 33, BR,           79, 76, 70, 72, 58, 76, 58, 68, 10),
    ]

    # --- ATLÉTICO GOIANIENSE ---
    atletico_go = Team(
        id=18, name="Atlético Goianiense", short_name="ACG",
        city="Goiânia", state="GO",
        stadium="Antônio Accioly", division=3, prestige=60,
        coach=Coach("Eduardo Souza", BR, tactical=70, motivation=72, experience=70),
        primary_color="red", secondary_color="black"
    )
    atletico_go.players = [
        _p("Ronaldo",           GK,  30, BR,           76, 50, 60, 22, 50, 68, 74, 54, 77),
        _p("Luan",              GK,  22, BR,           67, 50, 56, 20, 46, 60, 64, 48, 68),
        _p("Edson Fernando",    DEF, 28, BR,           74, 68, 68, 24, 60, 72, 72, 64, 12),
        _p("Alix Vinicius",     DEF, 27, BR,           73, 70, 66, 24, 58, 70, 70, 60, 12),
        _p("Adriano Martins",   DEF, 29, BR,           72, 68, 66, 22, 58, 70, 68, 58, 12),
        _p("Arthur",            DEF, 26, BR,           74, 74, 66, 26, 60, 70, 68, 56, 10),
        _p("Guilherme Romão",   DEF, 24, BR,           72, 72, 64, 24, 58, 68, 66, 54, 10),
        _p("Rhaldney",          MID, 26, BR,           75, 74, 72, 58, 70, 72, 66, 56, 10),
        _p("Baralhas",          MID, 29, BR,           77, 72, 74, 58, 72, 74, 68, 58, 10),
        _p("Shaylon",           MID, 30, BR,           76, 74, 72, 60, 72, 70, 64, 56, 10),
        _p("Jorginho",          MID, 30, BR,           74, 70, 72, 56, 72, 70, 66, 56, 10),
        _p("Léo Pereira",       MID, 29, BR,           74, 72, 70, 56, 70, 70, 64, 56, 10),
        _p("Luiz Fernando",     ATK, 29, BR,           77, 80, 72, 70, 60, 66, 52, 56, 10),
        _p("Derek",             ATK, 25, BR,           75, 78, 70, 68, 56, 64, 50, 56, 10),
        _p("Hyuri",             ATK, 28, BR,           73, 76, 68, 64, 54, 62, 48, 54, 10),
        _p("Emiliano Rodríguez", ATK, 28, "Uruguaio",  74, 76, 70, 68, 58, 64, 50, 58, 10),
        _p("Alejo Cruz",        ATK, 24, "Argentino",  75, 80, 72, 68, 58, 62, 48, 54, 10),
        _p("Janderson",         ATK, 28, BR,           72, 76, 68, 64, 54, 62, 48, 54, 10),
    ]

    # =========================================================
    # DIVISÃO 4
    # =========================================================

    # --- VITÓRIA ---
    vitoria = Team(
        id=19, name="Vitória", short_name="VIT",
        city="Salvador", state="BA",
        stadium="Barradão", division=4, prestige=63,
        coach=Coach("Thiago Carpini", BR, tactical=71, motivation=72, experience=62),
        primary_color="red", secondary_color="black"
    )
    vitoria.players = [
        _p("Lucas Arcanjo",     GK,  24, BR,           78, 52, 62, 22, 52, 68, 74, 56, 79),
        _p("Dalton",            GK,  34, BR,           72, 48, 58, 20, 48, 66, 70, 52, 73),
        _p("Camutanga",         DEF, 30, BR,           75, 68, 70, 26, 62, 74, 72, 66, 12),
        _p("Wagner Leonardo",   DEF, 27, BR,           77, 70, 70, 26, 62, 76, 76, 70, 12),
        _p("Marcos Victor",     DEF, 26, BR,           74, 70, 68, 24, 60, 72, 70, 62, 12),
        _p("Zeca",              DEF, 30, BR,           74, 76, 68, 30, 62, 70, 68, 56, 10),
        _p("Willian Oliveira",  DEF, 27, BR,           73, 74, 66, 26, 60, 68, 66, 54, 10),
        _p("Léo Naldi",         MID, 25, BR,           75, 72, 72, 56, 70, 72, 66, 56, 10),
        _p("Rodrigo Andrade",   MID, 26, BR,           76, 74, 72, 58, 70, 72, 66, 56, 10),
        _p("Luan",              MID, 31, BR,           74, 70, 70, 54, 68, 70, 64, 54, 10),
        _p("Dudu",              MID, 28, BR,           74, 72, 68, 54, 68, 70, 62, 54, 10),
        _p("Matheuzinho",       MID, 23, BR,           72, 70, 68, 52, 66, 68, 60, 52, 10),
        _p("Alerrandro",        ATK, 25, BR,           79, 80, 72, 74, 60, 72, 56, 64, 10),
        _p("Osvaldo",           ATK, 36, BR,           77, 76, 70, 72, 58, 68, 52, 60, 10),
        _p("Everaldo",          ATK, 33, BR,           75, 74, 68, 70, 58, 68, 52, 60, 10),
        _p("Janderson",         ATK, 27, BR,           73, 74, 66, 64, 54, 62, 48, 54, 10),
        _p("Oscar",             ATK, 29, BR,           73, 72, 66, 64, 54, 64, 48, 56, 10),
        _p("Jean Mota",         MID, 30, BR,           74, 70, 70, 56, 70, 70, 64, 56, 10),
    ]

    # --- CRICIÚMA ---
    criciuma = Team(
        id=20, name="Criciúma", short_name="CRI",
        city="Criciúma", state="SC",
        stadium="Heriberto Hülse", division=4, prestige=58,
        coach=Coach("Eduardo Baptista", BR, tactical=72, motivation=73, experience=80),
        primary_color="yellow", secondary_color="black"
    )
    criciuma.players = [
        _p("Gustavo",           GK,  26, BR,           76, 50, 60, 22, 50, 66, 72, 54, 77),
        _p("Alisson",           GK,  31, BR,           69, 48, 56, 20, 48, 62, 66, 50, 70),
        _p("Claudinho",         DEF, 27, BR,           73, 68, 68, 24, 60, 70, 70, 62, 12),
        _p("Jonathan",          DEF, 28, BR,           73, 70, 66, 22, 58, 70, 68, 60, 12),
        _p("Rodrigo",           DEF, 30, BR,           72, 68, 66, 22, 58, 68, 68, 58, 12),
        _p("Tobias Figueiredo", DEF, 30, "Português",  73, 66, 68, 22, 60, 72, 70, 64, 12),
        _p("Victor Luís",       DEF, 30, BR,           73, 76, 66, 28, 60, 68, 66, 54, 10),
        _p("Barreto",           MID, 32, BR,           73, 68, 70, 54, 68, 68, 62, 54, 10),
        _p("Fellipe Mateus",    MID, 27, BR,           74, 72, 70, 56, 68, 70, 62, 54, 10),
        _p("Higor Meritão",     MID, 26, BR,           75, 74, 72, 58, 70, 70, 64, 56, 10),
        _p("Denner",            MID, 26, BR,           73, 70, 68, 54, 66, 68, 60, 52, 10),
        _p("Marquinhos Gabriel", MID, 33, BR,          74, 68, 72, 56, 70, 64, 60, 52, 10),
        _p("Bolasie",           ATK, 35, "Congolês",   76, 76, 72, 68, 58, 68, 54, 60, 10),
        _p("Arthur Caike",      ATK, 28, BR,           76, 80, 72, 70, 58, 64, 50, 56, 10),
        _p("Allano",            ATK, 28, BR,           75, 76, 68, 68, 56, 64, 50, 56, 10),
        _p("Ronald",            ATK, 24, BR,           74, 78, 68, 66, 56, 64, 48, 54, 10),
        _p("Jhonata Robert",    ATK, 28, BR,           73, 78, 66, 64, 54, 62, 48, 52, 10),
        _p("Matheusinho",       ATK, 27, BR,           73, 76, 66, 64, 54, 60, 48, 52, 10),
    ]

    # --- SANTOS (SÉRIE B) ---
    santos = Team(
        id=21, name="Santos", short_name="SAN",
        city="Santos", state="SP",
        stadium="Vila Belmiro", division=4, prestige=72,
        coach=Coach("Cléber Xavier", BR, tactical=74, motivation=74, experience=72),
        primary_color="white", secondary_color="black"
    )
    santos.players = [
        _p("Gabriel Brazão",    GK,  24, BR,           79, 52, 62, 24, 52, 70, 76, 56, 80),
        _p("Renan",             GK,  25, BR,           71, 50, 58, 22, 50, 64, 68, 52, 72),
        _p("Joaquim",           DEF, 25, BR,           77, 70, 72, 28, 64, 76, 76, 70, 12),
        _p("Gil",               DEF, 36, BR,           76, 64, 70, 26, 64, 78, 76, 72, 12),
        _p("Vinícius Balieiro", DEF, 24, BR,           74, 70, 68, 24, 60, 72, 70, 62, 12),
        _p("JP",                DEF, 27, BR,           74, 76, 66, 28, 60, 70, 68, 56, 10),
        _p("Escobar",           DEF, 29, "Colombiano", 74, 72, 68, 26, 60, 70, 68, 58, 10),
        _p("Diego Pituca",      MID, 30, BR,           76, 72, 72, 56, 72, 74, 68, 58, 10),
        _p("Gabriel Carabajal", MID, 30, "Argentino",  75, 70, 74, 56, 72, 70, 64, 54, 10),
        _p("Sandry",            MID, 23, BR,           75, 74, 72, 58, 70, 70, 64, 54, 10),
        _p("Jean Mota",         MID, 30, BR,           74, 68, 70, 54, 70, 68, 62, 54, 10),
        _p("Otero",             MID, 33, "Venezuelano", 76, 72, 74, 62, 70, 66, 60, 52, 10),
        _p("Guilherme",         ATK, 27, BR,           77, 80, 72, 72, 60, 68, 52, 60, 10),
        _p("Julio Furch",       ATK, 33, "Argentino",  76, 68, 68, 72, 56, 72, 58, 66, 10),
        _p("Willian Bigode",    ATK, 35, BR,           74, 76, 70, 68, 56, 64, 50, 56, 10),
        _p("Marcos Leonardo",   ATK, 21, BR,           78, 80, 72, 72, 60, 68, 52, 62, 10),
        _p("Ângelo",            ATK, 19, BR,           74, 86, 72, 66, 58, 60, 48, 52, 10),
        _p("Lucas Barbosa",     ATK, 25, BR,           73, 78, 68, 66, 56, 62, 48, 52, 10),
    ]

    # --- SPORT RECIFE (SÉRIE B) ---
    sport = Team(
        id=22, name="Sport Recife", short_name="SPR",
        city="Recife", state="PE",
        stadium="Ilha do Retiro", division=4, prestige=60,
        coach=Coach("Márcio Goiano", BR, tactical=68, motivation=72, experience=76),
        primary_color="red", secondary_color="black"
    )
    sport.players = [
        _p("Rafael Santos",     GK,  27, BR,           75, 50, 60, 22, 50, 66, 72, 54, 76),
        _p("Caíque França",     GK,  25, BR,           70, 50, 56, 20, 48, 62, 66, 50, 71),
        _p("Eduardo",           DEF, 28, BR,           73, 68, 66, 22, 58, 70, 68, 60, 12),
        _p("Tuti",              DEF, 30, BR,           74, 68, 68, 22, 60, 72, 70, 62, 12),
        _p("Rafael Thyere",     DEF, 30, BR,           73, 68, 66, 22, 58, 70, 68, 60, 12),
        _p("Felipinho",         DEF, 24, BR,           72, 74, 64, 24, 58, 66, 64, 52, 10),
        _p("Yan",               DEF, 22, BR,           71, 72, 62, 22, 56, 64, 62, 50, 10),
        _p("Fábio Matheus",     MID, 26, BR,           73, 70, 68, 52, 66, 68, 62, 52, 10),
        _p("Fabinho",           MID, 29, BR,           74, 70, 70, 54, 68, 70, 64, 54, 10),
        _p("Lucas Lima",        MID, 33, BR,           76, 68, 76, 58, 74, 62, 58, 50, 10),
        _p("Julián Fernández",  MID, 28, "Argentino",  74, 70, 72, 56, 70, 70, 64, 54, 10),
        _p("Biel",              MID, 22, BR,           72, 72, 68, 54, 66, 66, 58, 50, 10),
        _p("Chrystian Barletta", ATK, 25, BR,          76, 82, 72, 68, 58, 62, 48, 54, 10),
        _p("Zé Roberto",        ATK, 29, BR,           75, 76, 68, 68, 56, 66, 50, 56, 10),
        _p("Henrique Lordelo",  ATK, 24, BR,           74, 76, 68, 66, 54, 62, 48, 54, 10),
        _p("Rafael",            ATK, 30, BR,           73, 74, 66, 64, 54, 62, 48, 52, 10),
        _p("Luciano Juba",      ATK, 26, BR,           73, 76, 66, 62, 52, 60, 46, 50, 10),
    ]

    # --- CEARÁ (SÉRIE B) ---
    ceara = Team(
        id=23, name="Ceará", short_name="CEA",
        city="Fortaleza", state="CE",
        stadium="Arena Castelão", division=4, prestige=62,
        coach=Coach("Mozart", BR, tactical=72, motivation=72, experience=72),
        primary_color="black", secondary_color="white"
    )
    ceara.players = [
        _p("Richard",           GK,  32, BR,           76, 50, 60, 22, 50, 66, 72, 54, 77),
        _p("Bruno Ferreira",    GK,  23, BR,           68, 48, 54, 20, 46, 60, 64, 48, 69),
        _p("David Ricardo",     DEF, 29, BR,           73, 68, 66, 22, 58, 70, 68, 60, 12),
        _p("João Pedro",        DEF, 28, BR,           74, 70, 68, 24, 60, 72, 70, 62, 12),
        _p("Matheus Felipe",    DEF, 26, BR,           72, 70, 66, 22, 58, 68, 68, 58, 12),
        _p("Warley",            DEF, 27, BR,           72, 74, 64, 24, 58, 66, 64, 52, 10),
        _p("Eric Melo",         DEF, 25, BR,           71, 72, 62, 22, 56, 64, 62, 50, 10),
        _p("Richardson",        MID, 28, BR,           75, 70, 72, 54, 70, 72, 66, 54, 10),
        _p("Erick",             MID, 26, BR,           74, 72, 68, 52, 66, 68, 62, 52, 10),
        _p("Lucas Mugni",       MID, 30, "Argentino",  76, 70, 74, 58, 72, 66, 60, 50, 10),
        _p("De Lucca",          MID, 28, BR,           74, 70, 70, 54, 68, 68, 62, 52, 10),
        _p("Fernando Sobral",   MID, 28, BR,           74, 70, 70, 54, 68, 68, 62, 52, 10),
        _p("Saulo Mineiro",     ATK, 27, BR,           77, 80, 72, 70, 56, 66, 50, 58, 10),
        _p("Facundo Castro",    ATK, 26, "Uruguaio",   75, 76, 70, 68, 58, 62, 48, 54, 10),
        _p("Barceló",           ATK, 28, "Uruguaio",   75, 74, 68, 68, 56, 64, 50, 56, 10),
        _p("Cléber",            ATK, 31, BR,           73, 74, 66, 66, 54, 64, 48, 54, 10),
        _p("Depietri",          ATK, 27, "Argentino",  72, 72, 66, 64, 54, 62, 48, 52, 10),
    ]

    # --- MIRASSOL (SÉRIE B / NOVO ACESSO) ---
    mirassol = Team(
        id=24, name="Mirassol", short_name="MIR",
        city="Mirassol", state="SP",
        stadium="Maião", division=4, prestige=52,
        coach=Coach("Mozart Santos", BR, tactical=68, motivation=72, experience=66),
        primary_color="yellow", secondary_color="blue"
    )
    mirassol.players = [
        _p("Alex Muralha",      GK,  36, BR,           77, 48, 60, 22, 50, 64, 72, 54, 78),
        _p("Muralha Jr.",       GK,  21, BR,           66, 48, 52, 18, 44, 58, 62, 46, 67),
        _p("Luiz Otávio",       DEF, 31, BR,           74, 66, 68, 24, 60, 72, 72, 64, 12),
        _p("Cristovão",         DEF, 29, BR,           72, 66, 66, 22, 58, 68, 68, 58, 12),
        _p("Escura",            DEF, 28, BR,           71, 66, 62, 20, 56, 66, 64, 54, 12),
        _p("Santana",           DEF, 27, BR,           71, 70, 62, 22, 56, 64, 62, 50, 10),
        _p("Thalisson",         DEF, 23, BR,           70, 70, 60, 20, 54, 62, 60, 48, 10),
        _p("Neto Moura",        MID, 27, BR,           75, 70, 72, 54, 70, 72, 64, 54, 10),
        _p("Chrigor",           MID, 26, BR,           74, 68, 68, 50, 66, 68, 60, 52, 10),
        _p("Danielzinho",       MID, 24, BR,           73, 70, 68, 52, 66, 66, 60, 50, 10),
        _p("Pedro Lucas",       MID, 23, BR,           72, 70, 66, 50, 64, 64, 58, 48, 10),
        _p("Iury",              MID, 26, BR,           72, 68, 66, 50, 64, 64, 58, 48, 10),
        _p("Fabrício Daniel",   ATK, 28, BR,           76, 78, 68, 70, 56, 64, 50, 56, 10),
        _p("Giovanny",          ATK, 22, BR,           74, 78, 68, 66, 54, 60, 46, 52, 10),
        _p("Alex Silva",        ATK, 27, BR,           73, 74, 66, 64, 52, 62, 46, 52, 10),
        _p("Fernandinho",       ATK, 30, BR,           72, 72, 64, 62, 50, 62, 46, 52, 10),
        _p("Nicolas",           ATK, 22, BR,           71, 74, 64, 60, 50, 58, 44, 48, 10),
    ]

    coritiba = _named_team(
        25, "Coritiba", "CFC", "Curitiba", "PR", "Couto Pereira", 4, 61,
        "Fernando Seabra", "green", "white", 71,
        ["Pedro Morisco", "Pedro Rangel", "Gabriel Leite"],
        ["Tiago Coser", "Maicon", "Jacy", "João Almeida", "Felipe Guimarães", "Guilherme Aquino", "Bruno Melo", "Rodrigo Moledo"],
        [("Sebastián Gómez", "Colombiano"), "Willian Oliveira", "Jean Gabriel", "Geovane", "Josué", ("Carlos de Pena", "Uruguaio")],
        ["Clayson", "Lucas Ronier", "Dellatorre", "Nicolas Careca", "Gustavo Coutinho", "Iury Castilho", ("Joaquín Lavega", "Uruguaio"), "Pedro Rocha"]
    )
    goias = _named_team(
        26, "Goiás", "GOI", "Goiânia", "GO", "Serrinha", 4, 60,
        "Daniel Paulista", "green", "white", 70,
        ["Tadeu", "Thiago Rodrigues", "Marcão"],
        ["Ezequiel", "Lucas Ribeiro", "Luiz Felipe", "Titi", "Anthony", "Nicolas", "Rodrigo Soares", "Djalma Silva"],
        ["Gegê", "Juninho", ("Brayann", "Colombiano"), "Filipe Machado", "Lourenço", "Lucas Lima", "Jean Carlos"],
        ["Wellington Rato", "Bruno Sávio", ("Esli García", "Venezuelano"), "Pedrinho", "Anselmo Ramon", "Jajá", "Cadu"]
    )
    america_mg = _named_team(
        27, "América Mineiro", "AMG", "Belo Horizonte", "MG", "Independência", 4, 60,
        "Roger Silva", "green", "black", 70,
        ["Matheus Mendes", "Jori", "Dalberson"],
        ["Marlon", "Ricardo Silva", "Júlio", "Maguinho", "Nicolas", "Lucão", "Paulinho", "Miqueias"],
        ["Alê", "Moisés", "Fabinho Santos", "Miguelito", "Benítez", "Cauan Barros", "Jhosefer"],
        ["Fabinho", "Adyson", "Willian Bigode", "Guilherme Pato", "Renato Marques", "Brenner", "Stênio"]
    )
    avai = _named_team(
        28, "Avaí", "AVA", "Florianópolis", "SC", "Ressacada", 4, 58,
        "Cauan de Almeida", "blue", "white", 69,
        ["Igor Bohn", "Otávio Passos", "Léo Aragão"],
        ["Douglas Teixeira", "Quaresma", "Allyson", "Wallison", "Wesley Gasolina", "Guilherme Aquino", "Gabriel Simples", ("Nicolás Cabral", "Uruguaio")],
        ["Jean Lucas", "Daniel Penha", "Zé Ricardo", "Romildo Del Piage", "Wenderson", "Hyan", "Luiz Henrique", "Cristiano"],
        ["Rafael Bilu", "Felipe Avenatti", "Sorriso", "Gaspar", "Maurício Garcez", "Thayllon", "Igor Rosa"]
    )
    vila_nova = _named_team(
        29, "Vila Nova", "VIL", "Goiânia", "GO", "OBA", 4, 57,
        "Guto Ferreira", "red", "white", 69,
        ["Helton Leite", "Dalberson", "Airton"],
        ["Caio Marcelo", "Anderson Jesus", "Elias", "Weverton", "Tiago Pagnussat", "Higor", "Hayner", "Willian Formiga"],
        ["Dudu", "Nathan Camargo", "Dodô", "João Vieira", "Marco Antonio", "Willian Maranhão", "Marquinhos Gabriel"],
        ["Ruan Ribeiro", "Dellatorre", "Andre Luis", "Bruno Xavier", "Rafa Silva", "Emerson Urso", "Janderson"]
    )
    paysandu = _named_team(
        30, "Paysandu", "PAY", "Belém", "PA", "Curuzu", 4, 56,
        "Luizinho Lopes", "blue", "white", 68,
        ["Gabriel Mesquita", "Jean Drosny", "Matheus Nogueira"],
        ["Marcão", ("Yeferson Quintana", "Colombiano"), "Edílson", "Luccão", "Bruno Bispo", "PK", "Reverson", "Bryan Borges"],
        ["Leandro Vilela", "Marlon", "Matheus Vargas", "Cavan", "Ramon Martinez", "Giovanni", "Robinho"],
        ["Nicolas", "Marlon Douglas", "Benitez", "Edinho", "Ciel", "Kevin", "Eliel"]
    )
    crb = _named_team(
        31, "CRB", "CRB", "Maceió", "AL", "Rei Pelé", 4, 56,
        "Eduardo Barroca", "red", "white", 68,
        ["Matheus Albino", "Vitor Caetano", "Pablo"],
        ["Hereda", "Henri", "Segovia", "Fábio Alemão", "Lucas Lovat", "Weverton", "Ryan", "Hayner"],
        ["Danielzinho", "Higor Meritão", "Geovane", "Lucas Kallyel", "Gegê", "Mikael", "Douglas Baggio"],
        ["Anselmo Ramon", "Léo Pereira", "William Pottker", "Dadá Belmonte", "João Neto", "Thiaguinho", "Rafinha"]
    )
    novorizontino = _named_team(
        32, "Novorizontino", "NOV", "Novo Horizonte", "SP", "Jorge Ismael de Biasi", 4, 55,
        "Enderson Moreira", "yellow", "black", 68,
        ["Jordi", "Airton", "César Augusto"],
        ["Patrick", "Dantas", "Rômulo", "César Martins", "Mayk", "Rafael Donato", "Raí Ramos", ("Luis Oyama", BR)],
        ["Fábio Matheus", "Jean Irmer", "Marlon", "Matheus Frizzo", "Lucca", "Robson", "Waguininho"],
        ["Caio Dantas", "Nicolas Careca", "Léo Tocantins", "Bruno José", "Everaldo", "Neto Pessoa", "Jenison"]
    )

    # Reorganiza as divisões com 8 clubes cada
    internacional.division = 1
    gremio.division = 1
    sao_paulo.division = 2
    cruzeiro.division = 2
    fortaleza.division = 2
    bragantino.division = 2
    athletico_pr.division = 2
    bahia.division = 2
    vasco.division = 2
    santos.division = 2
    juventude.division = 3
    cuiaba.division = 3
    atletico_go.division = 3
    vitoria.division = 3
    criciuma.division = 3
    sport.division = 3
    ceara.division = 3
    mirassol.division = 3

    teams = [
        # Divisão 1
        flamengo, palmeiras, atletico_mg, corinthians, fluminense, botafogo, internacional, gremio,
        # Divisão 2
        sao_paulo, cruzeiro, fortaleza, bragantino, athletico_pr, bahia, vasco, santos,
        # Divisão 3
        juventude, cuiaba, atletico_go, vitoria, criciuma, sport, ceara, mirassol,
        # Divisão 4
        coritiba, goias, america_mg, avai, vila_nova, paysandu, crb, novorizontino,
    ]
    return teams


def _estimate_base_ovr(team: Team) -> int:
    top = sorted((float(p.overall) for p in team.players), reverse=True)[:11]
    if not top:
        return 70
    est = int(round(sum(top) / len(top))) - 2
    return max(62, min(88, est))


def apply_snapshot_2026(teams):
    """Atualiza treinadores e elencos (snapshot 2026) jogador a jogador."""
    roster_2026 = {
        1: {
            "gk": ["Rossi", "Matheus Cunha", "Dyogo Alves"],
            "def": ["Wesley", "Guillermo Varela", "Léo Pereira", "Léo Ortiz", "Danilo", "Alex Sandro", "Ayrton Lucas"],
            "mid": ["Erick Pulgar", "Allan", ("Nicolás De La Cruz", "Uruguaio"), ("Giorgian De Arrascaeta", "Uruguaio"), "Gerson", "Everton Araújo", ("Carlos Alcaraz", "Argentino")],
            "atk": ["Pedro", "Bruno Henrique", "Michael", "Luiz Araújo", "Everton Cebolinha", ("Gonzalo Plata", "Equatoriano"), "Juninho", "Matheus Gonçalves"],
        },
        2: {
            "gk": ["Weverton", "Marcelo Lomba", "Mateus Oliveira"],
            "def": [("Agustín Giay", "Argentino"), "Mayke", "Marcos Rocha", ("Gustavo Gómez", "Paraguaio"), "Murilo", "Naves", ("Joaquín Piquerez", "Uruguaio")],
            "mid": [("Aníbal Moreno", "Argentino"), ("Richard Ríos", "Colombiano"), ("Emiliano Martínez", "Uruguaio"), "Raphael Veiga", "Maurício", "Felipe Anderson", "Fabinho"],
            "atk": ["Estêvão", ("Facundo Torres", "Uruguaio"), "Paulinho", ("Flaco López", "Argentino"), "Vitor Roque", "Bruno Rodrigues", "Luighi", "Rony"],
        },
        3: {
            "gk": ["Everson", "Gabriel Delfim", "Matheus Mendes"],
            "def": ["Saravia", "Lyanco", "Bruno Fuchs", "Igor Rabello", ("Júnior Alonso", "Paraguaio"), "Guilherme Arana", "Rubens"],
            "mid": [("Fausto Vera", "Argentino"), ("Alan Franco", "Equatoriano"), "Otávio", "Igor Gomes", "Gustavo Scarpa", "Bernard", "Patrick"],
            "atk": ["Hulk", "Deyverson", ("Tomás Cuello", "Argentino"), "Cadu", ("Eduardo Vargas", "Chileno"), ("Cristian Pavón", "Argentino"), "Rony", "Alisson"],
        },
        4: {
            "gk": ["Hugo Souza", "Matheus Donelli", "Felipe Longo"],
            "def": ["Matheuzinho", "Léo Maná", "Félix Torres", "Cacá", "Gustavo Henrique", "Hugo", "Bidu"],
            "mid": ["Raniele", "Breno Bidon", "Maycon", "Alex Santana", "Charles", ("Rodrigo Garro", "Argentino"), ("André Carrillo", "Peruano")],
            "atk": ["Yuri Alberto", ("Memphis Depay", "Holandês"), "Ángel Romero", "Talles Magno", "Pedro Raul", "Giovane", "Wesley", "Kayke"],
        },
        5: {
            "gk": ["Fábio", "Vitor Eudes", "Pedro Rangel"],
            "def": ["Samuel Xavier", "Guga", ("Thiago Silva", BR), "Thiago Santos", "Manoel", "Renê", ("Fretes", "Argentino")],
            "mid": ["Martinelli", "Otávio", "Nonato", "Ganso", "Lima", ("Jhon Arias", "Colombiano"), ("Kevin Serna", "Colombiano")],
            "atk": [("Germán Cano", "Argentino"), "Keno", "Everaldo", ("Agustín Canobbio", "Uruguaio"), "Lelê", "Isaac", "Marquinhos", "Riquelme"],
        },
        6: {
            "gk": ["John", "Raul", "Léo Linck"],
            "def": ["Vitinho", ("Mateo Ponte", "Uruguaio"), ("Alexander Barboza", "Argentino"), "Bastos", "David Ricardo", "Alex Telles", "Cuiabano"],
            "mid": ["Gregore", "Marlon Freitas", "Patrick de Paula", ("Santiago Rodríguez", "Uruguaio"), ("Jefferson Savarino", "Venezuelano"), "Allan", "Newton"],
            "atk": ["Igor Jesus", "Artur", "Jeffinho", "Matheus Martins", ("Rwan Cruz", BR), ("Elias Manoel", BR), "Santiago", "Kayque"],
        },
        7: {
            "gk": [("Sergio Rochet", "Uruguaio"), "Anthoni", "Ivan"],
            "def": ["Bustos", "Braian Aguirre", "Vitão", ("Gabriel Mercado", "Argentino"), ("Agustín Rogel", "Uruguaio"), ("Alexandro Bernabei", "Argentino"), "Juninho"],
            "mid": ["Fernando", "Thiago Maia", "Bruno Henrique", "Bruno Gomes", ("Alan Patrick", BR), ("Gabriel Tabata", BR), "Rômulo"],
            "atk": [("Rafael Borré", "Colombiano"), ("Enner Valencia", "Equatoriano"), "Wesley", ("Lucas Alario", "Argentino"), "Vitinho", "Lucca", "Ricardo Mathias", "Gustavo Prado"],
        },
        8: {
            "gk": [("Agustín Marchesín", "Argentino"), "Gabriel Grando", "Caíque"],
            "def": ["João Pedro", "Fábio", "Kannemann", "Jemerson", "Rodrigo Ely", "Reinaldo", "Mayk"],
            "mid": [("Mathías Villasanti", "Paraguaio"), "Dodi", "Edenilson", ("Franco Cristaldo", "Argentino"), "Pepê", ("Miguel Monsalve", "Colombiano"), "Nathan"],
            "atk": [("Martin Braithwaite", "Dinamarquês"), ("Cristian Olivera", "Uruguaio"), "Pavon", "Aravena", "André Henrique", ("Matias Arezo", "Uruguaio"), "Alysson", "Soteldo"],
        },
        9: {
            "gk": ["Rafael", "Jandrei", "Young"],
            "def": ["Igor Vinícius", "Ferraresi", "Arboleda", "Alan Franco", "Sabino", "Patryck", "Welington"],
            "mid": ["Alisson", "Pablo Maia", ("Damián Bobadilla", "Paraguaio"), "Marcos Antônio", "Rodriguinho", "Wellington Rato", "Matheus Alves"],
            "atk": ["Calleri", "Lucas Moura", "Luciano", "Ferreira", "André Silva", "William Gomes", "Erick", "Henrique Carmo"],
        },
        10: {
            "gk": ["Cássio", "Anderson", "Léo Aragão"],
            "def": ["William", "Fagner", "Fabrício Bruno", "Jonathan Jesus", ("Lucas Villalba", "Argentino"), "Kaiki", "Marlon"],
            "mid": ["Lucas Romero", "Walace", "Matheus Henrique", "Christian", "Japa", "Eduardo", "Matheus Pereira"],
            "atk": ["Kaio Jorge", ("Lautaro Díaz", "Argentino"), "Dudu", ("Yannick Bolasie", "Congolês"), "Marquinhos", "Wanderson", "Gabriel Veron", "Rafa Silva"],
        },
        11: {
            "gk": ["João Ricardo", "Santos", "Magrão"],
            "def": ["Tinga", ("Emanuel Brítez", "Argentino"), "Titi", ("Kuscevic", "Chileno"), "Bruno Pacheco", ("Mancuso", "Argentino"), "Talocha"],
            "mid": ["Lucas Sasha", ("Pochettino", "Argentino"), ("Martínez", "Argentino"), "Hércules", "Zé Welison", ("Kervin Andrade", "Venezuelano"), "Calebe"],
            "atk": [("Lucero", "Argentino"), "Moisés", "Marinho", "Breno Lopes", "Yago Pikachu", "Renato Kayzer", "Allanzinho", "Pedro Rocha"],
        },
        12: {
            "gk": ["Cleiton", "Lucão", "Matheus Nogueira"],
            "def": [("Andrés Hurtado", "Equatoriano"), "Nathan Mendes", "Pedro Henrique", "Natan", ("Guzmán Rodríguez", "Uruguaio"), "Juninho Capixaba", "Luan Cândido"],
            "mid": ["Jadsom", "Matheus Fernandes", "Eric Ramires", "Lucas Evangelista", "Raul", "Jhon Jhon", "Gustavinho"],
            "atk": [("Thiago Borbas", "Uruguaio"), "Eduardo Sasha", "Vitinho", "Helinho", ("Henry Mosquera", "Colombiano"), ("Ignacio Laquintana", "Uruguaio"), "Lincoln", "Talisson"],
        },
        13: {
            "gk": ["Mycael", "Léo Linck", "Santos"],
            "def": ["Léo Godoy", "Madson", "Kaique Rocha", "Belezi", "Matheus Felipe", "Lucas Esquivel", "Fernando"],
            "mid": ["Erick", "Felipinho", ("Bruno Zapelli", "Argentino"), "Christian", ("Canobbio", "Uruguaio"), "Giuliano", "Alex Santana"],
            "atk": ["Pablo", ("Mastriani", "Uruguaio"), ("Cuello", "Argentino"), "Rômulo", ("Di Yorio", "Argentino"), "Julimar", "Emersonn", "Isaac"],
        },
        14: {
            "gk": ["Marcos Felipe", "Danilo Fernandes", "Adriel"],
            "def": ["Gilberto", "Arias", "Kanu", "David Duarte", "Gabriel Xavier", "Iago Borduchi", "Luciano Juba"],
            "mid": ["Caio Alexandre", "Jean Lucas", "Everton Ribeiro", "Cauly", "Rezende", ("Nicolás Acevedo", "Uruguaio"), "Erick"],
            "atk": ["Everaldo", "Ademir", "Biel", ("Lucho Rodríguez", "Uruguaio"), "Kayky", "Tiago", "Rafael Ratão", "Willian José"],
        },
        15: {
            "gk": ["Léo Jardim", "Keiller", "Pablo"],
            "def": ["Paulo Henrique", ("Puma Rodríguez", "Uruguaio"), "João Victor", "Maicon", "Lucas Oliveira", "Lucas Piton", "Victor Luís"],
            "mid": ["Hugo Moura", "Jair", ("Juan Sforza", "Argentino"), ("Dimitri Payet", "Francês"), "Philippe Coutinho", "Paulinho", "Tchê Tchê"],
            "atk": [("Pablo Vegetti", "Argentino"), "Rayan", "Adson", "Alex Teixeira", "Rossi", "David", "GB", "Jean David"],
        },
        16: {
            "gk": ["Gabriel", "César", "Marcão"],
            "def": ["João Lucas", "Ewerthon", "Rodrigo Sam", "Danilo Boza", "Abner", "Alan Ruschel", "Marcos Paulo"],
            "mid": ["Jean Irmer", "Caique", "Mandaca", "Jadson", "Nenê", "Luis Oyama", "Luan Dias"],
            "atk": ["Erick Farias", "Gilberto", "Lucas Barbosa", "Marcelinho", "Edinho", "Taliari", "Gabriel Taliari", "Da Silva"],
        },
        17: {
            "gk": ["Walter", "João Carlos", "Mateus Pasinato"],
            "def": ["Matheus Alexandre", "Railan", "Marllon", "Alan Empereur", "Bruno Alves", "Ramon", "Sander"],
            "mid": ["Denilson", "Lucas Mineiro", "Fernando Sobral", "Max", "Clayson", "Filipe Augusto", "Ronald"],
            "atk": [("Isidro Pitta", "Paraguaio"), "Deyverson", "Jonathan Cafu", "Eliel", "Derik Lacerda", "André Luís", "Wellington Silva", "Alisson Safira"],
        },
        18: {
            "gk": ["Ronaldo", "Luan Polli", "Pedro Paulo"],
            "def": ["Bruno Tubarão", "Maguinho", "Alix Vinicius", "Lucas Gazal", "Luiz Felipe", "Guilherme Romão", "Rhaldney"],
            "mid": ["Roni", "Baralhas", "Shaylon", "Jorginho", "Emiliano Rodríguez", "Léo Pereira", "Campanharo"],
            "atk": ["Luiz Fernando", "Derek", "Janderson", "Hyuri", "Alejo Cruz", "Danielzinho", "Yony González", "Gustavo Coutinho"],
        },
        19: {
            "gk": ["Lucas Arcanjo", "Muriel", "Dalton"],
            "def": ["Raul Cáceres", "Zeca", "Wagner Leonardo", "Camutanga", "Neris", "PK", "Patric Calmon"],
            "mid": ["Léo Naldi", "Rodrigo Andrade", "Willian Oliveira", "Jean Mota", "Matheuzinho", "Caio Vinícius", "Dudu"],
            "atk": ["Alerrandro", "Osvaldo", "Janderson", "Everaldo", "Iury Castilho", "Wellington Rato", "Fábio Soares", "Carlos Eduardo"],
        },
        20: {
            "gk": ["Gustavo", "Alisson", "Kauã"],
            "def": ["Claudinho", "Jonathan", "Rodrigo", ("Tobias Figueiredo", "Português"), "Victor Luís", "Marcelo Hermes", "Dudu"],
            "mid": ["Barreto", "Higor Meritão", "Fellipe Mateus", "Marquinhos Gabriel", "Newton", "Rômulo", "Miquéias"],
            "atk": [("Yannick Bolasie", "Congolês"), "Arthur Caíke", "Allano", "Ronald", "Matheusinho", "Jhonata Robert", "Éder", "Felipinho"],
        },
        21: {
            "gk": ["Gabriel Brazão", "João Paulo", "Diógenes"],
            "def": ["Aderlan", "JP Chermont", "Gil", "Joaquim", "Zé Ivaldo", "Escobar", "Kevyson"],
            "mid": ["Diego Pituca", "Tomás Rincón", "João Schmidt", "Giuliano", "Otero", "Cazares", "Miguelito"],
            "atk": ["Guilherme", "Pedrinho", "Julio Furch", "Willian Bigode", "Wendel Silva", "Lucas Braga", "Morelos", "Enzo Monteiro"],
        },
        22: {
            "gk": ["Caíque França", "Denis", "Adriel"],
            "def": ["Rosales", "Hereda", "Rafael Thyere", "Chico", "Luciano Castán", "Felipinho", "Igor Cariús"],
            "mid": ["Fabinho", "Felipe", "Lucas Lima", "Titi Ortíz", "Julián Fernández", "Pedro Vilhena", "Alan Ruiz"],
            "atk": ["Barletta", "Gustavo Coutinho", "Zé Roberto", "Romarinho", "Pablo Dyego", "Chrystian", "Lenny Lobato", "Diego Souza Jr"],
        },
        23: {
            "gk": ["Richard", "Bruno Ferreira", "Fernando Miguel"],
            "def": ["Rafael Ramos", "Raí Ramos", "David Ricardo", "Luiz Otávio", "Matheus Felipe", "Eric Melo", "Warley"],
            "mid": ["Richardson", "Lourenço", "Lucas Mugni", "Rômulo", "Aylon", "De Lucca", "Fernando Sobral"],
            "atk": ["Saulo Mineiro", "Facundo Castro", "Barceló", "Cléber", "Recalde", "Janderson", "Erick Pulga", "Guilherme Bissoli"],
        },
        24: {
            "gk": ["Alex Muralha", "Walter", "Vanderlei"],
            "def": ["Lucas Ramon", "Daniel Borges", "Luiz Otávio", "Rodrigo Ferreira", "João Victor", "Reinaldo", "Zeca"],
            "mid": ["Neto Moura", "Danielzinho", "Chico Kim", "Negueba", "Gabriel", "Yago Felipe", "Iury"],
            "atk": ["Dellatorre", "Quirino", "Zé Roberto", "Fernandinho", "Fabrício Daniel", "Rafinha", "Nicolas", "Alex Silva"],
        },
        25: {
            "gk": ["Pedro Morisco", "Pedro Rangel", "Gabriel Leite"],
            "def": ["Tiago Coser", "Maicon", "Jacy", "João Almeida", "Felipe Guimarães", "Guilherme Aquino", "Bruno Melo"],
            "mid": [("Sebastián Gómez", "Colombiano"), "Willian Oliveira", "Jean Gabriel", "Geovane", "Josué", ("Carlos de Pena", "Uruguaio"), "Matheus Bianqui"],
            "atk": ["Clayson", "Lucas Ronier", "Dellatorre", "Nicolas Careca", "Gustavo Coutinho", "Iury Castilho", ("Joaquín Lavega", "Uruguaio"), "Pedro Rocha"],
        },
        26: {
            "gk": ["Tadeu", "Thiago Rodrigues", "Marcão"],
            "def": ["Ezequiel", "Lucas Ribeiro", "Luiz Felipe", "Titi", "Anthony", "Nicolas", "Rodrigo Soares"],
            "mid": ["Gegê", "Juninho", ("Brayann", "Colombiano"), "Filipe Machado", "Lourenço", "Lucas Lima", "Jean Carlos"],
            "atk": ["Wellington Rato", "Bruno Sávio", ("Esli García", "Venezuelano"), "Pedrinho", "Anselmo Ramon", "Jajá", "Cadu", "Arthur Caíke"],
        },
        27: {
            "gk": ["Matheus Mendes", "Jori", "Dalberson"],
            "def": ["Marlon", "Ricardo Silva", "Júlio", "Maguinho", "Nicolas", "Lucão", "Paulinho"],
            "mid": ["Alê", "Moisés", "Fabinho Santos", "Miguelito", "Benítez", "Cauan Barros", "Jhosefer"],
            "atk": ["Fabinho", "Adyson", "Willian Bigode", "Guilherme Pato", "Renato Marques", "Brenner", "Stênio", "Aloísio"],
        },
        28: {
            "gk": ["Igor Bohn", "Otávio Passos", "Léo Aragão"],
            "def": ["Douglas Teixeira", "Quaresma", "Allyson", "Wallison", "Wesley Gasolina", "Guilherme Aquino", "Gabriel Simples"],
            "mid": ["Jean Lucas", "Daniel Penha", "Zé Ricardo", "Romildo Del Piage", "Wenderson", "Hyan", "Luiz Henrique"],
            "atk": ["Rafael Bilu", "Felipe Avenatti", "Sorriso", "Gaspar", "Maurício Garcez", "Thayllon", "Igor Rosa", "Mário Sérgio"],
        },
        29: {
            "gk": ["Helton Leite", "Dalberson", "Airton"],
            "def": ["Caio Marcelo", "Anderson Jesus", "Elias", "Weverton", "Tiago Pagnussat", "Higor", "Hayner"],
            "mid": ["Dudu", "Nathan Camargo", "Dodô", "João Vieira", "Marco Antonio", "Willian Maranhão", "Marquinhos Gabriel"],
            "atk": ["Ruan Ribeiro", "Dellatorre", "Andre Luis", "Bruno Xavier", "Rafa Silva", "Emerson Urso", "Janderson", "Alesson"],
        },
        30: {
            "gk": ["Gabriel Mesquita", "Jean Drosny", "Matheus Nogueira"],
            "def": ["Marcão", ("Yeferson Quintana", "Colombiano"), "Edílson", "Luccão", "Bruno Bispo", "PK", "Reverson"],
            "mid": ["Leandro Vilela", "Marlon", "Matheus Vargas", "Cavan", "Ramon Martinez", "Giovanni", "Robinho"],
            "atk": ["Nicolas", "Marlon Douglas", "Benitez", "Edinho", "Ciel", "Kevin", "Eliel", "Diogo Oliveira"],
        },
        31: {
            "gk": ["Matheus Albino", "Vitor Caetano", "Pablo"],
            "def": ["Hereda", "Henri", "Segovia", "Fábio Alemão", "Lucas Lovat", "Weverton", "Ryan"],
            "mid": ["Danielzinho", "Higor Meritão", "Geovane", "Lucas Kallyel", "Gegê", "Mikael", "Douglas Baggio"],
            "atk": ["Anselmo Ramon", "Léo Pereira", "William Pottker", "Dadá Belmonte", "João Neto", "Thiaguinho", "Rafinha", "Labandeira"],
        },
        32: {
            "gk": ["Jordi", "Airton", "César Augusto"],
            "def": ["Patrick", "Dantas", "Rômulo", "César Martins", "Mayk", "Rafael Donato", "Raí Ramos"],
            "mid": ["Fábio Matheus", "Jean Irmer", "Marlon", "Matheus Frizzo", "Lucca", "Robson", "Waguininho"],
            "atk": ["Caio Dantas", "Nicolas Careca", "Léo Tocantins", "Bruno José", "Everaldo", "Neto Pessoa", "Jenison", "Rodolfo"],
        },
    }

    for team in teams:
        snap = roster_2026.get(team.id)
        if not snap:
            continue
        base_ovr = _estimate_base_ovr(team)
        team.players = _build_named_roster(
            base_ovr,
            snap["gk"],
            snap["def"],
            snap["mid"],
            snap["atk"],
        )


def apply_finances(teams):
    """Aplica dados financeiros e de torcida a cada clube"""
    # (id, torcida, caixa_R$mil, salario_mensal_R$mil)
    finances = {
        1:  (30_000_000, 400_000, 28_000),   # Flamengo
        2:  (14_000_000, 380_000, 24_000),   # Palmeiras
        3:  (13_000_000, 280_000, 20_000),   # Atlético-MG
        4:  (30_000_000,  45_000, 19_000),   # Corinthians (dívida alta)
        5:  (12_000_000, 110_000, 16_000),   # Fluminense
        6:  (12_000_000, 310_000, 20_000),   # Botafogo (Textor)
        7:   (8_000_000, 160_000, 14_000),   # Internacional
        8:   (9_000_000, 140_000, 13_000),   # Grêmio
        9:  (15_000_000,  70_000, 14_000),   # São Paulo
        10:  (9_000_000,  90_000, 13_000),   # Cruzeiro
        11:  (3_500_000, 120_000, 11_000),   # Fortaleza
        12:  (1_500_000, 130_000,  9_500),   # Bragantino
        13:  (5_000_000,  80_000,  9_000),   # Athletico-PR
        14:  (3_000_000,  75_000,  8_500),   # Bahia
        15: (10_000_000,  50_000,  9_000),   # Vasco
        16:  (1_000_000,  40_000,  5_500),   # Juventude
        17:  (1_200_000,  35_000,  5_000),   # Cuiabá
        18:  (1_500_000,  30_000,  4_500),   # Atlético-GO
        19:  (3_000_000,  30_000,  5_000),   # Vitória
        20:    (800_000,  25_000,  4_500),   # Criciúma
        21: (10_000_000,  55_000,  7_000),   # Santos
        22:  (2_500_000,  25_000,  4_000),   # Sport
        23:  (2_500_000,  28_000,  4_000),   # Ceará
        24:    (500_000,  20_000,  3_500),   # Mirassol
        25:  (2_800_000,  35_000,  4_800),   # Coritiba
        26:  (2_600_000,  32_000,  4_600),   # Goiás
        27:  (2_400_000,  30_000,  4_500),   # América-MG
        28:  (1_500_000,  22_000,  3_800),   # Avaí
        29:  (1_300_000,  20_000,  3_600),   # Vila Nova
        30:  (1_400_000,  20_000,  3_600),   # Paysandu
        31:  (1_200_000,  18_000,  3_500),   # CRB
        32:    (900_000,  16_000,  3_200),   # Novorizontino
    }
    for t in teams:
        if t.id in finances:
            t.torcida, t.caixa, t.salario_mensal = finances[t.id]
    return teams


def _ensure_minimum_rosters(teams, minimum_players: int):
    """Completa elencos abaixo do mínimo com jogadores genéricos."""
    for team in teams:
        while len(team.players) < minimum_players:
            idx = len(team.players) + 1
            if idx % 6 == 0:
                position = GK
            elif idx % 3 == 0:
                position = DEF
            elif idx % 3 == 1:
                position = MID
            else:
                position = ATK
            first = GENERIC_FIRST_NAMES[(idx + team.id) % len(GENERIC_FIRST_NAMES)]
            last = GENERIC_LAST_NAMES[(idx * 2 + team.id) % len(GENERIC_LAST_NAMES)]
            base = max(18, min(92, int(team.players[-1].overall if team.players else 50) - 2))
            team.players.append(
                _p(f"{first} {last}", position, 23 + (idx % 9), BR, base,
                   62 if position != GK else 48, 64 if position != GK else 58,
                   58 if position == ATK else 28, 62 if position != GK else 48,
                   66, 64 if position != ATK else 48, 60,
                   base + 3 if position == GK else 10)
            )


def _assign_team_stars(teams, stars_per_team: int = 3):
    """Marca os melhores jogadores do elenco como CRAQUE."""
    for team in teams:
        for player in team.players:
            player.is_star = False
        top_players = sorted(team.players, key=lambda p: p.overall, reverse=True)[:stars_per_team]
        for player in top_players:
            player.is_star = True
