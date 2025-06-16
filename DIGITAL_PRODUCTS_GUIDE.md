# Digital Products System Guide

## Overview
The digital products system has been enhanced with two main categories:
1. **Discord Roles** - Automatically assigned roles upon purchase
2. **Minecraft Skins** - Downloadable skin files with secure delivery

## Features Added

### 1. Enhanced Digital Templates Page
- **Category Tabs**: Organized interface with Discord Roles, Minecraft Skins, and Other Digital categories
- **Visual Templates**: Pre-made skin templates with preview images
- **File Upload**: Direct upload capability for custom skins

### 2. Discord Roles Category
- Create role-based products that automatically assign Discord roles
- Discord-style dropdown for role selection
- Role preview with color and position information
- Auto-generated product descriptions based on role properties

### 3. Minecraft Skins Category
- **6 Featured Templates**:
  - 🎮 Premium Skin Pack (300 pitchforks) - ZIP with 5 skins
  - 🗡️ Medieval Knight (150 pitchforks) - Single PNG
  - 🧙‍♂️ Wizard Collection (200 pitchforks) - ZIP collection
  - 🦸‍♀️ Superhero Pack (250 pitchforks) - ZIP with capes
  - 🎨 Custom Commission (400 pitchforks) - Manual delivery
  - 🐺 Animal Pack (175 pitchforks) - ZIP with animal themes

### 4. Secure Download System
- **Download Tokens**: Unique, time-limited download links
- **Expiration**: 24-hour download window for security
- **Download Tracking**: Monitors download attempts and counts
- **Direct File Delivery**: Files download directly to user's device

## How It Works

### For Administrators:

#### Creating Discord Role Products:
1. Go to Admin Panel → Digital Templates
2. Select "Discord Roles" tab
3. Choose a role from the dropdown
4. Set product name and price
5. Add description (optional - auto-generated if empty)
6. Click "Create Role Product"

#### Creating Minecraft Skin Products:
1. Go to Admin Panel → Digital Templates
2. Select "Minecraft Skins" tab
3. Choose from featured templates OR upload custom skin
4. Click "Create" on desired template
5. Product is automatically created with proper delivery settings

#### File Management:
1. Go to Admin Panel → File Manager
2. Upload skin files (.png or .zip)
3. Files are automatically organized into subdirectories:
   - `skins/` - Minecraft skin files
   - `content/` - Other digital content
   - `documents/` - PDF, DOC files

### For Users:

#### Purchasing Minecraft Skins:
1. Browse products in main store
2. Purchase skin product with pitchforks
3. Receive instant download link (for auto-delivery items)
4. Access downloads from "My Purchases" page

#### Downloading Skins:
1. Go to "My Purchases" from user menu
2. Find completed skin purchases
3. Click "Download Skin" button
4. File downloads directly to device
5. Download link expires in 24 hours

## File Structure

```
static/uploads/skins/
├── README.txt                 # Instructions for admins
├── knight.png                # Sample knight skin
├── premium_pack.zip          # Sample premium pack
├── wizard_collection.zip     # Sample wizard collection
├── superhero_pack.zip        # Sample superhero pack
└── animal_pack.zip           # Sample animal pack
```

## Technical Details

### Database Changes:
- **Product Types**: Added 'minecraft_skin' type
- **Delivery Methods**: Enhanced 'download' method for file delivery
- **Download Tokens**: Secure token system for file access

### Security Features:
- **Token-based Downloads**: Unique tokens prevent unauthorized access
- **Time Expiration**: Downloads expire after 24 hours
- **User Verification**: Only purchase owners can download files
- **File Path Validation**: Prevents directory traversal attacks

### API Enhancements:
- **AJAX Support**: Template creation works with JavaScript
- **JSON Responses**: Better error handling for async requests
- **File Upload**: Proper handling of multipart form data

## Usage Tips

### For Admins:
1. **Test Templates**: Use sample files first to test the system
2. **File Organization**: Keep files organized in appropriate subdirectories
3. **Naming Convention**: Use descriptive, URL-safe filenames
4. **Regular Cleanup**: Monitor and clean up expired download tokens

### For Users:
1. **Download Quickly**: Links expire in 24 hours
2. **Check File Type**: PNG for individual skins, ZIP for collections
3. **Save Locally**: Download to a safe location on your device
4. **Report Issues**: Contact admins if download fails

## Troubleshooting

### Common Issues:
1. **Download Link Expired**: Purchase generates new tokens on completion
2. **File Not Found**: Admin needs to upload the referenced file
3. **Access Denied**: Only purchaser can download their files
4. **Large Files**: ZIP files may take longer to download

### Error Messages:
- "Invalid download link" - Token not found or expired
- "File not found" - Referenced file missing from server
- "Access denied" - User doesn't own the purchase

## Future Enhancements

Possible future additions:
1. **Video Previews**: Add video previews for skin templates
2. **3D Skin Viewer**: Interactive 3D preview of skins
3. **Bulk Downloads**: Download multiple purchases at once
4. **Download Analytics**: Track popular skins and download patterns
5. **User Reviews**: Allow users to rate and review skins

## Support

For technical issues or questions:
1. Check the troubleshooting section above
2. Verify file permissions and upload directory structure
3. Check server logs for detailed error messages
4. Ensure Discord bot has proper permissions for role assignment 