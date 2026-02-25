---
sidebar_position: 3
title: Capability Agreements
---

# Capability Agreements

When a requester finds a suitable provider through [discovery](discovery), they form a bilateral agreement. Agreements are between two parties only — no network-wide registration required.

## Cost Structure

Agreements use a discriminated cost model that adapts to different capability types:

```
CostStructure: enum {
    PerByte {
        cost_per_byte: u64,         // μMHR per byte transferred
    },
    PerInvocation {
        cost_per_call: u64,         // μMHR per function invocation
        max_input_bytes: u32,       // cost covers up to this input size
    },
    PerDuration {
        cost_per_epoch: u64,        // μMHR per epoch of service
    },
    PerCycle {
        cost_per_million_cycles: u64, // μMHR per million compute cycles
        max_cycles: u64,             // hard limit
    },
}
```

| Capability | Typical CostStructure |
|-----------|----------------------|
| Relay / Bandwidth | `PerByte` |
| Storage | `PerDuration` |
| Compute (contract) | `PerCycle` |
| Compute (function) | `PerInvocation` |
| Internet gateway | `PerByte` or `PerDuration` |

## Agreement Structure

```
CapabilityAgreement {
    provider: NodeID,
    consumer: NodeID,
    capability: CapabilityType,     // compute, storage, relay, proxy
    payment_channel: ChannelID,     // existing bilateral channel
    cost: CostStructure,
    valid_until: Timestamp,

    proof_method: enum {
        DeliveryReceipt,            // for relay
        ChallengeResponse,          // for storage (random read challenges)
        ResultHash,                 // for compute (hash of output)
        Heartbeat,                  // for ongoing services
    },

    signatures: (Sig_Provider, Sig_Consumer),
}
```

## Key Properties

### Bilateral

Agreements are strictly between two parties. This means:

- No central registry of agreements
- No third party needs to be involved or informed
- Agreements can be formed and dissolved without network-wide coordination
- Privacy is preserved — only the two parties know the terms

### Payment-Linked

Every agreement references an existing [payment channel](../economics/payment-channels) between the two parties. Payment flows automatically as the service is delivered.

### Time-Bounded

Agreements have an expiration (`valid_until`). This prevents stale agreements from persisting when nodes move or go offline. Parties can renew by forming a new agreement.

### Proof-Verified

Each agreement specifies how the consumer verifies that the provider is actually delivering. See [Verification](verification) for details on each proof method.

## Agreement Lifecycle

```
Agreement states:
  Active:   now < valid_until                        — service is being delivered
  Expired:  now >= valid_until                       — no new service; grace period begins
  Grace:    expired + up to 1 gossip round (60s)     — allows in-flight operations to complete
  Closed:   after grace period                       — agreement is fully terminated
```

### Expiry Behavior

| Capability | On Expiry | Grace Period |
|-----------|-----------|-------------|
| **Relay/Bandwidth** | No new packets routed after `valid_until` | In-flight packets in queue are delivered (up to 60s drain) |
| **Storage** | No new writes accepted | Data remains stored for 1 additional epoch; then subject to [garbage collection](../services/mhr-store#garbage-collection) |
| **Compute** | No new invocations accepted | Running invocations complete; results remain retrievable for 60s |
| **Internet Gateway** | Connection torn down at `valid_until` | In-flight TCP streams drained for up to 60s |

### Renewal

To renew, the consumer sends a new `CapabilityRequest` before the current agreement expires. If terms are unchanged, the provider can respond with a `CapabilityOffer` that extends `valid_until` — no full re-negotiation needed. If terms change, both parties sign a new `CapabilityAgreement`.

### Billing Boundaries

- **PerByte / PerInvocation / PerCycle**: Charged for actual usage up to `valid_until`. No charge after expiry.
- **PerDuration**: Charged for completed epochs only. Partial epochs at agreement end are not billed.

## Agreement Types

| Capability | Typical Duration | Proof Method | Example |
|-----------|-----------------|--------------|---------|
| **Relay/Bandwidth** | Per-packet or ongoing | Delivery Receipt | "Route my packets for the next hour" |
| **Storage** | Hours to months | Challenge-Response | "Store this 10 MB file for 30 days" |
| **Compute** | Per-invocation | Result Hash | "Run Whisper on this audio file" |
| **Internet Gateway** | Ongoing | Heartbeat | "Proxy my traffic to the internet" |

## Negotiation

Negotiation is **single-round** (take-it-or-leave-it) and strictly local — no auction, no bidding, no global price discovery:

```
Negotiation protocol:
  1. Consumer sends CapabilityRequest to provider
  2. Provider responds with CapabilityOffer (or Reject)
  3. Consumer accepts (signs) or walks away
  4. If accepted: both signatures form the CapabilityAgreement
  5. Service begins; payment flows through the channel

CapabilityRequest {
    consumer: NodeID,
    capability: CapabilityType,       // compute, storage, relay, proxy
    desired_cost: CostStructure,      // max cost consumer will accept
    desired_duration: u32,            // seconds
    payment_channel: ChannelID,       // existing channel with this provider
    proof_preference: ProofMethod,    // DeliveryReceipt, ChallengeResponse, etc.
    nonce: u64,                       // replay prevention
}
// Signed by consumer

CapabilityOffer {
    request_nonce: u64,               // matches the request
    provider: NodeID,
    actual_cost: CostStructure,       // provider's terms (≤ desired_cost, or reject)
    valid_until: Timestamp,           // agreement expiration
    proof_method: ProofMethod,        // may differ from preference
    constraints: Option<Vec<u8>>,     // provider-specific (e.g., max object size)
}
// Signed by provider
```

**Timeout**: If the provider doesn't respond within 30 seconds (or 3 gossip rounds on constrained links), the request is considered rejected. The consumer may retry with a different provider.

**No counter-offers**: The provider either meets or undercuts the consumer's desired cost, or rejects. This keeps negotiation to a single round-trip — critical for LoRa where each message takes seconds. If the consumer wants to negotiate, they send a new request with adjusted terms.

Prices are set by providers based on their own cost structure. Within [trust neighborhoods](../economics/trust-neighborhoods), trusted peers often offer discounted or free services.
