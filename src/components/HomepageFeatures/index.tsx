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
    title: 'Proof of Service',
    description: (
      <>
        Tokens are minted only when real services are delivered through funded
        payment channels. Relay, storage, and compute all earn proportionally.
        A 2% burn on every payment keeps supply honest.
      </>
    ),
  },
  {
    title: 'Free Local, Paid Routed',
    description: (
      <>
        Trusted neighbors relay for free — no tokens, no channels, no overhead.
        The economic layer only activates when traffic crosses trust boundaries,
        just like the real world.
      </>
    ),
  },
  {
    title: 'Zero Trust Economics',
    description: (
      <>
        Non-deterministic service assignment and net-income revenue caps make
        self-dealing structurally unprofitable. No staking, no slashing, no
        trust scores required.
      </>
    ),
  },
  {
    title: 'Transport Agnostic',
    description: (
      <>
        Any medium that can move bytes is a valid link — from 500 bps LoRa
        radio to 10 Gbps fiber. A single node can bridge multiple transports
        simultaneously.
      </>
    ),
  },
  {
    title: 'Partition Tolerant',
    description: (
      <>
        Network fragmentation is expected, not an error. Each partition operates
        independently with its own economy. On reconnection, the CRDT ledger
        converges automatically.
      </>
    ),
  },
  {
    title: 'Any Hardware',
    description: (
      <>
        A solar-powered ESP32 relays packets. A Raspberry Pi stores data for
        the mesh. A GPU workstation runs compute jobs. Every device participates
        at whatever level its hardware allows.
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
