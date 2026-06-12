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


if __name__ == "__main__":
    cli()