import styles from '../styles/detail.module.css';

interface OriginalArticlePanelProps {
  sourceUrl: string;
  title: string;
  sourceName: string;
  publishedAt: string;
  contentText?: string | null;
  primaryImage?: string | null;
  collapsed: boolean;
  onToggle: () => void;
}

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function getDomainFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return url;
  }
}

export default function OriginalArticlePanel({
  sourceUrl,
  title,
  sourceName,
  publishedAt,
  contentText,
  primaryImage,
  collapsed,
  onToggle,
}: OriginalArticlePanelProps) {
  const domain = getDomainFromUrl(sourceUrl);

  return (
    <div className={styles.detailCollapsible}>
      <button
        className={styles.detailCollapsibleHeader}
        onClick={onToggle}
        aria-expanded={!collapsed}
      >
        <span className={styles.detailCollapsibleHeaderLeft}>
          <span>📰</span>
          <span>Xem bài viết gốc</span>
        </span>
        <span
          className={`${styles.detailCollapsibleChevron} ${
            !collapsed ? styles.detailCollapsibleChevronOpen : ''
          }`}
        >
          ▼
        </span>
      </button>

      <div
        className={`${styles.detailCollapsibleContent} ${
          !collapsed ? styles.detailCollapsibleContentOpen : ''
        }`}
      >
        <div className={styles.detailCollapsibleInner}>
          {primaryImage && (
            <img
              src={primaryImage}
              alt={title}
              className={styles.originalCollapsibleImage}
            />
          )}

          <h3 className={styles.originalCollapsibleTitle}>{title}</h3>

          <div className={styles.originalCollapsibleMeta}>
            <span>{sourceName}</span>
            <span className={styles.metaDot}>·</span>
            <span>{formatDate(publishedAt)}</span>
            <span className={styles.metaDot}>·</span>
            <span>🌐 {domain}</span>
          </div>

          <a
            href={sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.originalCollapsibleReadMore}
          >
            Đọc bài gốc đầy đủ ↗
          </a>

          {contentText ? (
            <div className={styles.originalCollapsibleBody}>
              {contentText.split('\n').map((para, idx) => {
                const cleanPara = para.trim();
                if (!cleanPara) return null;
                return <p key={idx}>{cleanPara}</p>;
              })}
            </div>
          ) : (
            <div className={styles.originalNoContent}>
              <p>Không tìm thấy nội dung văn bản gốc đã thu thập.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
