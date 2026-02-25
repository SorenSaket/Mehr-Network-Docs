#!/usr/bin/env node

import { readFile, access } from 'node:fs/promises';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';
import { mdToPdf } from 'md-to-pdf';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '..');
const DOCS_DIR = join(PROJECT_ROOT, 'docs');
const OUTPUT_PATH = join(PROJECT_ROOT, 'static', 'mehr-protocol-spec-v1.0.pdf');
const STYLESHEET = join(__dirname, 'pdf-styles.css');

// Document order matching sidebars.ts
const SECTIONS = [
  {
    category: null,
    docs: ['introduction', 'faq'],
  },
  {
    category: 'Protocol Stack',
    docs: [
      'protocol/physical-transport',
      'protocol/network-protocol',
      'protocol/security',
    ],
  },
  {
    category: 'Economics',
    docs: [
      'economics/mhr-token',
      'economics/payment-channels',
      'economics/crdt-ledger',
      'economics/trust-neighborhoods',
      'economics/real-world-impact',
    ],
  },
  {
    category: 'Capability Marketplace',
    docs: [
      'marketplace/overview',
      'marketplace/discovery',
      'marketplace/agreements',
      'marketplace/verification',
    ],
  },
  {
    category: 'Service Primitives',
    docs: [
      'services/mhr-store',
      'services/mhr-dht',
      'services/mhr-pub',
      'services/mhr-compute',
    ],
  },
  {
    category: 'Applications',
    docs: [
      'applications/messaging',
      'applications/social',
      'applications/voice',
      'applications/naming',
      'applications/community-apps',
      'applications/hosting',
    ],
  },
  {
    category: 'Hardware',
    docs: ['hardware/reference-designs', 'hardware/device-tiers'],
  },
  {
    category: 'Development',
    docs: [
      'development/roadmap',
      'development/design-decisions',
      'development/open-questions',
    ],
  },
  {
    category: null,
    docs: ['specification'],
  },
];

function docIdToAnchor(docId) {
  return docId.replace(/\//g, '-');
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[`*_~[\]()]/g, '')
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
    .replace(/^-|-$/g, '');
}

// Build a set of all valid doc IDs for link resolution
const ALL_DOC_IDS = SECTIONS.flatMap((s) => s.docs);

function rewriteLinks(markdown, currentDocId) {
  const currentDir = currentDocId.includes('/')
    ? currentDocId.substring(0, currentDocId.lastIndexOf('/'))
    : '';

  return markdown.replace(
    /\[([^\]]*)\]\(([^)]+)\)/g,
    (match, text, href) => {
      // External links — leave unchanged
      if (href.startsWith('http://') || href.startsWith('https://')) {
        return match;
      }

      // Parse href into path and fragment
      let [path, fragment] = href.split('#');

      // Hash-only links
      if (!path) {
        const anchor = docIdToAnchor(currentDocId);
        const target = fragment ? `${anchor}--${fragment}` : anchor;
        return `[${text}](#${target})`;
      }

      // Resolve relative path to doc ID
      let resolvedPath = path;
      if (path.startsWith('../')) {
        // Parent-relative
        const parts = currentDir.split('/').filter(Boolean);
        let target = path;
        while (target.startsWith('../')) {
          parts.pop();
          target = target.substring(3);
        }
        resolvedPath = parts.length > 0 ? parts.join('/') + '/' + target : target;
      } else if (path.startsWith('./')) {
        resolvedPath = currentDir
          ? currentDir + '/' + path.substring(2)
          : path.substring(2);
      } else if (!path.includes('/') && currentDir) {
        // Same-directory relative (no slashes, not starting with ./ or ../)
        resolvedPath = currentDir + '/' + path;
      }

      // Clean up trailing slashes or .md extensions
      resolvedPath = resolvedPath.replace(/\.md$/, '').replace(/\/$/, '');

      // Check if this resolves to a known doc
      if (ALL_DOC_IDS.includes(resolvedPath)) {
        const anchor = docIdToAnchor(resolvedPath);
        const target = fragment ? `${anchor}--${fragment}` : anchor;
        return `[${text}](#${target})`;
      }

      // Unknown link — return as text
      return `[${text}](#)`;
    }
  );
}

function processHeadings(markdown, docId) {
  const prefix = docIdToAnchor(docId);
  let firstHeading = true;

  return markdown.replace(/^(#{1,4})\s+(.+)$/gm, (match, hashes, title) => {
    const slug = slugify(title);
    const level = hashes.length;

    if (firstHeading && level === 1) {
      firstHeading = false;
      return `<a id="${prefix}"></a>\n\n${hashes} ${title}`;
    }

    if (level >= 2) {
      return `<a id="${prefix}--${slug}"></a>\n\n${hashes} ${title}`;
    }

    return match;
  });
}

async function readDoc(docId) {
  const filePath = join(DOCS_DIR, `${docId}.md`);
  try {
    await access(filePath);
  } catch {
    console.warn(`  Warning: ${filePath} not found, skipping.`);
    return null;
  }

  const raw = await readFile(filePath, 'utf-8');
  const { content, data } = matter(raw);
  const title = data.title || docId;

  let processed = content.trim();
  // Strip MDX: import statements and JSX component tags (not valid in plain markdown)
  processed = processed.replace(/^import\s+.*$/gm, '');
  processed = processed.replace(/^<\w+[^>]*\/>\s*$/gm, '');
  processed = processHeadings(processed, docId);
  processed = rewriteLinks(processed, docId);

  return { docId, title, content: processed };
}

function generateTitlePage() {
  const date = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return `<div class="title-page">

<h1>Mehr Protocol</h1>

<div class="subtitle">Complete Specification</div>

<div class="version">Version 1.0 &mdash; Design Complete, Pre-Implementation</div>

<div class="date">Generated ${date}</div>

</div>

<div class="page-break"></div>
`;
}

function generateTOC(sections) {
  let toc = '<div class="toc">\n\n## Table of Contents\n\n';

  for (const section of sections) {
    if (section.category) {
      toc += `**${section.category}**\n\n`;
    }

    for (const doc of section.entries) {
      const anchor = docIdToAnchor(doc.docId);
      toc += `- [${doc.title}](#${anchor})\n`;
    }
    toc += '\n';
  }

  toc += '</div>\n\n<div class="page-break"></div>\n';
  return toc;
}

async function main() {
  console.log('Generating Mehr Protocol specification PDF...\n');

  // Read all docs
  const sectionData = [];
  for (const section of SECTIONS) {
    const entries = [];
    for (const docId of section.docs) {
      const doc = await readDoc(docId);
      if (doc) {
        entries.push(doc);
        console.log(`  Read: ${docId} — "${doc.title}"`);
      }
    }
    sectionData.push({ category: section.category, entries });
  }

  const totalDocs = sectionData.reduce((n, s) => n + s.entries.length, 0);
  console.log(`\n  Total: ${totalDocs} documents\n`);

  // Build the full markdown document
  const parts = [];

  // Title page
  parts.push(generateTitlePage());

  // Table of contents
  parts.push(generateTOC(sectionData));

  // All document sections
  for (const section of sectionData) {
    for (const doc of section.entries) {
      parts.push(doc.content);
      parts.push('\n\n<div class="page-break"></div>\n');
    }
  }

  const fullMarkdown = parts.join('\n\n');

  console.log('  Rendering PDF (this may take a moment)...');

  const pdf = await mdToPdf(
    { content: fullMarkdown },
    {
      dest: OUTPUT_PATH,
      pdf_options: {
        format: 'A4',
        margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: `
          <div style="font-size:8px; width:100%; text-align:center; color:#aaa; padding-top:4px;">
            Mehr Protocol Specification v1.0
          </div>`,
        footerTemplate: `
          <div style="font-size:8px; width:100%; text-align:center; color:#aaa; padding-bottom:4px;">
            <span class="pageNumber"></span> / <span class="totalPages"></span>
          </div>`,
      },
      stylesheet: STYLESHEET,
      launch_options: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
      },
    }
  );

  if (pdf?.filename) {
    console.log(`\n  PDF generated: ${pdf.filename}`);
  } else {
    console.log(`\n  PDF generated: ${OUTPUT_PATH}`);
  }

  console.log('  Done!\n');
}

main().catch((err) => {
  console.warn('PDF generation skipped:', err.message || err);
  console.warn('The existing PDF in static/ will be used instead.\n');
  // Don't exit(1) — let the build continue with the pre-existing PDF
});
