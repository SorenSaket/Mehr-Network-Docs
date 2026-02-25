---
sidebar_position: 2
title: FAQ
---

# Frequently Asked Questions

Plain-language answers. No jargon.

## The Basics

### What is Mehr?

Mehr is a network that lets devices talk to each other directly — without relying on a phone company, an ISP, or a cloud server. Your phone, laptop, or a cheap radio module can join the mesh and communicate with anyone nearby. Think of it like a community-owned telephone system that nobody controls.

### How do I join?

Install the app (or flash a device) and create an account. That's it. Your account is just a cryptographic key — no email, no phone number, no sign-up form. You're on the network immediately.

### What device do I need?

Anything from a [$30 solar-powered radio relay](hardware/reference-designs) to a smartphone to a full computer. The network adapts to what your device can do. Low-power devices relay text messages; powerful devices can host websites and run computations.

### Is it free?

**Talking to your friends and neighbors: always free.** You mark people as "trusted" (like adding a contact), and all communication between trusted people costs nothing.

**Reaching strangers or distant nodes:** costs a tiny amount of MHR (the network's internal token). You earn MHR automatically by helping relay other people's traffic — so for most people, the system is self-sustaining. You earn by participating, and you spend by using.

### Do I need to buy tokens?

No. You earn MHR by relaying traffic for others, which happens automatically in the background. The more your device helps the network, the more you earn. You can start using the network with zero tokens — free communication between trusted peers works immediately.

---

## Finding Things

### How do I find what's happening in my city?

Your device automatically discovers nearby nodes and their content. Here's how, from closest to furthest:

1. **Friends' feeds**: You follow people. Their posts show up on your device automatically, newest first. No algorithm choosing what you see — just a chronological feed.

2. **Neighborhood activity**: Your community has a label (like `mumbai-mesh` or `portland-mesh`). Subscribe to it and you'll see all local activity — forum posts, marketplace listings, wiki edits, new websites — from everyone in that community.

3. **Nearby nodes**: Your device constantly hears announcements from nearby nodes. You can browse what services and content exist within a few hops, like walking down a street and reading shop signs.

4. **Search**: If you want something specific that isn't nearby, you can search the wider network. It's slower and may cost a small amount, but you can find anything that anyone has published.

### How do I find my friends?

By their name. Everyone can pick a name scoped to their community — like `alice@portland-mesh` or `ravi@mumbai-mesh`. Type it in and you're connected. You can also use private nicknames ("Mom", "Work") that only exist on your device.

If you're physically near someone, your devices will discover each other automatically over radio or WiFi — no names needed.

### Is there a "feed" like Instagram or Twitter?

Yes, but better. You follow people and see their posts in chronological order. There is:

- **No algorithm** deciding what you see
- **No ads** injected into your feed
- **No central server** storing your social graph
- **No one** who can ban you from the network

On a good connection you get full images and video. On a weak radio link, you get text and tiny image previews. The app adapts automatically.

### Can I browse websites?

Yes. People host websites on Mehr just like on the regular internet, but without needing a server or domain name. You visit them by name (`mysite@portland-mesh`) or by direct link. Popular sites load fast because copies are cached throughout the network automatically.

---

## Communication

### How do I message someone?

Open the messaging app, pick a contact, type your message. It's end-to-end encrypted — only you and the recipient can read it. If they're offline, the network holds the message and delivers it when they come back online (like email, but encrypted).

### Can I make voice calls?

Yes, on connections with enough bandwidth. WiFi and cellular links support real-time voice. On slow radio links, voice isn't practical — use text messaging instead.

### Can I send photos and videos?

Yes. The app adapts to your connection:

| Connection | What you can send/receive |
|-----------|--------------------------|
| WiFi or cellular | Photos, videos, full media |
| Moderate radio link | Compressed images, text |
| Slow radio (LoRa) | Text only, with tiny image previews |

You never need to think about this — the app handles it automatically.

### What happens when I'm moving around?

Your device automatically handles roaming. It constantly listens for nearby nodes on all its radios (WiFi, Bluetooth, LoRa) and connects to the best one available — no manual switching required.

- **Walk into a cafe with a Mehr WiFi node?** Your device connects in under a second.
- **Walk out of WiFi range?** Traffic shifts to LoRa automatically. Apps adapt (images become text previews).
- **Visit the same cafe tomorrow?** Your device remembers it and reconnects instantly — no setup.
- **On a voice call while moving?** The call hands off between nodes with less than a second of interruption. Quality may change (WiFi → LoRa = high-fidelity → walkie-talkie) but the call doesn't drop.

Think of it like your phone switching between cell towers — except there's no phone company, no SIM card, and no monthly bill.

---

## Community

### How do communities form?

You mark people as trusted. They mark you as trusted. When a group of people all trust each other, that's a community. Nobody "creates" it or "runs" it — it emerges from real-world relationships.

Optionally, you can all label yourselves with the same community name (like `portland-mesh`) so newcomers can find you.

### Can I run a local forum?

Yes. A forum is just a shared space where community members post. A moderator contract enforces whatever rules your community agrees on. Different forums can have different rules — there's no platform-wide content policy.

### Can I sell things on a local marketplace?

Yes. Post a listing (text, photos, price), and it's visible to your neighborhood. Buyers contact you directly. Payment can happen in person, through an external service, or through MHR escrow (the network holds the payment until both sides confirm the deal).

### Can I host a website or blog?

Yes, and it's much simpler than traditional hosting:

| Traditional web | Mehr |
|----------------|-------|
| Rent a server | Not needed — content lives in the mesh |
| Buy a domain name ($10–50/year) | Pick a name for free (`myblog@mumbai-mesh`) |
| Get an SSL certificate | Not needed — everything is encrypted and verified automatically |
| Pay for traffic spikes | Visitors pay their own relay costs, not you |

You pay only for storage (tiny amounts of MHR), and popular content gets cheaper because it's cached everywhere.

---

## Privacy and Safety

### Is it private?

Yes. Messages are end-to-end encrypted. Social posts can be public or neighborhood-only. There is no central server with a copy of your messages, your contacts, or your browsing history. Your identity is a cryptographic key — you never need to provide your real name.

### Can someone spy on my messages?

No. End-to-end encryption means only the sender and recipient can read a message. Relay nodes carry encrypted blobs they cannot decrypt. Even your direct neighbors don't know if a packet originated from you or if you're just relaying it for someone else.

### Can someone shut down the network?

No single point of failure. There's no server to seize, no company to shut down, no domain to block. As long as any two devices can reach each other — by radio, WiFi, Bluetooth, or anything else — the network works.

---

## Economy

### How does money work on Mehr?

MHR is the network's internal token. Think of it like arcade tokens — they're valuable inside the arcade (network services), but they're not meant for trading on an exchange.

- **You earn MHR** by relaying traffic, storing data, or providing other services
- **You spend MHR** when your messages cross through untrusted infrastructure
- **Talking to friends is always free** — MHR only matters at trust boundaries

### What's it worth in real money?

MHR has no official exchange rate with any fiat currency. Its value comes from what it buys on the network — relay time, storage space, compute. The prices of these services float based on supply and demand, like any market. But you never need to convert MHR to dollars — it's a closed-loop system.

### Can I get rich from MHR?

That's not the point. MHR is designed to be spent on services, not hoarded or traded. There's no ICO, no pre-mine, no exchange listing. You earn it by contributing, you spend it by consuming. The goal is a functioning economy, not a speculative asset.

---

## Compared to What I Use Now

### How is this different from the regular internet?

| | Regular Internet | Mehr |
|--|----------------|-------|
| **Works without ISP** | No | Yes — radio, WiFi, anything |
| **Works during internet shutdown** | No | Yes — local mesh continues |
| **Free local communication** | No — you pay your ISP | Yes — trusted peers are free |
| **Your data on a corporate server** | Yes (Google, Meta, etc.) | No — data stays on your devices and your community's mesh |
| **Can be censored** | Yes — ISPs, DNS, app stores | Extremely difficult — no central control point |
| **Needs an account** | Email, phone number, ID | Just a cryptographic key (anonymous) |

### Can Mehr replace my internet connection?

**It depends on where you live.**

In a **dense area** (apartment building, neighborhood, campus) where many nodes run WiFi, the mesh delivers 10–300 Mbps per hop — comparable to cable internet. Add a few shared internet uplinks (Starlink, fiber, cellular) and the community mesh handles distribution. Most people would save 50–75% on connectivity costs. You can browse, stream, video call — normal internet use.

In a **rural or remote area** with only LoRa radio coverage, Mehr delivers 0.3–50 kbps — enough for text messaging, basic social feeds, and push-to-talk voice, but not video streaming or modern web browsing. Here, Mehr isn't replacing your internet — it's providing communication where there was none, or sharing one expensive satellite connection across an entire village.

| Your situation | What Mehr does |
|---------------|-----------------|
| Dense urban, many WiFi nodes | Replaces individual ISP subscriptions — share uplinks, save money |
| Suburban, mixed WiFi + LoRa | Supplements your connection — free local communication, shared backup uplink |
| Rural, LoRa only | Provides communication where there is none — text, voice, local services |
| No infrastructure at all | Only option that works — $30 solar radio nodes, no towers needed |

The key insight: Mehr doesn't compete with Starlink or cellular on raw speed. It **uses** them as transport — one Starlink dish becomes a shared community gateway. The mesh handles the local distribution and economics. Everyone gets internet access; the gateway operator earns; residents save.

### How is this different from Signal or WhatsApp?

Signal and WhatsApp need internet access and rely on central servers for delivery. Mehr works without internet, stores messages across the mesh (not one company's servers), and the network itself is decentralized. Nobody can block your access because there's nothing to block.

### How is this different from Bitcoin?

Bitcoin is money designed for global financial transactions. MHR is an internal utility token for paying network services. They share some concepts (cryptographic keys, no central authority) but serve completely different purposes. MHR is more like "bus tokens for the network" than a cryptocurrency.
