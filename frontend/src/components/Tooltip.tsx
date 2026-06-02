import { useCallback, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import styles from '../styles/detail.module.css';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom';
}

export default function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const tooltipId = useId();

  if (!content) {
    return <>{children}</>;
  }

  const show = useCallback(() => {
    timerRef.current = setTimeout(() => {
      if (!triggerRef.current) return;
      const rect = triggerRef.current.getBoundingClientRect();
      const x = rect.left + rect.width / 2;
      const y = position === 'top' ? rect.top : rect.bottom;
      setCoords({ x, y });
      setVisible(true);
    }, 200);
  }, [position]);

  const hide = useCallback(() => {
    clearTimeout(timerRef.current);
    setVisible(false);
  }, []);

  return (
    <>
      <span
        ref={triggerRef}
        className={styles.tooltipTrigger}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        aria-describedby={visible ? tooltipId : undefined}
      >
        {children}
      </span>
      {visible &&
        createPortal(
          <span
            id={tooltipId}
            role="tooltip"
            className={`${styles.tooltipPopup} ${position === 'bottom' ? styles.tooltipBottom : styles.tooltipTop}`}
            style={{ left: coords.x, top: coords.y }}
          >
            {content}
          </span>,
          document.body,
        )}
    </>
  );
}
