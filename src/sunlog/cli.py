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


if __name__ == "__main__":
    cli()