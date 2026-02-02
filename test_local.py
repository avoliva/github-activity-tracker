#!/usr/bin/env python3
"""Simple local development test script.

This script starts the server, tests the API endpoints, and verifies everything works.
For local development use only - not part of the main test suite.

Usage:
    python test_local.py [username]

Example:
    python test_local.py octocat
"""

import argparse
import subprocess
import sys
import time
from typing import Optional

import httpx

# Server configuration defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_WAIT_TIME = 30  # Maximum seconds to wait for server to start
CHECK_INTERVAL = 0.5  # Seconds between readiness checks


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def wait_for_server(base_url: str, timeout: int = MAX_WAIT_TIME) -> bool:
    """Wait for server to be ready.

    Args:
        base_url: Base URL of the server
        timeout: Maximum seconds to wait

    Returns:
        True if server is ready, False otherwise
    """
    print_info(f"Waiting for server to start (max {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{base_url}/docs", timeout=2.0, follow_redirects=True)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                print_success(f"Server is ready! (started in {elapsed:.2f}s)")
                return True
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(CHECK_INTERVAL)

    print_error(f"Server did not start within {timeout} seconds")
    return False


def test_user_activity(api_endpoint: str, username: str) -> bool:
    """Test the user activity endpoint.

    Args:
        api_endpoint: Base API endpoint URL
        username: GitHub username to test

    Returns:
        True if test passes, False otherwise
    """
    print_info(f"Testing user activity endpoint for '{username}'...")

    try:
        response = httpx.get(f"{api_endpoint}/{username}/activity", timeout=30.0)

        if response.status_code == 200:
            data = response.json()

            # Verify response structure
            required_fields = ["username", "repositories", "total_repositories", "total_events"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                print_error(f"Response missing required fields: {missing_fields}")
                return False

            if data["username"] != username:
                print_error(f"Username mismatch: expected '{username}', got '{data['username']}'")
                return False

            print_success("User activity retrieved successfully!")
            print_info(f"  Username: {data['username']}")
            print_info(f"  Total repositories: {data['total_repositories']}")
            print_info(f"  Total events: {data['total_events']}")
            print_info(f"  Repositories with activity: {len(data['repositories'])}")

            # Show sample repository data
            if data["repositories"]:
                sample_repo = data["repositories"][0]
                print_info(f"  Sample repository: {sample_repo.get('repository_name', 'N/A')}")
                print_info(f"    Is owner: {sample_repo.get('is_owner', 'N/A')}")
                print_info(f"    Activity types: {len(sample_repo.get('top_activity_types', []))}")

            return True

        elif response.status_code == 404:
            print_warning(f"User '{username}' not found (404)")
            print_info("This is expected if the user doesn't exist on GitHub")
            # Still consider this a success for testing purposes
            return True

        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            # Try to get more details from response
            try:
                error_detail = response.json().get("detail", "No detail provided")
                print_error(f"Error detail: {error_detail}")
            except Exception:
                pass
            return False

    except httpx.TimeoutException:
        print_error("Request timed out")
        return False
    except httpx.RequestError as e:
        print_error(f"Request error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def test_api_docs(base_url: str) -> bool:
    """Test that API documentation is accessible.

    Args:
        base_url: Base URL of the server

    Returns:
        True if docs are accessible, False otherwise
    """
    print_info("Testing API documentation endpoint...")

    try:
        response = httpx.get(f"{base_url}/docs", timeout=5.0, follow_redirects=True)
        if response.status_code == 200:
            print_success("API documentation is accessible")
            return True
        else:
            print_error(f"API docs returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to access API docs: {e}")
        return False


def test_openapi_spec(base_url: str) -> bool:
    """Test that OpenAPI spec is accessible.

    Args:
        base_url: Base URL of the server

    Returns:
        True if spec is accessible, False otherwise
    """
    print_info("Testing OpenAPI specification endpoint...")

    try:
        response = httpx.get(f"{base_url}/openapi.json", timeout=5.0)
        if response.status_code == 200:
            spec = response.json()
            if "openapi" in spec and "paths" in spec:
                print_success("OpenAPI specification is valid")
                print_info(f"  OpenAPI version: {spec.get('openapi', 'N/A')}")
                print_info(f"  API title: {spec.get('info', {}).get('title', 'N/A')}")
                print_info(f"  API version: {spec.get('info', {}).get('version', 'N/A')}")
                print_info(f"  Endpoints: {len(spec.get('paths', {}))}")
                return True
            else:
                print_error("OpenAPI spec missing required fields")
                return False
        else:
            print_error(f"OpenAPI spec returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to access OpenAPI spec: {e}")
        return False


def main() -> int:
    """Main test function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Test the GitHub Activity Tracker API locally")
    parser.add_argument(
        "username", nargs="?", default="octocat", help="GitHub username to test (default: octocat)"
    )
    parser.add_argument(
        "--no-start-server",
        action="store_true",
        help="Don't start the server (assume it's already running)",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )
    parser.add_argument("--debug", action="store_true", help="Show server output for debugging")

    args = parser.parse_args()

    # Set up URLs based on port
    server_host = DEFAULT_HOST
    server_port = args.port
    base_url = f"http://{server_host}:{server_port}"
    api_endpoint = f"{base_url}/api/v1/users"

    print(f"{Colors.BOLD}GitHub Activity Tracker - Local Test Script{Colors.RESET}")
    print("=" * 60)

    server_process: Optional[subprocess.Popen] = None
    server_output: list[str] = []

    def capture_server_output(pipe):
        """Capture server output for error debugging."""
        for line in iter(pipe.readline, ""):
            if line:
                server_output.append(line.strip())

    try:
        # Start server if needed
        if not args.no_start_server:
            print_info(f"Starting server on {server_host}:{server_port}...")
            if args.debug:
                # In debug mode, show server output in real-time
                server_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host",
                        server_host,
                        "--port",
                        str(server_port),
                        "--log-level",
                        "info",
                    ]
                )
            else:
                # Normal mode: capture output for error reporting
                server_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host",
                        server_host,
                        "--port",
                        str(server_port),
                        "--log-level",
                        "info",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

            # Wait for server to be ready
            if not wait_for_server(base_url):
                if server_process:
                    # Read any error output before terminating
                    try:
                        if server_process.stdout:
                            output = server_process.stdout.read()
                            if output:
                                print_error("Server startup output:")
                                print(output[-1000:])  # Last 1000 chars
                    except Exception:
                        pass
                    server_process.terminate()
                    server_process.wait(timeout=5)
                return 1

            # Give server a moment to fully initialize (lifespan, etc.)
            time.sleep(0.5)
        else:
            print_info("Skipping server start (--no-start-server specified)")
            # Quick check that server is running
            try:
                httpx.get(f"{base_url}/docs", timeout=2.0)
                print_success("Server appears to be running")
            except Exception:
                print_error("Server does not appear to be running")
                return 1

        print()
        print(f"{Colors.BOLD}Running API Tests{Colors.RESET}")
        print("-" * 60)

        # Run tests
        tests_passed = 0
        tests_total = 0

        # Test 1: API Documentation
        tests_total += 1
        if test_api_docs(base_url):
            tests_passed += 1
        print()

        # Test 2: OpenAPI Spec
        tests_total += 1
        if test_openapi_spec(base_url):
            tests_passed += 1
        print()

        # Test 3: User Activity Endpoint
        tests_total += 1
        test_result = test_user_activity(api_endpoint, args.username)
        if not test_result and server_process and not args.debug:
            # If test failed, try to read server output
            print()
            print_warning("Attempting to capture server error logs...")
            print("-" * 60)
            try:
                if server_process.stdout:
                    # Try to read any available output
                    import select

                    if hasattr(select, "select"):
                        # Unix-like system
                        ready, _, _ = select.select([server_process.stdout], [], [], 0.1)
                        if ready:
                            output = server_process.stdout.read(2000)
                            if output:
                                for line in output.split("\n")[-10:]:
                                    if line.strip():
                                        if any(
                                            keyword in line.lower()
                                            for keyword in [
                                                "error",
                                                "exception",
                                                "traceback",
                                                "failed",
                                            ]
                                        ):
                                            print(f"  {Colors.RED}{line}{Colors.RESET}")
                                        else:
                                            print(f"  {line}")
                    else:
                        # Windows or other - just show a message
                        print_info(
                            "Server logs not available. Run with --debug to see server output."
                        )
            except Exception as e:
                print_info(f"Could not read server logs: {e}")
                print_info("Tip: Run with --debug flag to see server output in real-time")
            print("-" * 60)
        if test_result:
            tests_passed += 1
        print()

        # Summary
        print("=" * 60)
        print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        print(f"  Tests passed: {tests_passed}/{tests_total}")

        if tests_passed == tests_total:
            print_success("All tests passed! 🎉")
            return 0
        else:
            print_error(f"{tests_total - tests_passed} test(s) failed")
            return 1

    except KeyboardInterrupt:
        print()
        print_warning("Test interrupted by user")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Clean up: stop server if we started it
        if server_process:
            print()
            print_info("Stopping server...")
            try:
                # Read any remaining output before terminating
                if server_process.stdout:
                    try:
                        server_process.stdout.close()
                    except Exception:
                        pass
                server_process.terminate()
                server_process.wait(timeout=5)
                print_success("Server stopped")
            except subprocess.TimeoutExpired:
                print_warning("Server did not stop gracefully, forcing termination...")
                server_process.kill()
                server_process.wait()
            except Exception as e:
                print_error(f"Error stopping server: {e}")


if __name__ == "__main__":
    sys.exit(main())
