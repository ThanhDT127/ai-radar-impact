# Detail Page Split View Restore

## Scenarios

### WHEN user opens InsightDetail page
THEN layout is 50/50 split (1fr 1fr grid)
AND left column shows: phân tích AI (summary, bullets, recommendations, risks)
AND right column shows: bài viết gốc (luôn hiển thị, không collapsible)
AND NO sticky sidebar with score bars

### WHEN user views detail page on mobile (≤1024px)
THEN layout collapses to single column
AND original article appears below AI analysis

### WHEN detail page renders bullets section
THEN shows exactly up to 5 bullet points max
AND bullets are sourced from: signal, so_what, why_it_matters, then summary_short sentences

### WHEN thumbnail/image available for card on dashboard
THEN always show thumbnail area (120×84px)
AND if image fails to load, show placeholder gradient with 📰 icon
AND NOT hide the thumbnail area entirely
