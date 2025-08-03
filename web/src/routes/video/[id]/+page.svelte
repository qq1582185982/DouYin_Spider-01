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
  let showVideo = false;
  let videoElement: HTMLVideoElement;
  let videoLoading = false;

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
      console.log('视频数据:', videoData);
      console.log('local_path:', videoData.video?.local_path);
      console.log('play_addr:', videoData.video?.play_addr);
      console.log('work_type:', videoData.work_type);
      console.log('images:', videoData.images);
      if (videoData.images && videoData.images.length > 0) {
        console.log('第一张图片数据:', videoData.images[0]);
      }
      
      // 诊断文件是否存在
      if (videoData && videoData.video?.local_path) {
        try {
          const checkResponse = await fetch(`http://localhost:8000/api/check-file/${workId}`);
          const checkData = await checkResponse.json();
          console.log('文件检查结果:', checkData);
          console.log('文件列表:', checkData.files_in_directory);
          console.log('完整save_path:', checkData.save_path);
          console.log('完整video_file:', checkData.video_file);
          
          if (!checkData.exists) {
            console.warn('视频文件不存在于服务器:', checkData);
          }
        } catch (e) {
          console.error('文件检查失败:', e);
        }
      }
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

  function playVideo() {
    showVideo = true;
  }

  function closeVideo() {
    showVideo = false;
    if (videoElement) {
      videoElement.pause();
    }
  }

  // 处理视频URL，确保可以播放
  function getVideoUrl(url: string): string {
    if (!url) return '';
    
    // 如果是静态路径，直接加上主机名
    if (url.startsWith('/static/') || url.startsWith('static/')) {
      const path = url.startsWith('/') ? url : '/' + url;
      // 不需要编码，因为Flask会自动处理
      return `http://localhost:8000${path}`;
    }
    
    // 如果是本地文件路径
    if (url.includes('\\') || url.startsWith('D:') || url.startsWith('C:')) {
      // 尝试转换为静态文件URL
      const match = url.match(/downloads[\\\/](.+)/);
      if (match) {
        // 转换路径分隔符
        const urlPath = match[1].replace(/\\/g, '/');
        return `http://localhost:8000/static/${urlPath}`;
      }
    }
    
    return url;
  }

  // 处理键盘事件
  function handleKeydown(e: KeyboardEvent) {
    if (showVideo && videoElement) {
      switch(e.key) {
        case 'Escape':
          closeVideo();
          break;
        case ' ':
          e.preventDefault();
          if (videoElement.paused) {
            videoElement.play();
          } else {
            videoElement.pause();
          }
          break;
        case 'ArrowLeft':
          videoElement.currentTime -= 5;
          break;
        case 'ArrowRight':
          videoElement.currentTime += 5;
          break;
      }
    }
  }

  onMount(() => {
    loadVideoDetail();
    
    // 添加键盘事件监听
    window.addEventListener('keydown', handleKeydown);
    
    return () => {
      window.removeEventListener('keydown', handleKeydown);
    };
  });

  // 监听路由参数变化
  $: if ($page.params.id) {
    loadVideoDetail();
  }
  
  // 获取图片URL
  function getImageUrl(image: any): string {
    if (typeof image === 'string') {
      return image;
    }
    if (image && typeof image === 'object') {
      // 尝试各种可能的字段
      if (image.url_list && Array.isArray(image.url_list) && image.url_list.length > 0) {
        return image.url_list[0];
      }
      if (image.url) {
        return image.url;
      }
      if (image.uri) {
        return image.uri;
      }
    }
    return '';
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
      <div class="space-y-6">
        <!-- 封面区域 - 居中显示 -->
        <div class="w-full">
          <div class="relative overflow-hidden rounded-lg bg-black">
            {#if videoData.work_type === '图集' && videoData.images && videoData.images.length > 0}
              <!-- 图集展示 -->
              <div class="bg-gray-100">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 p-2">
                  {#each videoData.images as image, index}
                    {@const imageUrl = getImageUrl(image)}
                    <div class="relative aspect-square overflow-hidden rounded-lg bg-gray-200">
                      <img 
                        src={imageUrl}
                        alt="{videoData.title} - 图片 {index + 1}"
                        class="h-full w-full object-cover hover:scale-105 transition-transform duration-300 cursor-pointer"
                        loading="lazy"
                        on:click={() => window.open(imageUrl, '_blank')}
                        on:error={(e) => {
                          console.error('图片加载失败:', imageUrl);
                          console.error('原始图片数据:', image);
                        }}
                      />
                      <div class="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                        {index + 1} / {videoData.images.length}
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {:else if showVideo && videoData.work_type === '视频' && (videoData.video?.local_path || videoData.video?.play_addr)}
              <!-- 视频播放器 -->
              <div class="relative aspect-video">
                {#if videoLoading}
                  <div class="absolute inset-0 flex items-center justify-center bg-black">
                    <div class="text-white text-center">
                      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4"></div>
                      <p class="text-sm">加载视频中...</p>
                    </div>
                  </div>
                {/if}
                
                <video
                  bind:this={videoElement}
                  src={videoData.video.local_path ? `http://localhost:8000/api/video/${videoData.work_id}` : videoData.video.play_addr}
                  controls
                  autoplay
                  class="w-full h-full object-contain"
                  on:loadstart={() => videoLoading = true}
                  on:canplay={() => videoLoading = false}
                  on:error={async (e) => {
                    videoLoading = false;
                    console.error('视频播放错误:', e);
                    console.error('原始URL:', videoData.video.play_addr);
                    console.error('本地URL:', videoData.video.local_path);
                    const processedUrl = getVideoUrl(videoData.video.local_path || videoData.video.play_addr);
                    console.error('处理后的URL:', processedUrl);
                    
                    // 尝试检查文件是否可访问
                    if (videoData.video.local_path) {
                      try {
                        const response = await fetch(processedUrl, { method: 'HEAD' });
                        console.error('文件检查响应:', response.status, response.statusText);
                        if (!response.ok) {
                          const errorResponse = await fetch(processedUrl);
                          const errorText = await errorResponse.text();
                          console.error('错误详情:', errorText);
                        }
                      } catch (fetchError) {
                        console.error('文件检查失败:', fetchError);
                      }
                    }
                    
                    toast.error('视频播放失败，请尝试在抖音中打开');
                  }}
                >
                  <p>您的浏览器不支持视频播放</p>
                </video>
                
                <!-- 关闭按钮 -->
                <Button
                  on:click={closeVideo}
                  variant="ghost"
                  size="icon"
                  class="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white z-10"
                >
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
                
                <!-- 快捷键提示 -->
                <div class="absolute bottom-2 left-2 text-white text-xs bg-black/50 px-2 py-1 rounded">
                  空格: 播放/暂停 | ←→: 快进/快退 | ESC: 退出
                </div>
              </div>
            {:else if videoData.work_type === '视频' && videoData.video?.cover}
              <!-- 毛玻璃背景 -->
              <div class="absolute inset-0">
                <img 
                  src={videoData.video.cover} 
                  alt={videoData.title}
                  class="w-full h-full object-cover filter blur-xl scale-110 opacity-50"
                  loading="lazy"
                />
              </div>
              
              <!-- 居中的封面 -->
              <div class="relative flex items-center justify-center aspect-video">
                <img 
                  src={videoData.video.cover} 
                  alt={videoData.title}
                  class="max-h-full max-w-full object-contain"
                  loading="lazy"
                />
                
                <!-- 播放按钮覆盖层 -->
                {#if videoData.video?.play_addr || videoData.video?.local_path}
                  <button
                    on:click={playVideo}
                    class="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/40 transition-colors group"
                  >
                    <div class="bg-white/90 rounded-full p-4 shadow-lg transform group-hover:scale-110 transition-transform">
                      <Play class="h-8 w-8 text-gray-900" fill="currentColor" />
                    </div>
                  </button>
                {:else}
                  <div class="absolute inset-0 flex items-center justify-center bg-black/20">
                    <div class="text-white text-center">
                      <p class="text-sm mb-2">视频地址不可用</p>
                      <Button on:click={openOriginalVideo} variant="secondary" size="sm">
                        在抖音中查看
                      </Button>
                    </div>
                  </div>
                {/if}
              </div>
            {:else}
              <div class="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                <Play class="h-16 w-16 text-gray-400" />
              </div>
            {/if}
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="grid gap-6 {isMobile ? 'grid-cols-1' : 'lg:grid-cols-3'}">
          <!-- 左侧：视频信息和详细信息 -->
          <div class="{isMobile ? '' : 'lg:col-span-2'} space-y-6">
            <!-- 视频信息卡片 -->
            <Card class="overflow-hidden">
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

            <!-- 基本信息和技术信息并排显示 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  <span>{videoData.download_time ? new Date(videoData.download_time).toLocaleString('zh-CN') : '未知'}</span>
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

        <!-- 右侧：统计信息和详细数据 -->
        <div class="space-y-6">
          <!-- 数据统计卡片 -->
          <Card>
            <CardHeader>
              <CardTitle class="text-lg">数据统计</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
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


        </div>
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