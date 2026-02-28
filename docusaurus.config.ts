import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Mehr Network',
  tagline: 'Decentralized Mesh Infrastructure Powered by Proof of Service',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://mehr.network',
  baseUrl: '/',

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  headTags: [
    // Structured data: Organization
    {
      tagName: 'script',
      attributes: { type: 'application/ld+json' },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Organization',
        name: 'Mehr Network',
        url: 'https://mehr.network',
        logo: 'https://mehr.network/img/logo.svg',
        description:
          'Decentralized mesh networking infrastructure powered by Proof of Service. Free between friends, paid between strangers.',
        sameAs: ['https://github.com/mehr-protocol'],
      }),
    },
    // Structured data: WebSite with search
    {
      tagName: 'script',
      attributes: { type: 'application/ld+json' },
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'Mehr Network Documentation',
        url: 'https://mehr.network',
        description:
          'Technical documentation for the Mehr Network — a decentralized mesh protocol using Proof of Service, CRDT-based ledgers, and self-sovereign identity.',
      }),
    },
    // Point AI crawlers to llms.txt
    {
      tagName: 'link',
      attributes: {
        rel: 'author',
        href: 'https://mehr.network/llms.txt',
        type: 'text/plain',
      },
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
        sitemap: {
          lastmod: 'date',
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/markdown-page/**'],
          filename: 'sitemap.xml',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    metadata: [
      { name: 'description', content: 'Mehr Network: decentralized mesh infrastructure powered by Proof of Service. Free between friends, paid between strangers. Protocol specification, hardware, economics, and developer documentation.' },
      { name: 'keywords', content: 'mesh network, decentralized, proof of service, CRDT, self-sovereign identity, LoRa, protocol, peer-to-peer, Mehr, MHR token' },
      { property: 'og:type', content: 'website' },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Mehr',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'https://github.com/mehr-protocol',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Introduction',
              to: '/docs/introduction',
            },
            {
              label: 'Protocol Stack',
              to: '/docs/protocol/physical-transport',
            },
            {
              label: 'Hardware',
              to: '/docs/hardware/reference-designs',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/mehr-protocol',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Specification (v1.0)',
              to: '/docs/specification',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Mehr Network Contributors.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['rust', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
