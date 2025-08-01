<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Video, Search, Calendar, User, Eye } from 'lucide-svelte';
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

  onMount(() => {
    loadWorks();
  });
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
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each works as work}
        <Card class="overflow-hidden">
          {#if work.video?.cover}
            <img 
              src={work.video.cover} 
              alt={work.title}
              class="h-48 w-full object-cover"
            />
          {/if}
          <CardHeader>
            <CardTitle class="line-clamp-2 text-base">{work.title || work.desc}</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2 text-sm">
              <div class="flex items-center gap-2 text-muted-foreground">
                <User class="h-4 w-4" />
                <span>{work.author.nickname}</span>
              </div>
              <div class="flex items-center gap-2 text-muted-foreground">
                <Calendar class="h-4 w-4" />
                <span>{formatDate(work.create_time)}</span>
              </div>
              <div class="flex items-center gap-4 text-muted-foreground">
                <div class="flex items-center gap-1">
                  <Eye class="h-4 w-4" />
                  <span>{formatNumber(work.statistics.play_count)}</span>
                </div>
                <div class="flex items-center gap-1">
                  <span>❤️</span>
                  <span>{formatNumber(work.statistics.digg_count)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      {/each}
    </div>
  {/if}
</div>