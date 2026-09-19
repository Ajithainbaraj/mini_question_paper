#!/usr/bin/env python3
"""
Test script to verify login validation is working correctly.
This checks if existing accounts can be validated.
"""

import json
import hashlib

# Load users from file
def _load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ users.json not found!")
        return {}

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _check_pw(password: str, hashed: str) -> bool:
    return _hash_pw(password) == hashed

print("=" * 70)
print("🔐 TESTING LOGIN VALIDATION")
print("=" * 70)
print()

# Load existing users
users = _load_users()

if not users:
    print("❌ No users found in users.json!")
    exit(1)

print(f"✅ Found {len(users)} accounts in users.json:")
print()
for username in users.keys():
    print(f"   • {username}")
print()
print("=" * 70)
print()

# Test default accounts
test_accounts = [
    ("admin", "admin123"),
    ("student", "student123"),
]

print("🧪 Testing Default Accounts:")
print("-" * 70)
print()

all_valid = True

for username, password in test_accounts:
    print(f"Testing: {username} / {password}")
    
    if username in users:
        stored_hash = users[username]
        input_hash = _hash_pw(password)
        is_valid = _check_pw(password, stored_hash)
        
        print(f"   Stored hash : {stored_hash[:40]}...")
        print(f"   Input hash  : {input_hash[:40]}...")
        print(f"   Match       : {'✅ YES' if is_valid else '❌ NO'}")
        
        if is_valid:
            print(f"   ✅ Login would succeed for '{username}'")
        else:
            print(f"   ❌ Login would FAIL for '{username}' (password mismatch)")
            all_valid = False
    else:
        print(f"   ❌ Account '{username}' NOT FOUND in users.json")
        all_valid = False
    
    print()

print("=" * 70)
print()

# Test other existing accounts
other_accounts = [u for u in users.keys() if u not in ["admin", "student"]]

if other_accounts:
    print("📋 Other Accounts Found:")
    print("-" * 70)
    for username in other_accounts:
        print(f"   • {username} (hash: {users[username][:20]}...)")
    print()
    print("   Note: You need to know their passwords to test validation")
    print()
    print("=" * 70)
    print()

# Final result
if all_valid:
    print("🎉 SUCCESS! All default accounts are valid!")
    print()
    print("✅ Login validation is working correctly")
    print()
    print("You can log in with:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("   OR")
    print()
    print("   Username: student")
    print("   Password: student123")
    print()
else:
    print("❌ FAILURE! Some accounts have issues")
    print()
    print("Possible causes:")
    print("1. Password hashing mismatch")
    print("2. users.json corrupted")
    print("3. Accounts not properly initialized")
    print()
    print("Try deleting users.json and restarting the app to regenerate defaults")
    print()

print("=" * 70)
print()

# Test the login logic step by step
print("🔍 Detailed Login Logic Test:")
print("-" * 70)
print()

test_user = "admin"
test_pass = "admin123"

print(f"1. User enters: username='{test_user}', password='{test_pass}'")
print()

print("2. Load users from users.json...")
users = _load_users()
print(f"   ✅ Loaded {len(users)} users")
print()

print(f"3. Check if '{test_user}' exists in users...")
if test_user in users:
    print(f"   ✅ User '{test_user}' found")
else:
    print(f"   ❌ User '{test_user}' NOT found")
    exit(1)
print()

print(f"4. Hash the entered password...")
entered_hash = _hash_pw(test_pass)
print(f"   Password hash: {entered_hash[:40]}...")
print()

print(f"5. Compare with stored hash...")
stored_hash = users[test_user]
print(f"   Stored hash: {stored_hash[:40]}...")
print()

print(f"6. Check if hashes match...")
if _check_pw(test_pass, stored_hash):
    print(f"   ✅ MATCH! Login would succeed")
    print()
    print("   → Session['logged_in'] = True")
    print(f"   → Session['username'] = '{test_user}'")
    print("   → Redirect to home page")
else:
    print(f"   ❌ NO MATCH! Login would fail")
    print()
    print("   → Show error: 'Invalid username or password'")

print()
print("=" * 70)
print()
print("✅ Login validation test complete!")
print()
print("To test in browser:")
print("1. Start the app: python app.py")
print("2. Go to: http://localhost:5000/login")
print("3. Try logging in with: admin / admin123")
print()
