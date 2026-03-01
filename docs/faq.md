---
sidebar_position: 2
title: FAQ
description: Frequently asked questions about the Mehr Network — covering protocol design, tokenomics, hardware requirements, and comparison with other mesh projects.
keywords: [FAQ, mesh network, questions, Mehr Network]
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

If someone wants to use the network without running a relay, they can acquire MHR from someone who has earned it. The network doesn't care how you got your tokens — only that you have them.

---

## Finding Things

### How do I find what's happening in my city?

Subscribe to your city's geographic feed. Content on Mehr is tagged with [hierarchical scopes](economics/trust-neighborhoods#hierarchical-scopes) — geographic (where it's relevant) and interest (what it's about). Your app uses these to show you relevant content:

1. **Neighborhood feed**: Everything posted by people near you. Cheapest and fastest — content is close.

2. **City feed**: Everything from your city. Subscribe to Portland and you see all Portland neighborhoods. Costs a bit more (further away) but still local.

3. **Region/country feed**: Broader scope, higher cost, more content. Use digest or headline-only mode to keep bandwidth low.

4. **Interest feeds**: Subscribe to topics — gaming, science, music, local events. These connect you with people who share your interests, regardless of where they live.

5. **Curated feeds**: Follow a curator — a real person who picks the best content. Like subscribing to a newsletter.

### How do I find my friends?

By their name. Everyone picks a name scoped to their location — like `alice@geo:us/oregon/portland` or `ravi@geo:india/mumbai`. Type it in and you're connected. You can also use private nicknames ("Mom", "Work") that only exist on your device.

If you're physically near someone, your devices discover each other automatically over radio or WiFi — no names needed.

### Is there a "feed" like Instagram or Twitter?

Yes, but you control it. There are five types of feeds:

- **Follow feed**: You follow people. Their posts appear in chronological order.
- **Geographic feed**: Everything from your neighborhood, city, or region.
- **Interest feed**: Everything tagged with a topic you care about (gaming, science, cooking).
- **Intersection feed**: Combine geographic + interest ("Portland Pokemon" = posts tagged with both).
- **Curated feed**: A human you trust picks the best content and publishes a list. Like a magazine editor.

There is no algorithm deciding what you see. No ads. No engagement optimization. Your feed is what you chose to follow.

### How does browsing work?

Every post has two layers:

1. **Free preview**: A headline, short summary, and blurry thumbnail. You see these for free — browse as much as you want.
2. **Full content**: The actual article, image, video, or file. You pay a tiny fee to open it, and a share goes to the author.

This means you never pay for content you don't want. You browse previews like window shopping and only pay when you open something.

### Can I browse websites?

Yes. People host websites on Mehr without needing a server or domain name. You visit them by name (`mysite@geo:us/oregon/portland`) or by direct link. Popular sites load fast because copies are cached throughout the network automatically.

---

## Creating Content

### How do I post something?

Write your post, add a headline and summary, optionally attach images or files, and publish. Your app creates a free preview (the envelope) and the paid content (the post) automatically.

You choose who sees it:
- **Geographic scope**: Tag your city, region, or neighborhood. Appears in geographic feeds.
- **Interest scope**: Tag a topic. Appears in interest feeds for that topic.
- **Both**: Tag a city AND a topic. Appears in both feeds.
- **No scope**: Only your trusted peers see it. The most private option.

### Does it cost money to post?

Yes — a tiny amount. Every post is stored on the network, and storage costs MHR. This is the anti-spam mechanism: posting costs tokens, so flooding the network with garbage is economically irrational.

Within your trust network (friends and neighbors), posting is free.

### Can I earn from my content?

Yes. When someone pays to read your full post, a portion of their fee goes back to you — this is called **kickback**. You set the percentage when you publish (default is about 50%).

Popular content that earns more kickback than it costs to store becomes **self-funding** — it lives as long as people read it, at no cost to you. Content nobody reads expires when you stop paying for storage.

### What kinds of content can I publish?

Anything: text posts, photo essays, music albums, video courses, scientific papers, games, software, podcasts. The same envelope/post system works for all content types. The preview shows whatever makes sense (track listing for music, abstract for papers, screenshots for games).

### What about curators?

Anyone can be a curator. You create a curated feed — a list of the best posts you've found — and publish it. Others subscribe to your feed. When they read posts you recommended, the original authors earn kickback AND you earn a separate fee for the curation. Two people get paid: the creator and the curator.

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
- **On a voice call while moving?** The call hands off between nodes with less than a second of interruption. Quality may change but the call doesn't drop.

---

## Community

### How do communities form?

You mark people as trusted. They mark you as trusted. When a group of people all trust each other, that's a community — a [trust neighborhood](economics/trust-neighborhoods). Nobody "creates" it or "runs" it — it emerges from real-world relationships.

Each person tags themselves with where they are (e.g., Portland, Oregon) and what they're into (e.g., gaming, science). These tags — called [scopes](economics/trust-neighborhoods#hierarchical-scopes) — are how feeds and names work. No authority approves your tags. Communities converge on naming through social consensus, the same way they do today.

### Can I run a local forum?

Yes. A forum is just a shared space where community members post. A moderator contract enforces whatever rules your community agrees on. Different forums can have different rules — there's no platform-wide content policy.

### Can I sell things on a local marketplace?

Yes. Post a listing (text, photos, price) tagged with your geographic scope, and it's visible to your neighborhood. Buyers contact you directly. Payment can happen in person, through an external service, or through MHR escrow.

### Can I host a website or blog?

Yes, and it's much simpler than traditional hosting:

| Traditional web | Mehr |
|----------------|-------|
| Rent a server | Not needed — content lives in the mesh |
| Buy a domain name ($10–50/year) | Pick a name for free (`myblog@geo:us/or/portland`) |
| Get an SSL certificate | Not needed — everything is encrypted and verified automatically |
| Pay for traffic spikes | Visitors pay their own relay costs, not you |

You pay only for storage (tiny amounts of MHR), and popular content gets cheaper because it's cached everywhere.

### Can I store my files on the network?

Yes. Mehr provides [decentralized cloud storage](applications/cloud-storage) — like Dropbox, but your files are encrypted on your device before being stored across multiple mesh nodes. No cloud provider has access to your files. Your devices sync automatically through the mesh. You can share files with specific people by granting them a decryption key.

If you don't want to deal with tokens, a [gateway operator](economics/token-economics#gateway-operators-fiat-onramp) can offer cloud storage as a fiat-billed service — same experience as any cloud storage app, but backed by the mesh.

### Can I earn by sharing my storage?

Yes — and it's one of the easiest ways to start earning MHR. Any device with spare disk space can offer [storage services](applications/cloud-storage#earning-mhr-through-storage). You configure how much space to share, storage nodes advertise their availability, and clients form agreements with you. You earn μMHR for every epoch your storage is used. No special hardware needed — a Raspberry Pi with a USB drive works fine.

### What happens when I move around?

Your device [roams seamlessly](applications/roaming). Mehr identity is your cryptographic key, not a network address. When you walk from WiFi to LoRa range to another WiFi node, your connections don't drop — traffic shifts to the best available transport in under a second. Apps adapt to link quality (images become previews on slow links, full quality returns on fast links). You can even plug an ethernet cable into different ports at different locations and stay connected with zero configuration.

---

## Privacy and Safety

### Is it private?

Yes. Messages are end-to-end encrypted. Social posts can be public (scoped) or neighborhood-only (unscoped). There is no central server with a copy of your messages, your contacts, or your browsing history. Your identity is a cryptographic key — you never need to provide your real name.

### Can someone spy on my messages?

No. End-to-end encryption means only the sender and recipient can read a message. Relay nodes carry encrypted blobs they cannot decrypt. Even your direct neighbors don't know if a packet originated from you or if you're just relaying it for someone else.

### Can someone shut down the network?

No single point of failure. There's no server to seize, no company to shut down, no domain to block. As long as any two devices can reach each other — by radio, WiFi, Bluetooth, or anything else — the network works.

### What about illegal or harmful content?

There is no central moderator. Instead, [content governance](economics/content-governance) is distributed:

- **Every node decides for itself** what to store, relay, and display. No node is forced to host or forward content it objects to.
- **Trust revocation** is the enforcement mechanism. If your community discovers you're producing harmful content, they remove you from trusted peers — cutting off your free relay, storage, credit, and reputation.
- **Economics limits abuse**: posting costs money, content starts local (doesn't go global without genuine demand), and there's no algorithm to amplify engagement.
- **Curators filter quality**: most readers follow curated feeds, not raw unfiltered streams.

This is the same tradeoff every free society makes: individual freedom with social consequences. No central authority decides what's allowed, but communities enforce their own norms.

---

## Economy

### How does money work on Mehr?

MHR is the network's internal token. Think of it like arcade tokens — valuable inside the arcade (network services), designed to be spent.

- **You earn MHR** by relaying traffic, storing data, or providing other services
- **You spend MHR** when your messages cross through untrusted infrastructure, or when you read paid content
- **Content creators earn MHR** through kickback — a share of what readers pay
- **Talking to friends is always free** — MHR only matters at trust boundaries

### What's it worth in real money?

MHR has no official exchange rate with any fiat currency. But because it buys real services (bandwidth, storage, compute, content), it has real value — and people will likely trade it informally. This is fine. The network's health doesn't depend on preventing exchange; it works as a closed-loop economy regardless.

### Can I buy MHR instead of earning it?

Yes. If someone sells you MHR they earned through relay work, you can spend it on the network. The seller earned those tokens through real service — the network benefited. You're indirectly funding infrastructure. This is no different from buying bus tokens.

### What if I don't want to run a relay? Can I just pay to use the network?

Yes. **Gateway operators** handle this. A gateway is a regular node that accepts fiat payment (subscription, prepaid, or pay-as-you-go) and gives you network access in return. From your perspective, you sign up, pay a monthly bill, and use the network — just like a phone plan. You never see or touch MHR tokens.

The gateway adds you as a trusted peer and extends credit, so your traffic flows through them for free. The gateway handles MHR costs on your behalf. Multiple gateways compete in any area, so pricing stays competitive. You can switch gateways at any time — your identity is yours, not the gateway's.

See [Gateway Operators](economics/token-economics#gateway-operators-fiat-onramp) for details.

### Can I get rich from MHR?

That's not the point. MHR is designed to be spent on services, not hoarded. There's no ICO and no hidden allocation — the genesis gateway receives a transparent, disclosed allocation visible in the ledger from day one. Tail emission (0.1% annual) mildly dilutes idle holdings. Lost keys permanently remove supply. The economic incentive is to earn and spend, not to accumulate.

---

## Licensing and Digital Assets

### Can I sell licenses for my work on Mehr?

Yes. Mehr has a built-in [digital licensing](applications/licensing) system. You publish a **LicenseOffer** alongside your asset (photo, music, software, dataset) specifying terms — price, whether derivatives are allowed, whether commercial use is permitted, and how many licenses can be issued. Buyers pay you directly (in MHR or fiat) and receive a **LicenseGrant** signed by both parties.

### How does license verification work?

A LicenseGrant is cryptographically signed by both the licensor and licensee. Anyone can verify it by checking the Ed25519 signatures — no network connection needed. When someone uses a licensed asset in a derivative work, they include the LicenseGrant hash in their post's references. Readers can follow the chain: derivative work → LicenseGrant → LicenseOffer → original asset.

### Can licenses be enforced?

Not at the protocol level. Mehr proves a license exists (or doesn't) — it doesn't prevent unlicensed use. This is the same as the real world: copyright exists whether or not someone violates it. Enforcement happens through social reputation (community trust) and legal systems (courts). The cryptographic proof makes disputes straightforward to resolve.

### Do licenses work outside of Mehr?

Yes. A LicenseGrant contains public keys and signatures that can be verified with standard cryptographic tools — no Mehr software needed. A website, archive, or court can verify license authenticity from the grant alone. The rights described in the license apply wherever the parties intend them to, not just on the Mehr network.

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
| **Content creators earn** | Platform takes most/all revenue | Direct kickback to creator (~50%) |

### Can Mehr replace my internet connection?

**It depends on where you live.**

In a **dense area** (apartment building, neighborhood, campus) where many nodes run WiFi, the mesh delivers 10–300 Mbps per hop — comparable to cable internet. Add a few shared internet uplinks (Starlink, fiber, cellular) and the community mesh handles distribution. Most people would save 50–75% on connectivity costs.

In a **rural or remote area** with only LoRa radio coverage, Mehr delivers 0.3–50 kbps — enough for text messaging, basic social feeds, and push-to-talk voice, but not video streaming. Here, Mehr provides communication where there was none, or shares one expensive satellite connection across an entire village.

| Your situation | What Mehr does |
|---------------|-----------------|
| Dense urban, many WiFi nodes | Replaces individual ISP subscriptions — share uplinks, save money |
| Suburban, mixed WiFi + LoRa | Supplements your connection — free local communication, shared backup uplink |
| Rural, LoRa only | Provides communication where there is none — text, voice, local services |
| No infrastructure at all | Only option that works — $30 solar radio nodes, no towers needed |

### How is this different from Signal or WhatsApp?

Signal and WhatsApp need internet access and rely on central servers for delivery. Mehr works without internet, stores messages across the mesh (not one company's servers), and the network itself is decentralized. Nobody can block your access because there's nothing to block.

### How is this different from Bitcoin?

Bitcoin is money designed for global financial transactions. MHR is an internal utility token for paying network services. They share some concepts (cryptographic keys, no central authority) but serve completely different purposes. MHR is more like "bus tokens for the network" than a cryptocurrency.

### How is this different from Mastodon/Bluesky?

Mastodon and Bluesky are decentralized social networks that still require internet access and depend on servers run by someone. On Mehr:

| | Mastodon/Bluesky | Mehr |
|---|---|---|
| **Requires internet** | Yes | No — works on radio alone |
| **Requires servers** | Yes (someone hosts instances) | No — content lives on mesh nodes |
| **Content moderation** | Server admin decides | Each node decides for itself |
| **Posting cost** | Free | Small fee (anti-spam) |
| **Creator revenue** | None built-in | Kickback on every read |
| **Works offline** | No | Yes — local mesh continues |
