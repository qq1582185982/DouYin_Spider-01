<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Video, Search, Calendar, User, Eye, ChevronLeft, ChevronRight } from 'lucide-svelte';
  import api from '$lib/api';
  import { formatDate, formatNumber } from '$lib/utils';

  function formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
  import type { WorkInfo } from '$lib/types';

  let works: WorkInfo[] = [];
  let loading = false;
  let page = 1;
  let total = 0;
  let limit = 20; // 固定每页20个，让CSS Grid处理响应式
  let searchQuery = '';
  let error: string | null = null;
  let retryCount = 0;
  const maxRetries = 3;
  let jumpToPage = '';

  async function loadWorks() {
    loading = true;
    error = null;
    
    try {
      const response = await api.getWorks(page, limit, searchQuery);
      works = response.data.items;
      total = response.data.total;
      retryCount = 0;
    } catch (err: any) {
      console.error('Failed to load works:', err);
      error = err?.message || '加载失败，请稍后重试';
      
      // 自动重试
      if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(() => {
          if (error) {
            loadWorks();
          }
        }, 1000 * retryCount);
      }
    } finally {
      loading = false;
    }
  }
  
  function retryLoad() {
    retryCount = 0;
    loadWorks();
  }

  function nextPage() {
    if (page * limit < total) {
      page += 1;
      loadWorks();
    }
  }

  function prevPage() {
    if (page > 1) {
      page -= 1;
      loadWorks();
    }
  }

  function goToPage(targetPage: number) {
    if (targetPage >= 1 && targetPage <= Math.ceil(total / limit)) {
      page = targetPage;
      loadWorks();
    }
  }

  function jumpToSpecificPage() {
    const targetPage = parseInt(jumpToPage);
    if (!isNaN(targetPage) && targetPage >= 1 && targetPage <= Math.ceil(total / limit)) {
      page = targetPage;
      jumpToPage = '';
      loadWorks();
    }
  }

  function handleJumpKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      jumpToSpecificPage();
    }
  }

  onMount(() => {
    loadWorks();
  });

  let searchTimer: number | undefined;
  function handleSearch() {
    // 使用防抖，避免输入时频繁请求
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      page = 1; // 搜索时重置到第一页
      loadWorks();
    }, 500);
  }

  $: if (searchQuery !== undefined) {
    handleSearch();
  }

  $: totalPages = Math.ceil(total / limit);
  $: hasNextPage = page < totalPages;
  $: hasPrevPage = page > 1;
</script>

<svelte:head>
  <title>视频列表 - DouYin Spider</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
</svelte:head>

<style>
  /* 平滑滚动 */
  :global(html) {
    scroll-behavior: smooth;
  }
  
  /* 触摸反馈优化 */
  @media (hover: none) and (pointer: coarse) {
    :global(.hover\:scale-105) {
      transform: none !important;
    }
    
    :global(.hover\:shadow-lg) {
      box-shadow: none !important;
    }
  }
</style>

<div class="space-y-4 sm:space-y-6 px-2 sm:px-0">
  <div class="text-center sm:text-left">
    <h1 class="text-2xl sm:text-3xl font-bold">视频列表</h1>
    <p class="text-sm sm:text-base text-muted-foreground">查看所有已爬取的视频</p>
  </div>

  <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 items-start sm:items-center">
    <div class="flex-1 w-full sm:w-auto">
      <Input
        type="search"
        placeholder="搜索视频标题..."
        bind:value={searchQuery}
        class="w-full sm:max-w-md"
      />
    </div>
    <div class="text-xs text-muted-foreground flex items-center px-2 bg-gray-50 rounded">
      自适应布局
    </div>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="flex flex-col items-center gap-3">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="text-muted-foreground text-sm">加载中...</p>
        {#if retryCount > 0}
          <p class="text-xs text-muted-foreground">第 {retryCount} 次重试...</p>
        {/if}
      </div>
    </div>
  {:else if error}
    <Card>
      <CardContent class="flex flex-col items-center justify-center py-12">
        <div class="text-red-500 mb-4">
          <svg class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 18.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <p class="text-muted-foreground mb-4">{error}</p>
        <Button on:click={retryLoad} variant="outline" size="sm">
          重新加载
        </Button>
      </CardContent>
    </Card>
  {:else if works.length === 0}
    <Card>
      <CardContent class="flex flex-col items-center justify-center py-12">
        <Video class="mb-4 h-12 w-12 text-muted-foreground" />
        <p class="text-muted-foreground">暂无视频数据</p>
        <p class="text-xs text-muted-foreground mt-2">请先爬取一些视频内容</p>
      </CardContent>
    </Card>
  {:else}
    <!-- 使用 CSS Grid 布局，类似参考项目的实现 -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      {#each works as work}
        <div class="group flex h-full min-w-0 flex-col overflow-hidden transition-shadow hover:shadow-md cursor-pointer rounded-lg border bg-card text-card-foreground shadow-sm" 
              on:click={() => {
                console.log('Clicking work:', work.work_id);
                goto(`/video/${work.work_id}`);
              }}
              role="button"
              tabindex="0"
              on:keydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  goto(`/video/${work.work_id}`);
                }
              }}>
          {#if work.video?.cover}
            <div class="relative overflow-hidden rounded-t-lg">
              <img 
                src={work.video.cover} 
                alt={work.title}
                class="aspect-[9/16] w-full object-cover transition-transform duration-200 group-hover:scale-105"
                loading="lazy"
                decoding="async"
                on:error={(e) => {
                  const target = e.target as HTMLImageElement;
                  if (target) {
                    target.style.display = 'none';
                    const nextEl = target.nextElementSibling as HTMLElement;
                    nextEl?.classList.remove('hidden');
                  }
                }}
              />
              <div class="hidden aspect-[9/16] w-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                <Video class="h-8 w-8 text-gray-400" />
              </div>
              
              <!-- 类型标记 -->
              <div class="absolute left-2 top-2">
                {#if work.work_type === '图集'}
                  <div class="flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white">
                    <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
                    </svg>
                    图文
                  </div>
                {:else if work.work_type === '视频'}
                  <div class="flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white">
                    <Video class="h-3 w-3" />
                    {#if work.video?.duration}
                      {formatDuration(work.video.duration)}
                    {:else}
                      视频
                    {/if}
                  </div>
                {:else}
                  <div class="flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white">
                    <Video class="h-3 w-3" />
                    {work.work_type || '视频'}
                  </div>
                {/if}
              </div>
            </div>
          {:else}
            <div class="aspect-[9/16] bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center rounded-t-lg">
              <Video class="h-8 w-8 text-gray-400" />
            </div>
          {/if}
          
          <CardHeader class="flex-shrink-0 pb-3">
            <CardTitle class="line-clamp-2 min-w-0 flex-1 text-sm leading-tight font-medium" title={work.title || work.desc || '无标题'}>
              {work.title || work.desc || '无标题'}
            </CardTitle>
            <div class="text-muted-foreground flex min-w-0 items-center gap-1 text-sm">
              <User class="h-3 w-3 shrink-0" />
              <span class="min-w-0 truncate" title={work.author.nickname}>
                {work.author.nickname}
              </span>
            </div>
          </CardHeader>
          
          <CardContent class="flex min-w-0 flex-1 flex-col justify-end pt-0">
            <div class="space-y-2">
              <div class="text-muted-foreground flex justify-between text-xs">
                <span class="truncate">创建时间</span>
                <span class="shrink-0">{formatDate(work.create_time)}</span>
              </div>
              
              <div class="text-muted-foreground flex justify-between text-xs">
                <div class="flex items-center gap-1">
                  <Eye class="h-3 w-3" />
                  <span>{formatNumber(work.statistics.play_count)}</span>
                </div>
                <div class="flex items-center gap-1">
                  <span>❤️</span>
                  <span>{formatNumber(work.statistics.digg_count)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </div>
      {/each}
    </div>

    <!-- 分页组件 -->
    {#if totalPages > 1}
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="text-sm text-muted-foreground text-center sm:text-left">
          显示第 {(page - 1) * limit + 1} - {Math.min(page * limit, total)} 条，共 {total} 条
          <span class="ml-2 text-xs opacity-70">
            (每页 {limit} 个)
          </span>
        </div>
        
        <div class="flex flex-col sm:flex-row items-center gap-2">
          <!-- 分页按钮 -->
          <div class="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              on:click={prevPage} 
              disabled={!hasPrevPage}
            >
              <ChevronLeft class="h-4 w-4" />
              上一页
            </Button>
            
            <div class="flex items-center gap-1">
              {#each Array.from({length: Math.min(5, totalPages)}, (_, i) => {
                const start = Math.max(1, page - 2);
                const end = Math.min(totalPages, start + 4);
                return start + i;
              }).filter(p => p <= totalPages) as pageNum}
                <Button
                  variant={pageNum === page ? "default" : "outline"}
                  size="sm"
                  class="w-8 h-8 p-0"
                  on:click={() => goToPage(pageNum)}
                >
                  {pageNum}
                </Button>
              {/each}
            </div>
            
            <Button 
              variant="outline" 
              size="sm"
              on:click={nextPage} 
              disabled={!hasNextPage}
            >
              下一页
              <ChevronRight class="h-4 w-4" />
            </Button>
          </div>

          <!-- 跳转到指定页面 -->
          <div class="flex items-center gap-1 sm:ml-2 sm:pl-2 sm:border-l">
            <span class="text-xs text-muted-foreground whitespace-nowrap">跳转到</span>
            <Input
              type="number"
              bind:value={jumpToPage}
              placeholder="页码"
              class="w-16 h-8 text-center text-sm"
              min="1"
              max={totalPages}
              on:keydown={handleJumpKeydown}
            />
            <span class="text-xs text-muted-foreground whitespace-nowrap">页</span>
            <Button
              variant="outline"
              size="sm"
              class="h-8 px-2"
              on:click={jumpToSpecificPage}
              disabled={!jumpToPage || parseInt(jumpToPage) < 1 || parseInt(jumpToPage) > totalPages}
            >
              跳转
            </Button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>