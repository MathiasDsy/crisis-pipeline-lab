type Cell = string | number | boolean | null | undefined

function escapeCell(value: Cell): string {
  const s = value === null || value === undefined ? '' : String(value)
  // Quote if the value contains a comma, quote, or newline.
  if (/[",\n]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

export function buildCsv(headers: string[], rows: Cell[][]): string {
  const lines = [headers.map(escapeCell).join(',')]
  for (const row of rows) {
    lines.push(row.map(escapeCell).join(','))
  }
  return lines.join('\n')
}

export function downloadCsv(filename: string, headers: string[], rows: Cell[][]): void {
  const csv  = buildCsv(headers, rows)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url  = URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  URL.revokeObjectURL(url)
}
