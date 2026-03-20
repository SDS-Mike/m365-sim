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

All 29 fixtures in this directory contain **real data** representing a greenfield GCC High tenant ("Contoso Defense Federal LLC", domain `contoso-defense.us`). Populated in Phase 16.

### Tenant Identity
- **Organization**: Contoso Defense Federal LLC
- **Primary domain**: `contoso-defense.us`
- **OnMicrosoft domain**: `contosodefensefederal.onmicrosoft.us`
- **Users**: Federal Admin + BreakGlass Admin (2 users)
- **Secure Score**: 12.0 / 198.0 (fresh tenant)
- **Directory Roles**: 14 built-in roles
- **Service Principals**: 9 SPs including Microsoft Graph

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
