"""
Smoke tests for m365-sim Commercial E5 hardened and partial scenarios.

Tests:
- Commercial E5 hardened: 8 CMMC policies, full auth methods, 3 devices, 3 compliance policies
- Commercial E5 partial: 3 CA policies, 1 auth method enabled, 1 device, 1 compliance policy
- Organization name is "Contoso Corp" (not "Contoso Defense LLC")
- Domain is contoso.com
- All use graph.microsoft.com URLs
- Break-glass account excluded from policies
- Fixture inheritance from greenfield
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
def mock_server_e5_hardened():
    """
    Session-scoped fixture that starts m365-sim server with commercial-e5 hardened scenario.

    - Picks a random available port
    - Starts: python server.py --cloud commercial-e5 --scenario hardened --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with commercial-e5 hardened scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--cloud", "commercial-e5", "--scenario", "hardened", "--port", str(port)],
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
            f"Commercial E5 hardened server failed to start on port {port} within {timeout}s"
        )

    yield url

    # Cleanup: kill subprocess
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="session")
def mock_server_e5_partial():
    """
    Session-scoped fixture that starts m365-sim server with commercial-e5 partial scenario.

    - Picks a random available port
    - Starts: python server.py --cloud commercial-e5 --scenario partial --port {port}
    - Waits for /health to respond (retry loop, 5s timeout)
    - Yields f"http://localhost:{port}"
    - Kills subprocess on teardown
    """
    port = get_free_port()
    url = f"http://localhost:{port}"

    # Start subprocess with commercial-e5 partial scenario
    process = subprocess.Popen(
        ["python3", "server.py", "--cloud", "commercial-e5", "--scenario", "partial", "--port", str(port)],
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
            f"Commercial E5 partial server failed to start on port {port} within {timeout}s"
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


class TestCommercialE5HardenedCAPolicy:
    """Tests for Commercial E5 hardened conditional access policies."""

    def test_e5_hardened_ca_policies_count(self, mock_server_e5_hardened, auth_headers):
        """GET /v1.0/identity/conditionalAccess/policies returns 8 CMMC policies."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 8

    def test_e5_hardened_ca_policies_report_only(self, mock_server_e5_hardened, auth_headers):
        """All CA policies have state=enabledForReportingButNotEnforced."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for policy in data["value"]:
            assert policy["state"] == "enabledForReportingButNotEnforced"

    def test_e5_hardened_ca_policies_breakglass_excluded(
        self, mock_server_e5_hardened, auth_headers
    ):
        """All CA policies exclude break-glass account (00000000-0000-0000-0000-000000000011)."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for policy in data["value"]:
            conditions = policy.get("conditions", {})
            users = conditions.get("users", {})
            exclude_users = users.get("excludeUsers", [])
            assert "00000000-0000-0000-0000-000000000011" in exclude_users


class TestCommercialE5HardenedAuthMethods:
    """Tests for Commercial E5 hardened authentication methods."""

    def test_e5_hardened_auth_methods_enabled(self, mock_server_e5_hardened, auth_headers):
        """microsoftAuthenticator, fido2, and temporaryAccessPass are enabled."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/policies/authenticationMethodsPolicy",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "authenticationMethodConfigurations" in data

        method_states = {
            config["id"]: config["state"]
            for config in data["authenticationMethodConfigurations"]
        }

        assert method_states["microsoftAuthenticator"] == "enabled"
        assert method_states["fido2"] == "enabled"
        assert method_states["temporaryAccessPass"] == "enabled"
        assert method_states["sms"] == "disabled"

    def test_e5_hardened_me_has_fido2(self, mock_server_e5_hardened, auth_headers):
        """GET /v1.0/me/authentication/methods includes FIDO2 entry."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/me/authentication/methods",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        fido2_found = False
        for method in data["value"]:
            if method.get("@odata.type") == "#microsoft.graph.fido2AuthenticationMethod":
                fido2_found = True
                assert method["displayName"] == "YubiKey 5C"
                break

        assert fido2_found


class TestCommercialE5HardenedDevices:
    """Tests for Commercial E5 hardened managed devices and compliance."""

    def test_e5_hardened_managed_devices(self, mock_server_e5_hardened, auth_headers):
        """GET /v1.0/deviceManagement/managedDevices returns 3 compliant devices."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/deviceManagement/managedDevices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        for device in data["value"]:
            assert device["complianceState"] == "compliant"

    def test_e5_hardened_compliance_policies(self, mock_server_e5_hardened, auth_headers):
        """GET /v1.0/deviceManagement/deviceCompliancePolicies returns 3 policies."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/deviceManagement/deviceCompliancePolicies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

        policy_names = {policy["displayName"] for policy in data["value"]}
        expected_names = {
            "CMMC-Windows-Compliance",
            "CMMC-iOS-Compliance",
            "CMMC-Android-Compliance",
        }
        assert policy_names == expected_names


class TestCommercialE5HardenedOrganization:
    """Tests for Commercial E5 hardened organization identity."""

    def test_e5_hardened_org_name(self, mock_server_e5_hardened, auth_headers):
        """Organization displayName is 'Contoso Corp' (not 'Contoso Defense LLC')."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0
        assert data["value"][0]["displayName"] == "Contoso Corp"

    def test_e5_hardened_org_domain(self, mock_server_e5_hardened, auth_headers):
        """Organization has contoso.com domain."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        org = data["value"][0]
        domains = org.get("verifiedDomains", [])
        domain_names = {d["name"] for d in domains}
        assert "contoso.com" in domain_names

    def test_e5_hardened_context_url(self, mock_server_e5_hardened, auth_headers):
        """CA policies use graph.microsoft.com in @odata.context."""
        response = httpx.get(
            f"{mock_server_e5_hardened}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "@odata.context" in data
        assert "graph.microsoft.com" in data["@odata.context"]
        assert "v1.0" in data["@odata.context"]


class TestCommercialE5PartialCAPolicy:
    """Tests for Commercial E5 partial conditional access policies."""

    def test_e5_partial_ca_policies_count(self, mock_server_e5_partial, auth_headers):
        """GET /v1.0/identity/conditionalAccess/policies returns 3 policies."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 3

    def test_e5_partial_ca_policies_report_only(self, mock_server_e5_partial, auth_headers):
        """All partial CA policies have state=enabledForReportingButNotEnforced."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for policy in data["value"]:
            assert policy["state"] == "enabledForReportingButNotEnforced"


class TestCommercialE5PartialAuthMethods:
    """Tests for Commercial E5 partial authentication methods."""

    def test_e5_partial_auth_methods_limited(self, mock_server_e5_partial, auth_headers):
        """Only microsoftAuthenticator is enabled; fido2 and tap are disabled."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/policies/authenticationMethodsPolicy",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        method_states = {
            config["id"]: config["state"]
            for config in data["authenticationMethodConfigurations"]
        }

        assert method_states["microsoftAuthenticator"] == "enabled"
        assert method_states["fido2"] == "disabled"
        assert method_states["temporaryAccessPass"] == "disabled"

    def test_e5_partial_me_no_fido2(self, mock_server_e5_partial, auth_headers):
        """GET /v1.0/me/authentication/methods has no FIDO2 entry."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/me/authentication/methods",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 2

        fido2_found = False
        for method in data["value"]:
            if method.get("@odata.type") == "#microsoft.graph.fido2AuthenticationMethod":
                fido2_found = True
                break

        assert not fido2_found


class TestCommercialE5PartialDevices:
    """Tests for Commercial E5 partial managed devices and compliance."""

    def test_e5_partial_managed_devices(self, mock_server_e5_partial, auth_headers):
        """GET /v1.0/deviceManagement/managedDevices returns 1 device."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/deviceManagement/managedDevices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1

        device = data["value"][0]
        assert device["complianceState"] == "compliant"

    def test_e5_partial_compliance_policies(self, mock_server_e5_partial, auth_headers):
        """GET /v1.0/deviceManagement/deviceCompliancePolicies returns 1 policy."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/deviceManagement/deviceCompliancePolicies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1

        policy = data["value"][0]
        assert policy["displayName"] == "CMMC-Windows-Compliance"


class TestCommercialE5PartialOrganization:
    """Tests for Commercial E5 partial organization identity."""

    def test_e5_partial_org_name(self, mock_server_e5_partial, auth_headers):
        """Organization displayName is 'Contoso Corp'."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert data["value"][0]["displayName"] == "Contoso Corp"

    def test_e5_partial_org_domain(self, mock_server_e5_partial, auth_headers):
        """Organization has contoso.com domain."""
        response = httpx.get(
            f"{mock_server_e5_partial}/v1.0/organization",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        org = data["value"][0]
        domains = org.get("verifiedDomains", [])
        domain_names = {d["name"] for d in domains}
        assert "contoso.com" in domain_names
