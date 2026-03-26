#!/usr/bin/env python3
"""
Award survey points to users by ASURITE ID.

Looks up each ASURITE in forklift's DB to get the Discord ID,
then awards points in the economy DB. Safe to re-run — already-awarded
users are skipped via the survey_bonus_received flag.

Usage:
    Paste ASURITEs directly (one per line, Ctrl+D when done):
        python scripts/award_survey_points.py

    Pipe from a file:
        python scripts/award_survey_points.py < asurites.txt

    Pass a custom point amount:
        python scripts/award_survey_points.py --points 250

    Dry run (no DB changes):
        python scripts/award_survey_points.py --dry-run

If you're copy-pasting a multi-column selection from Google Sheets,
use --column to specify which column (0-indexed) contains the ASURITE.
Default is 0 (first column). Example for the second column:
        python scripts/award_survey_points.py --column 1
"""

import sys
import sqlite3
import argparse
from pathlib import Path

FORKLIFT_DB = Path(__file__).resolve().parents[2] / "forklift" / "forklift.db"
ECONOMY_DB  = Path(__file__).resolve().parents[1] / "instance" / "store.db"
DEFAULT_POINTS = 250


def parse_args():
    parser = argparse.ArgumentParser(description="Award survey points by ASURITE")
    parser.add_argument("--points",   type=int, default=DEFAULT_POINTS,
                        help=f"Points to award per user (default: {DEFAULT_POINTS})")
    parser.add_argument("--column",   type=int, default=0,
                        help="0-indexed column to read ASURITE from when input has tabs (default: 0)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Preview without writing any changes")
    return parser.parse_args()


def read_asurites(column):
    """Read ASURITEs from stdin. Handles tab-separated Google Sheets paste."""
    asurites = []
    print("Paste ASURITEs (one per line). Press Ctrl+D when done:\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        # Handle tab-separated columns (Google Sheets multi-column copy)
        parts = line.split("\t")
        if column >= len(parts):
            print(f"  [WARN] Line has only {len(parts)} column(s), can't read column {column}: {line!r}")
            continue
        asurite = parts[column].strip()
        if not asurite:
            continue
        asurites.append(asurite)
    return asurites


def ensure_survey_column(econ_conn):
    """Add survey_bonus_received column if it doesn't exist yet."""
    try:
        econ_conn.execute("ALTER TABLE user ADD COLUMN survey_bonus_received BOOLEAN DEFAULT 0")
        econ_conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists


def lookup_discord(fork_conn, asurite):
    """Return (discord_user_id, display_name) for an ASURITE, or (None, None).
    Tries bare ASURITE first, then with @asu.edu appended."""
    candidates = [asurite]
    if "@" not in asurite:
        candidates.append(asurite + "@asu.edu")

    for candidate in candidates:
        row = fork_conn.execute(
            "SELECT discord_user_id, discord_global_name, discord_username "
            "FROM users WHERE asurite_id = ?",
            (candidate,)
        ).fetchone()
        if row and row[0]:
            display = row[1] or row[2] or row[0]
            return row[0], display

    return None, None


def award(econ_conn, discord_id, display_name, points, dry_run):
    """
    Award points to a user. Returns one of:
      'awarded'           - points successfully added
      'created_awarded'   - user didn't exist in economy DB, created and awarded
      'already_awarded'   - survey_bonus_received was already True, skipped
    """
    row = econ_conn.execute(
        "SELECT id, survey_bonus_received FROM user WHERE id = ?",
        (discord_id,)
    ).fetchone()

    if row:
        if row[1]:
            return "already_awarded"
        if not dry_run:
            econ_conn.execute(
                "UPDATE user SET balance = balance + ?, points = points + ?, "
                "survey_bonus_received = 1 WHERE id = ?",
                (points, points, discord_id)
            )
            econ_conn.commit()
        return "awarded"
    else:
        # User hasn't interacted with the bot yet — create a minimal record
        if not dry_run:
            econ_conn.execute(
                """INSERT INTO user (
                    id, username, discord_id, points, balance, survey_bonus_received,
                    messages_sent, messages_reacted_to, message_count, reaction_count,
                    voice_minutes, daily_claims_count, campus_photos_count,
                    daily_engagement_count, is_admin, enrollment_deposit_received,
                    has_boosted, birthday_points_received, verification_bonus_received,
                    onboarding_bonus_received, verify_corrected, onboarding_refunded
                ) VALUES (?, ?, ?, ?, ?, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)""",
                (discord_id, display_name, discord_id, points, points)
            )
            econ_conn.commit()
        return "created_awarded"


def main():
    args = parse_args()

    if not FORKLIFT_DB.exists():
        print(f"ERROR: forklift DB not found at {FORKLIFT_DB}")
        sys.exit(1)
    if not ECONOMY_DB.exists():
        print(f"ERROR: economy DB not found at {ECONOMY_DB}")
        sys.exit(1)

    asurites = read_asurites(args.column)
    if not asurites:
        print("No ASURITEs provided. Exiting.")
        sys.exit(0)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processing {len(asurites)} ASURITE(s) "
          f"— {args.points} points each\n")

    fork_conn = sqlite3.connect(f"file:{FORKLIFT_DB}?mode=ro", uri=True)
    econ_conn = sqlite3.connect(ECONOMY_DB)

    ensure_survey_column(econ_conn)

    results = {"awarded": [], "created_awarded": [], "already_awarded": [], "not_found": []}

    for asurite in asurites:
        discord_id, display_name = lookup_discord(fork_conn, asurite)

        if not discord_id:
            print(f"  NOT FOUND     {asurite}")
            results["not_found"].append(asurite)
            continue

        outcome = award(econ_conn, discord_id, display_name, args.points, args.dry_run)
        label = {
            "awarded":         "AWARDED      ",
            "created_awarded": "CREATED+AWD  ",
            "already_awarded": "ALREADY DONE ",
        }[outcome]
        print(f"  {label}  {asurite:20s}  →  {display_name} ({discord_id})")
        results[outcome].append(asurite)

    fork_conn.close()
    econ_conn.close()

    print(f"""
{'─' * 50}
{'[DRY RUN — no changes written] ' if args.dry_run else ''}Summary
  Awarded:        {len(results['awarded']) + len(results['created_awarded'])}
    └ new to bot: {len(results['created_awarded'])}
  Already done:   {len(results['already_awarded'])}
  Not in forklift:{len(results['not_found'])}
  Total input:    {len(asurites)}
{'─' * 50}""")

    if results["not_found"]:
        print("\nASURITEs with no forklift record (not verified via Discord):")
        for a in results["not_found"]:
            print(f"  {a}")


if __name__ == "__main__":
    main()
