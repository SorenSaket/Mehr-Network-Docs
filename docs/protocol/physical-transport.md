---
sidebar_position: 1
title: "Layer 0: Physical Transport"
description: Physical transport layer of the Mehr Network supporting LoRa, WiFi Direct, Bluetooth LE, Ethernet, and cellular with automatic medium selection.
keywords: [LoRa, WiFi, Bluetooth, physical layer, mesh transport]
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
:::tip[Key Insight]
The transport layer is a swappable implementation detail. Mehr defines the interface it needs (half-duplex, ≥5 bps, ≥500 byte MTU, mandatory encryption), not the implementation. All economic extensions ride as opaque payload in transport announces — the transport never needs to understand Mehr.
:::
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

:::caution[Trade-off]
Supporting 500 bps to 10 Gbps (a 20,000x range) means every protocol overhead byte must be budgeted. Data objects carry `min_bandwidth` requirements so large transfers are never attempted over constrained links — only hashes and metadata propagate on LoRa.
:::

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

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>Which radios should I buy to get started with Mehr?</summary>

The easiest entry point is an [RNode](https://reticulum.network/manual/hardware.html) — a LoRa-based radio that serves as the reference hardware for the transport layer. For higher bandwidth, any WiFi-capable device (Raspberry Pi, laptop, phone) can participate. You don’t need a specific radio to join — any supported transport works, and nodes with multiple interfaces bridge between them automatically.

</details>

<details className="faq-item">
<summary>What kind of range can I expect from LoRa?</summary>

LoRa typically achieves 2–15 km line-of-sight depending on antenna height, terrain, and power settings. In urban areas with buildings in the way, expect 1–5 km. Directional antennas and elevated mounting points dramatically improve range. For longer distances, WiFi point-to-point links can reach 1–10 km.

</details>

<details className="faq-item">
<summary>Can Mehr work over the regular internet, or does it require radio hardware?</summary>

Mehr works over any transport — including the internet. Ethernet, WiFi, and cellular connections all function as valid transports. You can run a Mehr node on a home computer connected to your router. Radio hardware (LoRa, packet radio) extends the network into areas without internet connectivity, but it’s not required.

</details>

<details className="faq-item">
<summary>What happens when a message crosses from LoRa to WiFi or vice versa?</summary>

Bridge nodes with multiple interfaces handle this transparently. A packet arriving on LoRa is forwarded over WiFi (or any other interface) by the bridge node. The sender and receiver don’t need to know which transports were used — the routing layer picks the best path automatically. The bridge node can earn relay rewards for providing this service.

</details>

<details className="faq-item">
<summary>Does mixing slow and fast transports create bottlenecks?</summary>

The protocol is designed for this. Data objects carry a `min_bandwidth` field that prevents large transfers from being attempted over slow links. A 500 KB image won’t be pushed over LoRa — only its hash and metadata propagate. Applications adapt to link quality in real time, degrading gracefully on constrained links and resuming full quality on fast ones.

</details>

<!-- faq-end -->
