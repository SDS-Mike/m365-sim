"""
Tests for the TenantBuilder fluent API.

Tests:
- Greenfield preset generates all expected fixture files
- Hardened preset generates all expected fixture files
- Generated users match specification
- Generated CA policies in hardened have correct state
- Custom builder works correctly
- All output is valid JSON
- Builder maintains fluent interface
- Server can load and serve generated fixtures
"""

import json
import tempfile
import pytest
from pathlib import Path

from builder.tenant_builder import TenantBuilder


class TestGreenFieldPreset:
    """Test TenantBuilder.greenfield_gcc_moderate() preset."""

    def test_greenfield_preset_creates_all_fixtures(self):
        """Greenfield preset generates all expected fixture files."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Check that all expected files exist
            expected_files = [
                "users.json",
                "organization.json",
                "me.json",
                "conditional_access_policies.json",
                "managed_devices.json",
                "compliance_policies.json",
                "device_configurations.json",
                "auth_methods_policy.json",
                "directory_roles.json",
                "role_assignments.json",
                "service_principals.json",
                "secure_scores.json",
                "me_auth_methods.json",
                "devices.json",
                "audit_sign_ins.json",
                "audit_directory.json",
                "security_incidents.json",
                "security_alerts.json",
                "information_protection_labels.json",
                "groups.json",
                "applications.json",
                "domains.json",
                "named_locations.json",
                "role_definitions.json",
                "role_eligibility_schedules.json",
                "role_assignment_schedules.json",
                "secure_score_control_profiles.json",
                "device_enrollment_configurations.json",
            ]

            for filename in expected_files:
                assert (output_dir / filename).exists(), f"Missing fixture: {filename}"

    def test_greenfield_users_match_spec(self):
        """Generated users match greenfield specification."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "users.json") as f:
                users_data = json.load(f)

            assert "value" in users_data
            users = users_data["value"]

            # Should have 2 users: Mike Morris and BreakGlass Admin
            assert len(users) == 2

            # Verify Mike Morris
            mike = next((u for u in users if u["displayName"] == "Mike Morris"), None)
            assert mike is not None
            assert mike["userPrincipalName"] == "mike@contoso-defense.com"
            assert mike["userType"] == "Member"
            assert mike["accountEnabled"] is True
            assert mike["id"] == "00000000-0000-0000-0000-000000000010"

            # Verify BreakGlass Admin
            breakglass = next(
                (u for u in users if u["displayName"] == "BreakGlass Admin"), None
            )
            assert breakglass is not None
            assert breakglass["userPrincipalName"] == "breakglass@contoso-defense.com"
            assert breakglass["id"] == "00000000-0000-0000-0000-000000000011"


class TestHardenedPreset:
    """Test TenantBuilder.hardened_gcc_moderate() preset."""

    def test_hardened_preset_creates_all_fixtures(self):
        """Hardened preset generates all expected fixture files."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Check that all expected files exist
            expected_files = [
                "users.json",
                "organization.json",
                "me.json",
                "conditional_access_policies.json",
                "managed_devices.json",
                "compliance_policies.json",
                "device_configurations.json",
                "auth_methods_policy.json",
            ]

            for filename in expected_files:
                assert (output_dir / filename).exists(), f"Missing fixture: {filename}"

    def test_hardened_ca_policies_report_only(self):
        """All hardened CA policies have enabledForReportingButNotEnforced state."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "conditional_access_policies.json") as f:
                policies_data = json.load(f)

            policies = policies_data["value"]

            # Should have 8 CA policies
            assert len(policies) == 8

            # All policies must be in enabledForReportingButNotEnforced state
            for policy in policies:
                assert (
                    policy["state"] == "enabledForReportingButNotEnforced"
                ), f"Policy {policy['displayName']} has wrong state: {policy['state']}"

    def test_hardened_managed_devices(self):
        """Hardened scenario includes 3 managed devices."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "managed_devices.json") as f:
                devices_data = json.load(f)

            devices = devices_data["value"]

            # Should have 3 managed devices
            assert len(devices) == 3

            # Check device names
            device_names = {d["deviceName"] for d in devices}
            assert device_names == {"CONTOSO-LT001", "CONTOSO-WS001", "CONTOSO-iPhone"}

            # All should be compliant
            for device in devices:
                assert device["complianceState"] == "compliant"

    def test_hardened_compliance_policies(self):
        """Hardened scenario includes compliance policies."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "compliance_policies.json") as f:
                policies_data = json.load(f)

            policies = policies_data["value"]

            # Should have 3 compliance policies (Windows, iOS, Android)
            assert len(policies) == 3

            policy_types = {p["@odata.type"] for p in policies}
            assert "#microsoft.graph.windowsCompliancePolicy" in policy_types
            assert "#microsoft.graph.iosCompliancePolicy" in policy_types
            assert "#microsoft.graph.androidCompliancePolicy" in policy_types

    def test_hardened_auth_methods_enabled(self):
        """Hardened scenario enables FIDO2, MicrosoftAuthenticator, and TemporaryAccessPass."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "auth_methods_policy.json") as f:
                policy_data = json.load(f)

            configs = policy_data["authenticationMethodConfigurations"]

            # Find each method and check enabled state
            fido2 = next((c for c in configs if c["id"] == "fido2"), None)
            assert fido2 is not None
            assert fido2["state"] == "enabled"

            ms_auth = next(
                (c for c in configs if c["id"] == "microsoftAuthenticator"), None
            )
            assert ms_auth is not None
            assert ms_auth["state"] == "enabled"

            tap = next((c for c in configs if c["id"] == "temporaryAccessPass"), None)
            assert tap is not None
            assert tap["state"] == "enabled"


class TestCustomBuilder:
    """Test building custom tenant configurations."""

    def test_custom_builder(self):
        """Custom builder with fluent methods generates valid fixtures."""
        builder = (
            TenantBuilder()
            .with_organization("Test Org", "test.example.com")
            .with_user("Alice", "alice@test.example.com", job_title="Admin")
            .with_user("Bob", "bob@test.example.com")
            .with_ca_policy(
                "Test Policy",
                grant_controls={"operator": "AND", "builtInControls": ["mfa"]},
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Verify organization
            with open(output_dir / "organization.json") as f:
                org_data = json.load(f)
            org = org_data["value"][0]
            assert org["displayName"] == "Test Org"

            # Verify users
            with open(output_dir / "users.json") as f:
                users_data = json.load(f)
            users = users_data["value"]
            assert len(users) == 2
            assert users[0]["displayName"] == "Alice"
            assert users[1]["displayName"] == "Bob"

            # Verify CA policy
            with open(output_dir / "conditional_access_policies.json") as f:
                policies_data = json.load(f)
            policies = policies_data["value"]
            assert len(policies) == 1
            assert policies[0]["displayName"] == "Test Policy"


class TestBuildOutput:
    """Test build output format and validity."""

    def test_build_output_is_valid_json(self):
        """Every generated fixture file is valid JSON."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Verify all JSON files are valid
            for json_file in output_dir.glob("*.json"):
                with open(json_file) as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError as e:
                        pytest.fail(f"Invalid JSON in {json_file.name}: {e}")

    def test_all_fixtures_have_odata_context(self):
        """All collection fixtures include @odata.context."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Check all JSON files that have a 'value' key
            for json_file in output_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)

                # If it has a 'value' key, it should have @odata.context
                if "value" in data:
                    assert (
                        "@odata.context" in data
                    ), f"{json_file.name} missing @odata.context"
                    assert isinstance(
                        data["@odata.context"], str
                    ), f"{json_file.name} @odata.context should be string"
                    assert "graph.microsoft.com" in data["@odata.context"]

    def test_organization_has_contoso_domain(self):
        """Organization fixture includes Contoso Defense domain."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            with open(output_dir / "organization.json") as f:
                org_data = json.load(f)

            org = org_data["value"][0]
            domains = [d["name"] for d in org["verifiedDomains"]]
            assert "contoso-defense.com" in domains


class TestFluentInterface:
    """Test that builder maintains fluent interface."""

    def test_builder_is_fluent(self):
        """All builder methods return self for chaining."""
        builder = TenantBuilder()

        # Each method should return the builder instance
        result = builder.with_organization("Test", "test.com")
        assert result is builder

        result = result.with_user("Test User", "user@test.com")
        assert result is builder

        result = result.with_ca_policy("Test Policy")
        assert result is builder

        result = result.with_device("Test Device")
        assert result is builder

        result = result.with_compliance_policy("Test Policy")
        assert result is builder

        result = result.with_device_configuration("Test Config")
        assert result is builder

        result = result.with_auth_method_enabled("fido2")
        assert result is builder

        result = result.with_directory_role("Test Role", "test-id")
        assert result is builder

        result = result.with_role_assignment("principal-id", "role-id")
        assert result is builder

        result = result.with_service_principal("Test SP", "app-id")
        assert result is builder

        result = result.with_secure_score(50.0, 100.0)
        assert result is builder

    def test_method_chaining(self):
        """Long chain of builder methods works correctly."""
        builder = (
            TenantBuilder()
            .with_user("User1", "user1@test.com")
            .with_user("User2", "user2@test.com")
            .with_ca_policy("Policy1")
            .with_ca_policy("Policy2")
            .with_device("Device1")
            .with_device("Device2")
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build(output_dir)

            # Verify all entities were added
            with open(output_dir / "users.json") as f:
                users = json.load(f)["value"]
            assert len(users) == 2

            with open(output_dir / "conditional_access_policies.json") as f:
                policies = json.load(f)["value"]
            assert len(policies) == 2

            with open(output_dir / "managed_devices.json") as f:
                devices = json.load(f)["value"]
            assert len(devices) == 2


class TestServerLoadsGeneratedFixtures:
    """Test that server can load and serve fixtures generated by builder."""

    def test_generated_fixtures_loadable_by_server(self):
        """Generated fixtures have correct structure for server to load."""
        builder = TenantBuilder.greenfield_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixtures_dir = Path(tmpdir)
            builder.build(fixtures_dir)

            # Verify fixtures are valid JSON and loadable
            with open(fixtures_dir / "users.json") as f:
                users_data = json.load(f)

            with open(fixtures_dir / "organization.json") as f:
                org_data = json.load(f)

            with open(fixtures_dir / "conditional_access_policies.json") as f:
                ca_data = json.load(f)

            with open(fixtures_dir / "managed_devices.json") as f:
                devices_data = json.load(f)

            # Verify the structure matches what the server expects
            assert "@odata.context" in users_data
            assert "value" in users_data
            assert len(users_data["value"]) == 2
            assert users_data["@odata.context"] == "https://graph.microsoft.com/v1.0/$metadata#users"

            assert "@odata.context" in org_data
            assert "value" in org_data
            assert org_data["value"][0]["displayName"] == "Contoso Defense LLC"
            assert org_data["@odata.context"] == "https://graph.microsoft.com/v1.0/$metadata#organization"

            assert "@odata.context" in ca_data
            assert "value" in ca_data
            assert len(ca_data["value"]) == 0  # Greenfield has no CA policies
            assert ca_data["@odata.context"] == "https://graph.microsoft.com/v1.0/$metadata#identity/conditionalAccess/policies"

            # Greenfield: empty managed devices
            assert "@odata.context" in devices_data
            assert "value" in devices_data
            assert len(devices_data["value"]) == 0

    def test_hardened_fixtures_loadable_by_server(self):
        """Hardened generated fixtures have correct structure for server to load."""
        builder = TenantBuilder.hardened_gcc_moderate()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixtures_dir = Path(tmpdir)
            builder.build(fixtures_dir)

            # Verify CA policies structure
            with open(fixtures_dir / "conditional_access_policies.json") as f:
                ca_data = json.load(f)

            assert "@odata.context" in ca_data
            assert "value" in ca_data
            assert len(ca_data["value"]) == 8  # Hardened has 8 CA policies

            # Verify all policies have required fields
            for policy in ca_data["value"]:
                assert "id" in policy
                assert "displayName" in policy
                assert "state" in policy
                assert "conditions" in policy

            # Verify managed devices
            with open(fixtures_dir / "managed_devices.json") as f:
                devices_data = json.load(f)

            assert len(devices_data["value"]) == 3
            for device in devices_data["value"]:
                assert "id" in device
                assert "deviceName" in device
                assert "complianceState" in device
