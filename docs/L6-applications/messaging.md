---
sidebar_position: 1
title: Messaging
description: "End-to-end encrypted, store-and-forward messaging built on MHR-Store, MHR-Pub, and Mehr payment channels."
keywords:
  - messaging
  - encryption
  - store-and-forward
  - offline delivery
  - E2E
  - chat
---

# Messaging

End-to-end encrypted, store-and-forward messaging built on the Mehr service primitives.

:::info[App Manifest]
Messaging is packaged as a **Full** (UI + compute) [AppManifest](/docs/L5-services/mhr-app). It composes MHR-Store for persistent message storage, MHR-Pub for delivery notifications and presence, and MHR-Compute contracts for group key management and co-admin delegation. The UI bundle handles compose/read views while pub/sub topic templates map to per-conversation and per-group notification channels.
:::

## Architecture

Messaging composes multiple service layers:

| Component | Built On |
|-----------|----------|
| Message storage & persistence | [MHR-Store](/docs/L5-services/mhr-store) |
| Delivery notifications | [MHR-Pub](/docs/L5-services/mhr-pub) |
| Transport encryption | Link-layer encryption (Reticulum-derived) |
| End-to-end encryption | [E2E encryption](/docs/L2-security/security#end-to-end-encryption-data-payloads) |

## How It Works

1. **Compose**: Alice writes a message to Bob
2. **Encrypt**: Message encrypted end-to-end for Bob's public key
3. **Store**: Encrypted message stored as an immutable DataObject in MHR-Store
4. **Notify**: MHR-Pub sends a notification to Bob (or his relay nodes)
5. **Deliver**: If Bob is online, he retrieves immediately. If offline, relay nodes cache the message for later delivery.
6. **Pay**: Relay and storage fees paid automatically via [payment channels](/docs/L3-economics/payment-channels)

## Offline Delivery

Relay nodes cache messages for offline recipients. When Bob comes back online:

1. His nearest relay nodes inform him of pending messages
2. He retrieves and decrypts them
3. The relay nodes are paid for the storage duration

This is store-and-forward messaging — similar to email, but encrypted and decentralized.

## Group Messaging

Group messages use shared symmetric keys managed by an MHR-Compute contract:

```
GroupState {
    group_id: Blake3Hash,
    members: Set<NodeID>,
    current_key: ChaCha20Key,        // current group symmetric key
    key_epoch: u64,                   // increments on every rotation
    admin: NodeID,                    // creator; can add/remove members
    co_admins: Vec<CoAdminCertificate>,  // up to 3 delegated co-admins
    admin_sequence: u64,             // monotonic counter for admin operations
}

CoAdminCertificate {
    co_admin: NodeID,
    permissions: enum { Full, MembersOnly, RotationOnly },
    granted_by: NodeID,              // must be the group creator
    signature: Ed25519Signature,     // creator's signature over (group_id, co_admin, permissions)
}
```

### Key Management

- **Creation**: The group creator generates the first symmetric key and encrypts it individually for each member's public key (standard E2E envelope per member)
- **Rotation**: When a member joins or leaves, the admin (or any authorized co-admin) generates a new key and distributes it to all current members. The key epoch increments. Old keys are retained locally so members can decrypt historical messages
- **No forward secrecy for groups**: A new member receives only the current key — they cannot decrypt messages sent before they joined. A removed member retains old keys for messages they already received but cannot decrypt new messages (new key was never sent to them)
- **Maximum group size**: Practical limit of ~100 members, constrained by key distribution bandwidth (each rotation sends one E2E-encrypted key envelope per member, ~100 bytes each)

### Co-Admin Delegation

The group creator can delegate admin authority to up to 3 co-admins via signed `CoAdminCertificate` records. This solves the single-admin availability problem without requiring threshold cryptography.

- **Any co-admin can independently**: add/remove members, rotate the group key, and (if granted `Full` permission) promote/demote other co-admins
- **Conflict resolution**: All admin operations carry a monotonically increasing `admin_sequence` number. If two co-admins issue conflicting operations (e.g., simultaneous key rotations), members accept the operation with the highest sequence number. Ties are broken by lowest admin public key hash
- **No threshold crypto**: Co-admin delegation uses only Ed25519 signatures — no multi-round key generation protocols, no new cryptographic primitives. Each delegation certificate is ~128 bytes
- **Graceful degradation**: If all admins go offline, the group continues functioning with its current key. No key rotation or membership changes occur until at least one admin returns

## Bandwidth on LoRa

A 1 KB text message over LoRa takes approximately 10 seconds to transmit — comparable to SMS delivery times. This is viable for text-based communication in constrained environments.

Attachments are DataObjects with `min_bandwidth` set appropriately. A photo attachment might declare `min_bandwidth: 10000` (10 kbps), meaning it will transfer when the recipient has a WiFi link available but won't be attempted over LoRa.

## Security Considerations

<details className="security-item">
<summary>Relay Metadata Leakage</summary>

**Vulnerability:** Even though message content is end-to-end encrypted, relay nodes can observe traffic patterns — who is communicating with whom, when, and how often. Timing correlation attacks could de-anonymize users.

**Mitigation:** Mehr's multi-hop relay architecture provides plausible deniability — a relay node cannot distinguish whether a neighbor originated a packet or is relaying it for someone else. Messages are encrypted blobs with no plaintext metadata. For high-sensitivity scenarios, users can pad messages to uniform sizes and introduce random delays.

</details>

<details className="security-item">
<summary>Group Admin Key Compromise</summary>

**Vulnerability:** If the group creator's private key is stolen, the attacker can add themselves to the group, rotate the symmetric key, and read all future messages. No threshold cryptography is used.

**Mitigation:** The group creator can perform [key rotation](/docs/L5-services/mhr-id) via MHR-ID, which invalidates the compromised key. Co-admin delegation allows trusted members to manage the group if the creator is unavailable. Group members who notice unauthorized changes can leave and form a new group. The design trades multi-party key management complexity for simplicity — appropriate for a mesh network where constrained devices cannot run heavy MPC protocols.

</details>

<details className="security-item">
<summary>No Forward Secrecy for Groups</summary>

**Vulnerability:** Group messaging uses a shared symmetric key. Compromising this key exposes all past messages encrypted with it — there is no per-message forward secrecy as in Signal's Double Ratchet protocol.

**Mitigation:** Admin-initiated key rotation periodically refreshes the group key, limiting the window of exposure. The key is distributed via individual X25519 key exchanges with each member, so compromising one member doesn't reveal the distribution channel to others. For conversations requiring forward secrecy, use direct (1:1) messaging, which supports per-session key exchange.

</details>
