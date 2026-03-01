import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'introduction',
        'eli5',
        'faq',
      ],
    },
    {
      type: 'category',
      label: 'Protocol Stack',
      collapsed: false,
      items: [
        'protocol/physical-transport',
        'protocol/network-protocol',
        'protocol/security',
        'protocol/versioning',
      ],
    },
    {
      type: 'category',
      label: 'Economics',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'MHR Token',
          collapsed: true,
          items: [
            'economics/mhr-token',
            'economics/token-economics',
            'economics/token-security',
          ],
        },
        'economics/payment-channels',
        {
          type: 'category',
          label: 'Ledger & Settlement',
          collapsed: true,
          items: [
            'economics/crdt-ledger',
            'economics/epoch-compaction',
          ],
        },
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
        'services/mhr-name',
        {
          type: 'category',
          label: 'MHR-ID: Identity',
          collapsed: true,
          items: [
            'services/mhr-id/index',
            'services/mhr-id/verification',
            'services/mhr-id/mobility',
            'services/mhr-id/faq',
          ],
        },
        {
          type: 'category',
          label: 'MHR-App: Applications',
          collapsed: true,
          items: [
            'services/mhr-app/index',
            'services/mhr-app/upgrades',
            'services/mhr-app/security',
            'services/mhr-app/faq',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Applications',
      collapsed: true,
      items: [
        'applications/messaging',
        'applications/social',
        'applications/voice',
        'applications/community-apps',
        'applications/voting',
        'applications/licensing',
        'applications/cloud-storage',
        'applications/roaming',
        'applications/hosting',
        'applications/business',
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
        'interoperability/bittorrent',
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
        'development/partition-defense-comparison',
        'development/open-questions',
      ],
    },
    'specification',
  ],
};

export default sidebars;
