<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-950 px-4 transition-colors">
    <div class="w-full max-w-md bg-white dark:bg-gray-900 shadow-lg dark:shadow-none dark:border dark:border-gray-800 rounded-xl p-8">
      <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 text-center mb-6">
        {{ isRegister ? "Регистрация" : "Вход в систему" }}
      </h2>

      <form @submit.prevent="submit" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Username
          </label>
          <input
            v-model="username"
            type="text"
            placeholder="Введите логин"
            class="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   focus:border-blue-500 transition placeholder-gray-400 dark:placeholder-gray-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Password
          </label>
          <input
            v-model="password"
            type="password"
            :placeholder="isRegister ? 'Минимум 8 символов' : 'Введите пароль'"
            class="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   focus:border-blue-500 transition placeholder-gray-400 dark:placeholder-gray-500"
          />
        </div>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

        <button
          type="submit"
          class="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg
                 hover:bg-blue-700 transition active:scale-[0.98]"
        >
          {{ isRegister ? "Создать аккаунт" : "Войти" }}
        </button>
      </form>

      <button
        @click="toggleMode"
        class="w-full mt-4 text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        {{ isRegister ? "Уже есть аккаунт? Войти" : "Нет аккаунта? Зарегистрироваться" }}
      </button>

      <p class="text-center text-sm text-gray-500 dark:text-gray-500 mt-4">
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
const error = ref("");
const isRegister = ref(false);
const auth = useAuthStore();

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  error.value = "";
};

const submit = async () => {
  error.value = "";
  try {
    if (isRegister.value) {
      await auth.register(username.value, password.value);
    } else {
      await auth.login(username.value, password.value);
    }
    window.location.href = "/";
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    if (Array.isArray(detail)) {
      error.value = detail[0]?.msg ?? "Ошибка валидации";
    } else {
      error.value = detail ?? (isRegister.value ? "Не удалось зарегистрироваться" : "Неверный логин или пароль");
    }
  }
};
</script>
