#!/usr/bin/env python3
"""
Test script for database builder CLI integration.
"""

import sys
import subprocess
from pathlib import Path

def test_help_command():
    """Test that help command includes database builder options."""
    print("Testing help command...")
    
    result = subprocess.run([
        sys.executable, "main.py", "--help"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Help command failed with return code {result.returncode}")
        print(f"Error: {result.stderr}")
        return False
    
    # Check if database builder options are present
    help_text = result.stdout
    required_options = [
        "--build-database",
        "--wiki-url",
        "--databases-dir",
        "--rate-limit",
        "--skip-images"
    ]
    
    missing_options = []
    for option in required_options:
        if option not in help_text:
            missing_options.append(option)
    
    if missing_options:
        print(f"❌ Missing database builder options in help: {missing_options}")
        return False
    
    print("✅ Help command includes database builder options")
    return True

def test_database_builder_dry_run():
    """Test database builder with dry run (should fail gracefully)."""
    print("Testing database builder argument parsing...")
    
    # Test with invalid arguments to check parsing
    result = subprocess.run([
        sys.executable, "main.py", 
        "--build-database", 
        "--rate-limit", "1.0",
        "--timeout", "10",
        "--skip-images",
        "--quiet"
    ], capture_output=True, text=True)
    
    # We expect this to fail due to network issues, but argument parsing should work
    print(f"Database builder return code: {result.returncode}")
    
    if "Error: Database build failed" in result.stderr or "Starting database build process" in result.stdout:
        print("✅ Database builder arguments parsed correctly")
        return True
    else:
        print(f"❌ Unexpected output from database builder")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        return False

def main():
    """Run all tests."""
    print("Testing Database Builder CLI Integration")
    print("=" * 50)
    
    tests = [
        test_help_command,
        test_database_builder_dry_run
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())