#!/usr/bin/env python3
"""
Test runner for FelixGPT unit tests
Runs all unit tests and provides detailed coverage and pass rate information
"""

import unittest
import sys
import os
from io import StringIO
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_test_suite(test_module_name, component_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"TESTING: {component_name}")
    print(f"Module: {test_module_name}")
    print(f"{'='*60}")
    
    # Capture test output
    test_output = StringIO()
    
    # Load and run the test suite
    loader = unittest.TestLoader()
    start_time = time.time()
    
    try:
        # Import the test module
        test_module = __import__(f'tests.unit.{test_module_name}', fromlist=[test_module_name])
        
        # Load tests from the module
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(
            stream=test_output, 
            verbosity=2, 
            buffer=True
        )
        result = runner.run(suite)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Get test output
        output = test_output.getvalue()
        
        # Calculate pass rate
        total_tests = result.testsRun
        failed_tests = len(result.failures)
        error_tests = len(result.errors)
        passed_tests = total_tests - failed_tests - error_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Print results
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Duration: {duration:.2f}s")
        
        # Print failures and errors if any
        if result.failures:
            print(f"\n{'-'*40}")
            print("FAILURES:")
            print(f"{'-'*40}")
            for test, traceback in result.failures:
                print(f"\nFAILED: {test}")
                print(f"Traceback:\n{traceback}")
        
        if result.errors:
            print(f"\n{'-'*40}")
            print("ERRORS:")
            print(f"{'-'*40}")
            for test, traceback in result.errors:
                print(f"\nERROR: {test}")
                print(f"Traceback:\n{traceback}")
        
        # Show detailed test output for verbose mode
        print(f"\n{'-'*40}")
        print("DETAILED TEST OUTPUT:")
        print(f"{'-'*40}")
        print(output)
        
        return {
            'component': component_name,
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'errors': error_tests,
            'pass_rate': pass_rate,
            'duration': duration,
            'success': failed_tests == 0 and error_tests == 0
        }
        
    except ImportError as e:
        print(f"ERROR: Could not import test module {test_module_name}")
        print(f"Error: {e}")
        return {
            'component': component_name,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'pass_rate': 0.0,
            'duration': 0.0,
            'success': False,
            'import_error': str(e)
        }
    except Exception as e:
        print(f"ERROR: Unexpected error running tests for {component_name}")
        print(f"Error: {e}")
        return {
            'component': component_name,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'pass_rate': 0.0,
            'duration': 0.0,
            'success': False,
            'unexpected_error': str(e)
        }

def print_test_scenarios():
    """Print the test scenarios for each component"""
    print("\n" + "="*80)
    print("TEST SCENARIOS OVERVIEW")
    print("="*80)
    
    scenarios = {
        "Settings Management (models/settings.py)": [
            "1. Default settings generation and structure validation",
            "2a. Load settings when file doesn't exist - should return defaults", 
            "2b. Load settings with corrupted JSON - should return defaults",
            "2c. Load settings with valid JSON file",
            "3a. Successfully save settings to file",
            "3b. Handle IO error during save operation",
            "4a. Merge nested dictionaries correctly",
            "4b. Merge settings with completely new keys", 
            "5a. Get enabled providers in correct priority order",
            "5b. Get enabled providers when all are disabled",
            "6a. Budget check when tracking is disabled",
            "6b. Budget check within reasonable limit", 
            "6c. Budget check exceeding reasonable limit",
            "7a. Generate UI classes from settings",
            "7b. Generate UI classes with missing ui_settings",
            "8a. Extract model configuration from settings",
            "8b. Get model config when models key is missing"
        ],
        
        "Cost Tracking (models/cost_tracker.py)": [
            "1a. Cost estimation for OpenAI GPT-4",
            "1b. Cost estimation for Anthropic Claude", 
            "1c. Cost estimation for Google Gemini",
            "1d. Cost estimation for unknown provider/model",
            "2a. Token estimation for simple message",
            "2b. Token estimation with context",
            "2c. Token estimation for empty message",
            "3a. Record costs and verify daily aggregation",
            "3b. Record costs and verify monthly aggregation", 
            "3c. Record costs and verify total aggregation",
            "4a. Budget validation within limits",
            "4b. Budget validation exceeding daily limit",
            "4c. Budget validation exceeding monthly limit",
            "5a. Load costs when file doesn't exist",
            "5b. Load costs with corrupted JSON file",
            "5c. Verify costs are persisted to file",
            "5d. Handle IO errors during save",
            "6a. Clean up old daily cost data",
            "6b. Clean up with boundary date (exactly 90 days)",
            "7a. Generate comprehensive cost summary",
            "7b. Generate cost summary with no data",
            "8a. Get spending for specific date",
            "8b. Get spending for date with no data", 
            "8c. Get spending for specific month",
            "9. Verify costs are properly isolated by provider"
        ],
        
        "LLM Orchestration (models/llm_clients.py)": [
            "1. Orchestrator initialization and client setup",
            "2a. Update settings changes Google model",
            "3a. Get enabled providers when all are enabled",
            "3b. Get enabled providers when some are disabled", 
            "3c. Get enabled providers with custom priorities",
            "4a. Budget checking when disabled",
            "4b. Budget checking when enabled",
            "5a. Chat with all providers in parallel mode",
            "5b. Chat with all providers in sequential mode",
            "5c. Chat with smart routing stops at first success",
            "5d. Chat with no enabled providers",
            "6a. Successful OpenAI API call",
            "6b. OpenAI API call with error",
            "7a. Successful Anthropic API call",
            "7b. Anthropic API call with error", 
            "8a. Successful Google API call",
            "8b. Google API call with error",
            "9. Call unknown provider",
            "10a. Budget checking prevents expensive requests",
            "10b. Budget checking allows reasonable requests",
            "11. Context preparation respects limit",
            "12. Response settings are passed to API calls"
        ]
    }
    
    for component, test_scenarios in scenarios.items():
        print(f"\n{component}:")
        print("-" * len(component))
        for scenario in test_scenarios:
            print(f"  • {scenario}")

def main():
    """Main test runner"""
    print("FelixGPT Unit Test Suite")
    print("="*60)
    
    # Print test scenarios
    print_test_scenarios()
    
    # Test components to run
    test_components = [
        ('test_settings', 'Settings Management'),
        ('test_cost_tracker', 'Cost Tracking'),
        ('test_llm_clients', 'LLM Orchestration')
    ]
    
    # Run all test suites
    total_start_time = time.time()
    results = []
    
    for test_module, component_name in test_components:
        result = run_test_suite(test_module, component_name)
        results.append(result)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*80}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    overall_total = 0
    overall_passed = 0
    overall_failed = 0
    overall_errors = 0
    
    for result in results:
        print(f"\n{result['component']}:")
        print(f"  Tests: {result['total']}")
        print(f"  Passed: {result['passed']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Pass Rate: {result['pass_rate']:.1f}%")
        print(f"  Duration: {result['duration']:.2f}s")
        print(f"  Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
        
        overall_total += result['total']
        overall_passed += result['passed']
        overall_failed += result['failed']
        overall_errors += result['errors']
    
    overall_pass_rate = (overall_passed / overall_total * 100) if overall_total > 0 else 0
    
    print(f"\n{'-'*40}")
    print("OVERALL RESULTS:")
    print(f"{'-'*40}")
    print(f"Total Tests: {overall_total}")
    print(f"Total Passed: {overall_passed}")
    print(f"Total Failed: {overall_failed}")
    print(f"Total Errors: {overall_errors}")
    print(f"Overall Pass Rate: {overall_pass_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    
    # Determine overall success
    overall_success = overall_failed == 0 and overall_errors == 0
    print(f"Overall Status: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    # Exit code
    sys.exit(0 if overall_success else 1)

if __name__ == '__main__':
    main()