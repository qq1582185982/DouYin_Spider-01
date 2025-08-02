<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { 
    ArrowLeft, 
    ExternalLink, 
    User, 
    Calendar, 
    Eye, 
    Heart, 
    MessageCircle, 
    Share2, 
    Play,
    Download,
    RefreshCw
  } from 'lucide-svelte';
  import api from '$lib/api';
  import { formatDate, formatNumber } from '$lib/utils';
  import type { WorkInfo } from '$lib/types';

  let videoData: WorkInfo | null = null;
  let loading = false;
  let error: string | null = null;
  let isMobile = false;
  let innerWidth = 0;

  $: isMobile = innerWidth < 768;

  async function loadVideoDetail() {
    const workId = $page.params.id;
    if (!workId) {
      error = '无效的视频ID';
      toast.error('无效的视频ID');
      return;
    }

    loading = true;
    error = null;

    try {
      // 使用新的 API 方法获取单个作品详情
      const response = await api.getWork(workId);
      videoData = response.data;
    } catch (err: any) {
      console.error('加载视频详情失败:', err);
      error = err?.message || '加载失败，请稍后重试';
      toast.error('加载视频详情失败', {
        description: err?.message
      });
    } finally {
      loading = false;
    }
  }

  function goBack() {
    goto('/videos');
  }

  function openOriginalVideo() {
    if (videoData?.work_url) {
      window.open(videoData.work_url, '_blank');
    }
  }

  onMount(() => {
    loadVideoDetail();
  });

  // 监听路由参数变化
  $: if ($page.params.id) {
    loadVideoDetail();
  }
</script>

<svelte:head>
  <title>{videoData?.title || '视频详情'} - DouYin Spider</title>
</svelte:head>

<svelte:window bind:innerWidth />

<div class="min-h-screen bg-gray-50">
  <!-- 顶部导航栏 -->
  <div class="sticky top-0 z-10 bg-white border-b">
    <div class="container mx-auto px-4 py-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="sm" on:click={goBack}>
          <ArrowLeft class="h-4 w-4" />
          返回列表
        </Button>
        <div class="h-4 border-l border-gray-300"></div>
        <h1 class="text-lg font-semibold truncate">
          {videoData?.title || '视频详情'}
        </h1>
      </div>
    </div>
  </div>

  <div class="container mx-auto px-4 py-6">
    {#if loading}
      <div class="flex items-center justify-center py-16">
        <div class="flex flex-col items-center gap-3">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p class="text-muted-foreground text-sm">加载中...</p>
        </div>
      </div>
    {:else if error}
      <div class="flex items-center justify-center py-16">
        <Card>
          <CardContent class="flex flex-col items-center justify-center py-12">
            <div class="text-red-500 mb-4">
              <svg class="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 18.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <p class="text-muted-foreground mb-4">{error}</p>
            <Button on:click={goBack} variant="outline" size="sm">
              返回列表
            </Button>
          </CardContent>
        </Card>
      </div>
    {:else if videoData}
      <!-- 主要内容区域 -->
      <div class="grid gap-6 {isMobile ? 'grid-cols-1' : 'lg:grid-cols-3'}">
        <!-- 左侧：视频信息和封面 -->
        <div class="{isMobile ? '' : 'lg:col-span-2'}">
          <Card class="overflow-hidden">
            <div class="relative">
              {#if videoData.video?.cover}
                <div class="aspect-[9/16] max-h-96 bg-gray-100 flex items-center justify-center overflow-hidden">
                  <img 
                    src={videoData.video.cover} 
                    alt={videoData.title}
                    class="h-full w-full object-cover"
                    loading="lazy"
                  />
                </div>
                <!-- 播放按钮覆盖层 -->
                <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity">
                  <Button size="lg" class="rounded-full">
                    <Play class="h-6 w-6 mr-2" />
                    播放视频
                  </Button>
                </div>
              {:else}
                <div class="aspect-[9/16] max-h-96 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                  <Play class="h-16 w-16 text-gray-400" />
                </div>
              {/if}
            </div>

            <CardHeader>
              <div class="flex items-start justify-between gap-4">
                <CardTitle class="text-xl leading-tight">
                  {videoData.title || videoData.desc || '无标题'}
                </CardTitle>
                <Badge variant="secondary">
                  {videoData.work_type}
                </Badge>
              </div>
            </CardHeader>

            <CardContent class="space-y-4">
              <!-- 作者信息 -->
              <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div class="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                  {videoData.author.nickname.charAt(0)}
                </div>
                <div class="flex-1">
                  <h3 class="font-medium">{videoData.author.nickname}</h3>
                  <p class="text-sm text-muted-foreground">
                    {videoData.author.follower_count ? `${formatNumber(videoData.author.follower_count)} 粉丝` : '抖音用户'}
                  </p>
                </div>
              </div>

              <!-- 视频描述 -->
              {#if videoData.desc && videoData.desc !== videoData.title}
                <div class="space-y-2">
                  <h4 class="font-medium">视频描述</h4>
                  <p class="text-sm text-muted-foreground leading-relaxed">
                    {videoData.desc}
                  </p>
                </div>
              {/if}

              <!-- 话题标签 -->
              {#if videoData.topics && videoData.topics.length > 0}
                <div class="space-y-2">
                  <h4 class="font-medium">相关话题</h4>
                  <div class="flex flex-wrap gap-2">
                    {#each videoData.topics as topic}
                      <Badge variant="outline" class="text-xs">
                        #{topic}
                      </Badge>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- 操作按钮 -->
              <div class="flex gap-2 pt-4 border-t">
                <Button on:click={openOriginalVideo} class="flex-1">
                  <ExternalLink class="h-4 w-4 mr-2" />
                  在抖音中打开
                </Button>
                <Button variant="outline" class="flex-1">
                  <Download class="h-4 w-4 mr-2" />
                  重新下载
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- 右侧：统计信息和详细数据 -->
        <div class="space-y-6">
          <!-- 数据统计卡片 -->
          <Card>
            <CardHeader>
              <CardTitle class="text-lg">数据统计</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="text-center p-3 bg-blue-50 rounded-lg">
                  <div class="flex items-center justify-center gap-1 text-blue-600 mb-1">
                    <Eye class="h-4 w-4" />
                    <span class="text-xs">播放量</span>
                  </div>
                  <div class="font-semibold text-blue-700">
                    {formatNumber(videoData.statistics.play_count)}
                  </div>
                </div>

                <div class="text-center p-3 bg-red-50 rounded-lg">
                  <div class="flex items-center justify-center gap-1 text-red-600 mb-1">
                    <Heart class="h-4 w-4" />
                    <span class="text-xs">点赞量</span>
                  </div>
                  <div class="font-semibold text-red-700">
                    {formatNumber(videoData.statistics.digg_count)}
                  </div>
                </div>

                <div class="text-center p-3 bg-green-50 rounded-lg">
                  <div class="flex items-center justify-center gap-1 text-green-600 mb-1">
                    <MessageCircle class="h-4 w-4" />
                    <span class="text-xs">评论量</span>
                  </div>
                  <div class="font-semibold text-green-700">
                    {formatNumber(videoData.statistics.comment_count)}
                  </div>
                </div>

                <div class="text-center p-3 bg-purple-50 rounded-lg">
                  <div class="flex items-center justify-center gap-1 text-purple-600 mb-1">
                    <Share2 class="h-4 w-4" />
                    <span class="text-xs">分享量</span>
                  </div>
                  <div class="font-semibold text-purple-700">
                    {formatNumber(videoData.statistics.share_count)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- 基本信息卡片 -->
          <Card>
            <CardHeader>
              <CardTitle class="text-lg">基本信息</CardTitle>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="flex items-center gap-2 text-sm">
                <Calendar class="h-4 w-4 text-muted-foreground" />
                <span class="text-muted-foreground">发布时间：</span>
                <span>{formatDate(videoData.create_time)}</span>
              </div>

              <div class="flex items-center gap-2 text-sm">
                <Download class="h-4 w-4 text-muted-foreground" />
                <span class="text-muted-foreground">下载时间：</span>
                <span>{videoData.download_time ? formatDate(new Date(videoData.download_time).getTime()) : '未知'}</span>
              </div>

              {#if videoData.file_size}
                <div class="flex items-center gap-2 text-sm">
                  <RefreshCw class="h-4 w-4 text-muted-foreground" />
                  <span class="text-muted-foreground">文件大小：</span>
                  <span>{(videoData.file_size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
              {/if}

              <div class="flex items-center gap-2 text-sm">
                <Badge variant={videoData.is_complete ? "default" : "destructive"} class="text-xs">
                  {videoData.is_complete ? "下载完成" : "下载中"}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <!-- 技术信息卡片 -->
          <Card>
            <CardHeader>
              <CardTitle class="text-lg">技术信息</CardTitle>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="space-y-2">
                <div class="text-sm">
                  <span class="text-muted-foreground">作品ID：</span>
                  <code class="bg-gray-100 px-2 py-1 rounded text-xs">{videoData.work_id}</code>
                </div>
                
                <div class="text-sm">
                  <span class="text-muted-foreground">用户ID：</span>
                  <code class="bg-gray-100 px-2 py-1 rounded text-xs">{videoData.author.user_id}</code>
                </div>

                {#if videoData.work_url}
                  <div class="text-sm">
                    <span class="text-muted-foreground">原始链接：</span>
                    <button 
                      on:click={openOriginalVideo}
                      class="text-blue-600 hover:text-blue-800 text-xs underline break-all"
                    >
                      {videoData.work_url}
                    </button>
                  </div>
                {/if}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    {:else}
      <div class="flex items-center justify-center py-16">
        <Card>
          <CardContent class="flex flex-col items-center justify-center py-12">
            <p class="text-muted-foreground">未找到视频数据</p>
            <Button on:click={goBack} variant="outline" size="sm" class="mt-4">
              返回列表
            </Button>
          </CardContent>
        </Card>
      </div>
    {/if}
  </div>
</div>

<style>
  /* 平滑滚动 */
  :global(html) {
    scroll-behavior: smooth;
  }
</style>