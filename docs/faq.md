---
sidebar_position: 2
title: FAQ
description: Frequently asked questions about the Mehr Network — covering protocol design, tokenomics, hardware requirements, and comparison with other mesh projects.
keywords: [FAQ, mesh network, questions, Mehr Network]
pdf: false
---

# Frequently Asked Questions

Plain-language answers. No jargon.

## The Basics

<details className="faq-item">
<summary>What is Mehr?</summary>

Mehr is a communication network that doesn't need the internet, phone towers, or any central service. Devices talk directly to each other using radios (LoRa, WiFi, Bluetooth) and relay messages through the mesh — like passing a note through friends until it reaches the person you want.

There's no company in the middle. No account to create. No server to depend on. Your identity is a cryptographic key pair — you generate it on your device, and that's it. See [Introduction](introduction) for the full overview.

</details>

<details className="faq-item">
<summary>How do I join?</summary>

Get a device (even just a phone), install the Mehr app, and power it on. Your device generates a cryptographic identity and starts discovering nearby nodes. There's no sign-up, no email, no phone number required.

To become part of a community, mark your neighbors as trusted — and have them mark you as trusted. That's it. The trust graph *is* the network.

</details>

<details className="faq-item">
<summary>What device do I need?</summary>

Anything from a $5 ESP32 module to a full desktop. The protocol adapts to what you have:

| Device | What It Does |
|--------|-------------|
| ESP32 + LoRa ($5–15) | Basic radio relay — extends mesh coverage |
| Raspberry Pi ($35–50) | Full node — relay, storage, naming, routing |
| Android phone | All services + UI — messaging, social, voice |
| Desktop/server | High-capacity relay, storage provider, compute provider |

See [Device Tiers](hardware/device-tiers) for detailed specifications per tier.

</details>

<details className="faq-item">
<summary>Is it free?</summary>

Talking to your trusted peers (friends, family, neighbors) is always free — no tokens, no fees. This is the [trust neighborhoods](/docs/L3-economics/trust-neighborhoods) model: if you trust someone, relaying their traffic costs you nothing.

When your traffic crosses through strangers' infrastructure — people you don't know, who have no reason to carry your traffic for free — that costs a small amount of [MHR tokens](/docs/L3-economics/mhr-token). You earn tokens by relaying traffic for others, so for most users the system balances out: you earn by participating and spend by using.

</details>

<details className="faq-item">
<summary>Do I need to buy tokens?</summary>

No. You earn MHR automatically by relaying traffic and providing services. A device that's turned on and connected earns tokens passively. If you don't want to deal with tokens at all, a [gateway operator](/docs/L3-economics/token-economics#gateway-operators-fiat-onramp) can handle it — you pay a small monthly fee (in regular money) and they take care of the crypto side.

</details>

---

## Finding Things

<details className="faq-item">
<summary>How do I find local news and events?</summary>

Content on Mehr is tagged with [geographic scopes](/docs/L3-economics/trust-neighborhoods#hierarchical-scopes) — like `geo:us/or/portland`. When you open the social feed, you see posts from your neighborhood first, then your city, then your region. It's like a local newspaper that writes itself.

A local event or city feed might look like: `events@geo:us/or/portland`. Anyone in the Portland trust network can post to it. Popular content — posts that lots of people in the scope read — propagates outward automatically.

</details>

<details className="faq-item">
<summary>How do I find my friends?</summary>

By exchanging public keys — either in person (QR code scan) or through a mutual trusted contact. Once you have someone's key, you can always find them on the mesh. They can also register a human-readable name like `alice@geo:us/or/portland` through [MHR-Name](/docs/L5-services/mhr-name), and you can look them up by name.

</details>

<details className="faq-item">
<summary>How do I browse without a search engine?</summary>

Three ways:

1. **Trust-based feeds**: You see content from people your community trusts. This is the default experience — open the app and see what your neighborhood is reading.
2. **Curated channels**: People you trust create curated feeds — hand-picked collections of the best content on a topic. Subscribe to feeds that match your interests.
3. **Name resolution**: If you know what you're looking for, type its name. [MHR-Name](/docs/L5-services/mhr-name) resolves human-readable names to content — like DNS, but without central authority.

</details>

---

## Creating Content

<details className="faq-item">
<summary>Does it cost money to post?</summary>

Yes — a tiny amount. Every post is stored on the network, and storage costs MHR. This is the anti-spam mechanism: posting costs tokens, so flooding the network with garbage is economically irrational.

Within your trust network (friends and neighbors), posting is free.

</details>

<details className="faq-item">
<summary>Can I earn from my content?</summary>

Yes. When someone pays to read your full post, a portion of their fee goes back to you — this is called **kickback**. You set the percentage when you publish (default is about 50%).

Popular content that earns more kickback than it costs to store becomes **self-funding** — it lives as long as people read it, at no cost to you. Content nobody reads expires when you stop paying for storage.

</details>

<details className="faq-item">
<summary>What kinds of content can I publish?</summary>

Anything: text posts, photo essays, music albums, video courses, scientific papers, games, software, podcasts. The same envelope/post system works for all content types. The preview shows whatever makes sense (track listing for music, abstract for papers, screenshots for games).

</details>

<details className="faq-item">
<summary>What about curators?</summary>

Anyone can be a curator. You create a curated feed — a list of the best posts you've found — and publish it. Others subscribe to your feed. When they read posts you recommended, the original authors earn kickback AND you earn a separate fee for the curation. Two people get paid: the creator and the curator.

</details>

---

## Communication

<details className="faq-item">
<summary>How do I message someone?</summary>

Open the messaging app, pick a contact, type your message. It's end-to-end encrypted — only you and the recipient can read it. If they're offline, the network holds the message and delivers it when they come back online (like email, but encrypted).

</details>

<details className="faq-item">
<summary>Can I make voice calls?</summary>

Yes, on connections with enough bandwidth. WiFi and cellular links support real-time voice. On slow radio links, voice isn't practical — use text messaging instead.

</details>

<details className="faq-item">
<summary>Can I send photos and videos?</summary>

Yes. The app adapts to your connection:

| Connection | What you can send/receive |
|-----------|--------------------------|
| WiFi or cellular | Photos, videos, full media |
| Moderate radio link | Compressed images, text |
| Slow radio (LoRa) | Text only, with tiny image previews |

You never need to think about this — the app handles it automatically.

</details>

<details className="faq-item">
<summary>What happens when I'm moving around?</summary>

Your device automatically handles roaming. It constantly listens for nearby nodes on all its radios (WiFi, Bluetooth, LoRa) and connects to the best one available — no manual switching required.

- **Walk into a cafe with a Mehr WiFi node?** Your device connects in under a second.
- **Walk out of WiFi range?** Traffic shifts to LoRa automatically. Apps adapt (images become text previews).
- **On a voice call while moving?** The call hands off between nodes with less than a second of interruption. Quality may change but the call doesn't drop.

</details>

---

## Community

<details className="faq-item">
<summary>How do communities form?</summary>

You mark people as trusted. They mark you as trusted. When a group of people all trust each other, that's a community — a [trust neighborhood](/docs/L3-economics/trust-neighborhoods). Nobody "creates" it or "runs" it — it emerges from real-world relationships.

Each person tags themselves with where they are (e.g., Portland, Oregon) and what they're into (e.g., gaming, science). These tags — called [scopes](/docs/L3-economics/trust-neighborhoods#hierarchical-scopes) — are how feeds and names work. No authority approves your tags. Communities converge on naming through social consensus, the same way they do today.

</details>

<details className="faq-item">
<summary>Can I run a local forum?</summary>

Yes. A forum is just a shared space where community members post. A moderator contract enforces whatever rules your community agrees on. Different forums can have different rules — there's no platform-wide content policy.

</details>

<details className="faq-item">
<summary>Can I sell things on a local marketplace?</summary>

Yes. Post a listing (text, photos, price) tagged with your geographic scope, and it's visible to your neighborhood. Buyers contact you directly. Payment can happen in person, through an external service, or through MHR escrow.

</details>

<details className="faq-item">
<summary>Can I host a website or blog?</summary>

Yes, and it's much simpler than traditional hosting:

| Traditional web | Mehr |
|----------------|-------|
| Rent a server | Not needed — content lives in the mesh |
| Buy a domain name ($10–50/year) | Pick a name for free (`myblog@geo:us/or/portland`) |
| Get an SSL certificate | Not needed — everything is encrypted and verified automatically |
| Pay for traffic spikes | Visitors pay their own relay costs, not you |

You pay only for storage (tiny amounts of MHR), and popular content gets cheaper because it's cached everywhere.

</details>

<details className="faq-item">
<summary>Can I store my files on the network?</summary>

Yes. Mehr provides [decentralized cloud storage](/docs/L6-applications/cloud-storage) — like Dropbox, but your files are encrypted on your device before being stored across multiple mesh nodes. No cloud provider has access to your files. Your devices sync automatically through the mesh. You can share files with specific people by granting them a decryption key.

If you don't want to deal with tokens, a [gateway operator](/docs/L3-economics/token-economics#gateway-operators-fiat-onramp) can offer cloud storage as a fiat-billed service — same experience as any cloud storage app, but backed by the mesh.

</details>

<details className="faq-item">
<summary>Can I earn by sharing my storage?</summary>

Yes — and it's one of the easiest ways to start earning MHR. Any device with spare disk space can offer [storage services](/docs/L6-applications/cloud-storage#earning-mhr-through-storage). You configure how much space to share, storage nodes advertise their availability, and clients form agreements with you. You earn μMHR for every epoch your storage is used. No special hardware needed — a Raspberry Pi with a USB drive works fine.

</details>

<details className="faq-item">
<summary>What happens when I move to a different location?</summary>

Your device [roams seamlessly](/docs/L6-applications/roaming). Mehr identity is your cryptographic key, not a network address. When you walk from WiFi to LoRa range to another WiFi node, your connections don't drop — traffic shifts to the best available transport in under a second. Apps adapt to link quality (images become previews on slow links, full quality returns on fast links). You can even plug an ethernet cable into different ports at different locations and stay connected with zero configuration.

</details>

---

## Privacy and Safety

<details className="faq-item">
<summary>Is it private?</summary>

Yes. Messages are end-to-end encrypted. Social posts can be public (scoped) or neighborhood-only (unscoped). There is no central server with a copy of your messages, your contacts, or your browsing history. Your identity is a cryptographic key — you never need to provide your real name.

</details>

<details className="faq-item">
<summary>Can someone spy on my messages?</summary>

No. End-to-end encryption means only the sender and recipient can read a message. Relay nodes carry encrypted blobs they cannot decrypt. Even your direct neighbors don't know if a packet originated from you or if you're just relaying it for someone else.

</details>

<details className="faq-item">
<summary>Can someone shut down the network?</summary>

No single point of failure. There's no server to seize, no company to shut down, no domain to block. As long as any two devices can reach each other — by radio, WiFi, Bluetooth, or anything else — the network works.

</details>

<details className="faq-item">
<summary>What about illegal or harmful content?</summary>

There is no central moderator. Instead, [content governance](/docs/L3-economics/content-governance) is distributed:

- **Every node decides for itself** what to store, relay, and display. No node is forced to host or forward content it objects to.
- **Trust revocation** is the enforcement mechanism. If your community discovers you're producing harmful content, they remove you from trusted peers — cutting off your free relay, storage, credit, and reputation.
- **Economics limits abuse**: posting costs money, content starts local (doesn't go global without genuine demand), and there's no algorithm to amplify engagement.
- **Curators filter quality**: most readers follow curated feeds, not raw unfiltered streams.

This is the same tradeoff every free society makes: individual freedom with social consequences. No central authority decides what's allowed, but communities enforce their own norms.

</details>

---

## Economy

<details className="faq-item">
<summary>How does money work on Mehr?</summary>

MHR is the network's internal token. Think of it like arcade tokens — valuable inside the arcade (network services), designed to be spent.

- **You earn MHR** by relaying traffic, storing data, or providing other services
- **You spend MHR** when your messages cross through untrusted infrastructure, or when you read paid content
- **Content creators earn MHR** through kickback — a share of what readers pay
- **Talking to friends is always free** — MHR only matters at trust boundaries

</details>

<details className="faq-item">
<summary>What's it worth in real money?</summary>

MHR has no official exchange rate with any fiat currency. But because it buys real services (bandwidth, storage, compute, content), it has real value — and people will likely trade it informally. This is fine. The network's health doesn't depend on preventing exchange; it works as a closed-loop economy regardless.

</details>

<details className="faq-item">
<summary>Can I buy MHR instead of earning it?</summary>

Yes. If someone sells you MHR they earned through relay work, you can spend it on the network. The seller earned those tokens through real service — the network benefited. You're indirectly funding infrastructure. This is no different from buying bus tokens.

</details>

<details className="faq-item">
<summary>What if I don't want to run a relay? Can I just pay to use the network?</summary>

Yes. **Gateway operators** handle this. A gateway is a regular node that accepts fiat payment (subscription, prepaid, or pay-as-you-go) and gives you network access in return. From your perspective, you sign up, pay a monthly bill, and use the network — just like a phone plan. You never see or touch MHR tokens.

The gateway adds you as a trusted peer and extends credit, so your traffic flows through them for free. The gateway handles MHR costs on your behalf. Multiple gateways compete in any area, so pricing stays competitive. You can switch gateways at any time — your identity is yours, not the gateway's.

See [Gateway Operators](/docs/L3-economics/token-economics#gateway-operators-fiat-onramp) for details.

</details>

<details className="faq-item">
<summary>Can I get rich from MHR?</summary>

That's not the point. MHR is designed to be spent on services, not hoarded. There's no ICO and no hidden allocation — the genesis gateway receives a transparent, disclosed allocation visible in the ledger from day one. Tail emission (0.1% annual) mildly dilutes idle holdings. Lost keys permanently remove supply. The economic incentive is to earn and spend, not to accumulate.

</details>

---

## Licensing and Digital Assets

<details className="faq-item">
<summary>Can I sell licenses for my work on Mehr?</summary>

Yes. Mehr has a built-in [digital licensing](/docs/L6-applications/licensing) system. You publish a **LicenseOffer** alongside your asset (photo, music, software, dataset) specifying terms — price, whether derivatives are allowed, whether commercial use is permitted, and how many licenses can be issued. Buyers pay you directly (in MHR or fiat) and receive a **LicenseGrant** signed by both parties.

</details>

<details className="faq-item">
<summary>How does license verification work?</summary>

A LicenseGrant is cryptographically signed by both the licensor and licensee. Anyone can verify it by checking the Ed25519 signatures — no network connection needed. When someone uses a licensed asset in a derivative work, they include the LicenseGrant hash in their post's references. Readers can follow the chain: derivative work → LicenseGrant → LicenseOffer → original asset.

</details>

<details className="faq-item">
<summary>Can licenses be enforced?</summary>

Not at the protocol level. Mehr proves a license exists (or doesn't) — it doesn't prevent unlicensed use. This is the same as the real world: copyright exists whether or not someone violates it. Enforcement happens through social reputation (community trust) and legal systems (courts). The cryptographic proof makes disputes straightforward to resolve.

</details>

<details className="faq-item">
<summary>Do licenses work outside of Mehr?</summary>

Yes. A LicenseGrant contains public keys and signatures that can be verified with standard cryptographic tools — no Mehr software needed. A website, archive, or court can verify license authenticity from the grant alone. The rights described in the license apply wherever the parties intend them to, not just on the Mehr network.

</details>

---

## Compared to What I Use Now

<details className="faq-item">
<summary>How is this different from the regular internet?</summary>

| | Regular Internet | Mehr |
|--|----------------|-------|
| **Works without ISP** | No | Yes — radio, WiFi, anything |
| **Works during internet shutdown** | No | Yes — local mesh continues |
| **Free local communication** | No — you pay your ISP | Yes — trusted peers are free |
| **Your data on a corporate server** | Yes (Google, Meta, etc.) | No — data stays on your devices and your community's mesh |
| **Can be censored** | Yes — ISPs, DNS, app stores | Extremely difficult — no central control point |
| **Needs an account** | Email, phone number, ID | Just a cryptographic key (anonymous) |
| **Content creators earn** | Platform takes most/all revenue | Direct kickback to creator (~50%) |

</details>

<details className="faq-item">
<summary>Can Mehr replace my internet connection?</summary>

**It depends on where you live.**

In a **dense area** (apartment building, neighborhood, campus) where many nodes run WiFi, the mesh delivers 10–300 Mbps per hop — comparable to cable internet. Add a few shared internet uplinks (Starlink, fiber, cellular) and the community mesh handles distribution. Most people would save 50–75% on connectivity costs.

In a **rural or remote area** with only LoRa radio coverage, Mehr delivers 0.3–50 kbps — enough for text messaging, basic social feeds, and push-to-talk voice, but not video streaming. Here, Mehr provides communication where there was none, or shares one expensive satellite connection across an entire village.

| Your situation | What Mehr does |
|---------------|-----------------|
| Dense urban, many WiFi nodes | Replaces individual ISP subscriptions — share uplinks, save money |
| Suburban, mixed WiFi + LoRa | Supplements your connection — free local communication, shared backup uplink |
| Rural, LoRa only | Provides communication where there is none — text, voice, local services |
| No infrastructure at all | Only option that works — $30 solar radio nodes, no towers needed |

</details>

<details className="faq-item">
<summary>How is this different from Signal or WhatsApp?</summary>

Signal and WhatsApp need internet access and rely on central servers for delivery. Mehr works without internet, stores messages across the mesh (not one company's servers), and the network itself is decentralized. Nobody can block your access because there's nothing to block.

</details>

<details className="faq-item">
<summary>How is this different from Bitcoin?</summary>

Bitcoin is money designed for global financial transactions. MHR is an internal utility token for paying network services. They share some concepts (cryptographic keys, no central authority) but serve completely different purposes. MHR is more like "bus tokens for the network" than a cryptocurrency.

</details>

<details className="faq-item">
<summary>How is this different from Mastodon/Bluesky?</summary>

Mastodon and Bluesky are decentralized social networks that still require internet access and depend on servers run by someone. On Mehr:

| | Mastodon/Bluesky | Mehr |
|---|---|---|
| **Requires internet** | Yes | No — works on radio alone |
| **Requires servers** | Yes (someone hosts instances) | No — content lives on mesh nodes |
| **Content moderation** | Server admin decides | Each node decides for itself |
| **Posting cost** | Free | Small fee (anti-spam) |
| **Creator revenue** | None built-in | Kickback on every read |
| **Works offline** | No | Yes — local mesh continues |

</details>
