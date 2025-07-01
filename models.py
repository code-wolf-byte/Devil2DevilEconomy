# This file is deprecated - all models have been moved to shared.py
# Keeping for backward compatibility, but all imports should use shared.py

from shared import (
    User, Product, Purchase, Achievement, UserAchievement, 
    EconomySettings, RoleAssignment, DownloadToken, db
)

# Legacy import support - these should be updated to import from shared.py instead
__all__ = [
    'User', 'Product', 'Purchase', 'Achievement', 'UserAchievement',
    'EconomySettings', 'RoleAssignment', 'DownloadToken', 'db'
]