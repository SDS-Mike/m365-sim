"""
Smoke tests for m365-sim hardened-enforced scenario.

Tests:
- Enforced conditional access policies (8 CMMC policies with state=enabled)
- Enforced state verification (NOT report-only)
- Break-glass account exclusion
- Enabled auth methods (Authenticator, FIDO2, TAP)
- Managed devices (3 compliant devices)
- Compliance policies (3 policies)
- Org identity and cloud endpoint verification
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
def mock_server_enforced_gcc_moderate():
    """
    Session-scoped fixture that starts m365-sim server with hardened-enforced scenario (GCC Moderate).

    - Picks a random available port
    - Starts: python server.py --scenario hardened-enforced --cloud gcc-moderate --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with hardened-enforced scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--scenario", "hardened-enforced", "--cloud", "gcc-moderate", "--port", str(port)],
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
        raise RuntimeError(
            f"Enforced (GCC Moderate) server failed to start on port {port} within {timeout}s"
        )

    yield url

    # Cleanup: kill subprocess
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="session")
def mock_server_enforced_gcc_high():
    """
    Session-scoped fixture that starts m365-sim server with hardened-enforced scenario (GCC High).

    - Picks a random available port
    - Starts: python server.py --scenario hardened-enforced --cloud gcc-high --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with hardened-enforced scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--scenario", "hardened-enforced", "--cloud", "gcc-high", "--port", str(port)],
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
        raise RuntimeError(
            f"Enforced (GCC High) server failed to start on port {port} within {timeout}s"
        )

    yield url

    # Cleanup: kill subprocess
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="session")
def mock_server_enforced_commercial_e5():
    """
    Session-scoped fixture that starts m365-sim server with hardened-enforced scenario (Commercial E5).

    - Picks a random available port
    - Starts: python server.py --scenario hardened-enforced --cloud commercial-e5 --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with hardened-enforced scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--scenario", "hardened-enforced", "--cloud", "commercial-e5", "--port", str(port)],
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
        raise RuntimeError(
            f"Enforced (Commercial E5) server failed to start on port {port} within {timeout}s"
        )

    yield url

    # Cleanup: kill subprocess
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def auth_headers():
    """Return Bearer token headers for authenticated requests."""
    return {"Authorization": "Bearer test-token"}


class TestEnforcedCAPolicy:
    """Tests for enforced conditional access policies."""

    def test_enforced_ca_policies_count(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GET /v1.0/identity/conditionalAccess/policies returns 8 CMMC policies."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 8

    def test_enforced_ca_policies_enabled(self, mock_server_enforced_gcc_moderate, auth_headers):
        """All CA policies have state=enabled (NOT report-only)."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for policy in data["value"]:
            assert policy["state"] == "enabled", f"Policy {policy['displayName']} has state {policy['state']}"
            # Ensure no policy has enabledForReportingButNotEnforced (report-only)
            assert policy["state"] != "enabledForReportingButNotEnforced"

    def test_enforced_ca_policies_breakglass_excluded(
        self, mock_server_enforced_gcc_moderate, auth_headers
    ):
        """All CA policies exclude break-glass account (00000000-0000-0000-0000-000000000011)."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for policy in data["value"]:
            # Check that break-glass is in excludeUsers (if condition has users)
            conditions = policy.get("conditions", {})
            users = conditions.get("users", {})
            exclude_users = users.get("excludeUsers", [])
            assert "00000000-0000-0000-0000-000000000011" in exclude_users, \
                f"Policy {policy['displayName']} missing break-glass exclusion"

    def test_enforced_ca_policy_names(self, mock_server_enforced_gcc_moderate, auth_headers):
        """All 8 CMMC policy names are present."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        policy_names = {policy["displayName"] for policy in data["value"]}
        expected_names = {
            "CMMC-MFA-AllUsers",
            "CMMC-MFA-Admins",
            "CMMC-Block-Legacy-Auth",
            "CMMC-Compliant-Device",
            "CMMC-Approved-Apps",
            "CMMC-Session-Timeout",
            "CMMC-Risk-Based-Access",
            "CMMC-Location-Based",
        }
        assert policy_names == expected_names


class TestEnforcedAuthMethods:
    """Tests for enforced authentication methods."""

    def test_enforced_auth_methods_enabled(self, mock_server_enforced_gcc_moderate, auth_headers):
        """microsoftAuthenticator, fido2, and temporaryAccessPass are enabled."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/policies/authenticationMethodsPolicy",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "authenticationMethodConfigurations" in data

        # Build map of method ID to state
        method_states = {
            config["id"]: config["state"]
            for config in data["authenticationMethodConfigurations"]
        }

        assert method_states["microsoftAuthenticator"] == "enabled"
        assert method_states["fido2"] == "enabled"
        assert method_states["temporaryAccessPass"] == "enabled"
        assert method_states["sms"] == "disabled"

    def test_enforced_me_has_fido2(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GET /v1.0/me/authentication/methods includes FIDO2 entry."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/me/authentication/methods",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        # Check for FIDO2 method
        fido2_found = False
        for method in data["value"]:
            if method.get("@odata.type") == "#microsoft.graph.fido2AuthenticationMethod":
                fido2_found = True
                assert "displayName" in method
                assert method["displayName"] == "YubiKey 5C"
                break

        assert fido2_found


class TestEnforcedDevices:
    """Tests for enforced managed devices and compliance."""

    def test_enforced_managed_devices(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GET /v1.0/deviceManagement/managedDevices returns 3 compliant devices."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/deviceManagement/managedDevices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        # All devices should be compliant
        for device in data["value"]:
            assert device["complianceState"] == "compliant"
            assert "deviceName" in device
            assert "osVersion" in device

    def test_enforced_compliance_policies(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GET /v1.0/deviceManagement/deviceCompliancePolicies returns 3 policies."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/deviceManagement/deviceCompliancePolicies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        # Check for expected policy names
        policy_names = {policy["displayName"] for policy in data["value"]}
        expected_names = {
            "CMMC-Windows-Compliance",
            "CMMC-iOS-Compliance",
            "CMMC-Android-Compliance",
        }
        assert policy_names == expected_names


class TestEnforcedCloudEndpoints:
    """Tests for cloud-specific endpoint verification."""

    def test_enforced_gcc_moderate_uses_graph_microsoft_com(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GCC Moderate enforced uses graph.microsoft.com endpoint."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "@odata.context" in data
        assert "graph.microsoft.com" in data["@odata.context"]

    def test_enforced_gcc_high_uses_graph_microsoft_us(self, mock_server_enforced_gcc_high, auth_headers):
        """GCC High enforced uses graph.microsoft.us endpoint."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_high}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "@odata.context" in data
        assert "graph.microsoft.us" in data["@odata.context"]

    def test_enforced_commercial_e5_uses_graph_microsoft_com(self, mock_server_enforced_commercial_e5, auth_headers):
        """Commercial E5 enforced uses graph.microsoft.com endpoint."""
        response = httpx.get(
            f"{mock_server_enforced_commercial_e5}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "@odata.context" in data
        assert "graph.microsoft.com" in data["@odata.context"]


class TestEnforcedOrgIdentity:
    """Tests for organization identity in enforced scenarios."""

    def test_enforced_gcc_moderate_org_is_contoso_defense(self, mock_server_enforced_gcc_moderate, auth_headers):
        """GCC Moderate enforced organization is Contoso Defense LLC."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_moderate}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0
        org = data["value"][0]
        assert org["displayName"] == "Contoso Defense LLC"

    def test_enforced_commercial_e5_org_is_contoso_corp(self, mock_server_enforced_commercial_e5, auth_headers):
        """Commercial E5 enforced organization is Contoso Corp."""
        response = httpx.get(
            f"{mock_server_enforced_commercial_e5}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0
        org = data["value"][0]
        assert org["displayName"] == "Contoso Corp"

    def test_enforced_gcc_high_org_is_contoso_defense_federal(self, mock_server_enforced_gcc_high, auth_headers):
        """GCC High enforced organization is Contoso Defense Federal LLC."""
        response = httpx.get(
            f"{mock_server_enforced_gcc_high}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0
        org = data["value"][0]
        assert org["displayName"] == "Contoso Defense Federal LLC"
