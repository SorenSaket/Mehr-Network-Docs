import React from 'react';
import styles from './styles.module.css';

interface LayerData {
  number: number;
  name: string;
  items: string[];
  link: string;
}

const layers: LayerData[] = [
  {
    number: 6,
    name: 'Applications',
    items: ['Messaging', 'Social', 'Voice', 'Voting', 'Licensing', 'Hosting'],
    link: 'L6-applications/messaging',
  },
  {
    number: 5,
    name: 'Service Primitives',
    items: ['MHR-Store', 'MHR-DHT', 'MHR-Pub', 'MHR-Compute', 'MHR-Name', 'MHR-ID'],
    link: 'L5-services/mhr-store',
  },
  {
    number: 4,
    name: 'Capability Marketplace',
    items: ['Discovery', 'Agreements', 'Verification'],
    link: 'L4-marketplace/overview',
  },
  {
    number: 3,
    name: 'Economic Protocol',
    items: ['MHR Token', 'Payment Channels', 'CRDT Ledger', 'Trust'],
    link: 'L3-economics/mhr-token',
  },
  {
    number: 2,
    name: 'Security',
    items: ['Encryption', 'Authentication', 'Privacy'],
    link: 'L2-security/security',
  },
  {
    number: 1,
    name: 'Network Protocol',
    items: ['Identity', 'Addressing', 'Routing', 'Gossip'],
    link: 'L1-network/network-protocol',
  },
  {
    number: 0,
    name: 'Physical Transport',
    items: ['LoRa', 'WiFi', 'BLE', 'Cellular', 'TCP/IP', 'Serial'],
    link: 'L0-physical/physical-transport',
  },
];

export default function StackDiagram(): React.JSX.Element {
  return (
    <div className={styles.wrapper}>
      <div className={styles.stack}>
        {layers.map((layer) => (
          <a
            key={layer.number}
            href={`/docs/${layer.link}`}
            className={`${styles.layer} ${styles[`layer${layer.number}`]}`}
          >
            <div className={styles.layerNumber}>L{layer.number}</div>
            <div className={styles.layerContent}>
              <div className={styles.layerName}>{layer.name}</div>
              <div className={styles.layerItems}>
                {layer.items.map((item) => (
                  <span key={item} className={styles.chip}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </a>
        ))}
      </div>
      <div className={styles.legend}>
        {layers.map((layer) => (
          <div key={layer.number} className={styles.legendItem}>
            <span className={`${styles.legendDot} ${styles[`layer${layer.number}`]}`} />
            <span className={styles.legendText}>
              L{layer.number}: {layer.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
