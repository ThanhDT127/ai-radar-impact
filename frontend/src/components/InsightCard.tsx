import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { InsightListItem } from '../types/insight';
import RelativeTime from './RelativeTime';
import UrgencyBadge from './UrgencyBadge';
import MomentumIndicator from './MomentumIndicator';
import styles from '../styles/card.module.css';

interface InsightCardProps {
  insight: InsightListItem;
  index?: number;
}

function hasVietnamese(text: string): boolean {
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(text);
}

function makeDisplayTitle(insight: InsightListItem): string {
  if (insight.summary_short && !hasVietnamese(insight.title)) {
    return insight.summary_short;
  }
  return insight.title;
}

const TIER_LABEL: Record<string, string> = {
  Tactical: 'Hành động ngay',
  Operational: 'Vận hành',
  Strategic: 'Chiến lược',
  Informational: 'Tham khảo',
};

const ADOPTION_LABEL: Record<string, string> = {
  Adopt: 'Áp dụng',
  Trial: 'Dùng thử',
  Assess: 'Đánh giá',
  Hold: 'Tạm hoãn',
};

const TIER_BORDER: Record<string, string> = {
  Tactical: 'var(--tier-tactical)',
  Operational: 'var(--tier-operational)',
  Strategic: 'var(--tier-strategic)',
  Informational: 'var(--tier-informational)',
};

const TIER_GLOW: Record<string, string> = {
  Tactical: 'var(--tier-tactical-glow)',
  Operational: 'var(--tier-operational-glow)',
  Strategic: 'var(--tier-strategic-glow)',
  Informational: 'var(--tier-informational-glow)',
};

const ROLE_SHORT_LABEL: Record<string, string> = {
  Executive: 'Leader',
  Engineering: 'Kỹ sư',
  'Data/AI': 'Data/AI',
  Product: 'Sản phẩm',
  'Content/Marketing': 'Marketing',
  'Legal/Compliance': 'Pháp lý',
  'HR/L&D': 'Nhân sự',
  'Toàn công ty': 'Toàn công ty',
  DevOps: 'DevOps',
  Infrastructure: 'Hạ tầng',
  Security: 'Bảo mật',
  'BA/QA': 'BA/QA',
  'Designer/UX': 'UX',
};

function generateCardBullets(insight: InsightListItem, displayTitle?: string): string[] {
  const bullets: string[] = [];
  if (insight.signal) bullets.push(insight.signal.trim());
  if (insight.so_what) bullets.push(insight.so_what.trim());
  if (insight.why_it_matters) bullets.push(insight.why_it_matters.trim());
  if (insight.summary_short && insight.summary_short !== displayTitle) {
    const sentences = insight.summary_short
      .split(/(?<=[.。!?])\s+/)
      .filter((s) => s.trim().length > 10);
    for (const sentence of sentences) {
      const clean = sentence.trim();
      if (bullets.length >= 3) break;
      if (!bullets.includes(clean)) bullets.push(clean);
    }
  }
  return bullets.slice(0, 3);
}

export default function InsightCard({ insight, index = 0 }: InsightCardProps) {
  const timeValue = insight.published_at ?? insight.created_at;
  const navigate = useNavigate();
  const displayTitle = makeDisplayTitle(insight);
  const primaryImage = insight.primary_image;
  const isUrgent = insight.urgency === 'critical' || insight.urgency === 'high';
  const tier = insight.intelligence_tier;
  const tierColor = tier ? (TIER_BORDER[tier] ?? 'var(--color-border)') : 'var(--color-border)';
  const tierGlow = tier ? (TIER_GLOW[tier] ?? 'transparent') : 'transparent';
  const bullets = generateCardBullets(insight, displayTitle);

  const [imageError, setImageError] = useState(false);
  const showImage = !!primaryImage && !imageError;

  const cardRef = useRef<HTMLAnchorElement>(null);
  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.animationDelay = `${index * 55}ms`;
          el.classList.add(styles.cardEnter);
          observer.unobserve(el);
        }
      },
      { threshold: 0.08 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [index]);

  return (
    <Link
      ref={cardRef}
      to={`/insights/${insight.id}`}
      className={styles.card}
      style={{
        borderLeftColor: tierColor,
        // @ts-ignore - CSS custom property
        '--card-tier-glow': tierGlow,
      }}
    >
      {/* Urgency strip at top for critical/high */}
      {isUrgent && (
        <div
          className={`${styles.urgencyStrip} ${insight.urgency === 'critical' ? styles.urgencyStripCritical : styles.urgencyStripHigh}`}
        />
      )}

      {/* Hero image — only show when real image exists */}
      {showImage && (
        <div className={styles.cardHeroImageWrap}>
          <img
            src={primaryImage!}
            alt=""
            className={styles.cardHeroImage}
            loading="lazy"
            onError={() => setImageError(true)}
          />
        </div>
      )}

      {/* Content section */}
      <div className={styles.cardBody}>
        {/* Meta row: source + time */}
        <div className={styles.cardMetaRow}>
          <span className={styles.sourcePill}>{insight.source_name}</span>
          <span className={styles.cardTimeInline}>
            <RelativeTime value={timeValue} showAbsolute={false} />
          </span>
          {insight.vietnam_relevance === 'high' && (
            <span className={styles.cardVietnamFlag} title="Liên quan cao đến Việt Nam" aria-label="Liên quan cao đến Việt Nam">🇻🇳</span>
          )}
        </div>

        {/* Title */}
        <h3 className={styles.cardTitle}>{displayTitle}</h3>

        {/* Technical Signals Row */}
        {(insight.practical_indicators?.has_code_example || 
          insight.practical_indicators?.has_benchmark || 
          insight.practical_indicators?.has_api_change || 
          insight.practical_indicators?.has_security_patch) && (
          <div className={styles.technicalSignalsRow}>
            {insight.practical_indicators.has_code_example && <span className={styles.technicalSignalBadge} title="Bài viết có chứa mã nguồn mẫu">💻 Có code mẫu</span>}
            {insight.practical_indicators.has_benchmark && <span className={styles.technicalSignalBadge} title="Bài viết có số liệu đo đạc, benchmark hiệu năng">📊 Có benchmark</span>}
            {insight.practical_indicators.has_api_change && <span className={styles.technicalSignalBadge} title="Bài viết đề cập đến việc thay đổi API/cú pháp">🔗 Thay đổi API</span>}
            {insight.practical_indicators.has_security_patch && <span className={styles.technicalSignalBadge} title="Bài viết có chứa bản vá hoặc thông tin bảo mật">🛡️ Bảo mật</span>}
          </div>
        )}

        {/* Bullets summary (max 3) */}
        {bullets.length > 0 && (
          <ul className={styles.cardBullets}>
            {bullets.map((bullet, idx) => (
              <li key={idx}>{bullet}</li>
            ))}
          </ul>
        )}

        {/* Tags: topics + roles */}
        <div className={styles.cardTagsRow}>
          {insight.topics.slice(0, 3).map((topic) => (
            <span
              key={topic}
              className={styles.cardTopicTag}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/?search=${topic}`);
              }}
            >
              {topic}
            </span>
          ))}
          {insight.affected_roles.slice(0, 3).map((role) => (
            <span
              key={role}
              className={styles.cardRoleTag}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/?role=${role}`);
              }}
            >
              {ROLE_SHORT_LABEL[role] ?? role}
            </span>
          ))}
        </div>
      </div>

      {/* Footer: badges */}
      <div className={styles.cardFooter}>
        <div className={styles.cardBadgesCompact}>
          {insight.urgency && (
            <span
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/?urgency=${insight.urgency}`);
              }}
              className={styles.clickableBadge}
            >
              <UrgencyBadge urgency={insight.urgency} />
            </span>
          )}
          {insight.intelligence_tier && (
            <span
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/?intelligence_tier=${insight.intelligence_tier}`);
              }}
              className={`${styles.tierBadgeInline} ${styles[`tier${insight.intelligence_tier}`]} ${styles.clickableBadge}`}
            >
              {TIER_LABEL[insight.intelligence_tier] ?? insight.intelligence_tier}
            </span>
          )}
          {insight.adoption_ring && (
            <span
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              className={`${styles.adoptionBadgeInline} ${styles.clickableBadge}`}
            >
              {ADOPTION_LABEL[insight.adoption_ring] ?? insight.adoption_ring}
            </span>
          )}
          {insight.momentum === 'rising' && (
            <span
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                navigate(`/?momentum=${insight.momentum}`);
              }}
              className={styles.clickableBadge}
            >
              <MomentumIndicator momentum={insight.momentum} />
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
