"""
OData $filter engine tests for m365-sim.

Tests:
- Single-field filters (eq operator)
- Compound filters (and/or operators)
- Multiple data types (string, bool, int)
- Filter + $top combination
- Graceful degradation (unparseable filters)
- Empty collections and no-match scenarios
- Hardened scenario specific filters
"""

import subprocess
import time
import socket
import pytest
import httpx


def get_free_port():
    """Get a free port by creating a socket and letting the OS assign one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session")
def mock_server_hardened_filter():
    """
    Session-scoped fixture that starts m365-sim server with hardened scenario.

    - Picks a random available port
    - Starts: python server.py --scenario hardened --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with hardened scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--scenario", "hardened", "--port", str(port)],
        cwd="/home/mmn/github/m365-sim",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready (retry loop, 5s timeout)
    start_time = time.time()
    timeout = 5
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"{url}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.1)
    else:
        # Timeout reached
        process.kill()
        raise RuntimeError(f"Server failed to start on port {port} within {timeout}s")

    yield url

    # Cleanup: kill subprocess
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


class TestFilterGreenfieldUsers:
    """Test $filter on /v1.0/users endpoint (greenfield scenario)."""

    def test_filter_users_by_member_type(self, mock_server, auth_headers):
        """$filter=userType eq 'Member' returns 2 members."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "userType eq 'Member'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 2
        for user in data["value"]:
            assert user["userType"] == "Member"

    def test_filter_users_by_guest_type(self, mock_server, auth_headers):
        """$filter=userType eq 'Guest' returns empty array (no guests in greenfield)."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "userType eq 'Guest'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 0

    def test_filter_users_account_enabled(self, mock_server, auth_headers):
        """$filter=accountEnabled eq true filters correctly."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "accountEnabled eq true"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        # Both users in greenfield have accountEnabled = true
        assert len(data["value"]) == 2
        for user in data["value"]:
            assert user["accountEnabled"] is True


class TestFilterServicePrincipals:
    """Test $filter on /v1.0/servicePrincipals endpoint."""

    def test_filter_service_principals_by_app_id(self, mock_server, auth_headers):
        """$filter=appId eq '00000003-0000-0000-c000-000000000000' returns exactly 1 SP."""
        response = httpx.get(
            f"{mock_server}/v1.0/servicePrincipals",
            params={"$filter": "appId eq '00000003-0000-0000-c000-000000000000'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1
        assert data["value"][0]["appId"] == "00000003-0000-0000-c000-000000000000"
        assert data["value"][0]["displayName"] == "Microsoft Graph"


class TestFilterWithTop:
    """Test $filter combined with $top parameter."""

    def test_filter_with_top(self, mock_server, auth_headers):
        """$filter=userType eq 'Member'&$top=1 returns 1 result (filter applied first)."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "userType eq 'Member'", "$top": "1"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1
        assert data["value"][0]["userType"] == "Member"


class TestCompoundFilters:
    """Test compound filters with and/or operators."""

    def test_filter_compound_and(self, mock_server, auth_headers):
        """$filter=userType eq 'Member' and accountEnabled eq true works."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "userType eq 'Member' and accountEnabled eq true"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        # Both users in greenfield meet both conditions
        assert len(data["value"]) == 2
        for user in data["value"]:
            assert user["userType"] == "Member"
            assert user["accountEnabled"] is True


class TestFilterEdgeCases:
    """Test filter edge cases and graceful degradation."""

    def test_filter_unparseable_returns_full(self, mock_server, auth_headers):
        """$filter=badSyntax!!! returns full result (graceful degradation)."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "badSyntax!!!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        # Should return unfiltered result (2 users)
        assert len(data["value"]) == 2

    def test_filter_empty_collection(self, mock_server, auth_headers):
        """Filter on empty collection returns empty."""
        response = httpx.get(
            f"{mock_server}/v1.0/groups",
            params={"$filter": "securityEnabled eq true"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 0

    def test_filter_no_match(self, mock_server, auth_headers):
        """Filter that matches nothing returns empty value."""
        response = httpx.get(
            f"{mock_server}/v1.0/users",
            params={"$filter": "userType eq 'NonExistent'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 0


class TestFilterHardenedScenario:
    """Test $filter on hardened scenario endpoints."""

    def test_filter_hardened_ca_policies_by_state(
        self, mock_server_hardened_filter, auth_headers
    ):
        """$filter=state eq 'enabledForReportingButNotEnforced' returns 8 policies."""
        response = httpx.get(
            f"{mock_server_hardened_filter}/v1.0/identity/conditionalAccess/policies",
            params={"$filter": "state eq 'enabledForReportingButNotEnforced'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 8
        for policy in data["value"]:
            assert policy["state"] == "enabledForReportingButNotEnforced"

    def test_filter_hardened_compliant_devices(
        self, mock_server_hardened_filter, auth_headers
    ):
        """$filter=complianceState eq 'compliant' returns 3 devices."""
        response = httpx.get(
            f"{mock_server_hardened_filter}/v1.0/deviceManagement/managedDevices",
            params={"$filter": "complianceState eq 'compliant'"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3
        for device in data["value"]:
            assert device["complianceState"] == "compliant"
