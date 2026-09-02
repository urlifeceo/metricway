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

        if (this.token) {
            localStorage.setItem("token", this.token);
        }
    },

    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("token");
    },
  },
});
