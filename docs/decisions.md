# m365-sim Design Decisions

## Decision Log

Each entry records a design question, the options considered, the resolution, and the rationale.

---

### DEC-001: Fixture Loading Strategy

**Date**: 2026-03-19
**Status**: PENDING
**Question**: Should fixture JSON files be loaded eagerly at server startup or lazily on first request?

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| A. Eager loading at startup | Simple dict lookup, startup errors surface immediately, no race conditions | Slightly slower startup (negligible for <500KB) |
| B. Lazy loading on first request | Marginally faster startup | Added complexity, first-request latency, potential race conditions |

**Resolution**:
**Rationale**:

---

### DEC-002: $filter Implementation Depth

**Date**: 2026-03-19
**Status**: PENDING
**Question**: Should the mock server ignore OData $filter query parameters or implement a minimal filter engine?

**Context**: Consumers use `$filter=userType eq 'Guest'` on `/users`, `$filter=securityEnabled eq true` on `/groups`, and `$filter=appId eq '...'` on `/servicePrincipals`.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| A. Ignore all filters, return full fixture | Simplest implementation, evaluators already handle full result sets | Won't catch filter-dependent bugs in evaluators |
| B. Minimal filter engine for `eq` comparisons | More realistic, catches evaluator assumptions about pre-filtered data | More code to maintain, risk of filter bugs in the mock itself |
| C. Option A for MVP, add B later if needed | Ship fast, add complexity only when proven necessary | Might mask real bugs until later |

**Resolution**:
**Rationale**:

---

### DEC-003: Stateful Write Operations

**Date**: 2026-03-19
**Status**: PENDING
**Question**: Should POST/PATCH operations mutate in-memory fixture state, or return fake responses without changing state?

**Context**: Deploy mode POSTs CA policies and PATCHes auth method configs. The hardened scenario represents the post-deploy state as a separate static fixture set.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| A. Stateless — fake responses only | Simple, hardened scenario is a separate fixture set, no reset mechanism needed | Can't test deploy-then-verify flows in a single test run |
| B. Stateful — writes mutate in-memory state | Enables deploy-then-verify testing, more realistic | Merge logic complexity, needs reset mechanism, harder to reason about test state |

**Resolution**:
**Rationale**:

---

### DEC-004: Integration Test Runner

**Date**: 2026-03-19
**Status**: PENDING
**Question**: Should smoke tests start the mock server as a subprocess (real HTTP) or use in-process ASGI transport?

**Context**: Consuming tools make real HTTP calls to the Graph API. The mock server needs to be reachable via HTTP for integration tests.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| A. Subprocess (real HTTP via httpx) | Tests real server startup, actual HTTP layer consumers use, catches port/process issues | Slower, potential port conflicts, process management in fixtures |
| B. In-process ASGI transport | Fast, no port conflicts, simpler fixture setup | Skips real HTTP layer, doesn't test server startup path |
| C. Both — subprocess for integration, ASGI for unit | Best coverage, fast unit tests + realistic integration tests | Two test patterns to maintain |

**Resolution**:
**Rationale**:

---

### DEC-005: TenantBuilder Timing

**Date**: 2026-03-19
**Status**: PENDING
**Question**: Should the TenantBuilder fluent API be part of the MVP or deferred until after greenfield/hardened fixtures and smoke tests are working?

**Context**: The kickoff spec provides exact JSON for greenfield and hardened scenarios. The builder generates fixture JSON programmatically as an alternative to hand-editing.

**Options**:
| Option | Pros | Cons |
|--------|------|------|
| A. Include in MVP (early phase) | Available immediately for generating test variants | No value until basic fixtures work, delays core deliverable |
| B. Defer to Phase 08 (after smoke tests) | Focus on core value first, builder becomes useful when we need custom scenarios for evaluator edge cases | Greenfield/hardened are hand-authored, could be error-prone without builder |

**Resolution**:
**Rationale**:
