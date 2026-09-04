import { defineStore } from 'pinia'
import type { ThemeMode } from '@/types/theme'

const STORAGE_KEY = 'theme'

function getSystemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: (localStorage.getItem(STORAGE_KEY) as ThemeMode | null) ?? 'system',
    systemDark: getSystemDark()
  }),

  getters: {
    isDark: (state): boolean => {
      if (state.mode === 'system') return state.systemDark
      return state.mode === 'dark'
    }
  },

  actions: {
    init() {
      window
        .matchMedia('(prefers-color-scheme: dark)')
        .addEventListener('change', (e) => {
          this.systemDark = e.matches
          this.apply()
        })
      this.apply()
    },

    setMode(mode: ThemeMode) {
      this.mode = mode
      localStorage.setItem(STORAGE_KEY, mode)
      this.apply()
    },

    cycle() {
      const order: ThemeMode[] = ['system', 'light', 'dark']
      const idx = (order.indexOf(this.mode) + 1) % order.length
      this.setMode(order[idx] ?? 'system')
    },

    apply() {
      document.documentElement.classList.toggle('dark', this.isDark)
    }
  }
})
