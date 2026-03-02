---
sidebar_position: 8
title: Digital Licensing
description: "Cryptographically verifiable digital licensing for assets like images, music, and software stored on the Mehr mesh."
keywords:
  - licensing
  - digital rights
  - cryptographic proof
  - content licensing
  - creator economy
---

# Digital Licensing

Mehr enables **cryptographically verifiable licensing** for digital assets — images, music, software, datasets, or any content. A license is a signed agreement between a licensor and licensee, stored on the mesh and verifiable by anyone. No enforcement mechanism exists at the protocol level — just like the real world, enforcement is social and legal. Mehr provides the *proof*.

:::info[App Manifest]
Digital licensing is packaged as a **Headless** (compute only) [AppManifest](/docs/L5-services/mhr-app). It composes MHR-Store for immutable LicenseOffer and LicenseGrant DataObjects, MHR-Compute for verification contracts that validate signature chains and expiry, MHR-DHT for license and asset discovery, and MHR-Name for licensor identity resolution. The manifest has no UI bundle — licensing logic is invoked by content applications (social, hosting) that embed license verification in their own interfaces.
:::

## Overview

```
                       Licensing Flow

  LICENSOR                                          LICENSEE
  ────────                                          ────────
  Publishes asset ──▶ DataObject on mesh
  Publishes LicenseOffer ──▶ "Here are my terms"

                    ◀── Licensee discovers offer
                    ◀── Licensee pays (MHR or fiat)

  Signs LicenseGrant ──▶ Bilateral signed proof
                         of license

  Licensee uses asset in derivative work:
    PostEnvelope.references includes LicenseGrant hash
    → Anyone can verify the chain:
       derivative → LicenseGrant → LicenseOffer → original asset
```

## LicenseOffer

A **LicenseOffer** is a DataObject published by the asset owner, advertising the terms under which others may license the asset:

```
LicenseOffer {
    licensor: NodeID,
    asset_hash: Blake3Hash,           // hash of the licensed DataObject
    license_type: enum {
        Perpetual,                    // one-time payment, permanent license
        Subscription {
            period: u64,              // epochs per billing cycle
        },
        Free,                         // no payment required (e.g., Creative Commons equivalent)
    },
    terms: LicenseTerms,
    price: u64,                       // μMHR per grant (0 for Free type)
    max_grants: Option<u32>,          // None = unlimited, Some(N) = limited edition
    grants_issued: u32,               // current count (updated by licensor)
    created: Timestamp,
    expires: Option<Timestamp>,       // offer expiry (None = open-ended)
    signature: Ed25519Sig,            // signed by licensor
}

LicenseTerms {
    derivative_allowed: bool,         // can licensee create derivative works?
    attribution_required: bool,       // must licensee credit the licensor?
    commercial_use: bool,             // can licensee use commercially?
    transfer_allowed: bool,           // can licensee transfer the license?
    custom_terms: Option<String>,     // human-readable terms (max 1024 chars)
}
```

### Offer Properties

- **Immutable once published**: A LicenseOffer is an immutable DataObject. To change terms, publish a new offer and let the old one expire.
- **Max grants**: Limited-edition licensing. A photographer might offer 100 licenses for a stock photo. `grants_issued` is tracked by the licensor and visible to potential licensees, but not enforced by the protocol — the licensor's reputation depends on honoring the limit.
- **Custom terms**: Free-text for anything the structured fields don't cover. Clients display this to the licensee before purchase.

## LicenseGrant

A **LicenseGrant** is the bilateral proof that a license was issued:

```
LicenseGrant {
    offer_hash: Blake3Hash,           // references the LicenseOffer
    licensee: NodeID,
    granted: Timestamp,
    expires: Option<Timestamp>,       // None for Perpetual, Some for Subscription
    payment_proof: Option<Blake3Hash>,// hash of payment channel state or settlement record
    signature_licensor: Ed25519Sig,   // signed by licensor
    signature_licensee: Ed25519Sig,   // signed by licensee
}
```

### Grant Properties

- **Bilaterally signed**: Both parties sign the grant. This prevents forged licenses (licensee can't self-sign) and disputed grants (licensor can't deny issuing it).
- **Payment proof**: References the [payment channel](/docs/L3-economics/payment-channels) state or settlement record that proves payment occurred. For fiat payments, this may be `None` — the off-protocol payment is between the parties.
- **Expiry**: Subscription licenses expire and must be renewed. The licensor publishes a new LicenseGrant for each renewal period.
- **Stored as DataObject**: The grant lives on the mesh as an immutable [DataObject](/docs/L5-services/mhr-store), retrievable by anyone who knows its hash.

## Verification

Anyone can verify a license chain:

```
Verification chain:

  1. Derivative work (PostEnvelope)
     └── references: [license_grant_hash]

  2. LicenseGrant
     ├── offer_hash → LicenseOffer
     ├── signature_licensor → verify against licensor's public key
     ├── signature_licensee → verify against licensee's public key
     └── expires → check if still valid

  3. LicenseOffer
     ├── asset_hash → original asset
     ├── signature → verify licensor owns the offer
     └── terms → check derivative_allowed, commercial_use, etc.

  4. Original asset (DataObject)
     └── verify licensor is the author (signature on the DataObject)
```

**How a client verifies a derivative work uses licensed assets:**

1. Read the derivative's `PostEnvelope.references` — look for hashes that resolve to LicenseGrant objects
2. Fetch each LicenseGrant from the DHT
3. Verify both signatures (licensor + licensee)
4. Check expiry (is the grant still valid?)
5. Fetch the LicenseOffer via `offer_hash`
6. Verify terms allow the observed use (derivative, commercial, etc.)
7. Optionally fetch the original asset to confirm the licensor is the author

Clients can display verification status: "Licensed from alice@geo:us/oregon/portland" with a link to the original asset.

## Payment Models

### One-Time (Perpetual)

```
Perpetual license flow:

  1. Licensee discovers LicenseOffer (browse, search, curator recommendation)
  2. Licensee opens payment channel with licensor (or uses existing one)
  3. Licensee pays price in μMHR
  4. Licensor signs LicenseGrant with expires: None
  5. Both parties sign; grant stored on mesh
  6. Licensee uses asset indefinitely
```

### Subscription (Recurring)

```
Subscription license flow:

  1. Licensee pays first period
  2. Licensor signs LicenseGrant with expires: granted + period
  3. Before expiry, licensee pays again
  4. Licensor signs a new LicenseGrant (new hash, new expiry)
  5. If licensee stops paying, license expires naturally
     → No revocation needed — expiry is the default
```

Subscription payment is bilateral — the licensor and licensee maintain a [payment channel](/docs/L3-economics/payment-channels) and settle periodically. There is no automatic billing; the licensee must actively renew.

### Fiat Payment

For off-network payments (fiat, barter, or any other arrangement), the `payment_proof` field is `None`. The LicenseGrant still proves the license was issued (both parties signed it) — the payment happened off-protocol.

This is the expected model for [gateway operator](/docs/L3-economics/token-economics#gateway-operators-fiat-onramp) customers who pay fiat and don't hold MHR.

## Use Cases

### Stock Media

A photographer publishes images on Mehr. Each image has a LicenseOffer:

```
LicenseOffer {
    licensor: photographer_node_id,
    asset_hash: photo_hash,
    license_type: Perpetual,
    terms: LicenseTerms {
        derivative_allowed: true,
        attribution_required: true,
        commercial_use: true,
        transfer_allowed: false,
    },
    price: 50_000,                    // 50,000 μMHR
    max_grants: None,                 // unlimited
    ...
}
```

A blogger finds the photo, pays 50,000 μMHR, receives a LicenseGrant, and includes it in their `PostEnvelope.references`. Any reader can verify the blogger licensed the image.

### Software Licensing

A developer publishes software with a subscription license:

```
LicenseOffer {
    license_type: Subscription { period: 52_560 },  // ~1 year in epochs
    terms: LicenseTerms {
        derivative_allowed: false,
        attribution_required: false,
        commercial_use: true,
        transfer_allowed: false,
    },
    price: 1_000_000,                // 1,000,000 μMHR per year
    max_grants: Some(500),           // 500-seat limit
    ...
}
```

### Creative Commons Equivalent

An artist publishes free-to-use artwork:

```
LicenseOffer {
    license_type: Free,
    terms: LicenseTerms {
        derivative_allowed: true,
        attribution_required: true,
        commercial_use: false,
        transfer_allowed: true,
    },
    price: 0,
    max_grants: None,
    ...
}
```

The LicenseGrant still exists (bilaterally signed) — it proves attribution rights even when no payment occurs.

## Off-Network Verifiability

License grants extend **beyond the Mehr network**. A LicenseGrant contains:

- The licensor's public key (verifiable without network access)
- The licensee's public key (verifiable without network access)
- Both signatures (verifiable with standard Ed25519 libraries)
- The asset hash (verifiable against the original file)

Anyone with a copy of the LicenseGrant and the public keys can verify the license — no network connection required. This means:

- A website can display "Licensed via Mehr" with a verifiable proof
- A court can verify license authenticity using standard cryptographic tools
- An archive can preserve license provenance alongside the licensed asset
- A marketplace outside Mehr can check license validity

## Wire Format

### LicenseOffer

| Field | Size | Description |
|-------|------|-------------|
| `licensor` | 16 bytes | Destination hash |
| `asset_hash` | 32 bytes | Blake3 hash of licensed asset |
| `license_type` | 1 byte | 0=Perpetual, 1=Subscription, 2=Free |
| `subscription_period` | 8 bytes | Epochs per cycle (only if Subscription, 0 otherwise) |
| `terms` | 5 bytes | 4 boolean flags (1 byte packed) + custom_terms length |
| `custom_terms` | variable | Length-prefixed UTF-8 (u16 length, max 1024 chars) |
| `price` | 8 bytes | μMHR |
| `max_grants` | 5 bytes | 1 byte flag + 4 bytes u32 (if present) |
| `grants_issued` | 4 bytes | u32 |
| `created` | 8 bytes | Unix timestamp |
| `expires` | 9 bytes | 1 byte flag + 8 bytes timestamp (if present) |
| `signature` | 64 bytes | Ed25519 signature |

Minimum size (no custom terms, no max_grants, no expiry): ~160 bytes.

### LicenseGrant

| Field | Size | Description |
|-------|------|-------------|
| `offer_hash` | 32 bytes | Blake3 hash of LicenseOffer |
| `licensee` | 16 bytes | Destination hash |
| `granted` | 8 bytes | Unix timestamp |
| `expires` | 9 bytes | 1 byte flag + 8 bytes timestamp (if present) |
| `payment_proof` | 33 bytes | 1 byte flag + 32 bytes hash (if present) |
| `signature_licensor` | 64 bytes | Ed25519 signature |
| `signature_licensee` | 64 bytes | Ed25519 signature |

Total: 226 bytes. Lightweight enough to gossip and store indefinitely.

## Limitations

- **No enforcement**: The protocol proves a license exists. It does not prevent unlicensed use. Enforcement is social (community reputation) and legal (courts), just like the real world.
- **No revocation**: A perpetual LicenseGrant, once signed, cannot be revoked at the protocol level. The licensor can publish a signed statement claiming revocation, but the original grant remains valid cryptographically. Subscription licenses handle this naturally via expiry.
- **Licensor authenticity**: The protocol proves the licensor signed the offer, but cannot prove they are the original creator of the asset. A plagiarist could license stolen work. This is an application-layer problem — reputation, identity claims, and peer vouches provide social proof of authorship.
- **`grants_issued` is self-reported**: The licensor updates this counter. A dishonest licensor could undercount to sell more than `max_grants`. Auditing is possible (count all LicenseGrants referencing the offer on the DHT) but not guaranteed to find all grants.

## Comparison with Existing Systems

| | Traditional Licensing | DRM | Mehr Licensing |
|---|---|---|---|
| **Proof of license** | Paper contract, email receipt | Encrypted content + license server | Bilaterally signed DataObject (cryptographic proof) |
| **Verification** | Contact the licensor | Phone home to license server | Verify Ed25519 signatures (offline-capable) |
| **Enforcement** | Legal system | Technical (content won't play without license) | None at protocol level (social + legal) |
| **Transfer** | Often prohibited or complex | Usually prohibited | If `transfer_allowed: true`, licensee can re-grant |
| **Revocation** | Legal notice | License server revokes | Subscription: expiry. Perpetual: not possible |
| **Works offline** | Paper contract: yes | Usually no (needs license server) | Yes (signatures are self-verifying) |
| **Cost** | Legal fees, platform fees | Platform cut (30%+ on app stores) | Direct bilateral payment (zero platform fee) |
