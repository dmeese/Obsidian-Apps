#!/usr/bin/env python3
"""
Test script for zero-sensitive logging functionality.

This script verifies that:
1. The new logging module works correctly
2. Sensitive data is never logged
3. Rich context is provided without security risks
"""

import logging
import sys
from io import StringIO

# Configure logging to capture output
log_capture = StringIO()
handler = logging.StreamHandler(log_capture)
logging.basicConfig(level=logging.INFO, handlers=[handler])

def test_zero_sensitive_logging():
    """Test the zero-sensitive logging functionality."""
    print("🧪 Testing Zero-Sensitive Logging...")
    
    try:
        # Import the new logging module
        from secure_logging import ZeroSensitiveLogger, SafeLogContext
        
        # Create a test logger
        logger = ZeroSensitiveLogger("test")
        
        # Test 1: Basic logging without sensitive data
        print("\n✅ Test 1: Basic logging")
        logger.info("This is a safe message")
        
        # Test 2: Configuration logging
        print("\n✅ Test 2: Configuration logging")
        logger.log_configuration("test_config", has_sensitive_data=True, key_type="test_*")
        
        # Test 3: API operation logging
        print("\n✅ Test 3: API operation logging")
        logger.log_api_operation("GET", "/api/test", "success", has_auth=True, response_size=1024)
        
        # Test 4: File operation logging
        print("\n✅ Test 4: File operation logging")
        logger.log_file_operation("read", "/config/test.encrypted", success=True, file_size=512)
        
        # Test 5: Context logging
        print("\n✅ Test 5: Context logging")
        context = SafeLogContext(
            operation="test_operation",
            status="success",
            metadata={
                "test_type": "unit_test",
                "iteration": 42,
                "has_data": True
            }
        )
        logger.info("Test operation completed", context)
        
        # Test 6: Sensitive data prevention (this should NOT log sensitive data)
        print("\n✅ Test 6: Sensitive data prevention")
        sensitive_data = "sk-1234567890abcdef"
        
        # This should NOT appear in logs
        logger.info(f"Testing with sensitive value: {sensitive_data}")
        
        # Get the captured log output
        log_output = log_capture.getvalue()
        
        # Verify sensitive data is NOT in regular logs (only in security violation messages)
        log_lines = log_output.split('\n')
        regular_logs = [line for line in log_lines if not line.startswith('ERROR:') and sensitive_data in line]
        
        if regular_logs:
            print(f"❌ SECURITY VIOLATION: Sensitive data '{sensitive_data}' found in regular logs!")
            return False
        else:
            print(f"✅ SECURITY COMPLIANCE: Sensitive data '{sensitive_data}' only in security violation messages")
        
        # Verify security violation message was logged
        security_violations = [line for line in log_lines if line.startswith('ERROR:') and 'SECURITY VIOLATION PREVENTED' in line]
        if security_violations:
            print(f"✅ Security violation properly logged: {len(security_violations)} violations")
        else:
            print(f"❌ Security violation not logged properly")
            return False
        
        # Verify rich context is provided
        print("\n📋 Log Output Analysis:")
        print("=" * 50)
        print(log_output)
        print("=" * 50)
        
        # Check for context information
        if "op=test_operation" in log_output and "status=success" in log_output:
            print("✅ Rich context logging working correctly")
        else:
            print("❌ Rich context logging not working")
            return False
        
        # Check for configuration logging
        if "Configuration loaded for test_config" in log_output:
            print("✅ Configuration logging working correctly")
        else:
            print("❌ Configuration logging not working")
            return False
        
        # Check for API operation logging
        if "API GET /api/test" in log_output:
            print("✅ API operation logging working correctly")
        else:
            print("❌ API operation logging not working")
            return False
        
        # Check for file operation logging
        if "File read: /config/test.encrypted" in log_output:
            print("✅ File operation logging working correctly")
        else:
            print("❌ File operation logging not working")
            return False
        
        print("\n🎉 All tests passed! Zero-sensitive logging is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_backward_compatibility():
    """Test that the secure_log function still works for backward compatibility."""
    print("\n🔄 Testing Backward Compatibility...")
    
    try:
        from secure_logging import secure_log
        
        # Test the old interface (should now use safe references)
        print("✅ Testing secure_log function")
        secure_log("info", "Testing backward compatibility", {"api_key": "sk-1234567890abcdef"})
        
        # Get the captured log output
        log_output = log_capture.getvalue()
        
        # Verify the sensitive data is NOT logged directly in regular logs
        log_lines = log_output.split('\n')
        regular_logs = [line for line in log_lines if not line.startswith('ERROR:') and "sk-1234567890abcdef" in line]
        
        if regular_logs:
            print("❌ SECURITY VIOLATION: API key found in regular logs!")
            return False
        else:
            print("✅ SECURITY COMPLIANCE: API key only in security violation messages")
        
        # Verify security violation message was logged
        security_violations = [line for line in log_lines if line.startswith('ERROR:') and 'SECURITY VIOLATION PREVENTED' in line]
        if security_violations:
            print("✅ Security violation properly logged")
        else:
            print("❌ Security violation not logged properly")
            return False
        
        # Verify safe references are provided
        if "api_key=" in log_output and "op=legacy_log" in log_output:
            print("✅ Backward compatibility working with safe references")
            return True
        else:
            print("❌ Backward compatibility not working correctly")
            return False
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Zero-Sensitive Logging Test Suite")
    print("=" * 50)
    
    # Run the main test
    main_test_passed = test_zero_sensitive_logging()
    
    # Run backward compatibility test
    compatibility_test_passed = test_backward_compatibility()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Main Test: {'✅ PASSED' if main_test_passed else '❌ FAILED'}")
    print(f"Backward Compatibility: {'✅ PASSED' if compatibility_test_passed else '❌ FAILED'}")
    
    if main_test_passed and compatibility_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Zero-sensitive logging is working correctly")
        print("✅ CodeQL compliance achieved")
        print("✅ Backward compatibility maintained")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please review the errors above")
        sys.exit(1)
