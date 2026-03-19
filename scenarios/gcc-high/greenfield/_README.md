# GCC High Greenfield Scenario

## Overview

This directory contains fixture files for a **GCC High** sovereign cloud tenant in greenfield state. GCC High (Government Community Cloud High) is a separate instance of Microsoft 365 designed exclusively for U.S. federal customers with specific security and compliance requirements.

## Key Characteristics

### Sovereign Cloud
- **Dedicated infrastructure**: GCC High runs on isolated, U.S.-based data centers separate from commercial Azure and GCC Moderate clouds
- **Data residency**: All data resides within the United States (IL4/IL5 security requirements)
- **Isolated identities**: Users and applications are managed separately from commercial Azure AD/Entra
- **Separate tenant ecosystem**: Tenants cannot interoperate with commercial cloud resources

### Compliance & Standards
- **FedRAMP High**: All services must meet FedRAMP High baseline controls
- **CJIS**: Criminal Justice Information Services compliance
- **IL4/IL5**: Information Assurance Level 4 (Controlled Information) and Level 5 (Secret Information) support
- **Audit logging**: Enhanced audit trail retention for federal compliance

## Graph API Endpoints

### Base URLs
- **GCC High Graph API**: `https://graph.microsoft.us/v1.0`
- **GCC Moderate Graph API**: `https://graph.microsoft.com/v1.0` (different)

### Authentication
- **GCC High Auth URL**: `https://login.microsoftonline.us`
- **GCC Moderate Auth URL**: `https://login.microsoftonline.com` (different)

### Metadata Context
All responses must use `graph.microsoft.us` in the `@odata.context` field:
```json
{
  "@odata.context": "https://graph.microsoft.us/v1.0/$metadata#users",
  "value": []
}
```

## Endpoint Availability Differences

### Availability in GCC High vs. GCC Moderate

| Resource | GCC High | GCC Moderate | Notes |
|----------|----------|-------------|-------|
| Users | ✓ | ✓ | Full parity |
| Groups | ✓ | ✓ | Full parity |
| Organization | ✓ | ✓ | Full parity |
| Conditional Access Policies | ✓ | ✓ | Full parity |
| Devices | ✓ | ✓ | Full parity |
| Directory Roles | ✓ | ✓ | Full parity |
| Service Principals | ✓ | ✓ | Full parity |
| Application Objects | ✓ | ✓ | Full parity |
| Domains | ✓ | ✓ | Full parity |
| Authentication Methods | ✓ | ✓ | Full parity |
| Security Alerts | ✓ | ✓ | Full parity |
| Compliance Policies | ✓ | ✓ | Full parity |
| Information Protection Labels | ~ | ~ | Limited feature availability |
| Secure Score | ✓ | ✓ | Full parity |

### Notes
- Most Microsoft Graph endpoints reach feature parity between GCC High and GCC Moderate
- Some newer features may be deployed to GCC Moderate before GCC High due to compliance vetting
- Sovereign cloud-specific endpoints (e.g., GCC High-only compliance controls) are rare

## Fixture Status

### Placeholder Fixtures
All fixtures in this directory are currently **placeholder stubs** with the following structure:

```json
{
  "@odata.context": "https://graph.microsoft.us/v1.0/$metadata#<resource>",
  "_TODO": "Populate with GCC High-specific fixture data",
  "value": []
}
```

The `_TODO` field documents what data should be populated when this fixture is fully implemented.

### Implementation Roadmap

| Fixture | Status | Priority | Notes |
|---------|--------|----------|-------|
| users.json | TODO | High | Core identity data |
| groups.json | TODO | High | Group memberships |
| organization.json | TODO | High | Tenant organization |
| conditional_access_policies.json | TODO | High | CA policy compliance |
| devices.json | TODO | High | Device inventory |
| managed_devices.json | TODO | Medium | Intune-managed devices |
| directory_roles.json | TODO | High | RBAC role definitions |
| role_assignments.json | TODO | High | Admin role assignments |
| service_principals.json | TODO | Medium | Enterprise app principals |
| applications.json | TODO | Medium | Application objects |
| domains.json | TODO | High | Verified tenant domains |
| auth_methods_policy.json | TODO | Medium | Authentication policy |
| compliance_policies.json | TODO | Medium | Device compliance |
| device_configurations.json | TODO | Medium | Device configuration profiles |
| information_protection_labels.json | TODO | Low | Sensitivity labels |
| secure_score_control_profiles.json | TODO | High | Secure Score framework |
| secure_scores.json | TODO | High | Secure Score metrics |
| All others | TODO | Low | Audit, incidents, alerts |

### Why Placeholders?

1. **Scenario isolation**: GCC High is a separate cloud ecosystem; fixtures will reflect cloud-specific tenant characteristics
2. **Compliance accuracy**: GCC High fixtures must strictly conform to FedRAMP High + IL4/IL5 compliance profiles
3. **Sovereign data**: Real GCC High data is compartmentalized; synthetic fixtures ensure no real data is exposed
4. **Future-proofing**: Placeholder stubs allow server routes to be tested without full fixture implementation

## Running with GCC High

Start the server with the GCC High cloud target:

```bash
python server.py --cloud gcc-high
```

Or with explicit scenario and cloud:

```bash
python server.py --scenario greenfield --cloud gcc-high --port 8888
```

## Example Request

```bash
curl -X GET \
  -H "Authorization: Bearer test-token" \
  http://localhost:8888/v1.0/users
```

Response (placeholder):
```json
{
  "@odata.context": "https://graph.microsoft.us/v1.0/$metadata#users",
  "_TODO": "Populate with GCC High-specific fixture data",
  "value": []
}
```

## References

- [Microsoft GCC High Overview](https://docs.microsoft.com/en-us/office365/servicedescriptions/office-365-platform-service-description/office-365-us-government/gcc-high-and-dod)
- [FedRAMP High Baseline Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [Information Assurance Level (IAL) Framework](https://www.nist.gov/publications/risk-management-framework-information-and-systems)
