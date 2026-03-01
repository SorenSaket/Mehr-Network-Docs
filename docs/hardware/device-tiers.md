---
sidebar_position: 2
title: Device Capabilities by Tier
description: "Capability matrix showing what each hardware tier can do on the Mehr network, from minimal relays to inference nodes."
keywords:
  - device tiers
  - capabilities
  - hardware
  - relay
  - gateway
  - compute
---

# Device Capabilities by Tier

Each hardware tier has different capabilities, which determine what the node can do on the network and how it earns MHR.

## Capability Matrix

:::tip[Key Insight]
Every tier participates in gossip and payment channels — even the cheapest ESP32 relay. The protocol scales by restricting *what* each tier does (no WASM on Minimal, no ML on Gateway), not *whether* it participates in the economy.
:::

| Capability | Minimal | Community | Gateway | Backbone | Inference |
|-----------|---------|-----------|---------|----------|-----------|
| Packet relay | Yes | Yes | Yes | Yes | Yes |
| LoRa transport | Yes | Yes | Yes | Optional | No |
| WiFi transport | No | Yes | Yes | Yes (directional) | Optional |
| Cellular transport | No | No | Yes | No | No |
| Ethernet/Fiber | No | No | Optional | Yes | Yes |
| MHR-Byte contracts | Yes | Yes | Yes | Yes | Yes |
| WASM contracts | No | Light | Full | Full | Full |
| MHR-Store storage | No | ~16 GB | ~256 GB | ~1 TB | ~512 GB |
| MHR-DHT participation | Minimal | Yes | Backbone | Backbone | Yes |
| Epoch consensus | No | No | Yes | Yes | Yes |
| Internet gateway | No | No | Yes | Optional | Optional |
| ML inference | No | No | No | No | Yes |
| Gossip participation | Full | Full | Full | Full | Full |
| Payment channels | Yes | Yes | Yes | Yes | Yes |

## Power and Deployment

| Tier | Power Draw | Power Source | Typical Deployment |
|------|-----------|-------------|-------------------|
| Minimal | 0.5W | Solar + LiPo | Outdoor, pole/tree-mounted |
| Community | 3W | USB wall adapter | Indoor, near window for LoRa |
| Gateway | 10W | 12V supply | Indoor, weatherproof enclosure |
| Backbone | 25W+ | Mains + UPS | Indoor, rack-mounted or desktop |
| Inference | 100W+ | Mains | Indoor, rack or desktop |

## Earning Potential

What each tier naturally earns from:

### Minimal (ESP32 + LoRa)
- Packet relay fees only
- Low per-packet revenue but high volume and zero operating cost (solar)
- Value: extends mesh range, maintains connectivity

### Community (Pi Zero + LoRa + WiFi)
- Bridging fees (LoRa ↔ WiFi translation)
- Basic compute delegation
- Small-scale storage
- Value: connects LoRa mesh to local WiFi network

### Gateway (Pi 4/5 + Cellular)
- Internet gateway fees (highest per-byte revenue)
- Storage fees
- Compute fees
- Epoch consensus participation
- Value: connects mesh to the wider internet

### Backbone (Mini PC + Directional WiFi)
- High-volume transit routing
- Large-scale storage
- Full compute services
- Value: high-bandwidth links between mesh segments

### Inference (GPU/NPU Workstation)
- ML inference fees (highest per-invocation revenue)
- Heavy compute services
- Includes: GPU workstations, servers with NPU/TPU, FPGA accelerators
- Value: provides advanced capabilities to the entire mesh

## Delegation Patterns

Since nodes delegate what they can't do locally, natural delegation chains form:

```
Minimal relay
  → delegates everything except routing to →
Community bridge
  → delegates bulk storage and internet to →
Gateway node
  → delegates heavy compute to →
Inference node (GPU/NPU)
```

Each delegation is a bilateral [capability agreement](../marketplace/agreements) with payment flowing through [channels](../economics/payment-channels).

:::caution[Trade-off]
Delegation chains add latency and cost at each hop. A Minimal relay delegating compute to a Community node, which delegates storage to a Gateway, creates a 3-link economic dependency. If any link fails, the upstream node must re-discover and re-negotiate — trading simplicity for resilience.
:::
