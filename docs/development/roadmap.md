---
sidebar_position: 1
title: Roadmap
---

# Implementation Roadmap

The NEXUS implementation is organized into four phases, progressing from core networking fundamentals to a full ecosystem.

## Phase 1: Foundation

**Focus**: Core networking and basic economics

- Implement network protocol (Rust, targeting Reticulum-derived or clean-room implementation)
- Cost annotations on routing
- Bilateral payment channels
- Basic CRDT ledger with gossip
- ESP32 + LoRa firmware (relay only)
- Raspberry Pi software (bridge + basic compute)
- CLI tools for node management

**Deliverable**: A working mesh network with cost-aware routing and basic micropayments between nodes.

## Phase 2: Economics

**Focus**: Real-world deployment and economic mechanisms

- Deploy 3-5 test networks (physical hardware, not simulation)
- Cryptographic delivery receipts
- Trust neighborhoods with stochastic relay rewards
- Epoch compaction
- Capability advertisement and discovery
- Basic NXS-Store and NXS-DHT
- Mobile client (consumer)

**Deliverable**: Test networks with functioning trust-based economics, capability discovery, and mobile access.

## Phase 3: Services

**Focus**: Service primitives and first applications

- NXS-Pub (publish/subscribe)
- NXS-Compute (NXS-Byte interpreter)
- Compute and storage delegation
- Messaging application
- Social application (text only initially)
- NXS-Name (community-label-scoped naming)

**Deliverable**: Usable messaging and social applications running on the mesh.

## Phase 4: Ecosystem

**Focus**: Advanced capabilities and ecosystem growth

- Full WASM compute for gateway nodes
- Media tiering for social
- Voice (Codec2 + Opus)
- Marketplace, forums
- Third-party protocol bridges (SSB, Matrix, Briar)
- Hardware partnerships

**Deliverable**: A full-featured decentralized platform with rich applications and interoperability with existing protocols.

## Implementation Language

The primary implementation language is **Rust**, chosen for:

- Memory safety without garbage collection (critical for embedded targets)
- `no_std` support for ESP32 firmware
- Strong ecosystem for cryptography and networking
- Single codebase from microcontroller to server

## Test Network Strategy

Real physical test networks, not simulations:

- Simulation cannot capture the realities of LoRa propagation, WiFi interference, and real-world device failure modes
- Each test network should represent a different deployment scenario (urban, rural, indoor, mixed)
- Test networks validate both the protocol and the economic model
