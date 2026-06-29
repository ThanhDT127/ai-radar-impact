import { Link, useParams } from 'react-router-dom';
import type { InsightReference } from '../types/insight';
import { useQuery } from '@tanstack/react-query';
import { fetchInsightById } from '../api/insights';

import Breadcrumb from '../components/Breadcrumb';
import MomentumIndicator from '../components/MomentumIndicator';
import OriginalArticlePanel from '../components/OriginalArticlePanel';
import RecommendationsByRole from '../components/RecommendationsByRole';
import RelativeTime from '../components/RelativeTime';
import RoleBadge from '../components/RoleBadge';
import Tooltip from '../components/Tooltip';
import { TOOLTIP } from '../components/TooltipContent';
import UrgencyBadge from '../components/UrgencyBadge';
import styles from '../styles/detail.module.css';
import badgeStyles from '../styles/badges.module.css';

import { useState } from 'react';

/* ── Label maps ── */

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

/* ── Helpers ── */

function generateBullets(insight: {
  signal?: string | null;
  so_what?: string | null;
  why_it_matters?: string | null;
  summary_short?: string | null;
  summary_medium?: string | null;
}): string[] {
  const bullets: string[] = [];
  if (insight.signal) bullets.push(insight.signal.trim());
  if (insight.so_what) bullets.push(insight.so_what.trim());
  if (insight.why_it_matters) bullets.push(insight.why_it_matters.trim());
  if (insight.summary_short) {
    const sentences = insight.summary_short
      .split(/(?<=[.。!?])\s+/)
      .filter((s) => s.trim().length > 10);
    for (const sentence of sentences) {
      const clean = sentence.trim();
      if (bullets.length >= 5) break;
      if (!bullets.includes(clean)) bullets.push(clean);
    }
  }
  if (insight.summary_medium && bullets.length < 5) {
    const sentences = insight.summary_medium
      .split(/(?<=[.。!?])\s+/)
      .filter((s) => s.trim().length > 10);
    for (const sentence of sentences) {
      const clean = sentence.trim();
      if (bullets.length >= 5) break;
      if (!bullets.includes(clean)) bullets.push(clean);
    }
  }
  return bullets.slice(0, 5);
}

export default function InsightDetail() {
  const { id } = useParams<{ id: string }>();
  const [viewMode, setViewMode] = useState<'split' | 'focus-ai' | 'focus-original'>(() => {
    return (localStorage.getItem('radar-view-mode') as any) || 'split';
  });

  const changeViewMode = (mode: 'split' | 'focus-ai' | 'focus-original') => {
    const currentScrollY = window.scrollY;
    setViewMode(mode);
    localStorage.setItem('radar-view-mode', mode);
    setTimeout(() => {
      window.scrollTo(0, currentScrollY);
    }, 50);
  };

  const { data: insight, isLoading, isError } = useQuery({
    queryKey: ['insight', id],
    queryFn: () => fetchInsightById(id!),
    enabled: !!id,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className={styles.detailPage}>
        <div className={styles.skeleton} style={{ minHeight: 320 }} />
      </div>
    );
  }

  if (isError || !insight) {
    return (
      <div className={`${styles.detailPage} ${styles.notFound}`}>
        <h2>Không tìm thấy bản tin</h2>
        <p>Bản tin này có thể đã bị xóa hoặc đường dẫn không còn hợp lệ.</p>
        <Link to="/">Về danh sách bản tin</Link>
      </div>
    );
  }

  const publishedValue = insight.published_at ?? insight.created_at;
  const bullets = generateBullets(insight);
  const hasIndicators = !!(insight.practical_indicators && (
    insight.practical_indicators.has_code_example ||
    insight.practical_indicators.has_benchmark ||
    insight.practical_indicators.has_api_change ||
    insight.practical_indicators.has_migration_guide ||
    insight.practical_indicators.has_security_patch
  ));

  return (
    <div className={styles.detailPage}>
      {/* Breadcrumb */}
      <Breadcrumb tier={insight.intelligence_tier} title={insight.title} />

      {/* ── Header Section ── */}
      <div className={styles.detailHeaderWrap}>
        <div className={styles.detailHeaderLeft}>
          <div className={styles.detailSourceTime}>
            <span className={styles.sourcePill}>{insight.source_name}</span>
            <span className={styles.metaDot}>•</span>
            <span className={styles.timeText}><RelativeTime value={publishedValue} /></span>
            <span className={styles.metaDot}>•</span>
            <a
              href={insight.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.originalLinkButton}
            >
              Đọc nguồn gốc ↗
            </a>
          </div>

          <h1 className={styles.detailTitle}>{insight.title}</h1>

          {/* Metadata Grid Box */}
          <div className={styles.metaRibbon}>
            {/* Box 1: Đánh giá & Tiên liệu */}
            <div className={styles.metaRibbonGroup}>
              <span className={styles.metaGroupLabel}>ĐÁNH GIÁ & TIÊN LIỆU</span>
              <div className={styles.metaGroupContent}>
                {insight.intelligence_tier && (
                  <Link to={`/?intelligence_tier=${insight.intelligence_tier}`}>
                    <Tooltip content={TOOLTIP.tier[insight.intelligence_tier as keyof typeof TOOLTIP.tier] ?? ''}>
                      <span className={`${styles.tierBadgeInline} ${styles[`tier${insight.intelligence_tier}`]} ${styles.clickableBadge}`}>
                        {TIER_LABEL[insight.intelligence_tier] ?? insight.intelligence_tier}
                      </span>
                    </Tooltip>
                  </Link>
                )}
                {insight.urgency && (
                  <Link to={`/?urgency=${insight.urgency}`}>
                    <span className={styles.clickableBadge}>
                      <UrgencyBadge urgency={insight.urgency} />
                    </span>
                  </Link>
                )}
                {insight.momentum && (
                  <Link to={`/?momentum=${insight.momentum}`}>
                    <span className={styles.clickableBadge}>
                      <MomentumIndicator momentum={insight.momentum} />
                    </span>
                  </Link>
                )}
                {insight.adoption_ring && (
                  <Tooltip content={TOOLTIP.adoption[insight.adoption_ring as keyof typeof TOOLTIP.adoption] ?? ''}>
                    <span className={`${badgeStyles.adoptionBadgeInline} ${badgeStyles[`adoption${insight.adoption_ring}`]}`}>
                      {ADOPTION_LABEL[insight.adoption_ring] ?? insight.adoption_ring}
                    </span>
                  </Tooltip>
                )}
              </div>
            </div>

            {/* Box 2: Phạm vi tác động */}
            <div className={styles.metaRibbonGroup}>
              <span className={styles.metaGroupLabel}>PHẠM VI TÁC ĐỘNG</span>
              <div className={styles.metaGroupContent}>
                {insight.affected_roles.map((role) => (
                  <Link key={role} to={`/?role=${role}`}>
                    <RoleBadge role={role} />
                  </Link>
                ))}
                {insight.topics.map((topic) => (
                  <Link key={topic} to={`/?search=${topic}`}>
                    <span className={`${badgeStyles.topicTag} ${styles.clickableBadge}`}>{topic}</span>
                  </Link>
                ))}
              </div>
            </div>

            {/* Box 3: Chỉ số thực hành */}
            {hasIndicators && (
              <div className={styles.metaRibbonGroup}>
                <span className={styles.metaGroupLabel}>CHỈ SỐ THỰC HÀNH</span>
                <div className={styles.metaGroupContent}>
                  {insight.practical_indicators!.has_code_example && (
                    <Tooltip content={TOOLTIP.practicalIndicators.has_code}>
                      <span className={badgeStyles.indicatorIcon}>💻 Mã nguồn</span>
                    </Tooltip>
                  )}
                  {insight.practical_indicators!.has_benchmark && (
                    <Tooltip content={TOOLTIP.practicalIndicators.has_benchmark}>
                      <span className={badgeStyles.indicatorIcon}>📊 Benchmark</span>
                    </Tooltip>
                  )}
                  {insight.practical_indicators!.has_api_change && (
                    <Tooltip content={TOOLTIP.practicalIndicators.has_api_change}>
                      <span className={badgeStyles.indicatorIcon}>🔗 API</span>
                    </Tooltip>
                  )}
                  {insight.practical_indicators!.has_migration_guide && (
                    <Tooltip content={TOOLTIP.practicalIndicators.has_migration}>
                      <span className={badgeStyles.indicatorIcon}>📖 Hướng dẫn chuyển đổi</span>
                    </Tooltip>
                  )}
                  {insight.practical_indicators!.has_security_patch && (
                    <Tooltip content={TOOLTIP.practicalIndicators.has_security}>
                      <span className={badgeStyles.indicatorIcon}>🛡️ Bản vá bảo mật</span>
                    </Tooltip>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {insight.primary_image && (
          <div className={styles.detailHeaderRight}>
            <img
              src={insight.primary_image}
              alt=""
              className={styles.detailCoverImage}
            />
          </div>
        )}
      </div>

      {/* 💡 Core Summary (So What) on top */}
      {insight.so_what && (
        <section className={styles.detailHeaderSoWhat}>
          <div className={styles.detailSoWhatHeader}>
            <span className="sectionIcon">💡</span>
            <strong>Ý nghĩa cốt lõi (So What)</strong>
          </div>
          <p>{insight.so_what}</p>
        </section>
      )}

      {/* ── View Mode Controls ── */}
      <div className={styles.viewModeToolbar}>
        <span className={styles.viewModeLabel}>Chế độ xem:</span>
        <button
          type="button"
          className={`${styles.viewModeButton} ${viewMode === 'split' ? styles.viewModeActive : ''}`}
          onClick={(e) => { e.preventDefault(); changeViewMode('split'); }}
          title="Xem song ngữ song song 50/50"
        >
          ⚖️ Song song
        </button>
        <button
          type="button"
          className={`${styles.viewModeButton} ${viewMode === 'focus-ai' ? styles.viewModeActive : ''}`}
          onClick={(e) => { e.preventDefault(); changeViewMode('focus-ai'); }}
          title="Xem phân tích chi tiết tiếng Việt (80/20)"
        >
          🤖 Phân tích chi tiết
        </button>
        <button
          type="button"
          className={`${styles.viewModeButton} ${viewMode === 'focus-original' ? styles.viewModeActive : ''}`}
          onClick={(e) => { e.preventDefault(); changeViewMode('focus-original'); }}
          title="Xem bài viết gốc tiếng Anh (20/80)"
        >
          📰 Bài viết gốc
        </button>
      </div>

      {/* ── 50/50 Split View: Phân tích | Bản gốc ── */}
      <div className={`${styles.detailSplitView} ${styles[viewMode === 'split' ? 'layoutSplit' : (viewMode === 'focus-ai' ? 'layoutFocusAI' : 'layoutFocusOriginal')]}`}>

        {/* LEFT COLUMN: AI Analysis (Vietnamese) */}
        <div className={styles.detailSplitLeft}>

          {/* Focus Original Mode - Sidebar AI Mini */}
          {viewMode === 'focus-original' && (
            <div className={styles.focusOriginalSidebar}>
              <h3 className={styles.sidebarMiniTitle}>{insight.title}</h3>
              <button 
                type="button"
                className={styles.sidebarExpandButton}
                onClick={(e) => { e.preventDefault(); changeViewMode('split'); }}
                title="Mở rộng phân tích AI"
                style={{ marginTop: '12px', display: 'block' }}
              >
                Xem phân tích chi tiết ▶
              </button>
            </div>
          )}

          {/* Tóm tắt & Phân tích chi tiết */}
          {insight.summary_medium && viewMode !== 'focus-original' && (
            <section className={`${styles.detailSection} ${styles.detailSectionInfo}`}>
              <div className={styles.detailSectionHeader}>
                <span className="sectionIcon">🔎</span>
                <span>Tóm tắt & Phân tích chi tiết</span>
              </div>
              <p className={styles.detailSummaryMedium}>{insight.summary_medium}</p>
            </section>
          )}

          {/* Những điều cần biết (max 5 bullets) */}
          {bullets.length > 0 && viewMode !== 'focus-original' && (
            <section className={`${styles.detailSection} ${styles.detailSectionNeutral}`}>
              <div className={styles.detailSectionHeader}>
                <span className="sectionIcon">📋</span>
                <span>Những điều cần biết</span>
              </div>
              <ul className={styles.detailBullets}>
                {bullets.map((bullet, idx) => (
                  <li key={idx}>{bullet}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Khuyến nghị hành động */}
          {insight.recommendations && Object.keys(insight.recommendations).length > 0 && viewMode !== 'focus-original' && (
            <section className={`${styles.detailSection} ${styles.detailSectionSuccess}`}>
              <div className={styles.detailSectionHeader}>
                <span className="sectionIcon">👥</span>
                <span>Bạn nên làm gì? (Khuyến nghị theo vai trò)</span>
              </div>
              <RecommendationsByRole recommendations={insight.recommendations} />
            </section>
          )}

          {/* Rủi ro */}
          {insight.risks && insight.risks.length > 0 && viewMode !== 'focus-original' && (
            <section className={`${styles.detailSection} ${styles.detailSectionDanger}`}>
              <div className={styles.detailSectionHeader}>
                <span className="sectionIcon">⚠️</span>
                <span>Rủi ro cần lưu ý</span>
              </div>
              <ul className={styles.risksList}>
                {insight.risks.map((risk, idx) => (
                  <li key={idx}>{risk}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Footer: verification + references */}
          {viewMode !== 'focus-original' && (
            <div className={styles.splitLeftFooter}>
              <div className={styles.verificationBadge}>
                <span>🤖 Phân tích tự động bởi Gemini AI</span>
              </div>

              {insight.references && insight.references.length > 0 && (
                <div className={styles.splitLeftReferences}>
                  <h4>Các tin liên quan trong luồng:</h4>
                  <ul className={styles.referenceList}>
                    {insight.references.map((ref: InsightReference) => (
                      <li key={ref.id} className={styles.referenceItem}>
                        <span className={styles.sourcePill}>{ref.source_name}</span>
                        <a href={ref.source_url} target="_blank" rel="noopener noreferrer" className={styles.referenceLink}>
                          {ref.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Original Article (always visible) */}
        <div className={styles.detailSplitRight}>
          <OriginalArticlePanel
            sourceUrl={insight.source_url}
            title={insight.title}
            sourceName={insight.source_name}
            publishedAt={publishedValue}
            contentText={insight.content_text}
            primaryImage={insight.primary_image}
            collapsed={viewMode === 'focus-ai'}
            onToggle={() => {
              if (viewMode === 'focus-ai') {
                changeViewMode('split');
              } else {
                changeViewMode('focus-ai');
              }
            }}
          />
        </div>

      </div>
    </div>
  );
}
