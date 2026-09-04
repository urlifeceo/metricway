export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '—'
  return value.toLocaleString('ru-RU')
}

export function formatRatio(value: number | undefined | null): string {
  if (value === undefined || value === null || value === 0) return '—'
  return `${value}:1`
}

export function calcDelta(
  current: number | undefined | null,
  previous: number | undefined | null
): number | null {
  if (
    current === undefined ||
    current === null ||
    previous === undefined ||
    previous === null
  ) {
    return null
  }
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return null
  if (previous === 0) return null
  return ((current - previous) / Math.abs(previous)) * 100
}
