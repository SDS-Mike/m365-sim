"""
Smoke tests for m365-sim GET endpoints.

Tests:
- Health check (no auth required)
- Authentication enforcement
- All collection endpoints return 200 with 'value' key
- Specific endpoint content validation
"""

import pytest
import httpx


class TestHealth:
    """Health endpoint tests."""

    def test_health_no_auth_required(self, mock_server):
        """GET /health returns 200 without auth header."""
        response = httpx.get(f"{mock_server}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["scenario"] == "greenfield"
        assert data["cloud"] == "gcc-moderate"


class TestAuthentication:
    """Authentication enforcement tests."""

    def test_auth_required_missing_header(self, mock_server):
        """GET /v1.0/users without auth returns 401."""
        response = httpx.get(f"{mock_server}/v1.0/users")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "Authorization_RequestDenied"

    def test_auth_succeeds_with_bearer_token(self, mock_server, auth_headers):
        """GET /v1.0/users with auth header returns 200."""
        response = httpx.get(f"{mock_server}/v1.0/users", headers=auth_headers)
        assert response.status_code == 200


class TestIdentityEndpoints:
    """Tests for identity and user endpoints."""

    def test_users(self, mock_server, auth_headers):
        """GET /v1.0/users returns 200 with value key containing 2 users."""
        response = httpx.get(f"{mock_server}/v1.0/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert isinstance(data["value"], list)
        assert len(data["value"]) == 2

    def test_me(self, mock_server, auth_headers):
        """GET /v1.0/me returns 200 with displayName key."""
        response = httpx.get(f"{mock_server}/v1.0/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "displayName" in data

    def test_organization(self, mock_server, auth_headers):
        """GET /v1.0/organization returns 200 with tenant info."""
        response = httpx.get(f"{mock_server}/v1.0/organization", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "value" in data

    def test_domains(self, mock_server, auth_headers):
        """GET /v1.0/domains returns 200."""
        response = httpx.get(f"{mock_server}/v1.0/domains", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "value" in data

    def test_groups(self, mock_server, auth_headers):
        """GET /v1.0/groups returns 200 with empty value array."""
        response = httpx.get(f"{mock_server}/v1.0/groups", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert data["value"] == []


class TestSecurityEndpoints:
    """Tests for security, device, and conditional access endpoints."""

    def test_conditional_access_policies(self, mock_server, auth_headers):
        """GET /v1.0/identity/conditionalAccess/policies returns 200 with empty value array."""
        response = httpx.get(
            f"{mock_server}/v1.0/identity/conditionalAccess/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert data["value"] == []

    def test_auth_methods_policy(self, mock_server, auth_headers):
        """GET /v1.0/policies/authenticationMethodsPolicy returns 200 with authenticationMethodConfigurations."""
        response = httpx.get(
            f"{mock_server}/v1.0/policies/authenticationMethodsPolicy",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "authenticationMethodConfigurations" in data

    def test_auth_method_config_by_id(self, mock_server, auth_headers):
        """GET /v1.0/policies/.../fido2 returns fido2 config."""
        response = httpx.get(
            f"{mock_server}/v1.0/policies/authenticationMethodsPolicy/authenticationMethodConfigurations/fido2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "fido2"

    def test_secure_scores(self, mock_server, auth_headers):
        """GET /v1.0/security/secureScores returns 200 with currentScore 12.0."""
        response = httpx.get(
            f"{mock_server}/v1.0/security/secureScores",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0
        assert data["value"][0]["currentScore"] == 12.0

    def test_security_incidents(self, mock_server, auth_headers):
        """GET /v1.0/security/incidents returns 200 with empty value."""
        response = httpx.get(
            f"{mock_server}/v1.0/security/incidents",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data


class TestDeviceEndpoints:
    """Tests for device management endpoints."""

    def test_managed_devices(self, mock_server, auth_headers):
        """GET /v1.0/deviceManagement/managedDevices returns 200 with empty value."""
        response = httpx.get(
            f"{mock_server}/v1.0/deviceManagement/managedDevices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert data["value"] == []


class TestRoleEndpoints:
    """Tests for directory role endpoints."""

    def test_directory_roles(self, mock_server, auth_headers):
        """GET /v1.0/directoryRoles returns 200 with roles in value."""
        response = httpx.get(
            f"{mock_server}/v1.0/directoryRoles",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) > 0

    def test_role_assignments(self, mock_server, auth_headers):
        """GET /v1.0/roleManagement/directory/roleAssignments returns 200."""
        response = httpx.get(
            f"{mock_server}/v1.0/roleManagement/directory/roleAssignments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data


class TestAuditEndpoints:
    """Tests for audit log endpoints."""

    def test_audit_sign_ins(self, mock_server, auth_headers):
        """GET /v1.0/auditLogs/signIns returns 200 with 1 sign-in entry."""
        response = httpx.get(
            f"{mock_server}/v1.0/auditLogs/signIns",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        assert len(data["value"]) == 1


class TestInformationProtectionEndpoints:
    """Tests for information protection endpoints."""

    def test_information_protection_labels(self, mock_server, auth_headers):
        """GET /v1.0/informationProtection/policy/labels returns 200."""
        response = httpx.get(
            f"{mock_server}/v1.0/informationProtection/policy/labels",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()


class TestServicePrincipals:
    """Tests for service principal endpoints."""

    def test_service_principals(self, mock_server, auth_headers):
        """GET /v1.0/servicePrincipals returns 200 and includes Microsoft Graph SP."""
        response = httpx.get(
            f"{mock_server}/v1.0/servicePrincipals",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "value" in data
        # Check for Microsoft Graph SP (appId: 00000003-0000-0000-c000-000000000000)
        app_ids = [sp.get("appId") for sp in data["value"]]
        assert "00000003-0000-0000-c000-000000000000" in app_ids


class TestCollectionEndpoints:
    """Parameterized tests for all collection endpoints."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/v1.0/users",
            "/v1.0/domains",
            "/v1.0/groups",
            "/v1.0/devices",
            "/v1.0/deviceManagement/managedDevices",
            "/v1.0/deviceManagement/deviceCompliancePolicies",
            "/v1.0/deviceManagement/deviceConfigurations",
            "/v1.0/deviceManagement/deviceEnrollmentConfigurations",
            "/v1.0/identity/conditionalAccess/policies",
            "/v1.0/identity/conditionalAccess/namedLocations",
            "/v1.0/security/incidents",
            "/v1.0/security/alerts_v2",
            "/v1.0/security/secureScores",
            "/v1.0/security/secureScoreControlProfiles",
            "/v1.0/directoryRoles",
            "/v1.0/roleManagement/directory/roleAssignments",
            "/v1.0/roleManagement/directory/roleDefinitions",
            "/v1.0/roleManagement/directory/roleEligibilitySchedules",
            "/v1.0/roleManagement/directory/roleAssignmentSchedules",
            "/v1.0/auditLogs/signIns",
            "/v1.0/auditLogs/directoryAudits",
            "/v1.0/informationProtection/policy/labels",
            "/v1.0/servicePrincipals",
            "/v1.0/applications",
        ],
    )
    def test_all_collection_endpoints_have_value_key(self, mock_server, auth_headers, endpoint):
        """All collection endpoints return 200 with 'value' key."""
        response = httpx.get(f"{mock_server}{endpoint}", headers=auth_headers)
        assert response.status_code == 200, f"Failed for endpoint {endpoint}"
        data = response.json()
        assert "value" in data, f"Missing 'value' key in endpoint {endpoint}"
