<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Users, Download, AlertCircle } from 'lucide-svelte';
  import api from '$lib/api';
  import type { SpiderTask } from '$lib/types';

  let userUrl = '';
  let loading = false;
  let error = '';
  let currentTask: SpiderTask | null = null;
  let saveChoice = 'all';

  const saveOptions = [
    { value: 'all', label: '保存所有信息' },
    { value: 'media', label: '仅保存媒体文件' },
    { value: 'media-video', label: '仅保存视频' },
    { value: 'media-image', label: '仅保存图片' },
    { value: 'excel', label: '仅保存Excel' }
  ];

  async function handleSubmit() {
    if (!userUrl.trim()) {
      error = '请输入用户主页URL';
      return;
    }

    error = '';
    loading = true;

    try {
      const response = await api.spiderUser(userUrl, saveChoice);
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
      error = e.message || '爬取失败';
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>用户爬取 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">用户爬取</h1>
    <p class="text-muted-foreground">输入抖音用户主页URL，爬取该用户的所有作品</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>爬取设置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="userUrl" class="mb-2 block text-sm font-medium">
          用户主页URL
        </label>
        <Input
          id="userUrl"
          type="url"
          bind:value={userUrl}
          placeholder="https://www.douyin.com/user/MS4wLjABAAAA..."
          disabled={loading}
        />
        <p class="mt-1 text-xs text-muted-foreground">
          请输入完整的抖音用户主页链接
        </p>
      </div>

      <div>
        <label class="mb-2 block text-sm font-medium">
          保存方式
        </label>
        <div class="space-y-2">
          {#each saveOptions as option}
            <label class="flex items-center space-x-2">
              <input
                type="radio"
                name="saveChoice"
                value={option.value}
                bind:group={saveChoice}
                disabled={loading}
                class="h-4 w-4 border-gray-300 text-primary focus:ring-primary"
              />
              <span class="text-sm">{option.label}</span>
            </label>
          {/each}
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
          爬取中...
        {:else}
          <Users class="mr-2 h-4 w-4" />
          开始爬取
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