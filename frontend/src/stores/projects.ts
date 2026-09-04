import { defineStore } from 'pinia'
import api from '@/api'
import type { Project } from '@/types/projects'

const TOKEN_KEY = 'project_token'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [] as Project[],
    currentToken: localStorage.getItem(TOKEN_KEY),
    loading: false,
    showCreateModal: false,
    createdProject: null as Project | null,
    error: null as string | null
  }),

  getters: {
    currentProject(state): Project | null {
      return state.projects.find(p => p.project_token === state.currentToken) ?? null
    }
  },

  actions: {
    async fetchProjects() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/projects')
        this.projects = res.data
        if (this.currentToken && !this.projects.some(p => p.project_token === this.currentToken)) {
          this.currentToken = null
          localStorage.removeItem(TOKEN_KEY)
        }
        if (!this.currentToken && this.projects.length) {
          const first = this.projects[0]
          if (first) this.selectProject(first.project_token)
        }
      } catch {
        this.error = 'Failed to load projects'
      } finally {
        this.loading = false
      }
    },

    async createProject(name: string) {
      this.error = null
      try {
        const res = await api.post('/projects', { name })
        this.projects.push(res.data)
        this.createdProject = res.data
        this.selectProject(res.data.project_token)
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        this.error = detail ?? 'Failed to create project'
      }
    },

    selectProject(token: string) {
      this.currentToken = token
      this.createdProject = null
      localStorage.setItem(TOKEN_KEY, token)
    },

    reset() {
      this.projects = []
      this.currentToken = null
      this.createdProject = null
      localStorage.removeItem(TOKEN_KEY)
    }
  }
})
