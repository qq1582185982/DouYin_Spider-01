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

  async function loadWorks() {
    loading = true;
    try {
      const response = await api.getWorks(page, limit);
      works = response.data.items;
      total = response.data.total;
    } catch (error) {
      console.error('Failed to load works:', error);
    } finally {
      loading = false;
    }
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
    loadWorks();
  });

  $: totalPages = Math.ceil(total / limit);
  $: hasNextPage = page < totalPages;
  $: hasPrevPage = page > 1;
</script>

<svelte:head>
  <title>视频列表 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">视频列表</h1>
    <p class="text-muted-foreground">查看所有已爬取的视频</p>
  </div>

  <div class="flex gap-4">
    <div class="flex-1">
      <Input
        type="search"
        placeholder="搜索视频标题..."
        bind:value={searchQuery}
        class="max-w-md"
      />
    </div>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <p class="text-muted-foreground">加载中...</p>
    </div>
  {:else if works.length === 0}
    <Card>
      <CardContent class="flex flex-col items-center justify-center py-12">
        <Video class="mb-4 h-12 w-12 text-muted-foreground" />
        <p class="text-muted-foreground">暂无视频数据</p>
      </CardContent>
    </Card>
  {:else}
    <div class="flex flex-wrap gap-4 justify-start">
      {#each works as work}
        <Card class="overflow-hidden flex-shrink-0">
          {#if work.video?.cover}
            <div class="h-64 w-48 bg-gray-100 flex items-center justify-center overflow-hidden">
              <img 
                src={work.video.cover} 
                alt={work.title}
                class="h-full w-full object-cover"
              />
            </div>
          {/if}
          <div class="w-48">
            <CardHeader class="pb-2">
              <CardTitle class="line-clamp-2 text-sm leading-tight">{work.title || work.desc || '无标题'}</CardTitle>
            </CardHeader>
            <CardContent class="pt-0">
              <div class="space-y-2 text-xs">
                <div class="flex items-center gap-1 text-muted-foreground">
                  <User class="h-3 w-3" />
                  <span class="truncate">{work.author.nickname}</span>
                </div>
                <div class="flex items-center gap-1 text-muted-foreground">
                  <Calendar class="h-3 w-3" />
                  <span>{formatDate(work.create_time)}</span>
                </div>
                <div class="flex items-center justify-between text-muted-foreground">
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
        </Card>
      {/each}
    </div>

    <!-- 分页组件 -->
    {#if totalPages > 1}
      <div class="flex items-center justify-between">
        <div class="text-sm text-muted-foreground">
          显示第 {(page - 1) * limit + 1} - {Math.min(page * limit, total)} 条，共 {total} 条
        </div>
        
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
      </div>
    {/if}
  {/if}
</div>