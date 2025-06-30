"""
Balance consistency utilities for the Devil2Devil Economy system.
"""

def fix_balance_consistency(app, db, User):
    """Fix balance/points consistency for ALL users in the database"""
    try:
        with app.app_context():
            # Get ALL users in the database
            all_users = User.query.all()
            
            if not all_users:
                print("⚠️  No users found in the database!")
                return True
            
            print(f"🔧 Processing {len(all_users)} users to ensure balance/points consistency...")
            print("-" * 60)
            
            fixed_count = 0
            consistent_count = 0
            
            for user in all_users:
                old_balance = user.balance or 0
                old_points = user.points or 0
                
                # Ensure both fields exist and are not None
                if user.balance is None:
                    user.balance = 0
                if user.points is None:
                    user.points = 0
                
                # Use balance as the authoritative source since that's what's displayed in all user-facing commands
                if user.balance != user.points:
                    user.points = user.balance
                    print(f"🔧 {user.username}: balance={old_balance}, points={old_points} → both={user.balance}")
                    fixed_count += 1
                else:
                    print(f"✅ {user.username}: already consistent (balance=points={user.balance})")
                    consistent_count += 1
            
            # Commit the changes
            db.session.commit()
            print("-" * 60)
            print(f"✅ Balance consistency check complete!")
            print(f"   - Fixed {fixed_count} users with inconsistencies")
            print(f"   - {consistent_count} users were already consistent")
            print(f"   - Total users processed: {len(all_users)}")
            print("")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error fixing balance consistency: {e}")
        return False
    
    return True 