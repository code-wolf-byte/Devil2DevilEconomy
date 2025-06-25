#!/usr/bin/env python3
"""
Test script to check Discord bot connection and role fetching
"""
import asyncio
import os
from shared import bot
import dotenv

# Load environment variables
dotenv.load_dotenv()

async def test_bot_connection():
    """Test if the bot can connect and fetch roles"""
    print("Testing Discord bot connection...")
    
    try:
        # Wait for bot to be ready (with timeout)
        max_wait = 10  # seconds
        wait_time = 0
        while not bot.is_ready() and wait_time < max_wait:
            await asyncio.sleep(0.5)
            wait_time += 0.5
            print(f"Waiting for bot to be ready... ({wait_time:.1f}s)")
        
        if not bot.is_ready():
            print("❌ Bot is not ready after waiting")
            return False
        
        print("✅ Bot is ready!")
        
        # Check if bot is in any guilds
        if not bot.guilds:
            print("❌ Bot is not in any Discord servers")
            return False
        
        print(f"✅ Bot is in {len(bot.guilds)} server(s)")
        
        # Get the first guild
        guild = bot.guilds[0]
        print(f"✅ Connected to server: {guild.name} (ID: {guild.id})")
        
        # Check bot's permissions
        print(f"✅ Bot's top role: {guild.me.top_role.name}")
        print(f"✅ Bot can manage roles: {guild.me.guild_permissions.manage_roles}")
        
        # Get all roles
        roles = guild.roles
        print(f"✅ Found {len(roles)} total roles")
        
        # Get manageable roles
        manageable_roles = []
        for role in roles:
            if role.name != '@everyone' and guild.me.top_role > role:
                manageable_roles.append(role)
        
        print(f"✅ Bot can manage {len(manageable_roles)} roles")
        
        # Show some example roles
        for i, role in enumerate(manageable_roles[:5]):
            print(f"  - {role.name} (ID: {role.id}, Position: {role.position})")
        
        if len(manageable_roles) > 5:
            print(f"  ... and {len(manageable_roles) - 5} more roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot connection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_endpoint():
    """Test the Flask endpoint for getting Discord roles"""
    print("\nTesting Flask endpoint...")
    
    try:
        import requests
        
        # Test the endpoint (this will redirect to login, but we can check the response)
        response = requests.get("http://localhost:5000/admin/get-discord-roles", allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ Flask endpoint is working (redirecting to login as expected)")
            return True
        elif response.status_code == 200:
            print("✅ Flask endpoint returned data successfully")
            return True
        else:
            print(f"❌ Flask endpoint returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Flask endpoint: {e}")
        return False

if __name__ == "__main__":
    print("Discord Bot Connection Test")
    print("=" * 40)
    
    # Test bot connection
    success = asyncio.run(test_bot_connection())
    
    if success:
        print("\n✅ Bot connection test passed!")
    else:
        print("\n❌ Bot connection test failed!")
    
    # Test Flask endpoint
    flask_success = test_flask_endpoint()
    
    if flask_success:
        print("✅ Flask endpoint test passed!")
    else:
        print("❌ Flask endpoint test failed!")
    
    print("\nTest completed!") 