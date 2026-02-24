---
sidebar_position: 3
title: Capability Agreements
---

# Capability Agreements

When a requester finds a suitable provider through [discovery](discovery), they form a bilateral agreement. Agreements are between two parties only — no network-wide registration required.

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

## Agreement Types

| Capability | Typical Duration | Proof Method | Example |
|-----------|-----------------|--------------|---------|
| **Relay/Bandwidth** | Per-packet or ongoing | Delivery Receipt | "Route my packets for the next hour" |
| **Storage** | Hours to months | Challenge-Response | "Store this 10 MB file for 30 days" |
| **Compute** | Per-invocation | Result Hash | "Run Whisper on this audio file" |
| **Internet Gateway** | Ongoing | Heartbeat | "Proxy my traffic to the internet" |

## Negotiation

Negotiation is simple and local:

1. Consumer discovers provider via [capability discovery](discovery)
2. Consumer sends a request with desired terms (capability type, duration, max cost)
3. Provider responds with an offer (actual cost, constraints)
4. If acceptable, both parties sign the agreement
5. Service begins; payment flows through the channel

There is no auction, no bidding process, and no global price discovery. Prices are set by providers based on their own cost structure. Within [trust neighborhoods](../economics/community-zones), trusted peers often offer discounted or free services.
