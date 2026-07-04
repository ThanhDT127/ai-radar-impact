# Dark Mode Polish

## Scenarios

### WHEN dark mode is active
THEN KPI card colored backgrounds use subtle opacity (≤0.08 alpha)
AND card surfaces have consistent contrast
AND all badge text is readable on dark surface
AND no warm-tone sepia colors appear (rgba(49,35,18,...) or rgba(184,77,30,...))

### WHEN filter chips are rendered in dark mode
THEN chip backgrounds use cool indigo-based colors
AND NOT warm sepia tones
AND active chip has visible contrast against surface
