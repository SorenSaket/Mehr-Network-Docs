---
sidebar_position: 1
slug: /introduction
title: Introduction
---

# NEXUS Protocol

**A Decentralized Capability Marketplace Over Transport-Agnostic Mesh**

NEXUS is a decentralized network where every resource — bandwidth, compute, storage, connectivity — is a discoverable, negotiable, verifiable, payable capability. Nodes participate at whatever level their hardware allows. Nothing is required except a cryptographic keypair.

## Why NEXUS?

The internet depends on centralized infrastructure: ISPs, cloud providers, DNS registrars, certificate authorities. When any of these fail — through censorship, natural disaster, or economic exclusion — people lose connectivity entirely.

NEXUS is designed for a world where:

- A village with no internet can still communicate internally over LoRa radio
- A country with internet shutdowns can maintain mesh connectivity between citizens
- A community can run its own local network and bridge to the wider internet through any available uplink
- Every device — from a $30 solar-powered relay to a GPU workstation — contributes what it can and pays for what it needs

## Core Principles

### 1. Transport Agnostic

Any medium that can move bytes is a valid link. The protocol never assumes IP, TCP, or any specific transport. It works from 500 bps radio to 10 Gbps fiber. A single node can bridge between multiple transports simultaneously.

### 2. Capability Agnostic

Nodes are not classified into fixed roles. A node advertises what it can do. What it cannot do, it delegates to a neighbor and pays for the service. Hardware determines capability; the market determines role.

### 3. Partition Tolerant

Network fragmentation is not an error state — it is expected operation. A village on LoRa **is** a partition. A country with internet cut **is** a partition. Every protocol layer functions correctly during partitions and converges correctly when partitions heal.

### 4. Free Local, Paid Routed

Direct neighbors communicate for free. You pay only when your packets traverse other people's infrastructure. This mirrors real-world economics — talking to your neighbor costs nothing, sending a letter across the country does.

### 5. Layered Separation

Each layer depends only on the layer below it. Applications never touch transport details. Payment never touches routing internals. Security is not bolted on — it is structural.

## Protocol Stack Overview

NEXUS is organized into seven layers, each building on the one below:

| Layer | Name | Purpose |
|-------|------|---------|
| 0 | [Physical Transport](protocol/physical-transport) | Wraps existing transports (LoRa, WiFi, cellular, etc.) behind a uniform interface |
| 1 | [Network Protocol](protocol/network-protocol) | Identity, addressing, routing, and gossip |
| 2 | [Security](protocol/security) | Encryption, authentication, and privacy |
| 3 | [Economic Protocol](economics/nxs-token) | NXS token, stochastic relay rewards, CRDT ledger, trust neighborhoods |
| 4 | [Capability Marketplace](marketplace/overview) | Capability advertisement, discovery, agreements, and verification |
| 5 | [Service Primitives](services/nxs-store) | NXS-Store, NXS-DHT, NXS-Pub, NXS-Compute |
| 6 | [Applications](applications/messaging) | Messaging, social, voice, naming, forums |

## How It Works — A Simple Example

1. **Alice** has a Raspberry Pi with a LoRa radio and WiFi. She's in a rural area with no internet.
2. **Bob** has a gateway node 5 km away with a cellular modem providing internet access.
3. **Carol** is somewhere on the internet and wants to message Alice.

Here's what happens:

- Carol's message is encrypted end-to-end for Alice's public key
- It routes through the internet to Bob's gateway
- Bob relays it over LoRa to Alice (earning a small NXS fee)
- Alice's device decrypts and displays the message
- Bob's relay cost is paid automatically through a bilateral payment channel

No central server. No accounts. No subscriptions. Just cryptographic identities and a marketplace for capabilities.

## Next Steps

- **Understand the protocol**: Start with [Physical Transport](protocol/physical-transport) and work up the stack
- **Explore the economics**: Learn how [NXS tokens](economics/nxs-token) and [payment channels](economics/payment-channels) enable decentralized resource markets
- **See the hardware**: Check out the [reference designs](hardware/reference-designs) for building NEXUS nodes
- **Read the full spec**: The complete [protocol specification](specification) covers every detail
