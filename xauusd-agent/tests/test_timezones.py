from datetime import datetime, time

from src.timezones import LONDON, MONTREAL, NEW_YORK, session_window_for_day


def test_montreal_new_york_same_offset_in_summer():
    """En ete (EDT), Montreal et New York doivent avoir le meme decalage."""
    ref = datetime(2026, 7, 15, 12, 0, tzinfo=MONTREAL)
    ny_session = session_window_for_day(NEW_YORK, time(8, 0), time(17, 0), ref, "NY")
    assert ny_session.start_montreal.hour == 8  # meme heure locale, meme fuseau EDT/EST-aligned


def test_london_montreal_offset_changes_around_dst_transition():
    """
    Les changements d'heure US/Canada et UK ne sont pas synchronises (le
    Royaume-Uni change generalement plus tard fin octobre / plus tot fin mars
    que les US certaines annees). Ce test verifie juste que le calcul est bien
    refait dynamiquement et ne suppose pas un decalage fixe.
    """
    # 2026 : le Canada/les US passent a l'heure d'ete le 8 mars, le Royaume-Uni
    # seulement le 29 mars. Le 15 mars, Montreal est deja en EDT (UTC-4) alors
    # que Londres est encore en GMT (UTC+0) : l'ecart entre les deux zones
    # n'est donc pas celui de janvier (les deux en heure standard).
    standard_ref = datetime(2026, 1, 15, 12, 0, tzinfo=MONTREAL)
    asymmetric_ref = datetime(2026, 3, 15, 12, 0, tzinfo=MONTREAL)

    standard_london = session_window_for_day(LONDON, time(8, 0), time(16, 30), standard_ref, "London")
    asymmetric_london = session_window_for_day(LONDON, time(8, 0), time(16, 30), asymmetric_ref, "London")

    assert standard_london.start_montreal.hour != asymmetric_london.start_montreal.hour or \
        standard_london.start_montreal.minute != asymmetric_london.start_montreal.minute
