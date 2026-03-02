---
sidebar_position: 5
title: "Design Rationale: Variable Packet Size & Route Probing"
description: "Design rationale for variable-size packets and route bandwidth/MTU probing in the Mehr mesh network."
keywords:
  - variable packet size
  - MTU discovery
  - route probing
  - bandwidth detection
  - LoRa constraints
  - protocol design
---

# Design Rationale: Variable Packet Size & Route Probing

:::info[Status]
**Specified in v1.0.** This page summarizes the design rationale. The normative specification lives in the pages linked below.
:::

## Problem

The Mehr wire format originally used a fixed 484-byte maximum packet size — constrained by LoRa's duty-cycle limits. This wastes 68–95% of WiFi/Ethernet frame capacity and limits throughput on high-bandwidth links.

Three questions drove this design:

1. Can nodes probe a route's bandwidth and maximum packet size?
2. Should the protocol support variable-size packets that adapt to the path?
3. Does designing around LoRa's tiny MTU hurt performance on higher-bandwidth transports?

## Decision

**Yes to all three.** The protocol defines three transport classes (Constrained 484 B, Standard 1,500 B, Bulk 4,096 B) negotiated per-link via `LinkCapabilities`. Path MTU propagates passively through `bottleneck_mtu` in CompactPathCost announces. Active probing is opt-in and rate-limited.

Fragmentation is deferred — application-layer chunking (MHR-Store 4 KB chunks) is simpler and avoids reassembly buffer pressure on constrained devices.

## Key Trade-offs

| Choice | Benefit | Cost |
|--------|---------|------|
| Transport classes instead of global MTU | 3–8.5× throughput on fast links | Per-link negotiation complexity |
| Passive MTU via announces | Zero additional bandwidth | 1 extra byte per announce |
| Active probing opt-in | Real-time path measurement | Bandwidth cost; rate-limited to 1/min |
| Deferred fragmentation | Simpler, no reassembly buffers | Cross-transport paths (WiFi→LoRa→WiFi) must size to bottleneck |
| LoRa retains fixed-size padding | Traffic analysis resistance on RF | No variable-size benefit on constrained links |

## Specified In

| Topic | Specification Page |
|-------|-------------------|
| Transport classes, LinkCapabilities, Path MTU | [Physical Transport — Transport Classes](/docs/L0-physical/physical-transport#transport-classes-and-variable-packet-sizes) |
| `bottleneck_mtu` in CompactPathCost | [Network Protocol — CompactPathCost](/docs/L1-network/network-protocol#mehr-extension-compact-path-cost) |
| Active route probing | [Network Protocol — Route Probing](/docs/L1-network/network-protocol#route-probing) |
| PacketTooBig signal | [Physical Transport — Path MTU Behavior](/docs/L0-physical/physical-transport#path-mtu-behavior) |
| Security considerations | [Physical Transport — Security](/docs/L0-physical/physical-transport#security-considerations) |
| FAQ | [Physical Transport — FAQ](/docs/L0-physical/physical-transport#frequently-asked-questions) |
