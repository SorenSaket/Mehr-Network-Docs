---
sidebar_position: 1
title: "Layer 0: Physical Transport"
---

# Layer 0: Physical Transport

NEXUS builds on the [Reticulum Network Stack](https://reticulum.network/) for its transport and link layers. Reticulum provides transport-agnostic networking over any medium that supports at least a half-duplex channel with ≥5 bps throughput and ≥500 byte MTU. NEXUS extends Reticulum with cost annotations and economic primitives.

## Reticulum as Foundation

Reticulum already solves the hard problems of transport abstraction:

- **Any medium is a valid link**: LoRa, WiFi, Ethernet, serial, packet radio, fiber, free-space optical
- **Multiple simultaneous interfaces**: A node can bridge between transports automatically
- **Announce-based routing**: No manual configuration of addresses, subnets, or routing tables
- **Mandatory encryption**: All traffic is encrypted; unencrypted packets are dropped as invalid
- **Sender anonymity**: No source address in packets
- **Proven at 5 bps**: Tested on extremely constrained radio links

NEXUS uses Reticulum's transport interface, destination model, and link establishment. It extends the protocol with cost annotations on announces and an economic layer above.

### Implementation Strategy

| Platform | Implementation |
|---|---|
| Raspberry Pi, desktop, phone | Reticulum Python reference implementation (or compatible) |
| ESP32, embedded | Rust implementation of Reticulum wire protocol (`no_std`) |

Both implementations speak the same wire protocol and interoperate on the same network. The Rust implementation targets devices that cannot run Python.

## Supported Transports

| Transport | Typical Bandwidth | Typical Range | Duplex | Notes |
|---|---|---|---|---|
| **LoRa (ISM band)** | 0.3-50 kbps | 2-15 km | Half | Unlicensed, low power, high range. [RNode](https://reticulum.network/manual/hardware.html) as reference hardware. |
| **WiFi Ad-hoc** | 10-300 Mbps | 50-200 m | Full | Ubiquitous, short range |
| **WiFi P2P (directional)** | 100-800 Mbps | 1-10 km | Full | Point-to-point backbone links |
| **Cellular (LTE/5G)** | 1-100 Mbps | Via carrier | Full | Requires carrier subscription |
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

```
                    LoRa (10 kbps)              WiFi (100 Mbps)
  [Remote Sensor] ←───────────────→ [Bridge Node] ←──────────────→ [Gateway]
                                         │
                                    Bridges between
                                    two transports
```

## Bandwidth Ranges and Their Implications

The 20,000x range between the slowest and fastest supported transports (500 bps to 10 Gbps) has profound implications for protocol design:

- **All protocol overhead must be budgeted.** Gossip, routing updates, and economic state consume bandwidth that could carry user data. On a 1 kbps LoRa link, every byte matters.
- **Data objects carry minimum bandwidth requirements.** A 500 KB image declares `min_bandwidth: 10000` (10 kbps). LoRa nodes never attempt to transfer it — they only propagate its hash and metadata.
- **Applications adapt to link quality.** The protocol provides link metrics; applications decide what to send based on available bandwidth.

## What NEXUS Adds to Reticulum

Reticulum provides transport, routing, and encryption. NEXUS extends it with:

| Extension | Purpose |
|---|---|
| **Cost annotations on announces** | Enables economic routing — cheapest, fastest, or balanced path selection |
| **Stochastic relay rewards** | Incentivizes relay operators without per-packet payment overhead |
| **Capability advertisements** | Makes compute, storage, and connectivity discoverable and purchasable |
| **CRDT economic ledger** | Tracks balances without consensus or blockchain |
| **Trust graph** | Enables free communication between trusted peers |

These extensions ride on top of Reticulum's existing gossip and announce mechanisms, staying within the protocol's bandwidth budget.
