---
sidebar_position: 2
title: Meshtastic Bridge
description: "Transport-level bridge between Mehr and Meshtastic, enabling access to thousands of deployed LoRa nodes worldwide."
keywords:
  - Meshtastic
  - LoRa
  - bridge
  - transport
  - radio
  - mesh hardware
---

# Meshtastic Bridge

Meshtastic is the highest-priority bridge target for Mehr. Tens of thousands of LoRa nodes are already deployed worldwide — cheap, solar-powered, community-operated. A transport-level bridge between Mehr and Meshtastic gives Mehr instant access to physical radio infrastructure without waiting for dedicated Mehr hardware deployments.

## Why Meshtastic First

| Factor | Detail |
|--------|--------|
| **Same physical layer** | Both use LoRa on ISM bands (868/915 MHz). Same radios, same antennas, same propagation characteristics. |
| **Massive hardware base** | LILYGO T-Beam, Heltec WiFi LoRa 32, RAK WisBlock — the same boards listed in Mehr's [reference designs](../hardware/reference-designs). Many are already deployed and powered. |
| **Low barrier** | No firmware changes needed on existing Meshtastic nodes for basic L0 relay. Bridge nodes handle translation. |
| **Complementary features** | Meshtastic provides GPS tracking, channel-based messaging, range testing. Mehr adds economics, storage, compute, and E2E encryption. |
| **Community alignment** | Open-source, community-driven, off-grid focused. Same user base. |

## Integration Architecture

The bridge operates at the **transport level** — deeper than a typical protocol bridge. Rather than translating application-layer messages, it translates at the packet/frame level, allowing Meshtastic nodes to participate as physical infrastructure in the Mehr mesh.

### Three Integration Modes

#### Mode 1: Meshtastic as L0 Transport (Opaque Relay)

Meshtastic nodes forward Mehr packets as opaque payloads without understanding them.

```
[Mehr L2 Node]                                            [Mehr L2 Node]
      │                                                         ▲
      ▼                                                         │
[Bridge Node]                                             [Bridge Node]
  Mehr L1 +        LoRa mesh (Meshtastic)                  Mehr L1 +
  Meshtastic    ═══════════════════════════════            Meshtastic
  firmware      [MT Node] → [MT Node] → [MT Node]        firmware
                   L0          L0          L0
```

**How it works**:

1. Bridge node runs dual firmware: Mehr L1 + Meshtastic
2. Mehr packet arrives at bridge node via Mehr routing
3. Bridge encapsulates it as a Meshtastic `TEXT_MESSAGE_APP` or custom `PRIVATE_APP` portnum payload
4. Meshtastic mesh forwards it using Meshtastic's own flood/routing
5. Destination bridge node extracts the Mehr packet and delivers it to the Mehr network

**Meshtastic payload format**:

```
MehrOverMeshtastic {
    magic: u16 = 0x4D48,             // "MH" — identifies Mehr payload
    version: u8,                      // encapsulation version
    flags: u8,                        // fragmentation, priority
    fragment_id: u16,                 // for payloads exceeding Meshtastic MTU
    fragment_offset: u8,              // fragment sequence
    fragment_total: u8,               // total fragments
    payload: [u8],                    // Mehr packet (encrypted, opaque to MT nodes)
}
```

**MTU handling**: Meshtastic's maximum payload is ~228 bytes (varies by region/settings). Mehr packets that exceed this are fragmented at the bridge and reassembled at the destination bridge. The `fragment_id` field allows interleaving fragments from different Mehr packets.

**Key property**: Existing Meshtastic nodes require **zero changes**. They see a Meshtastic packet and forward it like any other. The Mehr content is opaque — encrypted and meaningless to nodes that don't understand it.
:::tip[Key Insight]
Mode 1 (opaque relay) gives Mehr instant access to the entire deployed Meshtastic network with zero firmware changes. Existing nodes forward Mehr packets as regular Meshtastic messages — they never need to understand the content.
:::
#### Mode 2: Meshtastic Nodes as Mehr L0 (Firmware Extension)

A lightweight firmware module lets Meshtastic nodes understand Mehr's announce format and participate in Mehr routing as L0 transport nodes.

```
[Mehr L2]  ←→  [Mehr L1]  ←→  [MT+L0]  ←→  [MT+L0]  ←→  [Mehr L1]  ←→  [Mehr L2]
                                  │              │
                            Meshtastic      Meshtastic
                            firmware +      firmware +
                            Mehr L0 module  Mehr L0 module
```

**What the L0 module does**:

- Recognizes Mehr announce packets (by magic bytes in the Meshtastic payload)
- Forwards them using Meshtastic's mesh routing (opaque byte forwarding)
- Reports link quality metrics (RSSI, SNR, hop count) that bridge nodes translate to [CompactPathCost](../protocol/network-protocol#mehr-extension-compact-path-cost)
- Does NOT parse economic extensions, run VRF lottery, or maintain payment channels

**Implementation**: ~2-5 KB of additional firmware on ESP32. The module hooks into Meshtastic's packet receive/forward pipeline and recognizes the `0x4D48` magic prefix.

**Benefit over Mode 1**: Better routing decisions. L0-aware Meshtastic nodes can prioritize Mehr traffic and report accurate link metrics, rather than treating Mehr packets as generic messages competing with Meshtastic traffic.

#### Mode 3: Dual-Protocol Node (Full Convergence)

A single device runs both Meshtastic and Mehr L1, sharing the same LoRa radio via time-division.

```
┌─────────────────────────────┐
│        Dual-Protocol Node    │
│                              │
│  ┌──────────┐  ┌──────────┐ │
│  │Meshtastic│  │ Mehr L1  │ │
│  │ Stack    │  │ Stack    │ │
│  └────┬─────┘  └────┬─────┘ │
│       │              │       │
│  ┌────┴──────────────┴────┐  │
│  │   Radio Time-Division   │  │
│  │   Manager (TDMA/slot)   │  │
│  └────────────┬───────────┘  │
│               │              │
│          [LoRa Radio]        │
│           SX1262/76          │
└─────────────────────────────┘
```

**Time-division approach**:

- Radio time is split between Meshtastic and Mehr traffic
- Default: 70% Meshtastic / 30% Mehr (configurable)
- Priority override: Mehr relay lottery wins get immediate transmission
- Listen periods are shared — both stacks receive all packets

**Why time-division, not frequency-division**: Most LoRa nodes have a single radio on a single frequency. Frequency splitting would halve bandwidth for both protocols. Time-division preserves full bandwidth for whichever protocol is transmitting.

**Target hardware**: ESP32-S3 with SX1262 (e.g., Heltec WiFi LoRa 32 V3, LILYGO T-Beam Supreme). These have enough flash (8 MB) and RAM (512 KB) for both stacks.

## Bridge Node Specification

A Meshtastic-Mehr bridge node is a physical device that participates in both networks. Minimum requirements:

| Component | Requirement |
|-----------|------------|
| **MCU** | ESP32-S3 (dual-core, 512 KB SRAM, 8 MB flash) |
| **Radio** | SX1262 LoRa transceiver |
| **Firmware** | Meshtastic + Mehr L1 (Mode 2 or 3) |
| **Power** | Solar viable (bridge adds ~15% power consumption over base Meshtastic) |
| **Cost** | $15-30 (same hardware as existing Meshtastic nodes) |

### Bridge Capabilities Advertised

The bridge node advertises itself in the Mehr [capability marketplace](../marketplace/overview):

```
NodeCapabilities {
    connectivity: {
        bandwidth_bps: 1200,          // LoRa link speed
        latency_ms: 2000,             // typical LoRa hop latency
        cost_per_byte: 10,            // μMHR per byte (higher than WiFi)
        internet_gateway: false,
    },
    bridge: {
        protocols: [Meshtastic],
        meshtastic_channels: 8,       // number of MT channels bridged
        meshtastic_region: "US",      // regulatory region
        mt_node_count: 23,            // known MT nodes reachable
    },
    availability: Solar,              // or AlwaysOn if grid-powered
}
```

### Routing Cost Translation

Meshtastic provides hop count and SNR. Mehr needs [CompactPathCost](../protocol/network-protocol#mehr-extension-compact-path-cost). The bridge translates:

```
CompactPathCost from Meshtastic metrics:
    cumulative_cost = base_lora_cost × mt_hop_count
    worst_latency_ms = mt_hop_count × avg_lora_hop_latency
    bottleneck_bps = lora_datarate (from Meshtastic region config)
    hop_count = mt_hop_count + mehr_hop_count
```

This lets Mehr's [cost-weighted routing](../protocol/network-protocol#routing) make informed decisions about paths that traverse Meshtastic segments. A Mehr node choosing between a 3-hop WiFi path and a 2-hop Meshtastic path can compare costs accurately.

## Message Translation

### Mehr-to-Meshtastic

For users who want to reach Meshtastic contacts from Mehr:

1. Mehr user sends message to a Meshtastic destination (identified by bridge attestation)
2. Bridge node receives the Mehr packet, decrypts the transport layer
3. Bridge re-encrypts for the Meshtastic channel (PSK-based, per Meshtastic's model)
4. Message delivered as a standard Meshtastic text message
5. Meshtastic recipient sees: `[MHR:alice] Hello from the other side`

**Security note**: E2E encryption breaks at the bridge. Mehr uses per-recipient Ed25519-based encryption; Meshtastic uses shared channel PSK. The bridge must decrypt and re-encrypt. Users are warned that messages crossing the bridge are readable by the bridge operator. For sensitive content, both parties should be on the same protocol.

:::caution[Trade-off]
The Meshtastic bridge is trust-sensitive: E2E encryption terminates at the bridge node. The bridge operator can read plaintext of all messages crossing protocols. For sensitive conversations, both parties must be on the same protocol — the bridge is only suitable for non-confidential traffic.
:::

### Meshtastic-to-Mehr

1. Meshtastic user sends a message on a bridged channel
2. Bridge node receives the Meshtastic packet
3. If the message targets a Mehr user (prefix `@mehr:` or configured mapping), bridge translates
4. Bridge encrypts E2E for the Mehr recipient and sends via Mehr routing
5. Bridge pays Mehr relay costs from its own balance

### Position and Telemetry

Meshtastic nodes broadcast GPS position and device telemetry. Bridges can optionally translate this:

- **Position** → Mehr `GeoPresence` claim (with consent — GPS data is sensitive)
- **Telemetry** → Mehr node health metrics (battery, temperature, signal quality)
- **Traceroute** → Contributes to Mehr's routing cost estimates for Meshtastic segments

This data flows one-way (Meshtastic → Mehr) unless the Meshtastic user has explicitly opted into Mehr identity attestation.

## Migration Path

For Meshtastic community members who want to adopt Mehr incrementally:

### Stage 1: Passive Bridge (Zero Changes)

- A community member deploys a bridge node alongside existing Meshtastic infrastructure
- Meshtastic nodes continue operating normally
- Bridge forwards Mehr traffic as opaque Meshtastic payloads (Mode 1)
- Meshtastic users notice nothing different
- Mehr users gain LoRa coverage through the Meshtastic mesh

### Stage 2: Awareness (Optional Firmware Update)

- Interested Meshtastic operators flash the L0-aware firmware extension
- Their nodes start reporting link quality to bridge nodes
- Mehr routing improves across Meshtastic segments
- No economic participation yet — pure transport contribution

### Stage 3: Economic Participation (L1 Upgrade)

- Operators who want to earn MHR upgrade to dual-protocol firmware (Mode 3)
- Their nodes participate in the VRF relay lottery
- Relay wins earn MHR through [payment channels](../economics/payment-channels)
- A $20 solar LoRa node becomes a revenue-generating relay

### Stage 4: Full Mehr (L2)

- Operators with Raspberry Pi or better hardware run full Mehr nodes
- Participate in storage, compute, and marketplace
- Meshtastic continues as one of their radio interfaces
- They are now bridge operators, earning from both relay and bridge services

Each stage is optional. A community can stay at Stage 1 indefinitely — Mehr gets radio coverage, Meshtastic users experience no disruption. The upgrade path exists for those who want economic participation.

## Meshtastic Protocol Considerations

### Channel Allocation

Meshtastic supports up to 8 channels. The bridge uses one channel for Mehr traffic:

| Channel | Use |
|---------|-----|
| 0 | Default Meshtastic (LongFast, community) |
| 1-6 | User-configured Meshtastic channels |
| 7 | Mehr bridge traffic (configurable) |

The Mehr bridge channel uses a well-known PSK derived from the bridge node's public key. Meshtastic nodes that don't understand Mehr simply ignore traffic on this channel (standard Meshtastic behavior — unknown channels are not displayed).

### Regional Compliance

Meshtastic enforces regional LoRa parameters (frequency, bandwidth, duty cycle) per its firmware configuration. The bridge inherits these constraints:

- **EU868**: 1% duty cycle limits → Mehr traffic budgeted within this limit
- **US915**: More permissive → higher Mehr throughput available
- **Duty cycle accounting**: Bridge tracks airtime for both Meshtastic and Mehr traffic combined, never exceeding regional limits

### Mesh Routing Interaction

Meshtastic uses a managed flood routing protocol. Mehr uses [Kleinberg small-world routing](../protocol/network-protocol#routing). These models differ fundamentally:

- **Meshtastic**: Broadcast-oriented, packets flood to all reachable nodes
- **Mehr**: Unicast-oriented, packets follow cost-optimal paths

The bridge resolves this mismatch:

- **Mehr → Meshtastic**: Bridge sends as Meshtastic direct message (unicast within Meshtastic's routing) when possible, or broadcast on the bridge channel for unknown destinations
- **Meshtastic → Mehr**: Bridge receives all Meshtastic traffic on the bridge channel, forwards only packets addressed to Mehr destinations

## Hardware Compatibility

All hardware listed in Meshtastic's [supported devices](https://meshtastic.org/docs/hardware/devices/) is compatible with Mode 1 (opaque relay — no firmware changes). Mode 2 and 3 require firmware space:

| Device | Mode 1 | Mode 2 (L0) | Mode 3 (Dual) | Notes |
|--------|--------|-------------|---------------|-------|
| Heltec V3 | Yes | Yes | Yes | 8 MB flash, good for dual stack |
| LILYGO T-Beam | Yes | Yes | Yes | GPS included, solar-ready |
| RAK WisBlock | Yes | Yes | Yes | Modular, industrial use |
| Heltec V2 | Yes | Yes | Limited | 4 MB flash, tight for dual |
| nRF52840 boards | Yes | Partial | No | Different MCU, limited flash |

**Recommended bridge hardware**: LILYGO T-Beam Supreme S3 — ESP32-S3, SX1262, GPS, solar charging circuit, 8 MB flash. ~$30, solar-capable, proven in Meshtastic deployments.
