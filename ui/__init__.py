"""
ClassicFoot UI — pacote que agrupa todos os módulos de interface.

Re-exporta tudo para manter compatibilidade com `from ui import ...`.
"""
from ui.common import (
    _ovr_text, _ellipsize_visible, _e,
    _team_color, _division_label,
    _fit_team_name, _fit_text,
    _box_width, _print_side_by_side,
    _mini_form,
)
from ui.lineup import (
    _pick_probable_lineup,
    _find_player_next_match,
    _render_probable_lineup,
)
from ui.menus import (
    banner, main_menu, game_menu,
    show_onboarding, show_credits, confirm_play,
)
from ui.dashboard import season_dashboard, show_next_round
from ui.tactics import show_tactics, choose_postura, show_training, prompt_contract_renewal
from ui.standings import show_standings, show_calendar, show_top_scorers
from ui.match import (
    show_match_result,
    _render_live_scores, _render_penalty_shootout,
    _render_substitution_screen, _matchday_has_player_game,
    _score_at_minute, _format_live_fixture,
)
from ui.copa import show_copa, show_copa_draw
from ui.finances import show_finances, show_torcida, show_stadium
from ui.transfers import show_transfer_market, show_auction_results, manage_player_sales
from ui.history import (
    show_notifications, show_season_end,
    show_history, prompt_job_offer,
)

__all__ = [
    # common
    "_ovr_text", "_ellipsize_visible", "_e",
    "_team_color", "_division_label",
    "_fit_team_name", "_fit_text",
    "_box_width", "_print_side_by_side",
    "_mini_form",
    # lineup
    "_pick_probable_lineup", "_find_player_next_match", "_render_probable_lineup",
    # menus
    "banner", "main_menu", "game_menu",
    "show_onboarding", "show_credits", "confirm_play",
    # dashboard
    "season_dashboard", "show_next_round",
    # tactics
    "show_tactics", "choose_postura", "show_training", "prompt_contract_renewal",
    # standings
    "show_standings", "show_calendar", "show_top_scorers",
    # match
    "show_match_result",
    "_render_live_scores", "_render_penalty_shootout",
    "_render_substitution_screen", "_matchday_has_player_game",
    "_score_at_minute", "_format_live_fixture",
    # copa
    "show_copa", "show_copa_draw",
    # finances
    "show_finances", "show_torcida", "show_stadium",
    # transfers
    "show_transfer_market", "show_auction_results", "manage_player_sales",
    # history
    "show_notifications", "show_season_end", "show_history", "prompt_job_offer",
]
