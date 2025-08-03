<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Link, Download, AlertCircle, Clipboard, Trash2, Eye, Video, Image, Loader2 } from 'lucide-svelte';
  import api from '$lib/api';
  import { toast } from 'svelte-sonner';

  let linksInput = '';
  let loading = false;
  let error = '';
  let currentTaskId = '';
  let overallProgress = 0;
  let previewing = false;
  let videoInfos: Array<{
    url: string;
    info?: any;
    error?: string;
    loading?: boolean;
  }> = [];
  let tasks: Array<{
    url: string;
    status: 'pending' | 'downloading' | 'completed' | 'failed';
    info?: any;
    error?: string;
    progress?: number;
  }> = [];

  // 从剪贴板粘贴
  async function pasteFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        linksInput = text;
        toast.success('已从剪贴板粘贴');
      }
    } catch (err) {
      toast.error('无法访问剪贴板');
    }
  }

  // 解析链接
  function parseLinks(input: string): string[] {
    const lines = input.split('\n').filter(line => line.trim());
    const links: string[] = [];
    
    for (const line of lines) {
      // 匹配抖音链接格式
      // 支持多种格式：
      // https://www.douyin.com/video/xxx
      // https://v.douyin.com/xxx
      // 分享文本中的链接
      const urlMatch = line.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
        links.push(urlMatch[0]);
      }
    }
    
    return [...new Set(links)]; // 去重
  }

  // 开始下载
  async function handleSubmit() {
    // 如果有预览信息但还在加载，等待
    if (videoInfos.some(v => v.loading)) {
      return;
    }
    
    // 使用有效的链接（过滤掉获取失败的）
    const validLinks = videoInfos
      .filter(v => v.info && !v.error)
      .map(v => v.url);
    
    if (validLinks.length === 0) {
      error = '没有有效的视频链接可以下载';
      return;
    }

    error = '';
    loading = true;
    
    try {
      // 调用批量下载接口
      const response = await api.spiderBatchWorks(validLinks, false);
      const taskData = response.data;
      
      currentTaskId = taskData.id;
      
      // 初始化任务列表，包含预览信息
      tasks = validLinks.map(url => {
        const videoInfo = videoInfos.find(v => v.url === url);
        return {
          url,
          status: 'pending' as const,
          info: videoInfo?.info
        };
      });
      
      // 跟踪任务进度
      pollTaskProgress(taskData.id);
      
      toast.success(`已创建下载任务，共 ${validLinks.length} 个视频`);
      
    } catch (e: any) {
      error = e.message || '创建下载任务失败';
      loading = false;
    }
  }
  
  // 轮询任务进度
  async function pollTaskProgress(taskId: string) {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.getTask(taskId);
        const task = response.data;
        
        // 更新整体进度
        overallProgress = Math.round((task.progress / task.total) * 100);
        
        // 更新任务列表
        if (task.results && task.results.length > 0) {
          // 创建一个映射来快速查找结果
          const resultMap = new Map(task.results.map((r: any) => [r.url, r]));
          
          // 更新任务状态
          tasks = tasks.map(t => {
            const result = resultMap.get(t.url);
            if (result) {
              return {
                ...t,
                status: result.status === 'success' ? 'completed' : 'failed',
                info: result.info,
                error: result.error,
                progress: 100
              };
            }
            return t;
          });
          
          // 标记正在处理的任务
          const completedCount = task.results.length;
          if (completedCount < tasks.length && task.status === 'running') {
            tasks[completedCount].status = 'downloading';
          }
        }
        
        // 任务完成或失败时停止轮询
        if (task.status === 'completed' || task.status === 'failed') {
          clearInterval(pollInterval);
          loading = false;
          
          if (task.status === 'completed') {
            toast.success('下载任务完成');
          } else {
            toast.error('下载任务失败');
          }
        }
      } catch (e) {
        clearInterval(pollInterval);
        loading = false;
        error = '获取任务状态失败';
      }
    }, 1000); // 每秒轮询一次
  }

  // 清空输入
  function clearInput() {
    linksInput = '';
    tasks = [];
    error = '';
    currentTaskId = '';
    overallProgress = 0;
    videoInfos = [];
    previewing = false;
  }
  
  // 预览视频
  async function previewVideos() {
    const links = parseLinks(linksInput);
    
    if (links.length === 0) {
      error = '请输入有效的视频链接';
      return;
    }
    
    error = '';
    previewing = true;
    
    // 初始化视频信息列表
    videoInfos = links.map(url => ({
      url,
      loading: true
    }));
    
    // 并行获取所有视频信息
    const promises = links.map(async (url, index) => {
      try {
        const response = await api.spiderWork(url, false);
        videoInfos[index] = {
          ...videoInfos[index],
          info: response.data,
          loading: false
        };
      } catch (e: any) {
        videoInfos[index] = {
          ...videoInfos[index],
          error: e.message || '获取视频信息失败',
          loading: false
        };
      }
    });
    
    await Promise.all(promises);
    previewing = false;
  }
  
  // 监听输入变化，自动预览
  let previewTimer: ReturnType<typeof setTimeout>;
  $: {
    if (linksInput) {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(() => {
        if (linksInput.trim() && parseLinks(linksInput).length > 0) {
          previewVideos();
        }
      }, 1000); // 输入停止1秒后自动预览
    } else {
      videoInfos = [];
    }
  }

  // 获取状态颜色
  function getStatusColor(status: string) {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'downloading':
        return 'text-blue-600';
      default:
        return 'text-gray-500';
    }
  }

  // 获取状态文本
  function getStatusText(status: string) {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'downloading':
        return '下载中';
      default:
        return '等待中';
    }
  }
  
  // 格式化数字
  function formatNumber(num: number): string {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    }
    return num.toString();
  }
  
  // 格式化时长
  function formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<svelte:head>
  <title>链接下载 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">链接下载</h1>
    <p class="text-muted-foreground">通过分享链接下载抖音视频</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>输入视频链接</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <div class="mb-2 flex items-center justify-between">
          <label for="links" class="block text-sm font-medium">
            视频链接（每行一个）
          </label>
          <div class="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              on:click={pasteFromClipboard}
              disabled={loading}
            >
              <Clipboard class="mr-2 h-4 w-4" />
              粘贴
            </Button>
            <Button
              variant="outline"
              size="sm"
              on:click={clearInput}
              disabled={loading}
            >
              <Trash2 class="mr-2 h-4 w-4" />
              清空
            </Button>
          </div>
        </div>
        
        <textarea
          id="links"
          bind:value={linksInput}
          placeholder={'请输入抖音视频链接，支持以下格式：\nhttps://www.douyin.com/video/xxx\nhttps://v.douyin.com/xxx\n或直接粘贴分享文本'}
          disabled={loading}
          rows="6"
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        ></textarea>
        
        <p class="mt-2 text-xs text-muted-foreground">
          提示：可以直接从抖音APP复制分享链接粘贴到这里
        </p>
      </div>

      {#if error}
        <div class="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-red-800">
          <AlertCircle class="h-4 w-4" />
          <span class="text-sm">{error}</span>
        </div>
      {/if}
    </CardContent>
  </Card>

  {#if videoInfos.length > 0}
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle>视频预览</CardTitle>
          {#if previewing}
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 class="h-4 w-4 animate-spin" />
              正在获取视频信息...
            </div>
          {/if}
        </div>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          {#each videoInfos as video, index}
            <div class="rounded-lg border p-4 {video.error ? 'border-red-200 bg-red-50' : ''}">
              {#if video.loading}
                <div class="flex items-center gap-2">
                  <Loader2 class="h-4 w-4 animate-spin" />
                  <span class="text-sm text-muted-foreground">正在获取视频信息...</span>
                </div>
              {:else if video.error}
                <div class="flex items-center gap-2 text-red-600">
                  <AlertCircle class="h-4 w-4" />
                  <span class="text-sm">{video.error}</span>
                </div>
              {:else if video.info}
                <div class="flex gap-4">
                  <!-- 视频封面 -->
                  <div class="relative h-32 w-24 flex-shrink-0 overflow-hidden rounded bg-gray-100">
                    {#if video.info.video?.cover || video.info.video_cover}
                      <img 
                        src={video.info.video?.cover || video.info.video_cover} 
                        alt="视频封面"
                        class="h-full w-full object-cover"
                      />
                      <div class="absolute bottom-1 right-1 rounded bg-black/60 px-1 py-0.5 text-[10px] text-white">
                        {formatDuration(video.info.duration || 0)}
                      </div>
                    {/if}
                    <div class="absolute left-1 top-1">
                      {#if video.info.work_type === 'video' || video.info.aweme_type === 0}
                        <div class="rounded bg-black/60 p-1">
                          <Video class="h-3 w-3 text-white" />
                        </div>
                      {:else}
                        <div class="rounded bg-black/60 p-1">
                          <Image class="h-3 w-3 text-white" />
                        </div>
                      {/if}
                    </div>
                  </div>
                  
                  <!-- 视频信息 -->
                  <div class="flex-1">
                    <h4 class="mb-1 font-medium">{video.info.desc || video.info.title || '无标题'}</h4>
                    <p class="mb-2 text-sm text-muted-foreground">
                      作者：{video.info.author?.nickname || video.info.nickname || '未知'}
                    </p>
                    <div class="flex flex-wrap gap-4 text-xs text-muted-foreground">
                      <span class="flex items-center gap-1">
                        <Eye class="h-3 w-3" />
                        {formatNumber(video.info.statistics?.play_count || video.info.play_count || 0)}
                      </span>
                      <span>❤ {formatNumber(video.info.statistics?.digg_count || video.info.digg_count || 0)}</span>
                      <span>💬 {formatNumber(video.info.statistics?.comment_count || video.info.comment_count || 0)}</span>
                      <span>↗ {formatNumber(video.info.statistics?.share_count || video.info.share_count || 0)}</span>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>
  {/if}

  <Card>
    <CardContent class="pt-6">
      <Button 
        on:click={handleSubmit} 
        disabled={loading || !linksInput.trim() || videoInfos.some(v => v.loading)}
        class="w-full"
      >
        {#if loading}
          <Download class="mr-2 h-4 w-4 animate-spin" />
          处理中...
        {:else}
          <Link class="mr-2 h-4 w-4" />
          开始下载
        {/if}
      </Button>
    </CardContent>
  </Card>

  {#if tasks.length > 0}
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle>下载进度</CardTitle>
          {#if loading}
            <span class="text-sm text-muted-foreground">
              总进度: {overallProgress}%
            </span>
          {/if}
        </div>
      </CardHeader>
      <CardContent>
        {#if loading && overallProgress > 0}
          <div class="mb-4">
            <div class="h-2 w-full rounded-full bg-gray-200">
              <div 
                class="h-2 rounded-full bg-primary transition-all duration-300"
                style="width: {overallProgress}%"
              ></div>
            </div>
          </div>
        {/if}
        
        <div class="space-y-3">
          {#each tasks as task, index}
            <div class="rounded-lg border p-4">
              <div class="mb-2 flex items-start justify-between">
                <div class="flex-1">
                  <p class="text-sm font-medium">链接 {index + 1}</p>
                  <p class="mt-1 break-all text-xs text-muted-foreground">
                    {task.url}
                  </p>
                </div>
                <span class={`text-sm font-medium ${getStatusColor(task.status)}`}>
                  {getStatusText(task.status)}
                </span>
              </div>
              
              {#if task.info}
                <div class="mt-2 text-sm text-muted-foreground">
                  <p>作者：{task.info.author?.nickname || task.info.nickname || '未知'}</p>
                  <p>描述：{task.info.desc || task.info.title || '无'}</p>
                </div>
              {/if}
              
              {#if task.error}
                <p class="mt-2 text-sm text-red-600">{task.error}</p>
              {/if}
              
              {#if task.status === 'downloading' && task.progress !== undefined}
                <div class="mt-2">
                  <div class="h-2 w-full rounded-full bg-gray-200">
                    <div 
                      class="h-2 rounded-full bg-blue-600 transition-all"
                      style="width: {task.progress}%"
                    ></div>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
        
        <div class="mt-4 flex justify-between text-sm text-muted-foreground">
          <span>总计：{tasks.length} 个链接</span>
          <span>
            完成：{tasks.filter(t => t.status === 'completed').length} 个，
            失败：{tasks.filter(t => t.status === 'failed').length} 个
          </span>
        </div>
      </CardContent>
    </Card>
  {/if}
</div>