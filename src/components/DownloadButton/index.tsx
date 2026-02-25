import type { ReactNode } from 'react';
import styles from './styles.module.css';

interface DownloadButtonProps {
  label?: string;
  href?: string;
}

export default function DownloadButton({
  label = 'Download Full Specification (PDF)',
  href = '/mehr-protocol-spec-v1.0.pdf',
}: DownloadButtonProps): ReactNode {
  return (
    <a href={href} download className={styles.downloadButton}>
      <svg
        className={styles.icon}
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      {label}
    </a>
  );
}
