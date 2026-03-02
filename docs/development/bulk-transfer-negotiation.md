---
sidebar_position: 7
title: "Design Rationale: Bulk Transfer Pre-Negotiation"
description: "Design rationale for probe response anonymity and bulk transfer pre-negotiation with progressive escrow."
keywords:
  - bulk transfer
  - bandwidth reservation
  - pre-negotiation
  - prepayment
  - probe anonymity
  - route probing
  - privacy
---

# Design Rationale: Bulk Transfer Pre-Negotiation

:::info[Status]
**Specified in v1.0.** This page summarizes the design rationale. The normative specification lives in the pages linked below.
:::

## Problem

Two related questions:

1. **Does route probing expose the sender's identity to the relay chain?** — Probe responses must travel back; does this leak who initiated the probe?
2. **Can we pre-negotiate an entire bulk transfer?** — Reserve bandwidth, agree on cost, and stream data with reduced per-packet overhead?

## Decisions

### Probe Anonymity

**No exposure.** Reverse-path routing means each relay only knows its immediate neighbors, not the probe originator. The response follows cached forwarding entries (`destination_hash + probe_id` → incoming interface), which expire after `3 × worst_latency_ms`. This is identical to the anonymity model for regular data packets — no source address in the packet.

### Bandwidth Reservation

**Yes — hop-by-hop propagation preserves anonymity.** The sender negotiates only with its direct neighbor, who independently propagates the reservation to the next hop. The sender never learns the path structure. Key design choices:

| Choice | Rationale |
|--------|-----------|
| Progressive escrow (10% upfront, per-chunk) | Aligns incentives — relay must deliver to earn. Full prepayment creates moral hazard. |
| VRF bypass during reservations | Eliminates ~666K VRF ops per GB; per-chunk deterministic payment is cheaper |
| No `hop_count` in commitment | Prevents sender from learning path length (deanonymization risk) |
| 60s inactivity = non-refundable escrow | Anti-DoS: bandwidth squatting costs real MHR |
| `allow_reroute` flag | Relay-initiated renegotiation if a ≥25% cheaper or ≥50% faster path appears |

### When Reservations vs. Stochastic Relay

| Transfer size | Recommendation |
|---------------|----------------|
| < 100 KB | Stochastic (default) |
| 100 KB – 1 MB | Either |
| 1 MB – 100 MB | Reservation beneficial |
| > 100 MB | Reservation strongly recommended |
| > 1 GB | Reservation + LargestMTU policy |

## Specified In

| Topic | Specification Page |
|-------|-------------------|
| Probe response routing | [Network Protocol — Probe Response Routing](/docs/L1-network/network-protocol#probe-response-routing) |
| Bandwidth reservation wire format | [Network Protocol — Bandwidth Reservation](/docs/L1-network/network-protocol#bandwidth-reservation) |
| Progressive escrow payment model | [Payment Channels — Reservation Payment](/docs/L3-economics/payment-channels#reservation-payment-progressive-escrow) |
| Reservation as capability agreement | [Marketplace Agreements — Bandwidth Reservations](/docs/L4-marketplace/agreements#bandwidth-reservations-as-agreements) |
| Security considerations | [Network Protocol — Security](/docs/L1-network/network-protocol#security-considerations) |
| FAQ | [Network Protocol — FAQ](/docs/L1-network/network-protocol#frequently-asked-questions) |
| Protocol constants | [Specification — Protocol Constants](../specification#protocol-constants) |
