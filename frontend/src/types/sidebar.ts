// types/sidebar.ts

export type SidebarStatus = "recent" | "passed" | "blocked" | "active" | "resolved" | "watching" | string

export interface SidebarItem {
  id: string

  title: string
  subtitle?: string
  description?: string

  status: SidebarStatus
  statusLabel?: string

  searchText: string

  meta?: {
    label: string
    value: string | number
  }[]

  badges?: {
    label: string
    type?: "success" | "warning" | "danger" | "neutral"
  }[]

  blockedAt?: string | null

  raw?: unknown
}

export interface SidebarTab {
  key: string
  label: string
}