<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="w-full max-w-md bg-white shadow-lg rounded-xl p-8">
      <h2 class="text-2xl font-bold text-gray-800 text-center mb-6">
        Вход в систему
      </h2>

      <form @submit.prevent="submit" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            v-model="username"
            type="text"
            placeholder="Введите логин"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   focus:border-blue-500 transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            v-model="password"
            type="password"
            placeholder="Введите пароль"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   focus:border-blue-500 transition"
          />
        </div>

        <button
          type="submit"
          class="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg
                 hover:bg-blue-700 transition active:scale-[0.98]"
        >
          Войти
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-4">
        © Metric Dashboard
      </p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";

const username = ref("");
const password = ref("");
const auth = useAuthStore();

const submit = async () => {
  try {
    await auth.login(username.value, password.value);
    window.location.href = "/";
  } catch {
    alert("Invalid credentials");
  }
};
</script>
