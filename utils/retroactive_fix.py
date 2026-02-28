"""
Retroactive fix script — run once from the project root:
    python utils/retroactive_fix.py

What it does:
1. Verification correction: users with verification_bonus_received=True and verify_corrected=False
   receive +100 pts (diff between old 200 and new 300 spec).
2. Onboarding refund: users with onboarding_bonus_received=True and onboarding_refunded=False
   have -500 pts deducted (floored at 0).
3. Message milestone awards: for each user, award any message-type achievements they qualify
   for based on current message_count (skips already-awarded ones).

The verify_corrected and onboarding_refunded columns act as idempotency guards — safe to run
multiple times; subsequent runs will report 0 changes.
"""

import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import app, db, User, Achievement, UserAchievement
from datetime import datetime


def run_verification_correction(session):
    """Add +100 to users who received the old 200-pt verification bonus."""
    users = User.query.filter_by(
        verification_bonus_received=True,
        verify_corrected=False
    ).all()

    count = 0
    for user in users:
        user.balance += 100
        user.points += 100
        user.verify_corrected = True
        count += 1

    if count:
        session.commit()

    return count


def run_onboarding_refund(session):
    """Subtract 500 from users who received the onboarding bonus (floor at 0)."""
    users = User.query.filter_by(
        onboarding_bonus_received=True,
        onboarding_refunded=False
    ).all()

    count = 0
    for user in users:
        user.balance = max(0, user.balance - 500)
        user.points = max(0, user.points - 500)
        user.onboarding_refunded = True
        count += 1

    if count:
        session.commit()

    return count


def run_message_milestone_awards(session):
    """Award message milestone achievements retroactively based on current message_count."""
    message_achievements = Achievement.query.filter_by(type='messages').order_by(
        Achievement.requirement
    ).all()

    if not message_achievements:
        print("  No message-type achievements found in DB — run startup to seed them first.")
        return 0

    users = User.query.all()
    total_awarded = 0

    for user in users:
        msg_count = user.message_count or 0
        already_awarded_ids = {ua.achievement_id for ua in user.achievements}

        for ach in message_achievements:
            if ach.id in already_awarded_ids:
                continue
            if msg_count >= ach.requirement:
                ua = UserAchievement(
                    user_id=user.id,
                    achievement_id=ach.id,
                    achieved_at=datetime.utcnow()
                )
                session.add(ua)
                user.balance += ach.points
                user.points += ach.points
                total_awarded += 1

    if total_awarded:
        session.commit()

    return total_awarded


def main():
    with app.app_context():
        print("=" * 55)
        print("  Retroactive Fix Script")
        print("=" * 55)

        print("\n[1/3] Verification bonus correction (+100 each)...")
        verify_count = run_verification_correction(db.session)
        print(f"      Corrected: {verify_count} user(s)")

        print("\n[2/3] Onboarding bonus refund (-500 each)...")
        refund_count = run_onboarding_refund(db.session)
        print(f"      Refunded:  {refund_count} user(s)")

        print("\n[3/3] Message milestone achievements...")
        ach_count = run_message_milestone_awards(db.session)
        print(f"      Awarded:   {ach_count} achievement(s) across all users")

        print("\n" + "=" * 55)
        print("  Summary")
        print("=" * 55)
        print(f"  Verify corrections : {verify_count}")
        print(f"  Onboarding refunds : {refund_count}")
        print(f"  Achievement awards : {ach_count}")
        print("=" * 55)

        if verify_count == 0 and refund_count == 0 and ach_count == 0:
            print("  Nothing to do — already fully applied.")
        else:
            print("  Done. Re-run to confirm idempotency (all counts should be 0).")


if __name__ == '__main__':
    main()
