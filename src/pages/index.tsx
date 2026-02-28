import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/introduction">
            Read the Documentation
          </Link>
        </div>
      </div>
    </header>
  );
}

function HomepageDescription() {
  return (
    <section className={styles.description}>
      <div className="container">
        <div className={styles.descriptionContent}>
          <p>
            Proof of work wastes electricity. Proof of stake rewards capital, not contribution.
            Mehr uses <strong>proof of service</strong> — every token in circulation was minted
            because someone relayed packets, stored data, or ran computations for a real paying client.
            No work is wasted. No token is unearned.
          </p>
          <p>
            The network runs on a simple principle: <strong>free between friends, paid between
            strangers</strong>. Communities communicate at zero cost over trusted local mesh.
            When traffic crosses trust boundaries, service providers earn through bilateral
            payment channels — and the protocol guarantees that cheating is structurally
            unprofitable, with zero trust assumptions.
          </p>
          <p>
            Identity is self-sovereign — your cryptographic key is your identity, with
            profile fields you control and per-field visibility (public, friends-only, or
            specific people). Names resolve from your position in the trust graph, not from
            a global registry. Applications are content-addressed packages stored in the
            mesh — no app store, no server, no single point of removal.
          </p>
          <p>
            Mehr works on any transport — LoRa radio, WiFi, fiber, cellular — and is designed
            for partition tolerance from the ground up. A village mesh that loses internet
            connectivity continues operating independently. When it reconnects, the CRDT-based
            ledger converges automatically. No consensus protocol. No downtime. No data loss.
          </p>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Decentralized Mesh Infrastructure"
      description="Decentralized mesh infrastructure powered by proof of service — every token is minted when real services are delivered">
      <HomepageHeader />
      <main>
        <HomepageDescription />
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
