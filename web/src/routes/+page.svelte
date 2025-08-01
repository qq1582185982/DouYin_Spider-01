<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { 
    Users, 
    Video, 
    Download, 
    HardDrive,
    Activity,
    CheckCircle,
    XCircle,
    Clock,
    Search,
    Radio
  } from 'lucide-svelte';
  import api from '$lib/api';
  import { formatBytes, cn } from '$lib/utils';
  import type { SystemStatus, SpiderTask } from '$lib/types';

  let systemStatus: SystemStatus | null = null;
  let recentTasks: SpiderTask[] = [];
  let loading = true;

  async function loadData() {
    try {
      const [statusResponse, tasksResponse] = await Promise.all([
        api.getSystemStatus(),
        api.getTasks()
      ]);
      systemStatus = statusResponse.data;
      recentTasks = tasksResponse.data.slice(0, 5);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  });

  function getTaskIcon(status: string) {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'failed': return XCircle;
      case 'running': return Activity;
      default: return Clock;
    }
  }

  function getTaskColor(status: string) {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'running': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  }
</script>

<svelte:head>
  <title>仪表盘 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">仪表盘</h1>
    <p class="text-muted-foreground">系统概览和统计信息</p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <p class="text-muted-foreground">加载中...</p>
    </div>
  {:else if systemStatus}
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">系统状态</CardTitle>
          <Activity class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {systemStatus.is_running ? '运行中' : '已停止'}
          </div>
          <p class="text-xs text-muted-foreground">
            Cookie {systemStatus.cookie_valid ? '有效' : '无效'}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">用户总数</CardTitle>
          <Users class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{systemStatus.total_users}</div>
          <p class="text-xs text-muted-foreground">已爬取用户</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">作品总数</CardTitle>
          <Video class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">{systemStatus.total_works}</div>
          <p class="text-xs text-muted-foreground">已爬取作品</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium">存储空间</CardTitle>
          <HardDrive class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">
            {formatBytes(systemStatus.disk_usage.used)}
          </div>
          <p class="text-xs text-muted-foreground">
            共 {formatBytes(systemStatus.disk_usage.total)}
          </p>
        </CardContent>
      </Card>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent class="space-y-2">
          <Button on:click={() => goto('/spider/user')} class="w-full justify-start" variant="outline">
            <Users class="mr-2 h-4 w-4" />
            爬取用户作品
          </Button>
          <Button on:click={() => goto('/spider/search')} class="w-full justify-start" variant="outline">
            <Search class="mr-2 h-4 w-4" />
            搜索爬取
          </Button>
          <Button on:click={() => goto('/live')} class="w-full justify-start" variant="outline">
            <Radio class="mr-2 h-4 w-4" />
            监控直播间
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>最近任务</CardTitle>
        </CardHeader>
        <CardContent>
          {#if recentTasks.length === 0}
            <p class="text-center text-muted-foreground">暂无任务</p>
          {:else}
            <div class="space-y-2">
              {#each recentTasks as task}
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <svelte:component 
                      this={getTaskIcon(task.status)} 
                      class={cn('h-4 w-4', getTaskColor(task.status))}
                    />
                    <span class="text-sm">
                      {task.type === 'user' ? '用户爬取' : task.type === 'search' ? '搜索爬取' : '作品爬取'}
                    </span>
                  </div>
                  <span class="text-xs text-muted-foreground">
                    {new Date(task.created_at).toLocaleString()}
                  </span>
                </div>
              {/each}
            </div>
          {/if}
        </CardContent>
      </Card>
    </div>
  {/if}
</div>