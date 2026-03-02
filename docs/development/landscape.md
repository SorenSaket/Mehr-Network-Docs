---
sidebar_position: 5
title: Landscape Analysis
description: "Honest comparison of Mehr against existing decentralized and mesh networking projects like IPFS, Helium, and Holochain."
keywords:
  - landscape
  - comparison
  - IPFS
  - Helium
  - Holochain
  - prior art
---

# Landscape Analysis

An honest comparison of Mehr against existing decentralized and mesh networking projects. The individual pieces of Mehr aren't novel — the combination is. Every feature exists somewhere else. What no existing project does is combine them all into a single coherent stack.

---

## Prior Art by Feature

| Mehr Feature | Who Did It First / Best |
|---|---|
| Transport-agnostic mesh | [Reticulum](https://reticulum.network/) — Mehr builds on it |
| LoRa mesh messaging | [Meshtastic](https://meshtastic.org/), [goTenna](https://gotenna.com/) |
| Cryptographic identity (no registrar) | [SSB](https://scuttlebutt.nz/), [Briar](https://briarproject.org/), Reticulum, many others |
| Content-addressed storage | [IPFS](https://ipfs.tech/) (2015) |
| Decentralized storage market | [Filecoin](https://filecoin.io/) |
| Paid mesh relay | [Althea](https://althea.net/) (mesh ISP economics) |
| Token incentives for infrastructure | [Helium](https://www.helium.com/) (DePIN) |
| CRDT-based state (no blockchain) | [Holochain](https://www.holochain.org/) (agent-centric + mutual credit) |
| Onion routing | [Tor](https://www.torproject.org/) (2002), [I2P](https://geti2p.net/) |
| Offline-first social | [SSB](https://scuttlebutt.nz/) (append-only feeds, gossip replication) |
| No-source-address privacy | Reticulum |
| DHT routing | Kademlia (2002), used by IPFS, BitTorrent, etc. |
| Erasure coding for storage | Standard technique (Reed-Solomon), Filecoin uses it |
| Smart contracts / compute | Ethereum, Filecoin FVM, Holochain |

---

## Project-by-Project Comparison

### Reticulum

[Reticulum](https://reticulum.network/) is the closest spiritual ancestor — Mehr explicitly builds on its transport layer.

**What it does**: A cryptography-based networking stack for building networks over any medium. Replaces IP-based networking with destination-hash-based addressing using Ed25519 keys.

**Transport**: Fully transport-agnostic. LoRa (via RNode), packet radio, WiFi, Ethernet, serial, BLE, free-space optical, AX.25. Proven on links as slow as 5 bps. TCP/IP can also serve as a carrier.

**Economics**: None. No token, no node compensation. Purely volunteer/altruistic relay.

**Storage**: None. Transport-only stack.

**Compute**: None.

**Privacy**: Strong. No source address in packets (structural sender anonymity). AES-256-CBC with ephemeral ECDH on Curve25519, forward secrecy.

**Constrained devices**: ESP32 serves as radio modem, but the Reticulum stack itself runs on the host (Python on Raspberry Pi or Linux).

**Partition tolerance**: Excellent. Designed for partitioned operation.

**Mehr adds**: Everything above transport — economics, storage, compute, marketplace, social. Reticulum is Layer 0; Mehr is Layers 1-6.

---

### Meshtastic

**What it does**: Open-source firmware that turns cheap LoRa hardware into off-grid mesh communicators. Text messaging and position sharing.

**Transport**: LoRa only for mesh hops. BLE for phone pairing, WiFi for configuration/MQTT bridge.

**Economics**: None.

**Storage**: Minimal store-and-forward for offline messages.

**Privacy**: Limited. AES-256 with a shared pre-shared key — all channel members share the same key.

**Constrained devices**: Runs natively on ESP32 and nRF52840. $15-50 per node.

**Partition tolerance**: Good for broadcasts. Direct messages can fail if the path breaks.

**Mehr adds**: Multi-transport bridging, economic incentives, content-addressed storage, DHT, compute, per-message E2E encryption (not shared PSK), cost-aware routing.

---

### Helium

**What it does**: Decentralized wireless infrastructure (DePIN) providing LoRaWAN for IoT and mobile coverage (5G/WiFi). Hotspot operators earn tokens.

**Transport**: LoRaWAN + WiFi/CBRS 5G. Hotspots connect to the Solana blockchain via internet backhaul. Star topology — not a mesh between hotspots.

**Economics**: HNT token on Solana. Proof of Coverage + data transfer rewards. Data Credits at fixed $0.00001, created by burning HNT.

**Storage**: None.

**Privacy**: Minimal. Hotspot locations are public. All transactions on a public blockchain.

**Constrained devices**: Hotspots require dedicated hardware ($200-500) with persistent internet and power.

**Partition tolerance**: Poor. Each hotspot requires continuous internet. No mesh between hotspots.

**Mehr adds**: Actual mesh topology, partition tolerance, no blockchain dependency, storage + compute, operation without internet.

---

### IPFS / Filecoin

**What it does**: IPFS is a content-addressed distributed file system. Filecoin adds economic incentives for persistent storage. libp2p is the networking library.

**Transport**: libp2p supports TCP, QUIC, WebSocket, WebRTC — but assumes internet connectivity. No LoRa or radio transport.

**Economics**: Filecoin FIL token. Storage providers earn FIL via Proof of Spacetime and Proof of Replication. Clients pay FIL to store data. On-chain settlement.

**Storage**: Core feature. Content-addressed blocks (CIDs) with Kademlia DHT. Filecoin adds persistence guarantees with cryptographic proofs.

**Compute**: Emerging. Filecoin Virtual Machine (FVM) is WASM-based. Compute-over-data in development (Bacalhau project).

**Privacy**: Limited. Data is public by default. No built-in encryption. Filecoin deals are on a public blockchain.

**Constrained devices**: Cannot run on constrained devices. Filecoin storage providers need GPUs for proof generation.

**Partition tolerance**: Moderate for IPFS (content available from any node that has it). Poor for Filecoin (proofs must be submitted to blockchain on schedule).

**Mehr adds**: Transport agnosticism, constrained-device support, no blockchain dependency, partition-tolerant economics, trust-based free tier, mesh radio capability.

---

### Holochain

**What it does**: Agent-centric distributed application framework. Each participant maintains their own signed hash chain and shares data to a DHT. No global consensus.

**Transport**: Internet-based (TCP/WebSocket). No radio or constrained transport support.

**Economics**: HoloFuel mutual-credit currency — balances created by counterparties, not minted from fixed supply. Fundamentally different from token-based systems.

**Storage**: Via validating DHT. Each app defines its own DNA (validation rules). Data sharded across responsible nodes.

**Compute**: Yes — each hApp runs application logic on participating nodes.

**Privacy**: Moderate. Source chains are private. DHT entries can be encrypted. No onion routing.

**Constrained devices**: Can run on Raspberry Pi. Far too heavy for microcontrollers.

**Partition tolerance**: Excellent. Agent-centric model means partitioned networks continue operating independently.

**Mehr adds**: Radio mesh transport, constrained-device support (ESP32), bandwidth-aware protocol design for LoRa, cost-aware routing, integrated connectivity marketplace.

---

### Scuttlebutt (SSB)

**What it does**: Peer-to-peer social networking via append-only logs and gossip. Offline-first, community-centric.

**Transport**: LAN discovery via multicast UDP. Internet via "Pub" relay servers. Direct TCP connections. No radio support.

**Economics**: None. Pubs run by volunteers.

**Storage**: Distributed through social graph replication — each node stores feeds of friends (and optionally friends-of-friends). No DHT.

**Privacy**: Moderate. Secret Handshake protocol authenticates connections. Private messages use asymmetric encryption. Social graph is visible.

**Constrained devices**: Requires Node.js (JavaScript implementation) or similar. Not suitable for microcontrollers.

**Partition tolerance**: Excellent. SSB's strongest feature. Feeds are append-only and self-certifying.

**Mehr adds**: Economic incentives, radio mesh, constrained-device support, content-addressed storage with erasure coding, DHT, compute contracts, cost-aware routing.

---

### Briar

**What it does**: Secure messenger for activists and journalists. Zero reliance on central infrastructure.

**Transport**: Multi-transport — Tor (internet), Bluetooth (10-30m), WiFi Direct. Also USB sneakernet. This multi-transport approach is similar to Mehr's philosophy, though narrower in scope.

**Economics**: None.

**Storage**: Messages stored encrypted on-device only.

**Privacy**: Excellent. E2E encryption, Tor routing hides metadata. Passed independent security audit (Cure53).

**Constrained devices**: Android app (primary). Desktop (beta). Cannot run on microcontrollers.

**Partition tolerance**: Good. Bluetooth and WiFi Direct work without internet. Cannot discover new peers in a partition.

**Mehr adds**: Economic incentives, extended range (LoRa), storage + compute services, DHT, cost-aware routing, social features.

---

### Matrix

**What it does**: Open standard for decentralized, federated real-time communication. Interoperable messaging and VoIP across independent homeservers.

**Transport**: HTTP/HTTPS over TCP/IP. WebSocket for clients. Assumes internet at all times.

**Economics**: None at protocol level. Homeserver operators bear costs.

**Storage**: Homeservers replicate room state. Not content-addressed.

**Privacy**: Moderate-Good. Olm/Megolm E2E encryption. Metadata visible to homeserver operators.

**Constrained devices**: Homeservers require server-class hardware. Not suitable for constrained devices.

**Partition tolerance**: Poor. Federation requires internet. Offline homeserver = unreachable users.

**Mehr adds**: Transport agnosticism, mesh radio, no server dependency, economic incentives, partition tolerance, constrained-device support.

---

### Hyphanet (formerly Freenet)

**What it does**: Censorship-resistant publishing and communication. Anonymous distributed data storage.

**Transport**: Internet-only (TCP/IP). No radio or mesh.

**Economics**: None. Volunteer node operators.

**Storage**: Core feature. Encrypted chunks distributed across the network. Content persists based on popularity.

**Privacy**: Strong. Two modes: Opennet (random connections) and Darknet (trusted peers only). Multi-layer encryption. Publishers and retrievers are anonymous.

**Constrained devices**: Requires Java runtime and persistent disk (10-20 GB). Cannot run on constrained devices.

**Partition tolerance**: Moderate. Darknet mode tolerates some fragmentation. Content availability degrades with partition size.

**Mehr adds**: Radio mesh transport, constrained-device support, economic incentives, cost-aware routing, compute contracts, integrated service marketplace.

---

### Althea

**What it does**: Protocol for decentralized ISP operation. Routers negotiate bandwidth pricing and route payments automatically.

**Transport**: Standard IP networking (WiFi, Ethernet, point-to-point wireless bridges). Uses Babel routing protocol. Not designed for LoRa or constrained radio.

**Economics**: Token-based. Routers pay neighbors per-byte for forwarding. Althea L1 blockchain for governance. Liquid Infrastructure Tokens (LITs) represent revenue-generating assets.

**Storage**: None. Connectivity protocol only.

**Privacy**: Limited. Traffic routing and payments are transparent between nodes. Standard ISP-like model.

**Constrained devices**: Requires OpenWrt-compatible routers. Not suitable for microcontrollers.

**Partition tolerance**: Poor. Economic model requires blockchain access for settlement.

**Mehr adds**: Radio mesh (LoRa), constrained-device support, no blockchain dependency, partition-tolerant economics (CRDT ledger), storage + compute, trust-based free tier.

---

### goTenna

**What it does**: Hardware mesh networking devices for off-grid communication. Primarily targets first responders and military. Proprietary closed-source protocol.

**Transport**: Proprietary radio on VHF/UHF bands. Bluetooth for phone pairing. No internet connectivity — purely radio mesh.

**Economics**: Hardware sales ($849+ per Pro X2 unit). Previously explored token incentives (Lot49 protocol) but did not commercialize.

**Storage**: None beyond store-and-forward.

**Privacy**: Moderate. 384-bit ECC E2E encryption. But proprietary and closed-source — no independent verification.

**Constrained devices**: Requires purchasing proprietary hardware. Cannot use off-the-shelf components.

**Partition tolerance**: Excellent for messaging. Zero-control-packet approach minimizes overhead.

**Mehr adds**: Open protocol, off-the-shelf hardware, economic incentives, storage + compute, DHT, social features, internet bridging, transport agnosticism.

---

### Yggdrasil / CJDNS

**What they do**: Encrypted IPv6 overlay networks with self-healing mesh routing. Cryptographic addresses derived from public keys.

**Transport**: Overlay on existing IP networks. Cannot run on non-IP transports.

**Economics**: None. Volunteer-operated.

**Storage**: None. Routing-only overlays.

**Privacy**: Moderate. All traffic encrypted. Addresses derived from keys. No onion routing — traffic analysis possible.

**Constrained devices**: Yggdrasil (Go) and CJDNS (C) can run on Raspberry Pi and OpenWrt routers. Cannot run on bare microcontrollers.

**Partition tolerance**: Good. Self-healing routing adapts to topology changes.

**Mehr adds**: Radio mesh transport, economic incentives, storage + compute, constrained-device support (ESP32), capability marketplace.

---

### Tor / I2P

**What they do**: Anonymous overlay networks. Tor: circuit-switched onion routing for internet access and hidden services. I2P: packet-switched garlic routing for internal services.

**Transport**: Internet-only. TCP (Tor) or UDP (I2P). Completely non-functional without internet.

**Economics**: None. Volunteer-operated relays.

**Storage**: None.

**Privacy**: Very strong. Multi-hop onion/garlic routing with layered encryption. Tor: 3 hops + directory authorities. I2P: 6-hop unidirectional tunnels.

**Constrained devices**: Cannot run on constrained devices.

**Partition tolerance**: None. Requires internet connectivity.

**Mehr adds**: Transport agnosticism (works without internet), economic incentives, storage + compute, constrained-device support, partition tolerance. Mehr's optional onion routing (`PathPolicy.ONION_ROUTE`) provides privacy for high-threat scenarios without requiring always-on anonymization.

---

### Session

**What it does**: Privacy-focused messenger requiring no phone number or email. Onion routing over a decentralized network of staked nodes.

**Transport**: Internet-based. Three-hop onion routing through Session Nodes. Session Network blockchain for staking and rewards.

**Economics**: Session Token (migrated from OXEN in 2025). Node operators stake tokens and earn rewards for routing and storage.

**Storage**: Temporary. Swarm-based message storage for offline delivery. Not general-purpose.

**Privacy**: Very strong. No registration info required. Onion routing hides IPs. E2E encryption.

**Constrained devices**: Clients on phones/desktops. Session Nodes require server-class hardware. Not suitable for microcontrollers.

**Partition tolerance**: Poor. Requires internet to reach Session Nodes.

**Mehr adds**: Transport agnosticism, mesh radio, constrained-device support, general-purpose storage + compute, no blockchain dependency, partition tolerance, trust-based free relay.

---

### Nostr

**What it does**: Minimalist protocol for decentralized social networking. Cryptographic keys for identity, relays for message distribution.

**Transport**: WebSocket connections to relay servers. Assumes internet.

**Economics**: No built-in token. Relay operators may charge. Lightning Network zaps for tipping.

**Storage**: Relays store events. No content-addressing, no DHT, no erasure coding. Persistence depends entirely on relay willingness.

**Privacy**: Weak. Events typically unencrypted. Relays see all content and metadata. IP addresses visible.

**Constrained devices**: Clients are lightweight. Relays need server hardware.

**Partition tolerance**: Moderate. Clients can connect to any subset of relays.

**Mehr adds**: Transport agnosticism, mesh radio, constrained-device support, protocol-level economic incentives, content-addressed storage with erasure coding, DHT, compute, E2E encryption by default, partition tolerance.

---

### Safe Network (formerly MaidSafe)

**What it does**: Fully autonomous, decentralized data network aiming to replace the client-server model. Self-managing with no human oversight.

**Transport**: Internet-based P2P. No radio or constrained transport support.

**Economics**: Token-based. MaidSafeCoin (MAID) placeholder; Safe Network Tokens (SNT) at mainnet. Users pay for storage; node operators earn for providing resources.

**Storage**: Core feature. Self-encryption, chunking, distributed across the network. Node operators cannot read stored content.

**Privacy**: Very strong by design. Self-encryption ensures data is encrypted before leaving the user's device.

**Constrained devices**: Intended for consumer hardware. Not suitable for microcontrollers.

**Partition tolerance**: Moderate. Section-based architecture tolerates some fragmentation but requires significant connectivity.

**Note**: After 18+ years of development, the project remains in alpha.

**Mehr adds**: Radio mesh transport, constrained-device support, partition tolerance as first-class constraint, shipping strategy (server-first, proven layers before extending).

---

### Dat / Hypercore Protocol

**What it does**: Peer-to-peer data sharing based on append-only, cryptographically signed logs (Hypercores). Now developed as the Pear Runtime for P2P applications.

**Transport**: Internet-based. Hyperswarm handles discovery via DHT with NAT holepunching. Supports LAN discovery. No radio.

**Economics**: None. Purely voluntary replication.

**Storage**: Yes. Append-only logs with Merkle tree verification. Partial replication — peers download only ranges they need. Hyperdrive provides file system abstraction. No incentive to store others' data.

**Privacy**: Limited. Hypercores identified by public keys. No encryption at rest by default. DHT exposes interest metadata.

**Constrained devices**: Node.js-based. Not suitable for microcontrollers.

**Partition tolerance**: Good. Append-only logs are inherently partition-tolerant.

**Mehr adds**: Economic incentives for storage, radio mesh, constrained-device support, erasure coding, cost-aware routing, compute contracts.

---

## Comparison Matrix

How each project maps to Mehr's key design axes.

| Project | Transport Agnostic | Token / Economics | Storage | Compute | Privacy | Runs on MCU | Partition Tolerant |
|---|---|---|---|---|---|---|---|
| **Mehr** | **Yes** (LoRa to fiber) | **Yes** (VRF lottery, CRDT ledger) | **Yes** (erasure-coded) | **Yes** (MHR-Byte + WASM) | **Yes** (no source addr + opt-in onion) | **Yes** (ESP32) | **Yes** (economic convergence) |
| Reticulum | **Yes** | No | No | No | **Yes** | Partial (modem only) | **Yes** |
| Meshtastic | LoRa only | No | No | No | Weak (shared PSK) | **Yes** | **Yes** |
| Helium | LoRaWAN + WiFi | **Yes** (HNT/Solana) | No | No | No | No | No |
| IPFS / Filecoin | IP only | **Yes** (FIL) | **Yes** | Partial (FVM) | No | No | Partial |
| Holochain | IP only | **Yes** (mutual credit) | **Yes** (DHT) | **Yes** (hApps) | Partial | No | **Yes** |
| SSB | LAN + internet | No | Partial (social graph) | No | Partial | No | **Yes** |
| Briar | Tor + BT + WiFi | No | No | No | **Yes** | No | Partial |
| Matrix | HTTP only | No | Partial (room state) | No | Partial (E2EE) | No | No |
| Hyphanet | TCP only | No | **Yes** | No | **Yes** | No | Partial |
| Althea | WiFi / Ethernet | **Yes** (blockchain) | No | No | No | No | No |
| goTenna | Proprietary radio | No | No | No | Partial | Proprietary HW | **Yes** |
| Yggdrasil / CJDNS | IP overlay | No | No | No | Partial | No | Partial |
| Tor / I2P | Internet only | No | No | No | **Yes** | No | No |
| Session | Internet only | **Yes** (staking) | Partial (temp msgs) | No | **Yes** | No | No |
| Nostr | WebSocket | Partial (Lightning) | Partial (relays) | No | No | No | Partial |
| Safe Network | Internet only | **Yes** (planned) | **Yes** (planned) | Partial (planned) | **Yes** | No | Partial |
| Dat / Hypercore | IP + LAN | No | **Yes** (append logs) | No | No | No | Partial |

---

## What's Actually Novel

Six aspects of Mehr's design have no direct equivalent in existing projects:

### 1. ESP32-to-Datacenter Unified Economic Protocol

No project spans this hardware range with a single economic protocol. Meshtastic runs on ESP32 but has no economics. Filecoin has economics but needs GPUs. Holochain needs at minimum a Raspberry Pi. Mehr's [three participation levels](/docs/L0-physical/physical-transport#participation-levels) (L0 transport-only, L1 relay with lottery, L2 full node) let a $5 microcontroller and a datacenter server participate in the same economy.

### 2. Stochastic Relay Rewards via VRF Lottery

Althea does paid relay but settles on a blockchain. Helium uses Solana. Mehr's [VRF lottery](/docs/L3-economics/payment-channels) reduces channel state updates by ~10x compared to per-packet payment, and the [CRDT ledger](/docs/L3-economics/crdt-ledger) converges without consensus. The specific mechanism — ECVRF-ED25519-SHA512-TAI lottery, bilateral payment channels, CRDT settlement, epoch compaction — doesn't exist elsewhere as a complete system.

### 3. Economic Partition Tolerance

SSB and Holochain handle *data* partition tolerance well. No project addresses what happens to *money* when the network splits. Mehr's CRDT ledger with [partition-aware epoch compaction](/docs/L3-economics/epoch-compaction#epoch-triggers), GCounter rebase, and bounded overminting (max 1.5x) is designed for the case where a village on LoRa is a permanent partition with its own functioning economy.

### 4. Trust-Based Free Tier Integrated with Paid Economics

CJDNS and Hyphanet's darknet use friend-of-friend topology, but without economics on top. Mehr's [trust graph](/docs/L3-economics/trust-neighborhoods) lets friends relay for free while the same protocol charges strangers — and the boundary is fluid. No other project makes this the core economic primitive, with the paid layer activating only when traffic crosses trust boundaries.

### 5. Cost-Aware Kleinberg Small-World Routing

No existing project combines formal small-world routing (O(log² N) hop guarantee) with per-link economic cost metrics. Reticulum has announce-based path discovery but no cost awareness. Althea has cost-aware routing but uses Babel (distance-vector, not small-world optimized). Mehr's [routing model](/docs/L1-network/network-protocol#routing) provides both scalability guarantees and economic efficiency.

### 6. Integrated Capability Marketplace

Filecoin does storage + emerging compute. Althea does connectivity. Holochain does storage + compute. No single project unifies storage, compute, and connectivity into one [discovery/negotiation/verification/payment framework](/docs/L4-marketplace/overview) where a node advertises whatever it can do and the market determines its role.

---

## The Closest Projects

Four projects come closest to Mehr's vision, each covering one or two layers:

| Project | What It Covers | What It Lacks |
|---|---|---|
| **Reticulum** | Transport + routing + identity (Layer 0-1) | Economics, storage, compute, marketplace |
| **Holochain** | Agent-centric data + mutual credit + apps | Radio mesh, constrained devices, bandwidth-aware design |
| **Althea** | Mesh ISP economics + paid relay | Radio mesh, storage, compute, partition tolerance (needs blockchain) |
| **IPFS / Filecoin** | Content-addressed storage + emerging compute market | Radio mesh, constrained devices, partition tolerance (needs blockchain) |

Mehr's contribution is integrating these into a single stack that runs from ESP32 to datacenter, works without internet, and converges economically after network partitions.
