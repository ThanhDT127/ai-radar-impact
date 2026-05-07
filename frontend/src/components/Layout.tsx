import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div>
      <header
        style={{
          height: 'var(--header-height)',
          position: 'sticky',
          top: 0,
          zIndex: 20,
          backdropFilter: 'blur(14px)',
          background: 'rgba(243, 237, 228, 0.78)',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        <div
          className="container"
          style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '12px' }}>
            <span
              style={{
                width: 38,
                height: 38,
                borderRadius: 12,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #b84d1e, #e28d56)',
                color: '#fff',
                fontWeight: 800,
              }}
            >
              AI
            </span>
            <div>
              <strong style={{ display: 'block', fontFamily: 'var(--font-display)' }}>
                AI Radar Impact
              </strong>
              <span style={{ color: 'var(--color-text-muted)', fontSize: '0.82rem' }}>
                Sources, roles, and impact signals
              </span>
            </div>
          </Link>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.88rem' }}>
            Dashboard phân tích
          </span>
        </div>
      </header>
      <main className="container">{children}</main>
    </div>
  );
}
