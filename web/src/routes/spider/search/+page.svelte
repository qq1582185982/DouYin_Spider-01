<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Link, Download, AlertCircle, Clipboard, Trash2 } from 'lucide-svelte';
  import api from '$lib/api';
  import { toast } from 'svelte-sonner';

  let linksInput = '';
  let loading = false;
  let error = '';
  let currentTaskId = '';
  let overallProgress = 0;
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
    const links = parseLinks(linksInput);
    
    if (links.length === 0) {
      error = '请输入有效的视频链接';
      return;
    }

    error = '';
    loading = true;
    
    try {
      // 调用批量下载接口
      const response = await api.spiderBatchWorks(links, false);
      const taskData = response.data;
      
      currentTaskId = taskData.id;
      
      // 初始化任务列表
      tasks = links.map(url => ({
        url,
        status: 'pending' as const
      }));
      
      // 跟踪任务进度
      pollTaskProgress(taskData.id);
      
      toast.success('下载任务已创建');
      
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
        />
        
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

      <Button 
        on:click={handleSubmit} 
        disabled={loading || !linksInput.trim()}
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