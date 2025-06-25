# Troubleshooting Guide: Deposit Check, Daily Engagement & Campus Photo Functions

## Problem: Custom Emoji Reward Functions Not Working

If the deposit check, daily engagement, and campus photo functions aren't working, follow these steps:

### 1. **Check Economy System Status**
First, verify the economy system is enabled:
```
/economy enable
```
(Admin only command)

### 2. **Verify Custom Emojis Are Created**
You need to create these exact custom emojis in your Discord server:

**Required Emojis:**
- `:campus_photo:` - For campus picture approval
- `:daily_engage:` - For daily engagement approval  
- `:deposit_check:` - For enrollment deposit approval

**How to create custom emojis:**
1. Go to Server Settings → Emoji → Upload Emoji
2. Upload images for each emoji
3. Name them exactly as shown above (no variations)
4. Ensure they're available to all server members

### 3. **Admin Permission Check**
The admin reacting must have **Administrator** permissions in the server.

### 4. **How the System Works**

**Daily Engagement:**
- User posts any message in Discord
- Admin reacts with `:daily_engage:` emoji
- User gets 25 pitchforks (20-hour cooldown)
- Maximum 365 approvals per user

**Campus Photos:**
- User posts a message with image attachments
- Admin reacts with `:campus_photo:` emoji
- User gets 100 pitchforks
- Maximum 5 approvals per user

**Deposit Check:**
- User posts about enrollment deposit
- Admin reacts with `:deposit_check:` emoji
- User gets 500 pitchforks (one-time bonus)

### 5. **Testing Steps**

1. **Test Daily Engagement:**
   ```
   1. User posts: "Hello everyone!"
   2. Admin reacts with :daily_engage: emoji
   3. User should receive DM with 25 pitchforks
   4. Message gets ✅ confirmation reaction
   ```

2. **Test Campus Photos:**
   ```
   1. User posts message with image attachment
   2. Admin reacts with :campus_photo: emoji
   3. User should receive DM with 100 pitchforks
   4. Message gets ✅ confirmation reaction
   ```

3. **Test Deposit Check:**
   ```
   1. User posts about enrollment deposit
   2. Admin reacts with :deposit_check: emoji
   3. User should receive DM with 500 pitchforks
   4. Message gets ✅ confirmation reaction
   ```

### 6. **Common Issues & Solutions**

**Issue:** No reaction or points awarded
**Solution:** 
- Check that custom emojis exist with exact names
- Verify admin has administrator permissions
- Confirm economy system is enabled

**Issue:** Error messages in logs
**Solution:**
- Check database connection
- Restart the bot application
- Verify .env file configuration

**Issue:** Users not receiving DMs
**Solution:**
- This is normal - system falls back to replying in channel
- Users can check balance with `/balance` command

### 7. **Debugging Commands**

**Check user limits:**
```
/limits
```
Shows remaining approvals for each category

**Check economy status:**
```
/balance
```
Shows current pitchfork balance

**Admin check user status:**
```
/give @user 1
```
Tests if admin commands work

### 8. **Environment Variables**
Ensure these are set in your `.env` file:
```
GENERAL_CHANNEL_ID=your_general_channel_id_here
DISCORD_TOKEN=your_discord_bot_token_here
```

### 9. **Restart Required**
After making changes to:
- Custom emojis
- .env file
- Code changes

Restart the bot application:
```bash
python app.py
```

### 10. **Log Files**
Check these files for error messages:
- `logs/economy_app.log`
- `logs/economy_errors.log`

### 11. **Testing Checklist**
- [ ] Economy system enabled (`/economy enable`)
- [ ] Custom emojis created with exact names
- [ ] Admin has administrator permissions
- [ ] Bot has permission to send messages and add reactions
- [ ] User hasn't reached maximum limits
- [ ] Database is properly connected
- [ ] Bot application is running without errors

### 12. **Still Not Working?**
If issues persist:
1. Check bot logs for error messages
2. Verify database connections
3. Test with a fresh user account
4. Ensure bot has proper permissions in Discord server
5. Try restarting the entire application

### 13. **Quick Fix Script**
Run this to test the system:
```python
# Test script - run in Discord
# 1. Post a message with an image
# 2. Admin react with :campus_photo:
# 3. Should see confirmation reaction ✅
# 4. User should get DM or channel reply
``` 