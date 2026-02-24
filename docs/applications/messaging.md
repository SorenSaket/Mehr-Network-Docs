---
sidebar_position: 1
title: Messaging
---

# Messaging

End-to-end encrypted, store-and-forward messaging built on the NEXUS service primitives.

## Architecture

Messaging composes multiple service layers:

| Component | Built On |
|-----------|----------|
| Message storage & persistence | [NXS-Store](../services/nxs-store) |
| Delivery notifications | [NXS-Pub](../services/nxs-pub) |
| Transport encryption | Link-layer encryption (Reticulum-derived) |
| End-to-end encryption | [E2E encryption](../protocol/security#end-to-end-encryption-data-payloads) |

## How It Works

1. **Compose**: Alice writes a message to Bob
2. **Encrypt**: Message encrypted end-to-end for Bob's public key
3. **Store**: Encrypted message stored as an immutable DataObject in NXS-Store
4. **Notify**: NXS-Pub sends a notification to Bob (or his relay nodes)
5. **Deliver**: If Bob is online, he retrieves immediately. If offline, relay nodes cache the message for later delivery.
6. **Pay**: Relay and storage fees paid automatically via [payment channels](../economics/payment-channels)

## Offline Delivery

Relay nodes cache messages for offline recipients. When Bob comes back online:

1. His nearest relay nodes inform him of pending messages
2. He retrieves and decrypts them
3. The relay nodes are paid for the storage duration

This is store-and-forward messaging — similar to email, but encrypted and decentralized.

## Group Messaging

Group messages use shared symmetric keys managed by an NXS-Compute contract:

- A group key is generated and shared with all members
- The contract handles key rotation when members join or leave
- Messages are encrypted with the current group key
- All members can decrypt; non-members cannot

## Bandwidth on LoRa

A 1 KB text message over LoRa takes approximately 10 seconds to transmit — comparable to SMS delivery times. This is viable for text-based communication in constrained environments.

Attachments are DataObjects with `min_bandwidth` set appropriately. A photo attachment might declare `min_bandwidth: 10000` (10 kbps), meaning it will transfer when the recipient has a WiFi link available but won't be attempted over LoRa.
