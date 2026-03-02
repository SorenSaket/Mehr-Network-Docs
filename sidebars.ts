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
      label: 'Layer 0: Physical Transport',
      collapsed: false,
      className: 'sidebar-layer-0',
      items: [
        'L0-physical/physical-transport',
      ],
    },
    {
      type: 'category',
      label: 'Layer 1: Network Protocol',
      collapsed: false,
      className: 'sidebar-layer-1',
      items: [
        'L1-network/network-protocol',
        'L1-network/versioning',
      ],
    },
    {
      type: 'category',
      label: 'Layer 2: Security',
      collapsed: false,
      className: 'sidebar-layer-2',
      items: [
        'L2-security/security',
      ],
    },
    {
      type: 'category',
      label: 'Layer 3: Economics',
      collapsed: false,
      className: 'sidebar-layer-3',
      items: [
        {
          type: 'category',
          label: 'MHR Token',
          collapsed: true,
          items: [
            'L3-economics/mhr-token',
            'L3-economics/token-economics',
            'L3-economics/token-security',
          ],
        },
        'L3-economics/payment-channels',
        {
          type: 'category',
          label: 'Ledger & Settlement',
          collapsed: true,
          items: [
            'L3-economics/crdt-ledger',
            'L3-economics/epoch-compaction',
          ],
        },
        'L3-economics/trust-neighborhoods',
        'L3-economics/propagation',
        'L3-economics/content-governance',
        'L3-economics/real-world-impact',
      ],
    },
    {
      type: 'category',
      label: 'Layer 4: Capability Marketplace',
      collapsed: false,
      className: 'sidebar-layer-4',
      items: [
        'L4-marketplace/overview',
        'L4-marketplace/discovery',
        'L4-marketplace/agreements',
        'L4-marketplace/verification',
      ],
    },
    {
      type: 'category',
      label: 'Layer 5: Service Primitives',
      collapsed: false,
      className: 'sidebar-layer-5',
      items: [
        'L5-services/mhr-store',
        'L5-services/mhr-dht',
        'L5-services/mhr-pub',
        'L5-services/mhr-compute',
        'L5-services/mhr-name',
        {
          type: 'category',
          label: 'MHR-ID: Identity',
          collapsed: true,
          items: [
            'L5-services/mhr-id',
            'L5-services/mhr-id-verification',
            'L5-services/mhr-id-mobility',
            'L5-services/mhr-id-faq',
          ],
        },
        {
          type: 'category',
          label: 'MHR-App: Applications',
          collapsed: true,
          items: [
            'L5-services/mhr-app',
            'L5-services/mhr-app-upgrades',
            'L5-services/mhr-app-security',
            'L5-services/mhr-app-faq',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Layer 6: Applications',
      collapsed: true,
      className: 'sidebar-layer-6',
      items: [
        'L6-applications/messaging',
        'L6-applications/social',
        'L6-applications/voice',
        'L6-applications/community-apps',
        'L6-applications/voting',
        'L6-applications/licensing',
        'L6-applications/cloud-storage',
        'L6-applications/roaming',
        'L6-applications/hosting',
        'L6-applications/business',
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
        'development/variable-packet-size',
        'development/bulk-transfer-negotiation',
        'development/partition-defense-comparison',
        'development/open-questions',
      ],
    },
    'specification',
  ],
};

export default sidebars;
