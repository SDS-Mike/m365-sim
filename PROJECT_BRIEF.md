# PROJECT_BRIEF.md

## Basic Information

- **Project Name**: m365-sim
- **Project Type**: api
- **Primary Goal**: A reusable Microsoft Graph API simulation platform for testing M365 compliance tools (primarily CMMC 2.0 L2 assessment workflows) against realistic tenant state without a live tenant.
- **Target Users**: Compliance tool integration test suites (immediate consumer), any M365 compliance or security tool developer (future consumers), CI/CD pipelines running automated compliance evaluator tests
- **Timeline**: 1 week
- **Team Size**: 1

## Functional Requirements

### Key Features (MVP)

- Phase 00 — Decision Log: Create docs/decisions.md recording resolution of 5 open design questions: (1) Fixture loading strategy (eager vs lazy), (2) $filter implementation depth (ignore vs minimal engine), (3) Stateful write operations (fake responses vs mutable state), (4) Integration test runner (subprocess vs in-process ASGI), (5) TenantBuilder timing (MVP vs deferred). Each decision must include the question, options considered, resolution, and rationale. This phase requires prompting the user to discuss and decide each question before proceeding.
- Phase 01 — Repo Bootstrap: Create directory structure (scenarios/gcc-moderate/greenfield/, scenarios/gcc-moderate/hardened/, scenarios/gcc-moderate/partial/, scenarios/gcc-high/greenfield/, builder/, sdk/, tests/, docs/), requirements.txt (fastapi, uvicorn, pytest, httpx), .gitignore, README.md stub, sdk/__init__.py
- Phase 02 — Server Scaffold: Single-file FastAPI server (server.py) with CLI args (--scenario default greenfield, --cloud default gcc-moderate, --port default 8888), startup fixture loading from scenarios/{cloud}/{scenario}/*.json, Bearer token auth check (any token accepted, 401 if missing Authorization header), 404 handler returning JSON with requested path, unmapped path warning logging
- Phase 03 — Route Table: Map all ~40 Graph API endpoints to fixture files — strip /v1.0/ prefix before matching. GET endpoints: /users, /users with $filter, /me, /me/authentication/methods, /users/{id}/authentication/methods, /devices, /deviceManagement/managedDevices, /deviceManagement/deviceCompliancePolicies, /deviceManagement/deviceConfigurations, /deviceManagement/deviceEnrollmentConfigurations, /identity/conditionalAccess/policies, /identity/conditionalAccess/namedLocations, /directoryRoles, /directoryRoles/{id}/members, /roleManagement/directory/roleAssignments, /roleManagement/directory/roleDefinitions, /roleManagement/directory/roleEligibilitySchedules, /roleManagement/directory/roleAssignmentSchedules, /policies/authenticationMethodsPolicy and sub-paths (microsoftAuthenticator, fido2, temporaryAccessPass), /auditLogs/signIns, /auditLogs/directoryAudits, /security/incidents, /security/alerts_v2, /security/secureScores, /security/secureScoreControlProfiles, /applications, /servicePrincipals, /groups, /organization, /domains, /informationProtection/policy/labels. Query param handling: $top=N truncates value array, $filter/$select/$expand logged but ignored. Write stubs: POST conditionalAccess/policies returns 201 with added id+createdDateTime, PATCH auth method configs returns 200, POST deviceManagement policies/configs returns 201. Error simulation: ?mock_status=429/403/404. X-Mock-Cloud header override.
- Phase 04 — Greenfield Fixture Set: All JSON fixture files for fresh G5 GCC Moderate tenant per kickoff spec — organization.json (Contoso Defense LLC, G5 assigned plans), users.json (Mike Morris GA + BreakGlass Admin), me.json, me_auth_methods.json (Authenticator + password, no FIDO2), conditional_access_policies.json (empty), auth_methods_policy.json (all disabled), managed_devices.json (empty), compliance_policies.json (empty), device_configurations.json (empty), secure_scores.json (currentScore 12.0/198.0), audit_sign_ins.json (one setup entry), audit_directory.json (empty), security_incidents.json (empty), security_alerts.json (empty), information_protection_labels.json (empty), directory_roles.json (GA, Security Admin, Compliance Admin, Global Reader + other built-ins), role_assignments.json (GA only), role_definitions.json, role_eligibility_schedules.json (empty), role_assignment_schedules.json (empty), applications.json, service_principals.json (Microsoft Graph SP + common pre-populated SPs), groups.json (empty), domains.json (contoso-defense.com + onmicrosoft.com), device_enrollment_configurations.json (empty), named_locations.json (empty), secure_score_control_profiles.json
- Phase 05 — Smoke Tests: tests/test_server.py using pytest + httpx. Pytest fixture starts server as subprocess on random port, waits for health, yields base URL, kills on teardown. Test every GET endpoint returns HTTP 200 with value key (or correct shape for singleton endpoints like /me). Test auth: request without Authorization header returns 401. Test $top truncation. Test write endpoints return correct status codes. Test error simulation (?mock_status=429 returns 429 with Retry-After header). Test 404 handler returns JSON with path.
- Phase 06 — Hardened Fixture Set: Delta from greenfield — conditional_access_policies.json with 8 CMMC policies all in enabledForReportingButNotEnforced state with break-glass excluded, auth_methods_policy.json with microsoftAuthenticator/temporaryAccessPass/fido2 all enabled, managed_devices.json with 3 devices (2 Windows compliant, 1 iOS compliant), compliance_policies.json with CMMC-Windows/iOS/Android policies, device_configurations.json with CMMC-ASR-Rules and CMMC-Defender-AV, me_auth_methods.json with added FIDO2 key. All other fixtures inherited/symlinked from greenfield.
- Phase 07 — GCC High Scaffold: Create scenarios/gcc-high/greenfield/ directory structure, _README.md documenting endpoint URL differences (graph.microsoft.us vs graph.microsoft.com, login.microsoftonline.us vs login.microsoftonline.com), known endpoint availability gaps. Copy greenfield fixture structure with all files marked as TODO placeholders.
- Phase 08 — TenantBuilder Fluent API: builder/tenant_builder.py — programmatic tenant state construction as alternative to hand-editing JSON. Methods like TenantBuilder().with_users([...]).with_ca_policies([...]).with_devices([...]).build() that generates fixture-compatible JSON files. Convenience presets: .greenfield_gcc_moderate() and .hardened_gcc_moderate(). Output to a scenario directory that server.py can load.

### Nice-to-Have Features (v2)

- OSCAL Component Definition generation from fixture data
- Partial scenario (mid-deployment state between greenfield and hardened)
- Commercial E5 cloud target with appropriate license SKUs
- Hot-reload of fixture files without server restart
- Stateful write operations that mutate in-memory fixture state for deploy-then-verify test flows
- Docker container packaging for CI environments
- Integration test harness (pytest fixture that runs a compliance assessment binary against mock server and asserts SPRS score ranges: greenfield -170 to -210, hardened -40 to -80)

## Technical Constraints

### Must Use

- Python 3.11+
- FastAPI
- uvicorn
- pytest
- httpx (test client)

### Cannot Use

- Django
- Flask
- database engines (all data is static JSON fixtures)

## Other Constraints

- MVP scope is GCC Moderate only — GCC High and Commercial E5 are scaffolded but not populated
- server.py must be a single-file FastAPI server runnable with uvicorn server:app --port 8888
- Fixture data must match real Microsoft Graph API response shapes exactly (consumers deserialize into typed structs)
- All fixture JSON must include @odata.context fields matching real Graph API responses
- Write operations return fake responses without mutating fixture state in MVP
- Auth accepts any Bearer token without validation — returns 401 only if Authorization header is missing entirely
- Hardened scenario CA policies MUST use state enabledForReportingButNotEnforced not enabled (matches real initial remediation deploy state)
- GCC Moderate uses standard Graph URLs (graph.microsoft.com) — it is NOT a sovereign cloud
- Greenfield tenant uses Contoso Defense LLC identity with contoso-defense.com domain throughout all fixtures

## Success Criteria

- All MVP features implemented and working
- Code passes linting and type checking
- Test coverage >= 80%
- Documentation complete

---

*Generated by DevPlan MCP Server*
