import type { ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import styles from '../styles/layout.module.css';
import ThemeToggle from './ThemeToggle';
import ScrollToTop from './ScrollToTop';

interface LayoutProps {
  children: ReactNode;
}

const TABS = [
  { to: '/', label: 'Insights', end: true },
  { to: '/subscribers', label: 'Người nhận', end: false },
];

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
          <nav className={styles.nav}>
            {TABS.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
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
