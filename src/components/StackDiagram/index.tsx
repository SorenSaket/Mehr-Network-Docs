import React from 'react';
import styles from './styles.module.css';

interface LayerData {
  number: number;
  name: string;
  items: string[];
  link: string;
  group: 'protocol' | 'economics' | 'marketplace' | 'services' | 'applications';
}

const layers: LayerData[] = [
  {
    number: 6,
    name: 'Applications',
    items: ['Messaging', 'Social', 'Voice', 'Naming', 'Forums', 'Hosting'],
    link: 'applications/messaging',
    group: 'applications',
  },
  {
    number: 5,
    name: 'Service Primitives',
    items: ['NXS-Store', 'NXS-DHT', 'NXS-Pub', 'NXS-Compute'],
    link: 'services/nxs-store',
    group: 'services',
  },
  {
    number: 4,
    name: 'Capability Marketplace',
    items: ['Discovery', 'Agreements', 'Verification'],
    link: 'marketplace/overview',
    group: 'marketplace',
  },
  {
    number: 3,
    name: 'Economic Protocol',
    items: ['NXS Token', 'Payment Channels', 'CRDT Ledger', 'Trust'],
    link: 'economics/nxs-token',
    group: 'economics',
  },
  {
    number: 2,
    name: 'Security',
    items: ['Encryption', 'Authentication', 'Privacy'],
    link: 'protocol/security',
    group: 'protocol',
  },
  {
    number: 1,
    name: 'Network Protocol',
    items: ['Identity', 'Addressing', 'Routing', 'Gossip'],
    link: 'protocol/network-protocol',
    group: 'protocol',
  },
  {
    number: 0,
    name: 'Physical Transport',
    items: ['LoRa', 'WiFi', 'BLE', 'Cellular', 'TCP/IP', 'Serial'],
    link: 'protocol/physical-transport',
    group: 'protocol',
  },
];

const groupLabels: Record<string, string> = {
  applications: 'Apps',
  services: 'Services',
  marketplace: 'Market',
  economics: 'Economics',
  protocol: 'Protocol',
};

export default function StackDiagram(): React.JSX.Element {
  return (
    <div className={styles.wrapper}>
      <div className={styles.stack}>
        {layers.map((layer, i) => {
          const prevGroup = i > 0 ? layers[i - 1].group : null;
          const showGroupLabel = layer.group !== prevGroup;

          return (
            <React.Fragment key={layer.number}>
              {showGroupLabel && (
                <div className={`${styles.groupLabel} ${styles[layer.group]}`}>
                  {groupLabels[layer.group]}
                </div>
              )}
              <a
                href={`/docs/${layer.link}`}
                className={`${styles.layer} ${styles[layer.group]}`}
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
            </React.Fragment>
          );
        })}
      </div>
      <div className={styles.legend}>
        {['protocol', 'economics', 'marketplace', 'services', 'applications'].map(
          (group) => (
            <div key={group} className={styles.legendItem}>
              <span className={`${styles.legendDot} ${styles[group]}`} />
              <span className={styles.legendText}>
                {groupLabels[group]}
              </span>
            </div>
          ),
        )}
      </div>
    </div>
  );
}
