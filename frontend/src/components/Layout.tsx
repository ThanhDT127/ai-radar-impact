import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import styles from '../styles/layout.module.css';
import ThemeToggle from './ThemeToggle';
import ScrollToTop from './ScrollToTop';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div>
      <header className={styles.header}>
        <div className={`container ${styles.headerInner}`}>
          <Link to="/" className={styles.brandLink}>
            <span className={styles.logoMark}>AI</span>
            <div>
              <strong className={styles.brandName}>AI Radar Impact</strong>
              <span className={styles.brandSub}>Intelligence Dashboard</span>
            </div>
          </Link>
          <div className={styles.headerActions}>
            <span className={styles.headerMeta}>Dashboard phân tích</span>
            <ThemeToggle />
          </div>
        </div>
      </header>
      <main className="container">{children}</main>
      <ScrollToTop />
    </div>
  );
}
