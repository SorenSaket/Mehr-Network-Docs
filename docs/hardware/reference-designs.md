---
sidebar_position: 1
title: Reference Designs
description: "Hardware reference designs for Mehr nodes, from $30 solar-powered ESP32 relays to GPU inference workstations."
keywords:
  - hardware
  - ESP32
  - LoRa
  - Raspberry Pi
  - reference design
  - solar
---

# Hardware Reference Designs

Mehr is designed to run on hardware ranging from $30 solar-powered relays to GPU workstations. Every device participates at whatever level its hardware allows.

## Device Tiers Overview

:::info[Specification]
Mehr defines five hardware tiers spanning $30 solar relays to GPU workstations. Each tier maps to a protocol participation level: Minimal nodes relay only (L1), while Gateway and above run the full L2 stack with marketplace, storage, and compute.
:::

| Tier | Hardware | Cost | Power | Primary Role |
|------|----------|------|-------|-------------|
| **Minimal** | ESP32 + LoRa SX1276 | ~$30 | 0.5W (solar) | Relay only |
| **Community** | Pi Zero 2 W + LoRa HAT + WiFi | ~$100 | 3W | LoRa/WiFi bridge, basic compute |
| **Gateway** | Pi 4/5 + LoRa + cellular modem + SSD | ~$300 | 10W | Internet uplink, storage, compute |
| **Backbone** | Mini PC + directional WiFi + fiber | ~$500+ | 25W+ | High-bandwidth backbone |
| **Inference** | x86 + GPU + Ethernet | ~$500+ | 100W+ | Heavy compute, ML inference |

## Minimal Relay Node

**Target**: Lowest-cost, always-on mesh relay

```
Components:
  - ESP32-S3 microcontroller
  - LoRa SX1276/SX1262 radio module
  - Small solar panel (2W) + LiPo battery
  - Weatherproof enclosure

Capabilities:
  - Packet relay only
  - MHR-Byte interpreter (~50 KB)
  - No storage beyond routing tables
  - 24/7 operation on solar power

Software:
  - Mehr firmware (Rust, no_std)
  - Transport: LoRa only
  - Runs: routing, payment channels, gossip
  - Cannot run: WASM, storage, heavy compute
```

**Earns from**: Routing fees (1-5 μMHR per packet relayed)

**Range**: 2-15 km line-of-sight with LoRa

:::tip[Key Insight]
A $30 solar-powered ESP32 relay earns MHR from routing fees at zero operating cost. The economics work because the node provides irreplaceable value — extending mesh range — that no centralized alternative can replicate from a data center.
:::

## Community Bridge Node

**Target**: Bridge between LoRa mesh and local WiFi network

```
Components:
  - Raspberry Pi Zero 2 W
  - LoRa HAT (SX1262)
  - Built-in WiFi
  - SD card (32 GB)
  - USB power supply (5V/2A)

Capabilities:
  - LoRa ↔ WiFi bridging
  - Basic MHR-Compute (MHR-Byte + light WASM)
  - Local storage (~16 GB usable)
  - MHR-DHT participation
  - Message caching for offline nodes

Software:
  - Mehr daemon (Rust, Linux)
  - Dual transport: LoRa + WiFi
  - Full protocol stack
```

**Earns from**: Bridging fees, compute delegation, storage

## Gateway Node

**Target**: Internet uplink for the mesh

```
Components:
  - Raspberry Pi 4/5 (4 GB+ RAM)
  - LoRa HAT
  - 4G/LTE cellular modem (or Ethernet)
  - SSD (256 GB+)
  - Powered supply (12V)

Capabilities:
  - Internet gateway (HTTP proxy, DNS relay)
  - Full MHR-Store storage node
  - MHR-DHT backbone participation
  - Full WASM compute
  - Epoch consensus participation

Software:
  - Full Mehr stack
  - Triple transport: LoRa + WiFi + Cellular/Ethernet
  - Gateway proxy services
```

**Earns from**: Internet gateway fees, storage fees, compute fees, routing

## Backbone Node

**Target**: High-bandwidth infrastructure linking mesh segments

```
Components:
  - Mini PC (Intel NUC or equivalent)
  - Directional WiFi antenna (point-to-point)
  - Fiber connection (where available)
  - SSD (1 TB+)
  - UPS/battery backup

Capabilities:
  - High-throughput routing (100+ Mbps)
  - Large-scale storage
  - Full compute services
  - Neighborhood discovery services
  - Epoch consensus coordination

Software:
  - Full Mehr stack, optimized for throughput
  - Transport: Directional WiFi + Fiber + Ethernet
```

**Earns from**: Bulk routing fees, backbone transit, storage

## Inference Node

**Target**: Heavy compute (ML inference, transcription, TTS)

```
Components:
  - x86 PC or server
  - GPU (NVIDIA RTX series or equivalent)
  - Ethernet connection
  - SSD (512 GB+)
  - Standard power supply

Capabilities:
  - ML model inference (Whisper, LLaMA, Stable Diffusion, etc.)
  - Speech-to-text, text-to-speech
  - Translation services
  - Any GPU-accelerated computation

Software:
  - Full Mehr stack
  - WASM runtime + native GPU compute
  - Model serving framework
  - Advertises offered_functions with pricing
```

**Earns from**: Compute fees for ML inference and heavy processing
