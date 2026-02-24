---
sidebar_position: 2
title: Device Capabilities by Tier
---

# Device Capabilities by Tier

Each hardware tier has different capabilities, which determine what the node can do on the network and how it earns NXS.

## Capability Matrix

| Capability | Minimal | Community | Gateway | Backbone | Inference |
|-----------|---------|-----------|---------|----------|-----------|
| Packet relay | Yes | Yes | Yes | Yes | Yes |
| LoRa transport | Yes | Yes | Yes | Optional | No |
| WiFi transport | No | Yes | Yes | Yes (directional) | Optional |
| Cellular transport | No | No | Yes | No | No |
| Ethernet/Fiber | No | No | Optional | Yes | Yes |
| NXS-Byte contracts | Yes | Yes | Yes | Yes | Yes |
| WASM contracts | No | Light | Full | Full | Full |
| NXS-Store storage | No | ~16 GB | ~256 GB | ~1 TB | ~512 GB |
| NXS-DHT participation | Minimal | Yes | Backbone | Backbone | Yes |
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

### Inference (GPU Workstation)
- ML inference fees (highest per-invocation revenue)
- Heavy compute services
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
Inference node
```

Each delegation is a bilateral [capability agreement](../marketplace/agreements) with payment flowing through [channels](../economics/payment-channels).
