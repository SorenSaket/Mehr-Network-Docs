import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'introduction',
    'eli5',
    'faq',
    {
      type: 'category',
      label: 'Protocol Stack',
      collapsed: false,
      items: [
        'protocol/physical-transport',
        'protocol/network-protocol',
        'protocol/security',
      ],
    },
    {
      type: 'category',
      label: 'Economics',
      collapsed: false,
      items: [
        'economics/mhr-token',
        'economics/payment-channels',
        'economics/crdt-ledger',
        'economics/trust-neighborhoods',
        'economics/propagation',
        'economics/content-governance',
        'economics/real-world-impact',
      ],
    },
    {
      type: 'category',
      label: 'Capability Marketplace',
      collapsed: false,
      items: [
        'marketplace/overview',
        'marketplace/discovery',
        'marketplace/agreements',
        'marketplace/verification',
      ],
    },
    {
      type: 'category',
      label: 'Service Primitives',
      collapsed: false,
      items: [
        'services/mhr-store',
        'services/mhr-dht',
        'services/mhr-pub',
        'services/mhr-compute',
      ],
    },
    {
      type: 'category',
      label: 'Applications',
      collapsed: true,
      items: [
        'applications/messaging',
        'applications/social',
        'applications/identity',
        'applications/voice',
        'applications/naming',
        'applications/community-apps',
        'applications/voting',
        'applications/licensing',
        'applications/cloud-storage',
        'applications/roaming',
        'applications/hosting',
      ],
    },
    {
      type: 'category',
      label: 'Interoperability',
      collapsed: true,
      items: [
        'interoperability/overview',
        'interoperability/meshtastic',
        'interoperability/reticulum-ecosystem',
        'interoperability/scuttlebutt',
        'interoperability/matrix',
      ],
    },
    {
      type: 'category',
      label: 'Hardware',
      collapsed: true,
      items: [
        'hardware/reference-designs',
        'hardware/device-tiers',
      ],
    },
    {
      type: 'category',
      label: 'Development',
      collapsed: true,
      items: [
        'development/roadmap',
        'development/landscape',
        'development/design-decisions',
        'development/versioning',
        'development/open-questions',
      ],
    },
    'specification',
  ],
};

export default sidebars;
