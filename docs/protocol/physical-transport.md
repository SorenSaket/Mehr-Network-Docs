---
sidebar_position: 1
title: "Layer 0: Physical Transport"
---

# Layer 0: Physical Transport

Mehr requires a transport layer that provides transport-agnostic networking over any medium supporting at least a half-duplex channel with ≥5 bps throughput and ≥500 byte MTU. The transport layer is a swappable implementation detail — Mehr defines the interface it needs, not the implementation.

## Transport Requirements

The transport layer must provide:

- **Any medium is a valid link**: LoRa, LTE-M, NB-IoT, WiFi, Ethernet, serial, packet radio, fiber, free-space optical
- **Multiple simultaneous interfaces**: A node can bridge between transports automatically
- **Announce-based routing**: No manual configuration of addresses, subnets, or routing tables
- **Mandatory encryption**: All traffic is encrypted; unencrypted packets are dropped as invalid
- **Sender anonymity**: No source address in packets
- **Constrained-link operation**: Functional at ≥5 bps

## Current Implementation: Reticulum

The current transport implementation uses the [Reticulum Network Stack](https://reticulum.network/), which satisfies all requirements above and is proven on links as slow as 5 bps. Mehr extends it with [CompactPathCost](network-protocol#mehr-extension-compact-path-cost) annotations on announces and an economic layer above.

Reticulum is an implementation choice, not an architectural dependency. Mehr extensions are carried as opaque payload data within Reticulum's announce DATA field — a clean separation that allows the transport to be replaced with a clean-room implementation in the future without affecting any layer above.

### Participation Levels

Not all nodes need to understand Mehr extensions. Three participation levels coexist on the same mesh:

| Level | Node Type | Understands | Earns MHR | Marketplace |
|-------|-----------|-------------|-----------|-------------|
| **L0** | Transport-only | Wire protocol only | No | No |
| **L1** | Mehr Relay | L0 + CompactPathCost + stochastic rewards | Yes (relay only) | No |
| **L2** | Full Mehr | Everything | Yes | Yes |

**L0 nodes** relay packets and forward announces (including Mehr extensions as opaque bytes) but do not parse economic extensions, earn rewards, or participate in the marketplace. They are zero-cost hops from Mehr's perspective. This ensures the mesh works even when some nodes run the transport layer alone.

**L1 nodes** are the minimum viable Mehr implementation — they parse CompactPathCost, run the VRF relay lottery, and maintain payment channels. This is the target for ESP32 firmware.

**L2 nodes** implement the full protocol stack including capability marketplace, storage, compute, and application services.

### Implementation Strategy

| Platform | Implementation |
|---|---|
| Raspberry Pi, desktop, phone | Rust implementation (primary) |
| ESP32, embedded | Rust `no_std` implementation (L1 minimum) |

All implementations speak the same wire protocol and interoperate on the same network.

## Supported Transports

| Transport | Typical Bandwidth | Typical Range | Duplex | Notes |
|---|---|---|---|---|
| **LoRa (ISM band)** | 0.3-50 kbps | 2-15 km | Half | Unlicensed, low power, high range. [RNode](https://reticulum.network/manual/hardware.html) as reference hardware. |
| **WiFi Ad-hoc** | 10-300 Mbps | 50-200 m | Full | Ubiquitous, short range |
| **WiFi P2P (directional)** | 100-800 Mbps | 1-10 km | Full | Point-to-point backbone links |
| **Cellular (LTE/5G)** | 1-100 Mbps | Via carrier | Full | Requires carrier subscription |
| **LTE-M** | 0.375-1 Mbps | Via carrier | Full | Licensed LPWAN; better building penetration than LoRa, carrier-managed |
| **NB-IoT** | 0.02-0.25 Mbps | Via carrier | Half | Licensed LPWAN; extreme range and battery life, carrier-managed |
| **Ethernet** | 100 Mbps-10 Gbps | Local | Full | Backbone, data center |
| **Serial (RS-232, AX.25)** | 1.2-56 kbps | Varies | Half | Legacy radio, packet radio |
| **Fiber** | 1-100 Gbps | Long haul | Full | Backbone |
| **Bluetooth/BLE** | 1-3 Mbps | 10-100 m | Full | Wearables, phone-to-phone |

A node can have **multiple interfaces active simultaneously**. The network layer selects the best interface for each destination based on cost, latency, and reliability.

## Multi-Interface Bridging

A node with both LoRa and WiFi interfaces automatically bridges between the two networks. Traffic arriving on LoRa can be forwarded over WiFi and vice versa.

The bridge node is where bandwidth characteristics change dramatically — and where the [capability marketplace](../marketplace/overview) becomes valuable. A bridge node can:

- Accept low-bandwidth LoRa traffic from remote sensors
- Forward it over high-bandwidth WiFi to a local network
- Earn relay rewards for the bridging service
- Advertise its bridging capability to nearby nodes

```mermaid
graph LR
    RS["Remote Sensor"] <-- "LoRa (10 kbps)" --> BN["Bridge Node"]
    BN <-- "WiFi (100 Mbps)" --> GW["Gateway"]
```

## Bandwidth Ranges and Their Implications

The 20,000x range between the slowest and fastest supported transports (500 bps to 10 Gbps) has profound implications for protocol design:

- **All protocol overhead must be budgeted.** Gossip, routing updates, and economic state consume bandwidth that could carry user data. On a 1 kbps LoRa link, every byte matters.
- **Data objects carry minimum bandwidth requirements.** A 500 KB image declares `min_bandwidth: 10000` (10 kbps). LoRa nodes never attempt to transfer it — they only propagate its hash and metadata.
- **Applications adapt to link quality.** The protocol provides link metrics; applications decide what to send based on available bandwidth.

## NAT Traversal

Residential nodes behind NATs (common for WiFi and Ethernet interfaces) are handled at the transport layer. The Reticulum transport uses its link establishment protocol to traverse NATs — an outbound connection from behind the NAT establishes a bidirectional link without requiring port forwarding or STUN/TURN servers.

For nodes that cannot establish outbound connections (rare), the announce mechanism still propagates their presence. Traffic destined for a NATed node is routed through a neighbor that does have a direct link — functionally equivalent to standard relay forwarding. No special NAT-awareness is needed at the Mehr protocol layers above transport.

## What Mehr Adds Above Transport

The transport layer provides packet delivery, routing, and encryption. Mehr adds everything above:

| Extension | Purpose |
|---|---|
| **[CompactPathCost](network-protocol#mehr-extension-compact-path-cost) on announces** | Enables economic routing — cheapest, fastest, or balanced path selection |
| **[Stochastic relay rewards](../economics/payment-channels)** | Incentivizes relay operators without per-packet payment overhead |
| **[Capability advertisements](../marketplace/overview)** | Makes compute, storage, and connectivity discoverable and purchasable |
| **[CRDT economic ledger](../economics/crdt-ledger)** | Tracks balances without consensus or blockchain |
| **[Trust graph](../economics/trust-neighborhoods)** | Enables free communication between trusted peers |
| **[Congestion control](network-protocol#congestion-control)** | CSMA/CA, per-neighbor fair sharing, priority queuing, backpressure |

These extensions ride on top of the transport's existing gossip and announce mechanisms, staying within the protocol's [bandwidth budget](network-protocol#bandwidth-budget).
