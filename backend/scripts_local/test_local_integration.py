#!/usr/bin/env python3
"""
Integration test suite for Vecinita local development environment.
Tests database connectivity, API endpoints, and full-stack functionality.
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path
from typing import Optional

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text: str):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    print(f"{BLUE}→ {text}{RESET}")

class IntegrationTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.env_file = Path("/workspaces/vecinita/.env")
        self.docker_compose_file = Path("/workspaces/vecinita/docker-compose.yml")
        
    def run_all_tests(self):
        """Run all integration tests"""
        print_header("VECINITA LOCAL DEVELOPMENT INTEGRATION TESTS")
        
        try:
            self.test_environment_setup()
            self.test_docker_services()
            self.test_database_connectivity()
            self.test_postgrest_api()
            self.test_api_endpoints()
            self.test_data_persistence()
            
        except Exception as e:
            print_error(f"Test suite error: {str(e)}")
            return False
        
        print_header("TEST SUMMARY")
        total = self.tests_passed + self.tests_failed
        print(f"Total Tests: {total}")
        print_success(f"Passed: {self.tests_passed}")
        if self.tests_failed > 0:
            print_error(f"Failed: {self.tests_failed}")
        
        return self.tests_failed == 0
    
    def test_environment_setup(self):
        """Test 1: Verify environment files and configuration"""
        print_header("TEST 1: Environment Setup")
        
        # Check .env file exists
        if not self.env_file.exists():
            print_error(".env file not found")
            self.tests_failed += 1
            return
        print_success(".env file exists")
        self.tests_passed += 1
        
        # Check environment variables
        env_vars = ["SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY"]
        with open(self.env_file) as f:
            env_content = f.read()
        
        for var in env_vars:
            if var in env_content:
                print_success(f"Environment variable {var} is configured")
                self.tests_passed += 1
            else:
                print_warning(f"Environment variable {var} not found")
                self.tests_failed += 1
        
        # Verify local environment
        if "http://localhost:3001" in env_content:
            print_success("Configured for LOCAL Supabase (PostgREST on localhost:3001)")
            self.tests_passed += 1
        else:
            print_warning("Not configured for local development")
    
    def test_docker_services(self):
        """Test 2: Verify Docker services are running"""
        print_header("TEST 2: Docker Services Status")
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(self.docker_compose_file), "ps", "--quiet"],
                capture_output=True,
                text=True,
                cwd="/workspaces/vecinita"
            )
            
            containers = result.stdout.strip().split("\n") if result.stdout.strip() else []
            print_info(f"Found {len(containers)} running containers")
            
            # Check for specific services
            services = {
                "postgres": "vecinita-postgres-local",
                "postgrest": "vecinita-postgrest-local",
                "pgadmin": "vecinita-pgadmin-local"
            }
            
            for service, container_name in services.items():
                status_result = subprocess.run(
                    ["docker", "inspect", "--format={{.State.Running}}", container_name],
                    capture_output=True,
                    text=True
                )
                
                if status_result.returncode == 0 and "true" in status_result.stdout:
                    print_success(f"{service} is running")
                    self.tests_passed += 1
                else:
                    print_error(f"{service} is NOT running")
                    self.tests_failed += 1
                    
        except Exception as e:
            print_error(f"Docker check failed: {str(e)}")
            self.tests_failed += 1
    
    def test_database_connectivity(self):
        """Test 3: Test PostgreSQL database connectivity"""
        print_header("TEST 3: Database Connectivity")
        
        try:
            # Test via docker exec
            result = subprocess.run(
                ["docker", "exec", "vecinita-postgres-local", "pg_isready"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print_success("PostgreSQL is accepting connections")
                self.tests_passed += 1
            else:
                print_error("PostgreSQL connection failed")
                self.tests_failed += 1
            
            # Check tables
            result = subprocess.run(
                ["docker", "exec", "vecinita-postgres-local", "psql", "-U", "postgres", "-d", "postgres", "-c", "\\dt"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            required_tables = ["chat_sessions", "chat_history", "documents"]
            for table in required_tables:
                if table in result.stdout:
                    print_success(f"Table '{table}' exists in database")
                    self.tests_passed += 1
                else:
                    print_error(f"Table '{table}' NOT found in database")
                    self.tests_failed += 1
                    
        except subprocess.TimeoutExpired:
            print_error("Database connectivity check timed out")
            self.tests_failed += 1
        except Exception as e:
            print_error(f"Database check failed: {str(e)}")
            self.tests_failed += 1
    
    def test_postgrest_api(self):
        """Test 4: Test PostgREST REST API"""
        print_header("TEST 4: PostgREST API")
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:3001/", timeout=5)
            if response.status_code == 200:
                print_success("PostgREST API is responding")
                self.tests_passed += 1
            else:
                print_error(f"PostgREST returned status {response.status_code}")
                self.tests_failed += 1
            
            # Test table endpoints
            endpoints = [
                ("chat_sessions", "Chat Sessions"),
                ("chat_history", "Chat History"),
                ("documents", "Documents")
            ]
            
            for endpoint, name in endpoints:
                try:
                    response = requests.get(f"http://localhost:3001/{endpoint}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        print_success(f"{name} API endpoint is accessible (empty array: {isinstance(data, list)})")
                        self.tests_passed += 1
                    else:
                        print_error(f"{name} returned status {response.status_code}")
                        self.tests_failed += 1
                except requests.exceptions.RequestException as e:
                    print_error(f"{name} request failed: {str(e)}")
                    self.tests_failed += 1
                    
        except requests.exceptions.ConnectionError:
            print_error("Cannot connect to PostgREST API at http://localhost:3001")
            self.tests_failed += 1
        except Exception as e:
            print_error(f"PostgREST test failed: {str(e)}")
            self.tests_failed += 1
    
    def test_api_endpoints(self):
        """Test 5: Test Vecinita backend API endpoints"""
        print_header("TEST 5: Vecinita Backend API Endpoints")
        
        try:
            # Try to connect to backend
            response = requests.get("http://localhost:8000/", timeout=3)
            print_success("Backend is running on localhost:8000")
            self.tests_passed += 1
            
            # Test health endpoint
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print_success("Backend /health endpoint is responding")
                self.tests_passed += 1
            
        except requests.exceptions.ConnectionError:
            print_warning("Backend is not running on localhost:8000 (expected if not started)")
            print_info("To start backend: cd backend && uv run -m uvicorn src.agent.main:app --reload")
        except Exception as e:
            print_warning(f"Backend test skipped: {str(e)}")
    
    def test_data_persistence(self):
        """Test 6: Test data persistence in database"""
        print_header("TEST 6: Data Persistence")
        
        try:
            # Query existing data to verify read access
            response = requests.get(
                "http://localhost:3001/chat_sessions",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print_success("Can read from chat_sessions table (returns JSON array)")
                    self.tests_passed += 1
                else:
                    print_warning("Unexpected response format")
                    self.tests_failed += 1
            else:
                print_warning(f"Query returned status {response.status_code}")
                self.tests_failed += 1
                
        except Exception as e:
            print_warning(f"Data persistence test failed: {str(e)}")
            self.tests_failed += 1

def main():
    """Main entry point"""
    tester = IntegrationTester()
    success = tester.run_all_tests()
    
    print_header("RECOMMENDATIONS")
    
    if success:
        print_success("All tests passed! Local development environment is ready.")
        print_info("Next steps:")
        print("  1. Start the backend: cd backend && uv run -m uvicorn src.agent.main:app --reload")
        print("  2. Run the frontend: cd frontend && npm run dev")
        print("  3. Open browser to http://localhost:5173 (or shown URL)")
    else:
        print_error("Some tests failed. Please check the errors above.")
        print_info("Troubleshooting:")
        print("  1. Ensure Docker Desktop is running")
        print("  2. Check docker-compose status: docker-compose -f docker-compose.yml ps")
        print("  3. View service logs: docker-compose -f docker-compose.yml logs")
        print("  4. Reset services: docker-compose -f docker-compose.yml down -v && docker-compose -f docker-compose.yml up -d")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
