import { defineStore } from "pinia";
import api from "@/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") as string | null,
    user: null as string | null,
  }),

  actions: {
    async login(username: string, password: string) {
        const params = new URLSearchParams();
        params.append("username", username);
        params.append("password", password);

        const res = await api.post("/auth/login", params, {
            headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            },
        });

        this.token = res.data.access_token;
        this.user = username;

        if (this.token) {
            localStorage.setItem("token", this.token);
        }
    },

    async register(username: string, password: string) {
      await api.post("/auth/register", { username, password });
      await this.login(username, password);
    },

    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("token");
    },
  },
});
