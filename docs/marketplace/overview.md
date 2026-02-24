---
sidebar_position: 1
title: Marketplace Overview
---

# Layer 4: Capability Marketplace

The capability marketplace is the unifying abstraction of NEXUS. Every node advertises what it can do. Every node can request capabilities it lacks. The marketplace matches supply and demand through local, bilateral negotiation — no central coordinator.

This is the layer that makes NEXUS a **distributed computer** rather than just a network.

## The Unifying Abstraction

In NEXUS, there are no fixed node roles. Instead:

- A node with a LoRa radio and solar panel advertises: *"I can relay packets 24/7"*
- A node with a GPU advertises: *"I can run Whisper speech-to-text"*
- A node with an SSD advertises: *"I can store 100 GB of data"*
- A node with a cellular modem advertises: *"I can route to the internet"*

Each of these is a **capability** — discoverable, negotiable, verifiable, and payable.

## Capability Advertisement

Every node broadcasts its capabilities to the network:

```
NodeCapabilities {
    node_id: NodeID,
    timestamp: Timestamp,
    signature: Ed25519Signature,

    // ── CONNECTIVITY ──
    interfaces: [{
        medium: TransportType,
        bandwidth_bps: u64,
        latency_ms: u32,
        reliability: f32,
        cost_per_byte: u64,
        internet_gateway: bool,
    }],

    // ── COMPUTE ──
    compute: {
        cpu_class: enum { Micro, Low, Medium, High },
        available_memory_mb: u32,
        nxs_byte: bool,            // can run basic contracts
        wasm: bool,                // can run full WASM
        cost_per_cycle: u64,
        offered_functions: [{
            function_id: Hash,
            description: String,
            cost_structure: CostStructure,
            max_concurrent: u32,
        }],
    },

    // ── STORAGE ──
    storage: {
        available_bytes: u64,
        storage_class: enum { Volatile, Flash, SSD, HDD },
        cost_per_byte_day: u64,
        max_object_size: u32,
        serves_content: bool,
    },

    // ── AVAILABILITY ──
    uptime_pattern: enum {
        AlwaysOn, Solar, Intermittent, Scheduled(schedule),
    },
}
```

### No Special Protocol Primitives

Heavy compute like ML inference, transcription, translation, and text-to-speech are **not protocol primitives**. They are compute capabilities offered by nodes that have the hardware to run them.

A node with a GPU advertises `offered_functions: [whisper-small, piper-tts]`. A consumer requests execution through the standard compute delegation path. The protocol is agnostic to what the function does — it only cares about discovery, negotiation, verification, and payment.

## Emergent Specialization

Nodes naturally specialize based on hardware and market dynamics:

| Hardware | Natural Specialization | Earns From | Delegates |
|---|---|---|---|
| ESP32 + LoRa + solar | Packet relay, availability | Routing fees | Everything else |
| Raspberry Pi + LoRa + WiFi | Compute, LoRa/WiFi bridge | Compute delegation, bridging | Bulk storage |
| Mini PC + SSD + Ethernet | Storage, DHT, HTTP proxy | Storage fees, proxy fees | Nothing |
| Phone (intermittent) | Consumer, occasional relay | Relaying while moving | Almost everything |
| GPU workstation | Heavy compute (inference, etc.) | Compute fees | Nothing |

## Capability Chains

Delegation cascades naturally:

```
Node A (LoRa relay)
  └── delegates compute to → Node B (Raspberry Pi)
      └── delegates storage to → Node C (Mini PC + SSD)
          └── delegates connectivity to → Node D (Gateway)
```

Each link is a bilateral agreement with its own [payment channel](../economics/payment-channels). No central coordination required.
