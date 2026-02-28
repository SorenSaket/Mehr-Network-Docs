#!/usr/bin/env node

/**
 * generate-llms-full.mjs
 *
 * Generates llms-full.txt — a single plain-text file containing all
 * Mehr Network documentation, designed for LLM ingestion.
 *
 * Runs as part of the build pipeline. Output goes to static/llms-full.txt
 * so Docusaurus serves it at /llms-full.txt.
 */

import { readdir, readFile, writeFile, stat } from 'node:fs/promises';
import { join, relative, basename } from 'node:path';
import matter from 'gray-matter';

const DOCS_DIR = 'docs';
const OUTPUT = 'static/llms-full.txt';

// Section ordering (matches llms.txt structure)
const SECTION_ORDER = [
  '', // root docs
  'protocol',
  'services',
  'economics',
  'hardware',
  'interoperability',
  'marketplace',
  'applications',
  'development',
];

const SECTION_TITLES = {
  '': 'Overview',
  'protocol': 'Protocol Stack',
  'services': 'Core Services',
  'economics': 'Economics',
  'hardware': 'Hardware',
  'interoperability': 'Interoperability',
  'marketplace': 'Marketplace',
  'applications': 'Applications',
  'development': 'Development',
};

async function getMarkdownFiles(dir) {
  const results = [];
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...await getMarkdownFiles(full));
    } else if (entry.name.endsWith('.md') || entry.name.endsWith('.mdx')) {
      results.push(full);
    }
  }
  return results;
}

function stripFrontMatter(content) {
  const { content: body } = matter(content);
  return body.trim();
}

function getSection(filePath) {
  const rel = relative(DOCS_DIR, filePath);
  const parts = rel.split(/[/\\]/);
  return parts.length > 1 ? parts[0] : '';
}

async function main() {
  const files = await getMarkdownFiles(DOCS_DIR);

  // Group by section
  const sections = new Map();
  for (const section of SECTION_ORDER) {
    sections.set(section, []);
  }

  for (const file of files) {
    const section = getSection(file);
    if (!sections.has(section)) {
      sections.set(section, []);
    }

    const raw = await readFile(file, 'utf-8');
    const { data: frontmatter, content } = matter(raw);
    const title = frontmatter.title || basename(file, '.md');
    const position = frontmatter.sidebar_position ?? 999;

    sections.get(section).push({
      title,
      position,
      path: relative(DOCS_DIR, file).replace(/\\/g, '/'),
      content: content.trim(),
    });
  }

  // Sort each section by sidebar_position
  for (const [, docs] of sections) {
    docs.sort((a, b) => a.position - b.position);
  }

  // Build output
  const lines = [];
  lines.push('# Mehr Network — Complete Documentation');
  lines.push('');
  lines.push('> Decentralized mesh networking infrastructure powered by Proof of Service.');
  lines.push('> Source: https://mehr.network');
  lines.push(`> Generated: ${new Date().toISOString().split('T')[0]}`);
  lines.push('');
  lines.push('---');
  lines.push('');

  for (const section of SECTION_ORDER) {
    const docs = sections.get(section);
    if (!docs || docs.length === 0) continue;

    const sectionTitle = SECTION_TITLES[section] || section;
    lines.push(`${'#'.repeat(section === '' ? 1 : 2)} ${sectionTitle}`);
    lines.push('');

    for (const doc of docs) {
      lines.push(`${'#'.repeat(section === '' ? 2 : 3)} ${doc.title}`);
      lines.push(`<!-- Source: docs/${doc.path} -->`);
      lines.push('');
      lines.push(doc.content);
      lines.push('');
      lines.push('---');
      lines.push('');
    }
  }

  const output = lines.join('\n');
  await writeFile(OUTPUT, output, 'utf-8');

  const stats = await stat(OUTPUT);
  const kb = (stats.size / 1024).toFixed(1);
  console.log(`✓ Generated ${OUTPUT} (${kb} KB, ${files.length} documents)`);
}

main().catch((err) => {
  console.error('Failed to generate llms-full.txt:', err);
  process.exit(1);
});
