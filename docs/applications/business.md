---
sidebar_position: 10
title: Business Use Cases
description: "How businesses — from neighborhood shops to distributed enterprises — use Mehr for communication, identity, commerce, and infrastructure."
keywords:
  - business
  - enterprise
  - commercial
  - gateway operator
  - ISP
  - identity verification
  - secure communication
  - marketplace
---

# Business Use Cases

Mehr isn't just for individuals. Every capability in the protocol — identity, storage, compute, naming, marketplace — maps to real business operations. The economic model rewards service providers, and the trust graph provides a natural framework for business relationships.

:::info[App Manifest]
Business applications are packaged as [AppManifest](../services/mhr-app) entries. A storefront is a **Full** manifest composing MHR-Store (product catalog), MHR-Name (brand name resolution), MHR-Compute (escrow and order logic), and MHR-Pub (inventory and price updates). A gateway operator is a **Service** manifest composing payment-channels (fiat↔MHR bridging) and trust-neighborhood management.
:::

## Local Business Scenarios

### Neighborhood Gateway Operator

**What you do:** Operate a mesh node with an internet uplink (Starlink, fiber, or cellular) and offer network access to your community.

**How it works:**

1. Deploy a Raspberry Pi or mini PC with LoRa + WiFi + internet uplink
2. Register as a [gateway operator](../economics/token-economics#gateway-operators-fiat-onramp)
3. Subscribers sign up (fiat monthly fee or prepaid)
4. You add subscribers as trusted peers — their traffic flows for free through your node
5. You handle MHR costs for onward relay; subscribers never touch tokens

**Revenue:** Fiat subscriptions + minting rewards from relay/storage volume. In areas with no ISP, you are the ISP — but with $100 in hardware instead of millions in tower infrastructure.

| Scale | Hardware | Monthly Revenue (est.) | Customers |
|-------|----------|----------------------|-----------|
| Apartment building | RPi + LoRa + WiFi | $200–500 | 20–50 units |
| Rural village | Solar node + Starlink | $100–300 | 10–30 households |
| Co-working space | Mini PC + Ethernet | $300–800 | 30–80 members |
| Campus / hotel | Multiple APs + gateway | $1,000–5,000 | 100–500 users |

### Local Marketplace Operator

**What you do:** Run a [curated feed](social) for your community's buy/sell listings.

**How it works:**

1. Create a curated commerce feed tagged with your geographic scope (e.g., `market@geo:us/or/portland`)
2. Merchants post listings (text, photos, price) as PostEnvelopes
3. You curate quality — approve legitimate sellers, flag scammers
4. Buyers browse your feed, contact sellers directly, pay in-person or via MHR escrow
5. You earn curation fees from listing visibility

**Value proposition:** No platform fees (no Etsy 6.5%, no eBay 13%). Buyers and sellers pay only relay costs. Your curation creates the value — and you earn from it directly through the [kickback system](social#kickback-economics).

### Café or Shop WiFi Node

**What you do:** Run a mesh WiFi node in your business. Customers get free local access; cross-mesh traffic earns you MHR.

**How it works:**

1. Set up a mesh-enabled WiFi access point ($30–50 hardware)
2. Customers connect automatically — their devices discover your node
3. Local traffic (within your trust neighborhood) is free — draws customers in
4. Cross-boundary traffic (customers accessing distant content) earns relay fees in MHR
5. Optional: offer premium bandwidth tiers via fiat subscription

**Analogy:** Free WiFi that actually pays you instead of costing you.

## Enterprise Scenarios

### Secure Team Communication

**Problem:** Corporate messaging (Slack, Teams) routes through third-party servers. Sensitive communications are accessible to the platform provider and vulnerable to server-side breaches.

**Mehr solution:** Teams use [group messaging](messaging) with end-to-end encryption. Messages traverse the mesh — no corporate server, no third-party platform. Admin delegation allows team leads to manage groups. The mesh operates on company-owned hardware (office nodes, employee devices).

| Traditional | Mehr |
|-------------|------|
| $8–25/user/month (Slack Business+) | Hardware cost only (one-time) |
| Messages stored on Slack's servers | Messages on employee devices + mesh nodes |
| Requires internet | Works over local mesh (no internet dependency) |
| Platform can read messages | E2E encrypted — only participants read messages |
| Single point of failure (platform outage) | Mesh is resilient — no single point of failure |

### Identity Verification Services

**Problem:** KYC (Know Your Customer), age verification, and credential checking require centralized identity providers that accumulate sensitive personal data.

**Mehr solution:** [MHR-ID](../services/mhr-id) provides self-certifying identity with [verifiable credentials](../services/mhr-id/verification). A verification service attests to a user's identity (e.g., "this person is over 18" or "this business is registered in Oregon") by signing an IdentityClaim. The claim is cryptographically verifiable without contacting the issuer — offline verification works.

**Business model:** Charge fiat per attestation. A notary, bank, or government office issues signed claims. Businesses that need to verify customers check claims locally — no API calls, no database queries, no data sharing with the verification provider.

### Distributed Team Infrastructure

**Problem:** Remote teams rely on cloud infrastructure (AWS, Azure) for file sharing, compute, and communication. Costs scale with usage, and data residency requirements complicate operations.

**Mehr solution:**

- **File sharing:** [Cloud storage](cloud-storage) with client-side encryption. Files distributed across team-operated mesh nodes. No cloud provider holds decryption keys.
- **Compute delegation:** Heavy workloads (CI/CD, data processing, ML inference) run on team members' hardware via [MHR-Compute](../services/mhr-compute) agreements. No cloud bill.
- **Communication:** Encrypted messaging and voice over the mesh. Works on-site (office mesh) and remotely (via internet-connected gateways).

### Supply Chain and IoT

**Problem:** Industrial IoT devices (sensors, controllers, monitoring equipment) typically require cellular connectivity and cloud platforms, creating recurring costs and single points of failure.

**Mehr solution:** IoT devices run as [L0/L1 mesh nodes](../hardware/device-tiers) communicating via LoRa. Sensor data flows through the mesh to collection points. Payment channels handle micro-costs automatically. No cellular SIM, no cloud subscription.

| Scenario | Mesh Advantage |
|----------|---------------|
| **Agricultural monitoring** | Solar-powered LoRa sensors across fields — no cellular coverage needed |
| **Warehouse tracking** | Indoor mesh of ESP32 nodes — asset location without dedicated infrastructure |
| **Fleet management** | Vehicle-mounted nodes form mobile mesh — location/status without cellular |
| **Building management** | HVAC, lighting, access control via mesh — no per-device cloud subscription |

### Content Platform / Digital Publishing

**Problem:** Content platforms (Substack, Patreon, Medium) take 5–30% of creator revenue. Creators depend on platform decisions about visibility, monetization, and content policy.

**Mehr solution:** Publishers host content directly on the mesh via [social feeds](social) and [hosting](hosting). Readers pay creators directly through the [kickback system](social#kickback-economics). No platform cut. Content propagation is driven by genuine demand, not algorithmic promotion.

**Revenue model:**

| Revenue Source | Who Earns | How |
|---------------|-----------|-----|
| Content reads | Creator | Kickback from reader's retrieval fee (~50%) |
| Curation | Curator | Curation fee from recommended reads |
| Premium content | Creator | Higher retrieval fee, full-post paywall |
| Licensing | Creator | [LicenseGrant](licensing) fees for derivatives/commercial use |

### Digital Licensing Business

**Problem:** Stock photo agencies, music libraries, and software vendors need centralized platforms to manage license issuance and verification. Platforms take 40–85% of license fees.

**Mehr solution:** Creators publish [LicenseOffers](licensing) directly. Buyers purchase [LicenseGrants](licensing) — cryptographically signed, verifiable without network access. No platform intermediary. The creator sets all terms and receives the full payment.

## Gateway as a Business

The [gateway operator](../economics/token-economics#gateway-operators-fiat-onramp) model is Mehr's primary business-facing primitive. Gateways bridge the fiat-to-crypto gap, making the network accessible to users and businesses that don't want to deal with tokens.

### Gateway Revenue Streams

| Stream | Source | Margin |
|--------|--------|--------|
| **Subscriber fees** | Monthly fiat subscriptions from consumers | Set by operator |
| **Minting rewards** | MHR minted from relay/storage volume across all service types | Protocol-defined |
| **Premium services** | Higher tiers (more storage, faster relay, compute access) | Set by operator |
| **Enterprise contracts** | Dedicated bandwidth/storage for business customers | Negotiated |
| **Roaming agreements** | Revenue sharing with other gateways for roaming subscribers | Bilateral |

### Competitive Dynamics

Multiple gateways can operate in the same area. Competition drives prices down and quality up — standard market economics. Consumers can switch gateways at any time because identity is self-certifying (no lock-in). This creates a natural check on pricing power.

A gateway in a **monopoly position** (sole operator in a rural area) has natural pricing power but faces the constraint that excessive pricing encourages community members to deploy their own nodes — the $35 cost of a Raspberry Pi is the ceiling on gateway extraction.

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>Do I need technical knowledge to run a gateway business?</summary>

Initial setup requires basic technical skills (installing software on a Raspberry Pi or mini PC, configuring WiFi and LoRa radios). Once running, the gateway operates autonomously — the protocol handles routing, billing, and service negotiation. The fiat billing side (subscriptions, payment processing) is an off-protocol business concern handled however you prefer.

</details>

<details className="faq-item">
<summary>How do businesses handle compliance and regulation?</summary>

Mehr provides infrastructure — how businesses use it is subject to local law, just like the internet. Gateway operators may need to comply with telecommunications regulations in their jurisdiction. Identity verification services must comply with data protection laws. The protocol itself is neutral — it provides cryptographic tools, not legal opinions.

</details>

<details className="faq-item">
<summary>Can a business accept MHR as payment for non-network services?</summary>

Yes. MHR is a transferable token — if a business wants to accept it for goods or services, nothing in the protocol prevents that. The business would need to value MHR based on what it can buy on the network (relay, storage, compute time). In practice, gateway operators are the natural fiat↔MHR exchange point.

</details>

<details className="faq-item">
<summary>What's the minimum investment to start a gateway business?</summary>

Hardware: $35–100 (Raspberry Pi + LoRa module + WiFi). Internet uplink: whatever you already have (home fiber, Starlink, cellular). Software: free (open source). The primary ongoing cost is the internet uplink. Revenue potential depends on subscriber count and local demand.

</details>

<!-- faq-end -->

## Security Considerations

<details className="security-item">
<summary>Gateway Operator Monopoly Abuse</summary>

**Vulnerability:** In areas with only one gateway operator, the operator can overcharge subscribers or degrade service quality without competitive pressure.

**Mitigation:** The barrier to entry is a $35 Raspberry Pi. Any community member can deploy a competing gateway. Social pressure (trust revocation) penalizes exploitative operators. Subscribers can leave instantly — identity is self-certifying, no lock-in.

</details>

<details className="security-item">
<summary>Fraudulent Business Listings</summary>

**Vulnerability:** A seller posts fake marketplace listings (products that don't exist, misleading descriptions) to collect payment.

**Mitigation:** Trust-weighted visibility means unknown sellers have low reach. Escrow via MHR payment channels allows conditional release (buyer confirms receipt before payment finalizes). Curator reputation is staked — a curator who includes fraudulent listings loses subscriber trust. Community trust revocation isolates repeat offenders.

</details>

<details className="security-item">
<summary>IoT Device Compromise</summary>

**Vulnerability:** A compromised IoT sensor node could flood the mesh with fake data or act as an attack vector for the wider network.

**Mitigation:** IoT devices operate as L0/L1 nodes with limited capabilities — they cannot run contracts, mint tokens, or participate in governance. Per-epoch credit limits cap the damage any single compromised node can cause. Trust revocation immediately isolates suspicious devices. The mesh's decentralized architecture means compromising one sensor doesn't grant access to the collection endpoint's data.

</details>
