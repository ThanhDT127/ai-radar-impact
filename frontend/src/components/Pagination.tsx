import { useEffect, useState } from 'react';
import styles from '../styles/pagination.module.css';

interface PaginationProps {
  page: number;
  total: number;
  size: number;
  onPageChange: (newPage: number) => void;
  variant?: 'default' | 'compact';
}

function buildPages(currentPage: number, totalPages: number): Array<number | 'ellipsis'> {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set<number>([1, totalPages, currentPage, currentPage - 1, currentPage + 1]);

  if (currentPage <= 3) {
    pages.add(2);
    pages.add(3);
    pages.add(4);
  }

  if (currentPage >= totalPages - 2) {
    pages.add(totalPages - 1);
    pages.add(totalPages - 2);
    pages.add(totalPages - 3);
  }

  const ordered = Array.from(pages).filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
  const result: Array<number | 'ellipsis'> = [];

  for (let index = 0; index < ordered.length; index += 1) {
    const page = ordered[index];
    const previous = ordered[index - 1];

    if (previous && page - previous > 1) {
      result.push('ellipsis');
    }

    result.push(page);
  }

  return result;
}

export default function Pagination({ page, total, size, onPageChange, variant = 'default' }: PaginationProps) {
  const totalPages = Math.ceil(total / size);
  const [jumpPage, setJumpPage] = useState(String(page));

  useEffect(() => {
    setJumpPage(String(page));
  }, [page]);

  if (totalPages <= 1) return null;

  const pages = buildPages(page, totalPages);

  const submitJump = () => {
    const parsed = Number.parseInt(jumpPage, 10);
    if (Number.isNaN(parsed)) {
      setJumpPage(String(page));
      return;
    }

    const nextPage = Math.min(totalPages, Math.max(1, parsed));
    setJumpPage(String(nextPage));

    if (nextPage !== page) {
      onPageChange(nextPage);
    }
  };

  if (variant === 'compact') {
    return (
      <div className={styles.paginationCompact}>
        <button
          className={styles.paginationBtnCompact}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          ←
        </button>
        <span className={styles.paginationInfoCompact}>
          {page} / {totalPages}
        </span>
        <button
          className={styles.paginationBtnCompact}
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          →
        </button>
      </div>
    );
  }

  return (
    <div className={styles.paginationShell}>
      <div className={styles.pagination}>
        <button
          className={styles.paginationBtn}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          ← Trước
        </button>

        <div className={styles.paginationPages}>
          {pages.map((item, index) => (
            item === 'ellipsis' ? (
              <span key={`ellipsis-${index}`} className={styles.paginationEllipsis}>…</span>
            ) : (
              <button
                key={item}
                type="button"
                className={item === page ? styles.paginationPageActive : styles.paginationPage}
                onClick={() => onPageChange(item)}
                aria-current={item === page ? 'page' : undefined}
              >
                {item}
              </button>
            )
          ))}
        </div>

        <button
          className={styles.paginationBtn}
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          Sau →
        </button>
      </div>

      <div className={styles.paginationJump}>
        <span className={styles.paginationInfo}>Trang {page} / {totalPages}</span>
        <label className={styles.paginationJumpBox}>
          <span>Tới trang</span>
          <input
            className={styles.paginationInput}
            inputMode="numeric"
            pattern="[0-9]*"
            value={jumpPage}
            onChange={(event) => setJumpPage(event.target.value.replace(/\D/g, ''))}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                submitJump();
              }
            }}
          />
        </label>
        <button type="button" className={styles.paginationGoBtn} onClick={submitJump}>
          Đi
        </button>
      </div>
    </div>
  );
}
