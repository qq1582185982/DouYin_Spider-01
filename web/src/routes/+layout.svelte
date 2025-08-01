<script lang="ts">
  import '../app.css';
  import AppSidebar from '$lib/components/app-sidebar.svelte';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import api from '$lib/api';

  let isInitialized = false;
  let hasValidCookie = false;

  onMount(async () => {
    const cookie = api.getCookie();
    if (cookie) {
      try {
        const response = await api.validateCookie(cookie);
        hasValidCookie = response.data;
      } catch (error) {
        console.error('Failed to validate cookie:', error);
      }
    }
    isInitialized = true;
  });
</script>

<div class="flex h-screen overflow-hidden">
  {#if isInitialized}
    <AppSidebar />
    <main class="flex-1 overflow-auto">
      <div class="container mx-auto p-6">
        {#if !hasValidCookie && !$page.url.pathname.includes('/settings')}
          <div class="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-yellow-800">
            <p class="text-sm">
              请先在 <a href="/settings" class="font-medium underline">设置页面</a> 配置抖音Cookie
            </p>
          </div>
        {/if}
        <slot />
      </div>
    </main>
  {/if}
</div>