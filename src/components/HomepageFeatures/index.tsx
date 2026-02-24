import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Transport Agnostic',
    description: (
      <>
        Works on any medium that can move bytes — from 500 bps LoRa radio to
        10 Gbps fiber. A single node can bridge between multiple transports
        simultaneously.
      </>
    ),
  },
  {
    title: 'Partition Tolerant',
    description: (
      <>
        Network fragmentation is expected operation, not an error. A village on
        LoRa is a partition. A country with internet cut is a partition. Every
        layer converges correctly when partitions heal.
      </>
    ),
  },
  {
    title: 'Capability Marketplace',
    description: (
      <>
        Every resource — bandwidth, compute, storage, connectivity — is
        discoverable, negotiable, verifiable, and payable. Hardware determines
        capability; the market determines role.
      </>
    ),
  },
  {
    title: 'Free Local, Paid Routed',
    description: (
      <>
        Direct neighbors communicate for free. You pay only when your packets
        traverse other people's infrastructure. Micropayments flow through
        bilateral payment channels.
      </>
    ),
  },
  {
    title: 'No Trusted Infrastructure',
    description: (
      <>
        No certificate authorities, no DNS, no central servers. Identity is a
        cryptographic keypair. Security is structural — Ed25519 signing,
        X25519 key exchange, ChaCha20-Poly1305 encryption.
      </>
    ),
  },
  {
    title: '$30 to $500+',
    description: (
      <>
        From a solar-powered ESP32 relay to a GPU inference node, every device
        participates at whatever level its hardware allows. Nothing is required
        except a keypair.
      </>
    ),
  },
];

function Feature({title, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md" style={{paddingTop: '2rem'}}>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
