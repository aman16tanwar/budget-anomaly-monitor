#!/usr/bin/env python3
"""
Test script for Unified Budget Monitoring Job
Tests the core logic without external API calls
"""
import os
import sys
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_smart_thresholds():
    """Test the smart threshold logic"""
    print("🧠 Testing Smart Threshold Logic...")
    
    # Mock Google Ads Budget Monitor
    try:
        from google_ads_budget_monitor import GoogleAdsBudgetMonitor
        
        # Create monitor instance (will fail on API init, but we can test methods)
        try:
            monitor = GoogleAdsBudgetMonitor()
        except Exception:
            # Create a mock instance for testing the logic
            monitor = Mock(spec=GoogleAdsBudgetMonitor)
            # Add the actual method implementations
            from google_ads_budget_monitor import GoogleAdsBudgetMonitor as GAM
            monitor.get_smart_thresholds = GAM.get_smart_thresholds.__get__(monitor)
            monitor.calculate_financial_impact = GAM.calculate_financial_impact.__get__(monitor)
            monitor.get_new_campaign_threshold = GAM.get_new_campaign_threshold.__get__(monitor)
        
        # Test cases for smart thresholds
        test_cases = [
            # Daily budgets
            {"budget": 25.0, "type": "STANDARD", "expected_warning": 5.0, "expected_critical": 10.0, "category": "Small Daily"},
            {"budget": 100.0, "type": "STANDARD", "expected_warning": 3.0, "expected_critical": 5.0, "category": "Medium Daily"},
            {"budget": 500.0, "type": "STANDARD", "expected_warning": 2.0, "expected_critical": 3.0, "category": "Large Daily"},
            {"budget": 2000.0, "type": "STANDARD", "expected_warning": 1.5, "expected_critical": 2.0, "category": "Enterprise Daily"},
            
            # Monthly budgets
            {"budget": 800.0, "type": "ACCELERATED", "expected_warning": 2.0, "expected_critical": 3.0, "category": "Small Monthly"},
            {"budget": 5000.0, "type": "ACCELERATED", "expected_warning": 1.3, "expected_critical": 1.8, "category": "Large Monthly"},
        ]
        
        print("🎯 Smart Threshold Test Results:")
        all_passed = True
        
        for i, case in enumerate(test_cases):
            try:
                thresholds = monitor.get_smart_thresholds(case["budget"], case["type"])
                
                warning_match = thresholds["warning"] == case["expected_warning"]
                critical_match = thresholds["critical"] == case["expected_critical"]
                
                status = "✅ PASS" if (warning_match and critical_match) else "❌ FAIL"
                if not (warning_match and critical_match):
                    all_passed = False
                
                print(f"  {i+1}. {case['category']} (${case['budget']}/day): {status}")
                print(f"     Expected: W={case['expected_warning']}x, C={case['expected_critical']}x")
                print(f"     Got:      W={thresholds['warning']}x, C={thresholds['critical']}x")
                
            except Exception as e:
                print(f"  {i+1}. {case['category']}: ❌ ERROR - {e}")
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Cannot import google_ads_budget_monitor: {e}")
        return False

def test_financial_impact():
    """Test financial impact calculations"""
    print("\n💰 Testing Financial Impact Calculations...")
    
    try:
        from google_ads_budget_monitor import GoogleAdsBudgetMonitor
        
        # Create mock monitor for testing
        monitor = Mock(spec=GoogleAdsBudgetMonitor)
        from google_ads_budget_monitor import GoogleAdsBudgetMonitor as GAM
        monitor.calculate_financial_impact = GAM.calculate_financial_impact.__get__(monitor)
        
        test_cases = [
            # Daily budget increases
            {"previous": 100, "current": 200, "type": "STANDARD", "expected_impact": 3000, "expected_level": "MEDIUM"},
            {"previous": 500, "current": 1000, "type": "STANDARD", "expected_impact": 15000, "expected_level": "HIGH"},
            {"previous": 10, "current": 30, "type": "STANDARD", "expected_impact": 600, "expected_level": "LOW"},
            {"previous": 5, "current": 10, "type": "STANDARD", "expected_impact": 150, "expected_level": "MINIMAL"},
            
            # Monthly budget increases
            {"previous": 2000, "current": 5000, "type": "ACCELERATED", "expected_impact": 3000, "expected_level": "MEDIUM"},
            {"previous": 5000, "current": 20000, "type": "ACCELERATED", "expected_impact": 15000, "expected_level": "HIGH"},
        ]
        
        print("💸 Financial Impact Test Results:")
        all_passed = True
        
        for i, case in enumerate(test_cases):
            try:
                impact = monitor.calculate_financial_impact(case["previous"], case["current"], case["type"])
                
                impact_match = abs(impact["monthly_impact"] - case["expected_impact"]) < 1
                level_match = impact["impact_level"] == case["expected_level"]
                
                status = "✅ PASS" if (impact_match and level_match) else "❌ FAIL"
                if not (impact_match and level_match):
                    all_passed = False
                
                budget_type = "daily" if case["type"] == "STANDARD" else "monthly"
                print(f"  {i+1}. ${case['previous']} → ${case['current']} ({budget_type}): {status}")
                print(f"     Expected: ${case['expected_impact']}/month, {case['expected_level']}")
                print(f"     Got:      ${impact['monthly_impact']:.0f}/month, {impact['impact_level']}")
                
            except Exception as e:
                print(f"  {i+1}. Test case: ❌ ERROR - {e}")
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"❌ Cannot import google_ads_budget_monitor: {e}")
        return False

def test_environment_setup():
    """Test if environment variables are properly set"""
    print("\n🔧 Testing Environment Setup...")
    
    required_vars = [
        'META_BUSINESS_ID',
        'META_ACCESS_TOKEN', 
        'GCP_PROJECT_ID',
        'GOOGLE_CHAT_WEBHOOK_URL',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_LOGIN_CUSTOMER_ID',
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_REFRESH_TOKEN'
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value.strip():
            present_vars.append(var)
        else:
            missing_vars.append(var)
    
    print(f"✅ Present variables ({len(present_vars)}/{len(required_vars)}):")
    for var in present_vars:
        value = os.getenv(var)
        # Mask sensitive values
        if 'TOKEN' in var or 'SECRET' in var or 'KEY' in var:
            display_value = value[:10] + "..." if len(value) > 10 else value
        else:
            display_value = value
        print(f"  - {var}: {display_value}")
    
    if missing_vars:
        print(f"\n❌ Missing variables ({len(missing_vars)}):")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def test_import_dependencies():
    """Test if all required modules can be imported"""
    print("\n📦 Testing Import Dependencies...")
    
    required_modules = [
        ('google_ads_budget_monitor', 'google_ads_budget_monitor'),
        ('meta_api_implementation_bigquery', 'meta_api_implementation_bigquery'),
        ('unified_chat_alerts', 'unified_chat_alerts'),
        ('dotenv', 'python-dotenv'),
        ('datetime', 'built-in'),
        ('logging', 'built-in'),
        ('os', 'built-in'),
        ('sys', 'built-in'),
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            successful_imports.append(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            failed_imports.append((module_name, package_name, str(e)))
            print(f"  ❌ {module_name} ({package_name}): {e}")
    
    print(f"\nImport Results: {len(successful_imports)}/{len(required_modules)} successful")
    
    if failed_imports:
        print("\n⚠️ Failed imports may cause runtime errors.")
        return False
    else:
        print("\n✅ All required modules can be imported!")
        return True

def test_file_structure():
    """Test if all required files are present"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        'unified_budget_monitoring_job.py',
        'google_ads_budget_monitor.py',
        'meta_api_implementation_bigquery.py',
        'unified_chat_alerts.py',
        '.env',
        'meta.json',
        'googleads.json',
        'requirements.txt',
        'customer_clients.csv'
    ]
    
    present_files = []
    missing_files = []
    
    for file_name in required_files:
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            present_files.append((file_name, file_size))
            print(f"  ✅ {file_name} ({file_size} bytes)")
        else:
            missing_files.append(file_name)
            print(f"  ❌ {file_name}")
    
    print(f"\nFile Structure: {len(present_files)}/{len(required_files)} files present")
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    else:
        print("\n✅ All required files are present!")
        return True

def main():
    """Run all tests"""
    print("🚀 Testing Unified Budget Monitoring System")
    print("=" * 60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️ python-dotenv not available, using system environment")
    except Exception as e:
        print(f"⚠️ Error loading .env file: {e}")
    
    # Run tests
    results = {
        'File Structure': test_file_structure(),
        'Environment Setup': test_environment_setup(), 
        'Import Dependencies': test_import_dependencies(),
        'Smart Thresholds': test_smart_thresholds(),
        'Financial Impact': test_financial_impact()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for deployment.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please address issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)