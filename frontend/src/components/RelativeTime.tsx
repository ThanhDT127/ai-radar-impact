interface RelativeTimeProps {
  value: string;
  showAbsolute?: boolean;
}

function formatAbsoluteDate(value: string): string {
  return new Date(value).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function formatRelativeTime(value: string): string {
  const now = Date.now();
  const then = new Date(value).getTime();
  const diffMs = Math.max(0, now - then);
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 60) return `${Math.max(1, diffMin)} phút trước`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} giờ trước`;

  const diffDay = Math.floor(diffHr / 24);
  if (diffDay === 1) return 'Hôm qua';
  if (diffDay < 7) return `${diffDay} ngày trước`;

  return formatAbsoluteDate(value);
}

export default function RelativeTime({ value, showAbsolute = true }: RelativeTimeProps) {
  const relative = formatRelativeTime(value);
  const absolute = formatAbsoluteDate(value);

  if (!showAbsolute || relative === absolute) {
    return <>{relative}</>;
  }

  return <>{relative} · {absolute}</>;
}
