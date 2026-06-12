# sunlog

A command-line tool for logging daily sun exposure and estimating how much
vitamin D your body synthesized. Tracks duration, UV index, skin coverage, and
skin tone, then gives you daily progress bars and a weekly summary so you can
track your vitamin D intake without supplements.

## Usage

### Log a session

```bash
sunlog log --duration 20 --uv 6 --coverage arms --skin-tone medium
```

This logs a 20-minute session at UV index 6 with arms exposed for someone
with medium skin tone, and prints the estimated vitamin D produced.

Options:
- `--duration` / `-d` - minutes spent in the sun (required)
- `--uv` / `-u` - UV index during exposure, e.g. `6` (required)
- `--coverage` / `-c` - skin area exposed: `minimal`, `arms`, `legs`, `full` (default: `arms`)
- `--skin-tone` / `-s` - `fair`, `medium`, or `dark` (default: `medium`)
- `--date` - date of exposure as `YYYY-MM-DD` (defaults to today)
- `--note` / `-n` - optional label like `"beach walk"`

### View history

```bash
sunlog history
```

Shows sessions from the last 30 days. Use `sunlog history --days 7` for the
last week, or `sunlog history --all` for everything.

### Weekly summary

```bash
sunlog summary
```

Displays a day-by-day progress bar toward a 1,000 IU daily target, plus
total IU, daily average, and your current streak. Use `sunlog summary --weeks 2`
to view multiple weeks.

### Delete an entry

```bash
sunlog delete 3
```

Deletes entry #3 (IDs are shown in `sunlog history`).

## Data storage

All data is stored locally in `~/.sunlog/data.json`. No account or internet
connection required.