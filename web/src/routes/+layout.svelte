<script lang="ts">
  import '../app.css';
  import AppSidebar from '$lib/components/app-sidebar.svelte';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { Menu, X } from 'lucide-svelte';
  import api from '$lib/api';

  let isInitialized = false;
  let hasValidCookie = false;
  let isMobileMenuOpen = false;
  let isMobile = false;
  
  function updateMobileState() {
    if (typeof window !== 'undefined') {
      isMobile = window.innerWidth < 768;
      if (!isMobile) {
        isMobileMenuOpen = false;
      }
    }
  }
  
  function toggleMobileMenu() {
    isMobileMenuOpen = !isMobileMenuOpen;
    updateBodyClass();
  }
  
  function closeMobileMenu() {
    isMobileMenuOpen = false;
    updateBodyClass();
  }
  
  function updateBodyClass() {
    if (typeof document !== 'undefined') {
      if (isMobile && isMobileMenuOpen) {
        document.body.classList.add('mobile-menu-open');
      } else {
        document.body.classList.remove('mobile-menu-open');
      }
    }
  }

  onMount(() => {
    async function init() {
      const cookie = api.getCookie();
      if (cookie) {
        try {
          const response = await api.validateCookie(cookie);
          hasValidCookie = response.data;
        } catch (error) {
          console.error('Failed to validate cookie:', error);
        }
      }
      
      updateMobileState();
      updateBodyClass();
      isInitialized = true;
    }
    
    init();
    
    const handleResize = () => {
      const wasMobile = isMobile;
      updateMobileState();
      if (wasMobile !== isMobile) {
        updateBodyClass();
      }
    };
    
    const handleOrientationChange = () => {
      setTimeout(() => {
        updateMobileState();
        updateBodyClass();
      }, 100);
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      document.body.classList.remove('mobile-menu-open');
    };
  });
</script>

<svelte:head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
</svelte:head>

<style>
  /* 移动端优化 */
  @media (max-width: 767px) {
    :global(body) {
      overflow-x: hidden;
    }
    
    :global(.mobile-menu-open) {
      overflow: hidden;
    }
  }
  
  /* 平滑滚动 */
  :global(html) {
    scroll-behavior: smooth;
  }
  
  /* 触摸反馈优化 */
  @media (hover: none) and (pointer: coarse) {
    :global(.hover\:bg-secondary\/50:hover) {
      background-color: rgba(var(--secondary), 0.5) !important;
    }
  }
</style>

<!-- 防止滚动穿透 -->
<svelte:window on:scroll={(e) => isMobile && isMobileMenuOpen && e.preventDefault()} />

<div class="flex h-screen overflow-hidden {isMobile && isMobileMenuOpen ? 'overflow-hidden' : ''}">
  {#if isInitialized}
    <!-- 移动端菜单按钮 -->
    {#if isMobile}
      <div class="fixed top-0 left-0 right-0 z-50 flex h-16 items-center justify-between bg-background border-b px-4">
        <h2 class="text-lg font-semibold">DouYin Spider</h2>
        <button
          on:click={toggleMobileMenu}
          class="p-2 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="切换菜单"
        >
          {#if isMobileMenuOpen}
            <X class="h-6 w-6" />
          {:else}
            <Menu class="h-6 w-6" />
          {/if}
        </button>
      </div>
    {/if}
    
    <!-- 遮罩层 -->
    {#if isMobile && isMobileMenuOpen}
      <div 
        class="fixed inset-0 z-40 bg-black/50 transition-opacity" 
        on:click={closeMobileMenu}
        on:keydown={(e) => e.key === 'Escape' && closeMobileMenu()}
        role="button"
        tabindex="0"
      ></div>
    {/if}
    
    <!-- 侧边栏 -->
    <AppSidebar 
      {isMobile} 
      {isMobileMenuOpen} 
      on:close={closeMobileMenu}
    />
    
    <!-- 主内容区 -->
    <main class="flex-1 overflow-auto {isMobile ? 'pt-16' : ''}">
      <div class="container mx-auto p-4 sm:p-6">
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