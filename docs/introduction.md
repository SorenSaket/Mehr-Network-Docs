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

## The State of the World

The internet depends on centralized infrastructure: ISPs, cloud providers, DNS registrars, certificate authorities. Every packet, every query, every byte passes through chokepoints owned by a small number of corporations. When any of these fail — through censorship, natural disaster, corporate decision, or economic exclusion — people lose connectivity entirely. The architecture has a single point of failure, and that point is someone else's business model.

The concentration is accelerating. Hyperscale data centers now account for 44% of global data center capacity, up from under 30% five years ago. Three cloud providers control 63% of the cloud infrastructure market. AI has made it worse — a single training run requires 15,000–25,000 advanced GPUs at a cost of $120M–$450M. NVIDIA controls 80–92% of the AI accelerator market. The specialized memory these chips require (HBM) is manufactured by exactly three companies, with the entire supply sold out years in advance. The ability to compute is being gatekept at the hardware level, and the gate is narrowing.

The internet was supposed to connect people. Instead, it routed everything through distant data centers and handed control to platforms that optimize for engagement, not truth or community. Algorithmic feeds decide what you see. You know more about celebrities than what's happening on your own street. Your neighbor could be building something extraordinary and you'd never hear about it. The infrastructure that was meant to strengthen communities instead bypasses them entirely.

Governments can shut down the internet with a phone call to a handful of ISPs. When all communication passes through centralized chokepoints, censorship is trivial. A country can be disconnected from the world — or from itself — overnight. Communities that depend entirely on infrastructure they don't own have no fallback when that infrastructure is turned against them.

Most hardware sits idle most of the time. A home internet connection averages below 5% utilization. A desktop GPU sits unused 22 hours a day. A neighborhood full of powerful devices amounts to a distributed supercomputer that nobody can use, because there's no way to share it. People pay full price for dedicated connections and hardware that mostly does nothing.

Decentralized networks were supposed to fix this. They haven't. Proof of Work concentrates around cheap electricity and specialized hardware — six mining pools mine over 95% of all Bitcoin blocks. Proof of Stake concentrates around existing capital — whale wallets hold 57% of Ethereum's supply, and the compounding effect makes wealth concentration self-reinforcing. Decentralized compute projects re-centralize through "Nodekeepers" and whale wallets. The pattern is consistent: when all compute is valued equally regardless of location, capital concentration wins.

## Goals

### Strengthen Communities

Communication within a community is free, direct, and unstoppable. Trusted neighbors relay for each other at zero cost. The economic layer only activates when traffic crosses trust boundaries — just like the real world, where you help your neighbors for free but charge strangers for using your infrastructure. The network makes local connections stronger, not routes around them.

### Democratize Infrastructure

A village with no ISP can still communicate. A country under internet shutdown still has a mesh. A community that can't afford $30/month per household shares one uplink across a neighborhood. Communication infrastructure is a commons, not a product. Any medium that can move bytes — from 500 bps radio to 10 Gbps fiber — is a valid link. Every device contributes what it can and pays for what it needs. Hardware determines capability; the market determines role.

### Distribute Power

Compute, storage, and bandwidth are not gatekept by whoever can build the biggest data center. A solar-powered relay on a rooftop serving its neighborhood earns based on the traffic it carries, not the capital behind it. Proximity to demand — not capital — determines value. A GPU in your neighbor's garage is cheaper to use than a GPU farm across the continent. The network structurally resists concentration, not reproduces it.

### Waste Nothing

Idle hardware becomes shared infrastructure. Your phone delegates AI inference to a neighbor's GPU. Your Raspberry Pi stores data for the mesh. Communities need far less total hardware to achieve the same capabilities — you earn when others use your resources, and you pay when you use theirs.

### Privacy as Default

Packets carry no source address. A relay node knows which neighbor handed it a packet, but not whether that neighbor originated it or is relaying it from someone else. Identity is a cryptographic keypair — not a name, not an IP address, not an account. Human-readable names are optional and trust-scoped. You decide what to reveal and to whom. This does not conflict with paid relay — [payment channels](economics/payment-channels#bilateral-payment-channels) are per-hop bilateral, so each relay settles with its direct neighbor without ever learning the end-to-end path.

### Partition Tolerance

Network fragmentation is not an error state — it is expected operation. A village on LoRa is a partition. A country with its internet cut is a partition. Every protocol layer functions correctly during partitions and converges correctly when partitions heal. The ledger compacts, the routing adapts, and the economics bound any damage to a predictable amount.

## What Makes Mehr Different

### Capability Marketplace

Nodes advertise what they can do. What they cannot do, they delegate to a neighbor and pay for the service. [Service discovery](marketplace/discovery) uses concentric rings so most requests resolve locally — your storage request finds a nearby provider before it ever discovers a distant data center. [Agreements](marketplace/agreements) are bilateral contracts between provider and client, and [verification](marketplace/verification) is cryptographic. A $30 solar relay and a GPU workstation participate on equal terms; the network routes requests to whoever can serve them best for the lowest cost.

### Proof of Service

Most decentralized networks create tokens through artificial work (hashing) or capital lockup (staking). Mehr mints tokens only when a provider delivers a real service — relaying traffic, storing data, or executing computations — to a client who pays through a funded payment channel. Minting is proportional to real economic activity and capped at 50% of net service income. A 2% burn on every payment creates a deflationary counterforce that keeps supply bounded.

### Zero Trust Economics

The economic layer assumes every participant is adversarial. Two mechanisms make cheating structurally unprofitable: **non-deterministic service assignment** (the client can't choose who serves the request) and a **net-income revenue cap** (cycling MHR produces zero minting). No staking, no slashing, no trust scores required. In isolated partitions, [additional defense layers](economics/token-security#attack-isolated-partition) bound damage to a predictable amount — even an infinitely long 3-node partition produces less than 1.5% total supply dilution.

### Free Between Friends

Nodes maintain [trust neighborhoods](economics/trust-neighborhoods) — sets of peers they relay for at zero cost. No tokens, no channels, no economic overhead. A local mesh where everyone trusts each other operates without the economic layer even activating. The boundary between free and paid is not set by the protocol — it emerges from each community's own trust relationships.

### Self-Sovereign Identity

Your identity is your cryptographic key — not an account on someone else's server. [MHR-ID](services/mhr-id) lets you build a rich profile (name, bio, avatar, linked accounts, achievements) where every field is a signed claim that peers can vouch for or dispute. You control who sees each field: public, trusted friends only, friends-of-friends, or specific people. No central identity provider. No data broker.

### Subjective Naming

There is no global DNS. [MHR-Name](services/mhr-name) provides human-readable names (`alice@geo:portland`, `my-blog@topic:tech`) that resolve from each viewer's position in the trust graph. Names registered by people you trust outrank names from strangers. Two communities can have different "alice" users — that's by design. Names can point to people, content, or [distributed applications](services/mhr-app).

### Distributed Applications

Applications on Mehr are not hosted on servers — they are [content-addressed packages](services/mhr-app) stored in the mesh. An AppManifest bundles contract code, UI, state schema, and dependencies into a single installable artifact. Users discover apps by name, install them locally, and upgrade via trust-weighted update propagation. No app store. No platform fee. No single point of removal.

## Protocol Stack Overview

Mehr is organized into seven layers, each building on the one below. Each layer depends only on the layer below it — applications never touch transport details, payment never touches routing internals, and security is structural, not bolted on. Click any layer to read its full specification.

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
