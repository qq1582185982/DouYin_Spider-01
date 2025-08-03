<script lang="ts">
  import { 
    Home, 
    Users, 
    Video, 
    Link, 
    Settings,
    FolderDown,
    Bell,
    Radar
  } from 'lucide-svelte';
  import { page } from '$app/stores';
  import { cn } from '$lib/utils';
  import { createEventDispatcher } from 'svelte';
  
  export let isMobile = false;
  export let isMobileMenuOpen = false;
  
  const dispatch = createEventDispatcher();
  
  function handleLinkClick() {
    if (isMobile) {
      dispatch('close');
    }
  }

  const menuItems = [
    {
      title: '总览',
      items: [
        { icon: Home, label: '仪表盘', href: '/' },
      ]
    },
    {
      title: '爬取功能',
      items: [
        { icon: Users, label: '用户爬取', href: '/spider/user' },
        { icon: Link, label: '链接下载', href: '/spider/search' },
        { icon: Bell, label: '订阅管理', href: '/subscriptions' },
        { icon: Radar, label: '扫描管理', href: '/scan' }
      ]
    },
    {
      title: '数据管理',
      items: [
        { icon: Video, label: '视频列表', href: '/videos' },
        { icon: FolderDown, label: '下载管理', href: '/downloads' }
      ]
    },
    {
      title: '系统',
      items: [
        { icon: Settings, label: '设置', href: '/settings' }
      ]
    }
  ];
</script>

<aside class="{cn(
  'bg-background border-r transition-transform duration-300 ease-in-out',
  isMobile 
    ? 'fixed top-0 left-0 z-50 h-full w-64 transform' + (isMobileMenuOpen ? ' translate-x-0' : ' -translate-x-full')
    : 'w-64 relative'
)}">
  <!-- 桥面端标题栏 -->
  {#if !isMobile}
    <div class="flex h-16 items-center border-b px-6">
      <h2 class="text-lg font-semibold">DouYin Spider</h2>
    </div>
  {/if}
  
  <!-- 移动端标题栏 -->
  {#if isMobile}
    <div class="flex h-16 items-center border-b px-6">
      <h2 class="text-lg font-semibold">DouYin Spider</h2>
    </div>
  {/if}
  
  <nav class="flex-1 space-y-4 sm:space-y-6 p-3 sm:p-4 overflow-y-auto h-[calc(100vh-4rem)]">
    {#each menuItems as group}
      <div>
        <h3 class="mb-2 px-2 text-xs font-medium uppercase text-muted-foreground">
          {group.title}
        </h3>
        <div class="space-y-1">
          {#each group.items as item}
            <a
              href={item.href}
              on:click={handleLinkClick}
              class={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors active:scale-95',
                $page.url.pathname === item.href
                  ? 'bg-secondary text-secondary-foreground'
                  : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
              )}
            >
              <svelte:component this={item.icon} class="h-4 w-4 flex-shrink-0" />
              <span class="truncate">{item.label}</span>
            </a>
          {/each}
        </div>
      </div>
    {/each}
    
    <!-- 移动端底部间距 -->
    {#if isMobile}
      <div class="h-16"></div>
    {/if}
  </nav>
</aside>