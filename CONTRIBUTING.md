# Contributing to m365-sim

m365-sim is a Microsoft Graph API simulation platform for testing M365 compliance and security tools against realistic tenant state without requiring a live tenant. Contributions that make the simulation more accurate, more complete, and more useful across cloud targets are welcome.

---

## What We Want

### Fixture data corrections and additions

The most valuable contributions are improvements to the JSON fixture files. If you find that a Graph API response in the fixtures does not match what a real tenant actually returns — wrong field names, missing fields, incorrect default values, wrong `@odata.type` strings — please open a PR with the correction and a note about where you observed the real behavior (cloud target, license SKU, API version).

Specifically wanted:

- **GCC High endpoint gaps** — which endpoints behave differently, return different schemas, or are unavailable on `graph.microsoft.us`. Documentation of missing or degraded endpoints is as valuable as fixture data.
- **Commercial E5 fixture data** — the current fixtures target GCC Moderate G5. Commercial E5 tenants have different license SKU names and some behavioral differences worth capturing.
- **Realistic service principal lists** — a fresh tenant has approximately 40 Microsoft-managed service principals pre-populated before an admin touches anything. The current fixture is incomplete. PRs that expand this with accurate data from real tenants are welcome.
- **Edge case tenant states** — guest-heavy tenants, hybrid AD/Entra tenants, tenants with legacy authentication still present, tenants with PIM configured, tenants mid-migration between states.
- **DoD and GCC High scenarios** — the scaffold exists but fixture content is marked TODO. If you have access to these environments and can contribute accurate data, this is high-priority work.

### New scenarios

The current scenarios are `greenfield`, `hardened`, and `partial`. New scenarios representing distinct real-world tenant states are welcome. Good candidates: a tenant that has been compromised (for incident response tool testing), a tenant with a mix of compliant and non-compliant devices, a tenant with stale guest accounts, a tenant in a hybrid AD/Entra configuration.

### Bug fixes in the mock server

If the server misroutes a path, handles query parameters incorrectly, returns wrong HTTP status codes, or behaves differently from the real Graph API in ways that affect test accuracy, please file an issue or submit a fix.

### Documentation

If the Graph API behaves in ways that are undocumented or contradict Microsoft's official documentation — and you have observed this against a real tenant — document it in the relevant scenario's `_notes.md` file. Tribal knowledge about real API behavior is worth preserving.

---

## What We Will Decline

### Real tenant data

Do not submit fixture data copied directly from a real tenant. Scrub all of the following before submitting:

- Real tenant IDs, domain names, user UPNs, display names
- Real policy IDs, device IDs, object IDs of any kind
- Real IP addresses from audit logs
- Any string that identifies a real organization, person, or device

Use the fictional `contoso-defense.com` / `Contoso Defense LLC` tenant identity that the existing fixtures use, or introduce a clearly fictional identity. If you are unsure whether something is safe to include, leave it out.

### Tool-specific business logic

m365-sim is a general-purpose Graph API simulator. It does not know about any specific compliance tool's internal logic, scoring algorithms, or assessment methodologies. The simulator's job is to return realistic Graph API responses. What consuming tools do with those responses is out of scope. PRs that add behavior specific to any particular tool will be declined.

### Heavy dependencies

The server is intentionally minimal. PRs that add substantial dependencies for minor convenience will not be merged. If you believe a dependency is justified, explain why in the PR description before investing time in the implementation.

---

## Submitting Changes

### For fixture data corrections

1. Open an issue describing the discrepancy — what the fixture currently returns vs what a real tenant returns
2. Note the cloud target (GCC Moderate, GCC High, Commercial, DoD), license SKU, and API version where you observed the real behavior
3. Submit a PR with the correction, keeping the same fictional tenant identifiers used in the existing fixtures

### For new scenarios

1. Open an issue describing the tenant state the scenario represents and why it is a useful test case
2. Use the existing `greenfield` scenario as a structural reference
3. Include a `_README.md` in the scenario directory explaining what state the tenant is in and what kinds of tools or tests it is intended to support

### For server bugs

1. Open an issue with the mismatched behavior — expected response vs actual response, and the request that triggered it
2. If you have a fix, submit a PR with a test case that would have caught the bug

### For GCC High and DoD fixture data

This work is particularly sensitive because sovereign cloud tenants may have stricter data handling requirements. Before contributing fixture data from these environments, confirm with your organization that sharing sanitized configuration data in a public repository is permitted. When in doubt, contribute structural observations and schema differences in documentation form rather than fixture files.

---

## Code Style

- Python files follow PEP 8
- JSON fixtures use 2-space indentation
- Fictional identifiers follow the existing pattern: UUIDs in the form `00000000-0000-0000-0000-0000000000XX`, tenant domain `contoso-defense.com`
- No trailing whitespace, files end with a newline

---

## License

By submitting a contribution you agree that your contribution will be licensed under the Apache 2.0 license that covers this project. If you are contributing on behalf of an employer, confirm that your employer permits the contribution under these terms.

---

## A Note on Scope

This project exists because testing M365 compliance and security tooling against live tenants is slow, risky, and not reproducible. The goal is a simulation that is accurate enough to catch real bugs in tools before they touch real tenants. Contributions that serve that goal are welcome regardless of what tool you are building. Contributions that narrow the project toward any single tool's needs are not.
