import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div>
      <header style={{
        height: 'var(--header-height)',
        borderBottom: '1px solid var(--color-border)',
        backgroundColor: 'rgba(15, 17, 23, 0.9)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div className="container" style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
              }}>📡</span>
              <span style={{
                fontWeight: 700,
                fontSize: '1rem',
                color: 'var(--color-text-primary)',
                letterSpacing: '-0.01em',
              }}>AI Radar</span>
            </div>
          </Link>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
            Intelligence Dashboard
          </span>
        </div>
      </header>
      <main className="container">
        {children}
      </main>
    </div>
  );
}
