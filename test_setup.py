#!/usr/bin/env python3
"""
Test script to verify the streamlined setup works correctly
"""

import os
import sys
import subprocess
import tempfile
import shutil

def test_setup():
    """Test the auto-setup functionality"""
    print("🧪 Testing streamlined setup...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy main files to temp directory
        shutil.copy('app.py', temp_dir)
        shutil.copy('bot.py', temp_dir)
        shutil.copy('requirements.txt', temp_dir)
        shutil.copytree('cogs', os.path.join(temp_dir, 'cogs'))
        shutil.copytree('templates', os.path.join(temp_dir, 'templates'))
        shutil.copytree('static', os.path.join(temp_dir, 'static'))
        
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            print("📁 Testing in temporary directory:", temp_dir)
            
            # Test 1: Check if app creates .env file
            print("\n✅ Test 1: .env file creation")
            result = subprocess.run([sys.executable, '-c', '''
import sys
sys.path.insert(0, ".")
from app import create_env_file
created = create_env_file()
print("ENV_CREATED:", created)
'''], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "ENV_CREATED: True" in result.stdout:
                print("   ✅ .env file created successfully")
            else:
                print("   ❌ Failed to create .env file")
                print("   Error:", result.stderr)
                return False
            
            # Test 2: Check if directories are created
            print("\n✅ Test 2: Directory creation")
            expected_dirs = ['logs', 'static/uploads', 'instance']
            all_dirs_exist = True
            
            for directory in expected_dirs:
                if os.path.exists(directory):
                    print(f"   ✅ {directory} created")
                else:
                    print(f"   ❌ {directory} missing")
                    all_dirs_exist = False
            
            if not all_dirs_exist:
                return False
            
            # Test 3: Check if .env file has correct content
            print("\n✅ Test 3: .env file content")
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    content = f.read()
                    required_vars = ['DISCORD_TOKEN', 'DISCORD_CLIENT_ID', 'DISCORD_CLIENT_SECRET']
                    for var in required_vars:
                        if var in content:
                            print(f"   ✅ {var} present in .env")
                        else:
                            print(f"   ❌ {var} missing from .env")
                            return False
            else:
                print("   ❌ .env file not found")
                return False
            
            print("\n🎉 All tests passed! Setup is working correctly.")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            return False
        finally:
            os.chdir(original_dir)

if __name__ == "__main__":
    success = test_setup()
    sys.exit(0 if success else 1) 