---
sidebar_position: 4
title: "MHR-ID: FAQ"
description: "Frequently asked questions about MHR-ID identity, claims, verification, and mobility."
keywords: [MHR-ID, FAQ, identity, verification, claims]
pdf: false
---

# MHR-ID: Frequently Asked Questions

<details>
<summary><strong>What is my identity on Mehr?</strong></summary>

Your identity is an Ed25519 key pair — your public key is your identity. No authority issues it, and no authority can revoke it. Everything else — your name, location claims, profile fields, external account links — are **claims** attached to that key, verified by peer vouches.

</details>

<details>
<summary><strong>Can I prove my physical location?</strong></summary>

Yes, via [RadioRangeProof](./verification.md#radiorangeproof). If nearby nodes can hear your LoRa radio beacon, they sign witness attestations proving you're within physical range. Multiple witnesses from known locations triangulate your approximate position. This works at neighborhood level on LoRa (1–15 km range), building level on WiFi, and room level on Bluetooth.

</details>

<details>
<summary><strong>What if I don't have internet access?</strong></summary>

Most MHR-ID features work without internet. Claims, vouches, profiles, visibility controls, and geographic verification all operate over the mesh. The only feature that requires internet is **external identity linking** (linking to GitHub, Twitter, etc.) — and even that can be verified by any peer with internet access, not just dedicated oracles.

</details>

<details>
<summary><strong>Can I link my GitHub/Twitter/Mastodon account?</strong></summary>

Yes. Post a signed challenge string on your external platform profile, then publish an ExternalIdentity claim on Mehr. Verification oracles (gateway nodes with internet) crawl the platform to confirm the link, or you can use OAuth flow. Any peer with internet can also manually verify and vouch for you. See [Identity Linking](./verification.md#identity-linking).

</details>

<details>
<summary><strong>Who can see my profile fields?</strong></summary>

You control visibility per-field. Each profile field is a separate claim with its own visibility setting:
- **Public**: Anyone can read it
- **TrustNetwork**: Your trusted peers and their trusted peers (2 hops)
- **DirectTrust**: Only your directly trusted peers
- **Named**: Only specific nodes you list

Different viewers see different subsets of your profile. See [Visibility Controls](./index.md#visibility-controls).

</details>

<details>
<summary><strong>What happens to my identity if I move cities?</strong></summary>

Your cryptographic identity stays the same — only your geo-scoped claims change. Old location vouches expire naturally (30 epochs), new location claims build via RadioRangeProof and peer attestation. Trust relationships, payment channels, and Topic-scoped communities are all **location-independent** and travel with you. See [Geographic Mobility](./mobility.md#geographic-mobility).

</details>

<details>
<summary><strong>What if my key is compromised?</strong></summary>

Publish a KeyRotation claim signed by **both** the old and new keys. This provides strong cryptographic evidence of legitimate migration. Trusted peers vouch for the rotation, services migrate agreements to the new key, and the old key's reputation transfers. If you've lost the old key entirely, you'll need to rebuild trust from scratch — there's no central recovery mechanism.

</details>

<details>
<summary><strong>How does MHR-ID compare to DID/SSI systems?</strong></summary>

MHR-ID is simpler and mesh-native. Unlike W3C DIDs, there's no DID document resolution, no blockchain anchoring, and no DID method abstraction layer. Your key **is** your identity. Claims replace VCs (Verifiable Credentials) with a lighter-weight, gossip-friendly format. Trust is computed locally from your trust graph, not from a credential issuer hierarchy. See the [comparison table](./mobility.md#comparison-with-other-identity-systems).

</details>

<details>
<summary><strong>Can I be anonymous?</strong></summary>

Yes. You can operate with just a key pair and no claims at all. No display name, no geo presence, no external links. You'll have a low verification level and be treated as untrusted by most nodes, but you can still use the network. For stronger anonymity, generate a new key pair — there's no link between keys unless you explicitly publish a KeyRotation claim.

</details>
