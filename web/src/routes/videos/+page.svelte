<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Video, Search, Calendar, User, Eye, ChevronLeft, ChevronRight } from 'lucide-svelte';
  import api from '$lib/api';
  import { formatDate, formatNumber } from '$lib/utils';
  import type { WorkInfo } from '$lib/types';

  let works: WorkInfo[] = [];
  let loading = false;
  let page = 1;
  let total = 0;
  let limit = 20;
  let searchQuery = '';
  let containerWidth = 0;
  let isMobile = false;
  let isTablet = false;
  let isLargeScreen = false;
  let error: string | null = null;
  let retryCount = 0;
  const maxRetries = 3;
  let currentCardsPerRow = 1;
  let currentRows = 1;

  async function loadWorks() {
    loading = true;
    error = null;
    
    try {
      const response = await api.getWorks(page, limit);
      works = response.data.items;
      total = response.data.total;
      retryCount = 0; // 重置重试计数
    } catch (err: any) {
      console.error('Failed to load works:', err);
      error = err?.message || '加载失败，请稍后重试';
      
      // 自动重试
      if (retryCount < maxRetries) {
        retryCount++;
        setTimeout(() => {
          if (error) { // 只有在仍然有错误时才重试
            loadWorks();
          }
        }, 1000 * retryCount); // 递增延时
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

  onMount(() => {
    updateLimit();
    loadWorks();
    
    // 防抖处理窗口大小变化
    let resizeTimeout: NodeJS.Timeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        updateLimit();
      }, 300); // 300ms防抖
    };
    
    // 方向改变监听（移动设备）
    const handleOrientationChange = () => {
      // 等待方向改变完成
      setTimeout(() => {
        updateLimit();
      }, 500);
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // 移动端触摸优化
    if ('ontouchstart' in window) {
      document.body.style.setProperty('-webkit-tap-highlight-color', 'transparent');
    }
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      clearTimeout(resizeTimeout);
    };
  });

  function updateDeviceType() {
    if (typeof window !== 'undefined') {
      const width = window.innerWidth;
      isMobile = width < 768;
      isTablet = width >= 768 && width < 1200;
      isLargeScreen = width >= 1200;
    }
  }

  function updateLimit() {
    if (typeof window !== 'undefined') {
      updateDeviceType();
      
      // 根据设备类型调整卡片尺寸和间距
      let cardWidth, containerPadding, cardHeight;
      
      if (isMobile) {
        // 移动端：2列布局，较小卡片
        cardWidth = 160; // 144px + 16px gap
        containerPadding = 32;
        cardHeight = 320; // 更紧凑的高度
      } else if (isTablet) {
        // 平板：3-4列布局
        cardWidth = 180; // 164px + 16px gap
        containerPadding = 64;
        cardHeight = 350;
      } else {
        // 桌面端：原有尺寸
        cardWidth = 208; // 192px + 16px gap
        containerPadding = 96;
        cardHeight = 392;
      }
      
      const availableWidth = window.innerWidth - containerPadding;
      let cardsPerRow = Math.max(1, Math.floor(availableWidth / cardWidth));
      
      // 移动端强制最多2列，平板最多4列
      if (isMobile) {
        cardsPerRow = Math.min(cardsPerRow, 2);
      } else if (isTablet) {
        cardsPerRow = Math.min(cardsPerRow, 4);
      }
      
      // 动态计算行数
      const headerHeight = isMobile ? 160 : (isTablet ? 180 : 200);
      const paginationHeight = isMobile ? 100 : 80;
      const availableHeight = window.innerHeight - headerHeight - paginationHeight;
      const maxRows = Math.max(1, Math.floor(availableHeight / cardHeight));
      
      // 智能计算最佳显示数量，确保布局均匀
      let newLimit;
      
      // 计算理想的行数范围
      const minRows = isMobile ? 1 : 2;
      const maxPossibleRows = Math.max(1, Math.floor(availableHeight / cardHeight));
      
      // 根据设备类型设置推荐行数
      let recommendedRows;
      if (isMobile) {
        recommendedRows = Math.min(4, maxPossibleRows); // 移动端最多4行
      } else if (isTablet) {
        recommendedRows = Math.min(4, maxPossibleRows); // 平板最多4行
      } else {
        recommendedRows = Math.min(5, maxPossibleRows); // 桌面端最多5行
      }
      
      // 确保至少有最小行数
      const actualRows = Math.max(minRows, recommendedRows);
      
      // 计算完整行的布局（优先显示完整行）
      newLimit = cardsPerRow * actualRows;
      
      // 设置设备相关的最小和最大值
      const minItems = isMobile ? cardsPerRow : cardsPerRow * 2; // 至少1行（移动端）或2行
      const maxItems = isMobile ? cardsPerRow * 4 : (isTablet ? cardsPerRow * 4 : cardsPerRow * 5);
      
      // 应用限制
      newLimit = Math.max(minItems, Math.min(maxItems, newLimit));
      
      // 确保结果是完整行的倍数（避免不均匀布局）
      newLimit = Math.floor(newLimit / cardsPerRow) * cardsPerRow;
      
      // 如果结果为0，至少显示一行
      if (newLimit === 0) {
        newLimit = cardsPerRow;
      }
      
      // 保存当前布局信息
      currentCardsPerRow = cardsPerRow;
      currentRows = Math.floor(newLimit / cardsPerRow);
      
      console.log('Layout calculation:', {
        deviceType: isMobile ? 'mobile' : (isTablet ? 'tablet' : 'desktop'),
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        availableWidth,
        availableHeight,
        cardWidth,
        cardHeight,
        cardsPerRow: currentCardsPerRow,
        rows: currentRows,
        newLimit,
        isCompleteGrid: newLimit % currentCardsPerRow === 0
      });
      
      if (newLimit !== limit) {
        const oldLimit = limit;
        limit = newLimit;
        page = 1; // 重置到第一页
        const completeRows = Math.floor(newLimit / cardsPerRow);
        console.log(`Limit changed from ${oldLimit} to ${newLimit} (${completeRows} complete rows of ${cardsPerRow} cards each)`);
        if (works.length > 0) {
          loadWorks(); // 重新加载数据
        }
      }
    }
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
  /* 移动端优化 */
  @media (max-width: 767px) {
    :global(.video-grid) {
      justify-content: center;
    }
  }
  
  /* 平滑滚动 */
  :global(html) {
    scroll-behavior: smooth;
  }
  
  /* 触摸反馈 */
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
        placeholder={isMobile ? "搜索视频..." : "搜索视频标题..."}
        bind:value={searchQuery}
        class="w-full sm:max-w-md"
      />
    </div>
    <div class="flex gap-2">
      <Button 
        variant="outline" 
        size="sm" 
        on:click={updateLimit}
        class="text-xs whitespace-nowrap"
      >
        {isMobile ? "调整" : "调整布局"}
      </Button>
      {#if !isMobile}
        <div class="text-xs text-muted-foreground flex items-center px-2 bg-gray-50 rounded">
          <span class="inline-block w-2 h-2 rounded-full mr-1"
                class:bg-green-500={isLargeScreen}
                class:bg-blue-500={isTablet}
                class:bg-orange-500={isMobile}></span>
          {isMobile ? "移动" : isTablet ? "平板" : "桌面"}模式
          <span class="ml-2 opacity-75">
            {currentCardsPerRow}列 × {currentRows}行
          </span>
        </div>
      {/if}
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
    <div class="flex flex-wrap gap-2 sm:gap-3 md:gap-4 video-grid"
         class:justify-center={isMobile}
         class:justify-start={!isMobile}>
      {#each works as work}
        <Card class="overflow-hidden flex-shrink-0 transition-all duration-200 hover:shadow-lg active:scale-95 {isMobile ? 'w-36' : isTablet ? 'w-40' : 'w-48'}">
          {#if work.video?.cover}
            <div class="bg-gray-100 flex items-center justify-center overflow-hidden rounded-t-lg {isMobile ? 'h-48' : isTablet ? 'h-52' : 'h-64'}">
              <img 
                src={work.video.cover} 
                alt={work.title}
                class="h-full w-full object-cover transition-transform duration-200 hover:scale-105"
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
              <div class="hidden h-full w-full flex items-center justify-center bg-gray-100">
                <Video class="h-8 w-8 text-gray-400" />
              </div>
            </div>
          {:else}
            <div class="bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center rounded-t-lg {isMobile ? 'h-48' : isTablet ? 'h-52' : 'h-64'}">
              <Video class="h-8 w-8 text-gray-400" />
            </div>
          {/if}
          <div class="flex-1">
            <CardHeader class="pb-2 px-3 pt-3">
              <CardTitle class="line-clamp-2 leading-tight font-medium {isMobile ? 'text-xs' : 'text-sm'}">
                {work.title || work.desc || '无标题'}
              </CardTitle>
            </CardHeader>
            <CardContent class="pt-0 px-3 pb-3">
              <div class="space-y-1.5 {isLargeScreen ? 'text-sm' : 'text-xs'}">
                <div class="flex items-center gap-1 text-muted-foreground">
                  <User class="h-3 w-3 flex-shrink-0" />
                  <span class="truncate text-xs font-medium">{work.author.nickname}</span>
                </div>
                {#if !isMobile}
                  <div class="flex items-center gap-1 text-muted-foreground">
                    <Calendar class="h-3 w-3 flex-shrink-0" />
                    <span class="text-xs">{formatDate(work.create_time)}</span>
                  </div>
                {/if}
                <div class="flex items-center justify-between text-muted-foreground text-xs">
                  <div class="flex items-center gap-1">
                    <Eye class="h-3 w-3" />
                    <span class="font-medium">{formatNumber(work.statistics.play_count)}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span>❤️</span>
                    <span class="font-medium">{formatNumber(work.statistics.digg_count)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </div>
        </Card>
      {/each}
    </div>

    <!-- 分页组件 -->
    {#if totalPages > 1}
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="text-sm text-muted-foreground text-center sm:text-left">
          {#if isMobile}
            <div class="text-xs">
              {page}/{totalPages} 页 · 共{total}条
            </div>
          {:else}
            显示第 {(page - 1) * limit + 1} - {Math.min(page * limit, total)} 条，共 {total} 条
            <span class="ml-2 text-xs opacity-70">
              (每页 {limit} 个)
            </span>
          {/if}
        </div>
        
        <div class="flex items-center gap-1 sm:gap-2">
          <Button 
            variant="outline" 
            size={isMobile ? "sm" : "sm"}
            on:click={prevPage} 
            disabled={!hasPrevPage}
            class={isMobile ? "px-2" : ""}
          >
            <ChevronLeft class="h-4 w-4" />
            {#if !isMobile}上一页{/if}
          </Button>
          
          <div class="flex items-center gap-0.5 sm:gap-1">
            {#each Array.from({length: Math.min(isMobile ? 3 : 5, totalPages)}, (_, i) => {
              const maxVisible = isMobile ? 3 : 5;
              const start = Math.max(1, page - Math.floor(maxVisible / 2));
              const end = Math.min(totalPages, start + maxVisible - 1);
              const adjustedStart = Math.max(1, end - maxVisible + 1);
              return adjustedStart + i;
            }).filter(p => p <= totalPages) as pageNum}
              <Button
                variant={pageNum === page ? "default" : "outline"}
                size="sm"
                class={`p-0 ${isMobile ? 'w-7 h-7 text-xs' : 'w-8 h-8'}`}
                on:click={() => goToPage(pageNum)}
              >
                {pageNum}
              </Button>
            {/each}
          </div>
          
          <Button 
            variant="outline" 
            size={isMobile ? "sm" : "sm"}
            on:click={nextPage} 
            disabled={!hasNextPage}
            class={isMobile ? "px-2" : ""}
          >
            {#if !isMobile}下一页{/if}
            <ChevronRight class="h-4 w-4" />
          </Button>
        </div>
      </div>
    {/if}
  {/if}
</div>