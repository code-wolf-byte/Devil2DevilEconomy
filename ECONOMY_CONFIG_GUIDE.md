# Economy Configuration System Guide

## Overview

The Economy Configuration System allows administrators to set up role-based bonus points before enabling the economy for the first time. This ensures that users who already have verified or onboarding roles receive appropriate bonus points when the economy is activated.

## Features

### 🎯 Pre-Economy Configuration
- Configure verified role and bonus points before enabling economy
- Select multiple onboarding roles with customizable bonus points
- Preview configuration before applying changes
- Safe validation of point values and role selections

### 🎁 Automatic First-Time Bonuses
- Users with configured roles automatically receive bonus points when economy is enabled
- Prevents duplicate bonuses with tracking flags
- Supports both single verified role and multiple onboarding roles
- Creates user accounts automatically if they don't exist

### 🔧 Admin Interface
- Intuitive web interface for role selection
- Real-time loading of Discord roles with color and hierarchy display
- Configuration preview and validation
- Integration with existing admin panel

## How to Use

### Step 1: Access Economy Configuration
1. Log in to the web interface as an admin
2. Go to **Admin Panel**
3. Click **Economy Config** in the Quick Actions section

### Step 2: Configure Verified Role
1. Select the Discord role that represents verified users
2. Set the bonus points for verified users (default: 200)
3. Preview shows which role is selected and point value

### Step 3: Configure Onboarding Roles
1. Select one or more Discord roles for onboarding completion
2. Set the bonus points for onboarding users (default: 500)
3. Multiple roles can be selected for different onboarding stages

### Step 4: Save and Enable
Choose one of two options:
- **Save Configuration**: Save settings without enabling economy
- **Enable Economy Now**: Save settings and immediately enable the economy system

## Technical Details

### Database Schema

The `EconomySettings` table has been extended with:
```sql
verified_role_id VARCHAR(20)           -- Discord role ID for verified users
onboarding_role_ids TEXT               -- JSON array of Discord role IDs
verified_bonus_points INTEGER          -- Points for verified role (default: 200)
onboarding_bonus_points INTEGER        -- Points for onboarding roles (default: 500)
roles_configured BOOLEAN               -- Whether configuration is complete
```

### First-Time Bonus Logic

When the economy is enabled for the first time:

1. **Verified Role Bonuses**:
   - Finds all members with the configured verified role
   - Awards `verified_bonus_points` to each user
   - Sets `verification_bonus_received = True` to prevent duplicates

2. **Onboarding Role Bonuses**:
   - Iterates through all configured onboarding roles
   - Awards `onboarding_bonus_points` to users with any onboarding role
   - Sets `onboarding_bonus_received = True` to prevent duplicates

3. **User Creation**:
   - Automatically creates database entries for Discord users who don't exist
   - Populates basic user information (ID, username, Discord ID)

### Safety Features

- **Duplicate Prevention**: Tracks bonus awards with database flags
- **Validation**: Ensures point values are within reasonable limits (0-10,000)
- **Role Verification**: Validates Discord roles exist and are accessible
- **Transaction Safety**: Uses database transactions for atomic operations
- **Error Handling**: Comprehensive error logging and user feedback

## Discord Bot Integration

### Modified Economy Command
The `/economy enable` command now:
- Checks if roles are configured before first-time enabling
- Provides helpful error message directing to web configuration
- Enhanced feedback with embed messages
- Automatic first-time bonus distribution

### Example Usage
```
/economy enable
```

**If not configured:**
```
⚠️ Economy Configuration Required

Before enabling the economy for the first time, please configure 
the roles and bonuses using the web interface:
Go to Admin Panel → Economy Config to set up verified and onboarding roles.

This ensures users with existing roles get their bonus points when 
the economy is enabled.
```

**If configured:**
```
✅ Economy System Enabled
The economy system is now active!

🎁 First-Time Bonuses
Bonus points are being awarded to users with configured roles!
```

## Migration and Setup

### Database Migration
Run the migration script to update your database:
```bash
python update_economy_settings.py
```

This will:
- Add new columns to the EconomySettings table
- Create default configuration values
- Preserve existing economy data where possible

### Configuration Files
No changes needed to environment variables or configuration files. The system uses the existing Discord bot connection and database.

## Best Practices

### Role Selection
- **Verified Role**: Choose a role that clearly indicates verified/trusted users
- **Onboarding Roles**: Select roles representing different stages of user onboarding
- **Avoid Bot Roles**: The system automatically skips bots, but avoid selecting bot-specific roles

### Point Values
- **Verified Bonus**: Moderate reward for basic verification (recommended: 100-300)
- **Onboarding Bonus**: Higher reward for completing onboarding (recommended: 300-700)
- **Balance**: Consider your economy's scale and other earning methods

### Timing
- Configure roles **before** your first economy enable
- Test with a small group of trusted users first
- Monitor for any issues and adjust point values as needed

## Troubleshooting

### Common Issues

**"Economy Configuration Required" Error**
- Solution: Complete the economy configuration in the web interface before enabling

**"Failed to load Discord roles" Error**
- Check Discord bot permissions
- Ensure bot is connected to the correct server
- Verify bot has "View Roles" permission

**Bonuses Not Awarded**
- Check that users actually have the configured roles
- Verify bot can see guild members (needs "Server Members Intent")
- Check logs for specific error messages

**Database Errors**
- Run the migration script: `python update_economy_settings.py`
- Check database file permissions
- Verify database path in configuration

### Logs and Debugging

The system provides detailed logging:
- Web interface actions logged to `economy_app.log`
- Discord bot actions logged to console and `economy_bot.log`
- First-time bonus distribution logged with user counts and success/failure status

## API Reference

### Web Routes

#### `GET /admin/economy-config`
Display the economy configuration page.

#### `POST /admin/economy-config`
Process economy configuration form.

**Form Parameters:**
- `action`: "save_config" or "enable_economy"
- `verified_role_id`: Discord role ID for verified users
- `onboarding_role_ids[]`: Array of Discord role IDs for onboarding
- `verified_bonus_points`: Integer (0-10000)
- `onboarding_bonus_points`: Integer (0-10000)

#### `GET /admin/get-discord-roles`
Returns JSON array of available Discord roles.

**Response:**
```json
{
  "roles": [
    {
      "id": "123456789",
      "name": "Verified",
      "color": "#00ff00",
      "position": 5,
      "permissions": 0,
      "assignable": true
    }
  ]
}
```

### Database Models

#### EconomySettings Properties
- `verified_role_id`: String - Discord role ID
- `onboarding_role_ids`: String - JSON array of role IDs
- `verified_bonus_points`: Integer - Points for verified role
- `onboarding_bonus_points`: Integer - Points for onboarding roles
- `roles_configured`: Boolean - Configuration completion status

#### Helper Methods
- `onboarding_roles_list`: Property returning parsed list of onboarding role IDs
- `set_onboarding_roles(role_ids)`: Method to set onboarding roles from list

## Future Enhancements

Potential improvements for future versions:
- Role-specific point values (different points for different onboarding roles)
- Time-based bonus multipliers
- Bulk bonus operations for existing users
- Advanced role hierarchy support
- Configuration templates for common setups
- Bonus reversal/adjustment tools

## Support

For issues with the Economy Configuration System:
1. Check this guide and troubleshooting section
2. Review application logs for error details
3. Verify Discord bot permissions and connectivity
4. Test configuration with a small group first

The system is designed to be safe and reversible - configuration can be changed and re-applied as needed. 