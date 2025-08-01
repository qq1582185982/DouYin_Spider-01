<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Search, Download, AlertCircle } from 'lucide-svelte';
  import api from '$lib/api';
  import type { SpiderTask } from '$lib/types';

  let query = '';
  let loading = false;
  let error = '';
  let currentTask: SpiderTask | null = null;

  // 搜索参数
  let options = {
    require_num: 20,
    sort_type: '0',
    publish_time: '0',
    filter_duration: '',
    search_range: '0',
    content_type: '0',
    save_choice: 'all'
  };

  const sortOptions = [
    { value: '0', label: '综合排序' },
    { value: '1', label: '最多点赞' },
    { value: '2', label: '最新发布' }
  ];

  const publishTimeOptions = [
    { value: '0', label: '不限' },
    { value: '1', label: '一天内' },
    { value: '7', label: '一周内' },
    { value: '180', label: '半年内' }
  ];

  const durationOptions = [
    { value: '', label: '不限' },
    { value: '0-1', label: '一分钟内' },
    { value: '1-5', label: '1-5分钟' },
    { value: '5-10000', label: '5分钟以上' }
  ];

  const contentTypeOptions = [
    { value: '0', label: '不限' },
    { value: '1', label: '视频' },
    { value: '2', label: '图文' }
  ];

  async function handleSubmit() {
    if (!query.trim()) {
      error = '请输入搜索关键词';
      return;
    }

    error = '';
    loading = true;

    try {
      const response = await api.spiderSearch(query, options);
      currentTask = response.data;
      
      // 轮询任务状态
      const pollInterval = setInterval(async () => {
        if (!currentTask) return;
        
        try {
          const taskResponse = await api.getTask(currentTask.id);
          currentTask = taskResponse.data;
          
          if (currentTask.status === 'completed' || currentTask.status === 'failed') {
            clearInterval(pollInterval);
            loading = false;
          }
        } catch (e) {
          clearInterval(pollInterval);
          loading = false;
        }
      }, 1000);
    } catch (e: any) {
      error = e.message || '搜索失败';
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>搜索爬取 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">搜索爬取</h1>
    <p class="text-muted-foreground">根据关键词搜索并爬取相关视频</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>搜索设置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="query" class="mb-2 block text-sm font-medium">
          搜索关键词
        </label>
        <Input
          id="query"
          type="text"
          bind:value={query}
          placeholder="输入要搜索的关键词"
          disabled={loading}
        />
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="mb-2 block text-sm font-medium">
            搜索数量
          </label>
          <Input
            type="number"
            bind:value={options.require_num}
            min="1"
            max="100"
            disabled={loading}
          />
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">
            排序方式
          </label>
          <select
            bind:value={options.sort_type}
            disabled={loading}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {#each sortOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">
            发布时间
          </label>
          <select
            bind:value={options.publish_time}
            disabled={loading}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {#each publishTimeOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">
            视频时长
          </label>
          <select
            bind:value={options.filter_duration}
            disabled={loading}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {#each durationOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium">
            内容形式
          </label>
          <select
            bind:value={options.content_type}
            disabled={loading}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {#each contentTypeOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>
      </div>

      {#if error}
        <div class="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-red-800">
          <AlertCircle class="h-4 w-4" />
          <span class="text-sm">{error}</span>
        </div>
      {/if}

      <Button 
        on:click={handleSubmit} 
        disabled={loading}
        class="w-full"
      >
        {#if loading}
          <Download class="mr-2 h-4 w-4 animate-spin" />
          搜索中...
        {:else}
          <Search class="mr-2 h-4 w-4" />
          开始搜索
        {/if}
      </Button>
    </CardContent>
  </Card>

  {#if currentTask}
    <Card>
      <CardHeader>
        <CardTitle>任务状态</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-2">
          <div class="flex justify-between">
            <span class="text-sm font-medium">任务ID:</span>
            <span class="text-sm text-muted-foreground">{currentTask.id}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm font-medium">关键词:</span>
            <span class="text-sm text-muted-foreground">{currentTask.query}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm font-medium">状态:</span>
            <span class="text-sm">
              {#if currentTask.status === 'pending'}
                等待中
              {:else if currentTask.status === 'running'}
                运行中
              {:else if currentTask.status === 'completed'}
                已完成
              {:else if currentTask.status === 'failed'}
                失败
              {/if}
            </span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm font-medium">进度:</span>
            <span class="text-sm">{currentTask.progress} / {currentTask.total}</span>
          </div>
          {#if currentTask.error}
            <div class="mt-2 rounded bg-red-50 p-2 text-sm text-red-800">
              {currentTask.error}
            </div>
          {/if}
        </div>
      </CardContent>
    </Card>
  {/if}
</div>