"""sunlog CLI - log and review your daily sun exposure & vitamin D intake."""

from datetime import date, datetime
from typing import Optional

import click

from sunlog.storage import add_entry
from sunlog.vitamin_d import (
    ExposureParams,
    coverage_options,
    estimate_vitamin_d,
    skin_tone_options,
)


def _fmt_iu(iu: float) -> str:
    return f"{iu:,.0f} IU"


@click.group()
@click.version_option()
def cli() -> None:
    """sunlog - track sun exposure and vitamin D synthesis."""


@cli.command()
@click.option("--duration", "-d", type=float, required=True,
              help="Duration of sun exposure in minutes.")
@click.option("--uv", "-u", type=float, required=True,
              help="UV index during exposure (0-11+). Check your weather app.")
@click.option("--coverage", "-c",
              type=click.Choice(coverage_options(), case_sensitive=False),
              default="arms", show_default=True,
              help="Skin area exposed: minimal, arms, legs, full.")
@click.option("--skin-tone", "-s",
              type=click.Choice(skin_tone_options(), case_sensitive=False),
              default="medium", show_default=True,
              help="Your skin tone - affects synthesis rate.")
@click.option("--date", "log_date", default=None,
              help="Date of exposure (YYYY-MM-DD). Defaults to today.")
@click.option("--note", "-n", default="",
              help="Optional note (e.g. 'beach walk').")
def log(
    duration: float,
    uv: float,
    coverage: str,
    skin_tone: str,
    log_date: Optional[str],
    note: str,
) -> None:
    """Log a sun exposure session."""
    if duration <= 0:
        raise click.BadParameter("Duration must be positive.", param_hint="--duration")
    if uv < 0:
        raise click.BadParameter("UV index can't be negative.", param_hint="--uv")

    entry_date = log_date or date.today().isoformat()

    try:
        date.fromisoformat(entry_date)
    except ValueError:
        raise click.BadParameter(f"Invalid date '{entry_date}'. Use YYYY-MM-DD.", param_hint="--date")

    params = ExposureParams(
        duration_minutes=duration,
        uv_index=uv,
        coverage=coverage,
        skin_tone=skin_tone,
    )
    iu = estimate_vitamin_d(params)

    entry = {
        "date": entry_date,
        "logged_at": datetime.now().isoformat(timespec="seconds"),
        "duration_minutes": duration,
        "uv_index": uv,
        "coverage": coverage,
        "skin_tone": skin_tone,
        "estimated_iu": iu,
        "note": note,
    }
    add_entry(entry)

    click.echo(f"\nSession logged for {entry_date}")
    click.echo(f"   Duration  : {duration:.0f} min")
    click.echo(f"   UV Index  : {uv}")
    click.echo(f"   Coverage  : {coverage}")
    click.echo(f"   Skin tone : {skin_tone}")
    if iu > 0:
        click.echo(f"   ~Vitamin D: {_fmt_iu(iu)}")
    else:
        click.echo("   ~Vitamin D: 0 IU (UV index too low for synthesis)")
    if note:
        click.echo(f"   Note      : {note}")





# history command
from datetime import timedelta
from sunlog.storage import load_entries


def _entries_for_range(entries: list, start: date, end: date) -> list:
    result = []
    for e in entries:
        try:
            d = date.fromisoformat(e["date"])
            if start <= d <= end:
                result.append(e)
        except (KeyError, ValueError):
            pass
    return result


@cli.command()
@click.option("--days", "-n", default=30, show_default=True,
              help="Show entries from the last N days.")
@click.option("--all", "show_all", is_flag=True, default=False,
              help="Show all entries.")
def history(days: int, show_all: bool) -> None:
    """Show past sun exposure sessions."""
    entries = load_entries()
    if not entries:
        click.echo("No sessions logged yet. Use `sunlog log` to add one.")
        return

    if show_all:
        filtered = entries
        label = "all time"
    else:
        cutoff = date.today() - timedelta(days=days - 1)
        filtered = _entries_for_range(entries, cutoff, date.today())
        label = f"last {days} days"

    if not filtered:
        click.echo(f"No sessions in {label}.")
        return

    click.echo(f"\n{'-'*60}")
    click.echo(f"  Sun exposure log - {label}  ({len(filtered)} session(s))")
    click.echo(f"{'-'*60}")

    all_dates = [e["date"] for e in entries]
    for i, e in enumerate(filtered, start=all_dates.index(filtered[0]["date"]) + 1):
        iu = e.get("estimated_iu", 0)
        note = f"  - {e['note']}" if e.get("note") else ""
        uv_warn = "  (low UV)" if e["uv_index"] < 2 else ""
        click.echo(
            f"  [{i:>3}] {e['date']}  {e['duration_minutes']:>3.0f} min  "
            f"UV {e['uv_index']:>4.1f}  {e['coverage']:<6}  "
            f"~{_fmt_iu(iu):>12}{uv_warn}{note}"
        )

    total_iu = sum(e.get("estimated_iu", 0) for e in filtered)
    click.echo(f"{'-'*60}")
    click.echo(f"  Total estimated vitamin D: {_fmt_iu(total_iu)}\n")





# summary command
RECOMMENDED_DAILY_IU = 1000


def _bar(value: float, maximum: float, width: int = 20) -> str:
    filled = int(round(width * min(value, maximum) / maximum)) if maximum else 0
    return "#" * filled + "-" * (width - filled)


@cli.command()
@click.option("--weeks", "-w", default=1, show_default=True,
              help="Number of weeks to summarize.")
def summary(weeks: int) -> None:
    """Show a weekly vitamin D summary with daily progress bars."""
    entries = load_entries()
    if not entries:
        click.echo("No sessions logged yet. Use `sunlog log` to add one.")
        return

    today = date.today()
    start = today - timedelta(weeks=weeks - 1, days=today.weekday())
    end = start + timedelta(weeks=weeks) - timedelta(days=1)

    click.echo(f"\n{'-'*52}")
    click.echo(f"  Weekly summary  ({start} -> {end})")
    click.echo(f"  Daily target: {_fmt_iu(RECOMMENDED_DAILY_IU)}")
    click.echo(f"{'-'*52}")

    total_iu = 0.0
    days_with_sun = 0
    streak = 0
    current_streak = 0

    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        day_entries = _entries_for_range(entries, day, day)
        day_iu = sum(e.get("estimated_iu", 0) for e in day_entries)
        total_iu += day_iu
        had_sun = day_iu > 0

        if had_sun:
            days_with_sun += 1
            current_streak += 1
            streak = max(streak, current_streak)
        else:
            current_streak = 0

        bar = _bar(day_iu, RECOMMENDED_DAILY_IU)
        marker = "OK " if day_iu >= RECOMMENDED_DAILY_IU else (".  " if had_sun else "   ")
        is_today = " <- today" if day == today else ""
        click.echo(
            f"  {marker}{day.strftime('%a %b %d')}  {bar}  {_fmt_iu(day_iu)}{is_today}"
        )

    avg_iu = total_iu / ((end - start).days + 1)
    click.echo(f"{'-'*52}")
    click.echo(f"  Total IU      : {_fmt_iu(total_iu)}")
    click.echo(f"  Daily average : {_fmt_iu(avg_iu)}")
    click.echo(f"  Days with sun : {days_with_sun} / {(end - start).days + 1}")
    click.echo(f"  Longest streak: {streak} day(s)\n")






# Delete command
import sys
from sunlog.storage import delete_entry


@cli.command()
@click.argument("entry_id", type=int)
def delete(entry_id: int) -> None:
    if delete_entry(entry_id):
        click.echo(f"Entry {entry_id} deleted.")
    else:
        click.echo(f"No entry with ID {entry_id}.", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()