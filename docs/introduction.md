---
sidebar_position: 1
slug: /introduction
title: Introduction
description: Overview of the Mehr Network — a decentralized mesh infrastructure using Proof of Service, self-sovereign identity, and CRDT-based economics.
keywords: [mesh network, decentralized, proof of service, introduction, Mehr]
---

import StackDiagram from '@site/src/components/StackDiagram';

# Mehr Network

**Decentralized Mesh Infrastructure Powered by Proof of Service**

Proof of work wastes electricity. Proof of stake rewards capital, not contribution. Mehr uses **proof of service** — a token is minted only when a real service is delivered to a real paying client through a funded payment channel. Relay a packet, store a block, run a computation — that's how MHR enters circulation. No work is wasted. No token is unearned.

Mehr is a decentralized network where every resource — bandwidth, compute, storage, connectivity — is a discoverable, negotiable, verifiable, payable capability. Nodes participate at whatever level their hardware allows. Nothing is required except a cryptographic keypair.

## What Makes Mehr Different

### Proof of Service

Most decentralized networks create tokens through artificial work (hashing) or capital lockup (staking). Mehr mints tokens only when a provider delivers a real service — relaying traffic, storing data, or executing computations — to a client who pays through a funded payment channel. Minting is proportional to real economic activity and capped at 50% of net service income. A 2% burn on every payment creates a deflationary counterforce that keeps supply bounded.

### Zero Trust Economics

The economic layer assumes every participant is adversarial. Two mechanisms make cheating structurally unprofitable in connected networks: **non-deterministic service assignment** (the client can't choose who serves the request) and a **net-income revenue cap** (cycling MHR produces zero minting). No staking, no slashing, no trust scores required. Identity is just a keypair — but opening a payment channel requires visible balance on the [CRDT ledger](economics/crdt-ledger), and building [reputation](protocol/security#reputation) requires sustained honest service, so Sybil identities face economic friction even without explicit identity verification.

In isolated partitions — where an attacker could control all nodes and nullify non-deterministic assignment — three defense layers [bound damage to a predictable amount](economics/token-security#attack-isolated-partition). During bootstrap (epoch < 100,000), **genesis-anchored minting** prevents all minting without provable connectivity to genesis nodes. **Active-set-scaled emission** limits minting to the partition's fraction of the network (`min(active_nodes, 100) / 100` of full emission — a 3-node partition gets at most 3%). A **2% service burn** on every payment provides friction during isolation and absorbs excess supply after reconnection. Cumulative excess is bounded because emission halves geometrically — even an infinitely long 3-node partition produces ~1.5% total supply dilution, and realistic durations (weeks to months) produce less than 0.1% (see [Supply Dynamics Proof](economics/token-security#supply-dynamics-proof)). When a partition reconnects, the [CRDT merge rules](economics/epoch-compaction#partition-safe-merge-rules) adopt the winning epoch's snapshot and recover missed settlements via proofs. Excess supply dilutes all holders equally, and the halving schedule makes any supply shock negligible over time.

### Free Between Friends

Communication within your trust network is free — no tokens, no channels, no economic overhead. A local mesh where everyone trusts each other operates at zero cost. The economic layer only activates when traffic crosses trust boundaries. This mirrors how communities actually work: you help your neighbors for free, but charge strangers for using your infrastructure.

### Self-Sovereign Identity

Your identity is your cryptographic key — not an account on someone else's server. [MHR-ID](services/mhr-id) lets you build a rich profile (name, bio, avatar, linked accounts, achievements) where every field is a signed claim that peers can vouch for or dispute. You control who sees each field: public, trusted friends only, friends-of-friends, or specific people. Geographic presence is verified by radio range proofs; external accounts are verified by [FUTO ID-style](https://docs.polycentric.io/futo-id/) crawler and OAuth challenges. No central identity provider. No data broker.

### Subjective Naming

There is no global DNS. [MHR-Name](services/mhr-name) provides human-readable names (`alice@geo:portland`, `my-blog@topic:tech`) that resolve from each viewer's position in the trust graph. Names registered by people you trust outrank names from strangers. Two communities can have different "alice" users — that's by design. Names can point to people, content, or [distributed applications](services/mhr-app).

### Distributed Applications

Applications on Mehr are not hosted on servers — they are [content-addressed packages](services/mhr-app) stored in the mesh. An AppManifest bundles contract code, UI, state schema, and dependencies into a single installable artifact. Users discover apps by name, install them locally, and upgrade via trust-weighted update propagation. No app store. No platform fee. No single point of removal.

## Vision

### Strengthen Communities

The internet was supposed to connect people. Instead, it routed everything through distant data centers owned by a handful of corporations. Mehr reverses this: communication within a community is **free, direct, and unstoppable**. Trusted neighbors relay for each other at zero cost. The economic layer only activates when traffic crosses trust boundaries — just like the real world.

### Democratize Communication

A village with no ISP should still be able to communicate. A country under internet shutdown should still have a mesh. A community that can't afford $30/month per household should be able to share one uplink across a neighborhood. Mehr makes communication infrastructure a commons, not a product.

### One Decentralized Computer

Every device on the network — from a $30 solar relay to a GPU workstation — contributes what it can. Storage, compute, bandwidth, and connectivity are pooled into a single capability marketplace. Your phone delegates AI inference to a neighbor's GPU. Your Raspberry Pi stores data for the mesh. No single point of failure, no single point of control. The network **is** the computer.

### Share Hardware, Save Money

Most hardware sits idle most of the time. A home internet connection averages less than 5% utilization. A desktop GPU sits unused 22 hours a day. Mehr turns idle capacity into shared infrastructure: you earn when others use your resources, and you pay when you use theirs. The result is that communities need far less total hardware to achieve the same capabilities.

## Why Mehr?

The internet depends on centralized infrastructure: ISPs, cloud providers, DNS registrars, certificate authorities. When any of these fail — through censorship, natural disaster, or economic exclusion — people lose connectivity entirely.

Mehr is designed for a world where:

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

The [CRDT ledger](economics/crdt-ledger) prevents unbounded state growth through **epoch compaction**: settlement history is periodically snapshotted into a compact bloom filter, GCounter deltas are rebased to zero, and nodes discard individual settlement records. Epochs are triggered by settlement count (≥ 10,000), memory pressure (≥ 500 KB), or a small-partition floor — so even a 20-node village compacts regularly.

When a partition reconnects after a long offline period, the epoch with the highest settlement count wins. The losing partition's settlements are recovered via [settlement proofs](economics/epoch-compaction#late-arrivals-after-compaction) during a 4-epoch verification window — bounded bandwidth, not an unbounded merge. Constrained devices store only their own balance and their neighbors' balances (~1.2 KB) plus the Merkle root, and verify any other balance [on demand](economics/epoch-compaction#snapshot-scaling) via a 640-byte Merkle proof.

### 4. Anonymous by Default

Packets carry no source address. A relay node knows which neighbor handed it a packet, but not whether that neighbor originated it or is relaying it from someone else. Identity is a cryptographic keypair — not a name, not an IP address, not an account. [Human-readable names](services/mhr-name) are optional and trust-scoped. [Profile fields](services/mhr-id#profile-fields) have per-field [visibility controls](services/mhr-id#visibility-controls) — you decide what to reveal and to whom. You can use the network, earn MHR, host content, and communicate without ever revealing who you are.

This does not conflict with paid relay. [Payment channels](economics/payment-channels#bilateral-payment-channels) are **per-hop bilateral** — each relay settles with the direct neighbor that handed it the packet, not with the original sender. The relay knows its immediate neighbor (link-layer information) but not whether that neighbor originated or forwarded the packet. Attribution for payment happens at each hop independently; no relay ever learns the end-to-end path, and no end-to-end payment coordination is needed. See [Per-Hop Independent Relay Rewards](development/design-decisions#per-hop-independent-relay-rewards) for the full design rationale.

### 5. Free Local, Paid Routed

Direct neighbors communicate for free. You pay only when your packets traverse other people's infrastructure. This mirrors real-world economics — talking to your neighbor costs nothing, sending a letter across the country does.

### 6. Layered Separation

Each layer depends only on the layer below it. Applications never touch transport details. Payment never touches routing internals. Security is not bolted on — it is structural.

## Protocol Stack Overview

Mehr is organized into seven layers, each building on the one below. Click any layer to read its full specification.

<StackDiagram />

## How It Works — A Simple Example

1. **Alice** has a Raspberry Pi with a LoRa radio and WiFi. She's in a rural area with no internet. She's registered as `alice@geo:us/oregon/bend` and her profile shows her bio, avatar, and a verified GitHub link.
2. **Bob** has a gateway node 5 km away with a cellular modem providing internet access. He's Alice's trusted peer — they relay for each other for free.
3. **Carol** is somewhere on the internet and wants to message Alice.

Here's what happens:

- Carol looks up `alice@geo:us/oregon/bend` — the name resolves to Alice's node via trust-weighted resolution
- Carol's message is encrypted end-to-end for Alice's public key
- It routes through the internet to Bob's gateway
- Bob relays it over LoRa to Alice (free, because Alice is his trusted peer)
- Alice's device decrypts and displays the message
- Carol's relay cost to reach Bob's gateway is paid automatically through a bilateral payment channel

Carol can see Alice's public profile fields (bio, avatar, verified GitHub) but not her phone number — Alice set that to DirectTrust visibility, so only her trusted peers can see it.

No central server. No accounts. No subscriptions. Just cryptographic identities, trust-weighted naming, and a marketplace for capabilities.

## Next Steps

- **Understand the protocol**: Start with [Physical Transport](protocol/physical-transport) and work up the stack
- **Explore the economics**: Learn how [MHR tokens](economics/mhr-token) and [stochastic relay rewards](economics/payment-channels) enable decentralized resource markets
- **Identity and naming**: See how [MHR-ID](services/mhr-id) builds self-sovereign profiles and how [MHR-Name](services/mhr-name) provides trust-weighted naming
- **Distributed apps**: Learn how [AppManifests](services/mhr-app) package and distribute applications across the mesh
- **See the real-world impact**: Understand [how Mehr affects existing economics](economics/real-world-impact) and how participants earn
- **See the hardware**: Check out the [reference designs](hardware/reference-designs) for building Mehr nodes
- **Read the full spec**: The complete [protocol specification](specification) covers every detail
