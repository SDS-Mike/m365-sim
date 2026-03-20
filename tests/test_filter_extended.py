"""
Test extended $filter operators: ne, gt, lt, ge, le, startswith, contains, in.

Tests integration with the mock server to ensure realistic Graph API behavior.
"""

import subprocess
import socket
import time

import httpx
import pytest


def get_free_port():
    """Get a free port by creating a socket and letting the OS assign one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope="session")
def mock_server_hardened():
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


def test_filter_ne_string(mock_server, auth_headers):
    """Test ne (not equal) operator with string values."""
    response = httpx.get(f"{mock_server}/v1.0/users?$filter=userType ne 'Guest'", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2
    for user in data["value"]:
        assert user.get("userType") != "Guest"


def test_filter_ne_excludes(mock_server, auth_headers):
    """Test ne operator excludes specified value."""
    response = httpx.get(f"{mock_server}/v1.0/users?$filter=userType ne 'Member'", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 0


def test_filter_gt_numeric(mock_server, auth_headers):
    """Test gt (greater than) operator with numeric comparison."""
    response = httpx.get(f"{mock_server}/v1.0/security/secureScores?$filter=currentScore gt 10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1
    assert data["value"][0]["currentScore"] > 10


def test_filter_lt_numeric(mock_server, auth_headers):
    """Test lt (less than) operator with numeric comparison."""
    response = httpx.get(f"{mock_server}/v1.0/security/secureScores?$filter=currentScore lt 50", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1
    assert data["value"][0]["currentScore"] < 50


def test_filter_ge_le(mock_server, auth_headers):
    """Test ge (greater than or equal) and le (less than or equal) operators."""
    # Test ge
    response = httpx.get(f"{mock_server}/v1.0/security/secureScores?$filter=currentScore ge 12", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1
    assert data["value"][0]["currentScore"] >= 12

    # Test le
    response = httpx.get(f"{mock_server}/v1.0/security/secureScores?$filter=currentScore le 12", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1
    assert data["value"][0]["currentScore"] <= 12


def test_filter_startswith(mock_server, auth_headers):
    """Test startswith() function operator."""
    response = httpx.get(f"{mock_server}/v1.0/users?$filter=startswith(displayName,'Mike')", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1
    assert data["value"][0]["displayName"] == "Mike Morris"


def test_filter_contains(mock_server, auth_headers):
    """Test contains() function operator."""
    response = httpx.get(f"{mock_server}/v1.0/users?$filter=contains(userPrincipalName,'contoso')", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2
    for user in data["value"]:
        assert "contoso" in user.get("userPrincipalName", "").lower()


def test_filter_in_operator(mock_server, auth_headers):
    """Test in operator with list of values."""
    response = httpx.get(
        f"{mock_server}/v1.0/directoryRoles?$filter=displayName in ('Global Administrator','Security Administrator')",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2
    display_names = {role.get("displayName") for role in data["value"]}
    assert "Global Administrator" in display_names
    assert "Security Administrator" in display_names


def test_filter_ne_with_and(mock_server, auth_headers):
    """Test compound filter with ne and and operators."""
    response = httpx.get(
        f"{mock_server}/v1.0/users?$filter=userType ne 'Guest' and accountEnabled eq true",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2
    for user in data["value"]:
        assert user.get("userType") != "Guest"
        assert user.get("accountEnabled") is True


def test_filter_contains_no_match(mock_server, auth_headers):
    """Test contains() with no matching results."""
    response = httpx.get(
        f"{mock_server}/v1.0/users?$filter=contains(displayName,'nonexistent')",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 0


def test_filter_eq_still_works(mock_server, auth_headers):
    """Test that original eq operator still works (regression test)."""
    response = httpx.get(f"{mock_server}/v1.0/users?$filter=accountEnabled eq true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2


def test_filter_and_or_still_work(mock_server, auth_headers):
    """Test that and/or combinators still work (regression test)."""
    response = httpx.get(
        f"{mock_server}/v1.0/users?$filter=accountEnabled eq true and userType eq 'Member'",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 2


def test_filter_numeric_string_comparison(mock_server, auth_headers):
    """Test that numeric comparison falls back to string when needed."""
    response = httpx.get(f"{mock_server}/v1.0/security/secureScores?$filter=currentScore gt 11", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 1


def test_filter_unparseable_returns_full_result(mock_server, auth_headers):
    """Test that unparseable filters return full result (graceful degradation)."""
    response = httpx.get(
        f"{mock_server}/v1.0/users?$filter=invalidOperator field 'value'",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # Should return all users without filtering
    assert "value" in data
    assert len(data["value"]) == 2


def test_filter_startswith_hardened_ca(mock_server_hardened, auth_headers):
    """Test startswith() on hardened CA policies."""
    response = httpx.get(
        f"{mock_server_hardened}/v1.0/identity/conditionalAccess/policies?$filter=startswith(displayName,'CMMC')",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 8
    for policy in data["value"]:
        assert policy.get("displayName", "").startswith("CMMC")


def test_filter_state_ne_disabled_hardened(mock_server_hardened, auth_headers):
    """Test ne operator on hardened CA policies state field."""
    response = httpx.get(
        f"{mock_server_hardened}/v1.0/identity/conditionalAccess/policies?$filter=state ne 'disabled'",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 8
    for policy in data["value"]:
        assert policy.get("state") != "disabled"
