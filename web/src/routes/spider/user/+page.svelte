<script lang="ts">
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Users, Download, AlertCircle, Search, CheckCircle, Video, Image } from 'lucide-svelte';
  import api from '$lib/api';
  import type { SpiderTask, UserSearchResult, UserVideo, UserVideosResponse } from '$lib/types';
  import { formatNumber } from '$lib/utils';

  let searchQuery = '';
  let searchLoading = false;
  let searchResults: UserSearchResult[] = [];
  let selectedUser: UserSearchResult | null = null;
  let userVideos: UserVideo[] = [];
  let userInfo: UserVideosResponse['user'] | null = null;
  let videosLoading = false;
  let selectedVideos = new Set<string>();
  let downloadLoading = false;
  let error = '';
  let currentTask: SpiderTask | null = null;
  let saveChoice = 'all';
  let showSearchResults = true; // 控制是否显示搜索结果

  const saveOptions = [
    { value: 'all', label: '保存所有信息' },
    { value: 'media', label: '仅保存媒体文件' },
    { value: 'media-video', label: '仅保存视频' },
    { value: 'media-image', label: '仅保存图片' },
    { value: 'excel', label: '仅保存Excel' }
  ];

  async function searchUsers() {
    if (!searchQuery.trim()) {
      error = '请输入搜索关键词';
      return;
    }

    error = '';
    searchLoading = true;
    searchResults = [];
    selectedUser = null;
    userVideos = [];
    selectedVideos.clear();
    showSearchResults = true; // 搜索时显示搜索结果

    try {
      const response = await api.searchUsers(searchQuery);
      searchResults = response.data;
      if (searchResults.length === 0) {
        error = '未找到相关用户';
      }
    } catch (e: any) {
      error = e.message || '搜索失败';
    } finally {
      searchLoading = false;
    }
  }

  async function viewUserVideos(user: UserSearchResult) {
    selectedUser = user;
    videosLoading = true;
    error = '';
    userVideos = [];
    selectedVideos.clear();
    showSearchResults = false; // 查看作品时隐藏搜索结果

    try {
      const response = await api.getUserVideos(user.user_url);
      userInfo = response.data.user;
      userVideos = response.data.works;
    } catch (e: any) {
      error = e.message || '获取视频列表失败';
    } finally {
      videosLoading = false;
    }
  }

  function backToSearch() {
    showSearchResults = true;
    selectedUser = null;
    userVideos = [];
    userInfo = null;
    selectedVideos.clear();
  }

  function toggleVideo(awemeId: string) {
    if (selectedVideos.has(awemeId)) {
      selectedVideos.delete(awemeId);
    } else {
      selectedVideos.add(awemeId);
    }
    selectedVideos = selectedVideos; // 触发更新
  }

  function selectAll() {
    userVideos.forEach(video => {
      selectedVideos.add(video.aweme_id);
    });
    selectedVideos = selectedVideos;
  }

  function selectNone() {
    selectedVideos.clear();
    selectedVideos = selectedVideos;
  }

  async function downloadSelected() {
    if (!selectedUser) return;

    error = '';
    downloadLoading = true;

    try {
      // 如果没有选中任何视频，则下载全部
      const videosToDownload = selectedVideos.size > 0 ? Array.from(selectedVideos) : undefined;
      
      const response = await api.spiderUser(selectedUser.user_url, saveChoice, false, videosToDownload);
      currentTask = response.data;
      
      // 轮询任务状态
      const pollInterval = setInterval(async () => {
        if (!currentTask) return;
        
        try {
          const taskResponse = await api.getTask(currentTask.id);
          currentTask = taskResponse.data;
          
          if (currentTask.status === 'completed' || currentTask.status === 'failed') {
            clearInterval(pollInterval);
            downloadLoading = false;
          }
        } catch (e) {
          clearInterval(pollInterval);
          downloadLoading = false;
        }
      }, 1000);
    } catch (e: any) {
      error = e.message || '下载失败';
      downloadLoading = false;
    }
  }

  function formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  function formatDate(timestamp: number): string {
    return new Date(timestamp * 1000).toLocaleDateString('zh-CN');
  }
</script>

<svelte:head>
  <title>用户爬取 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">用户爬取</h1>
    <p class="text-muted-foreground">搜索用户并选择要下载的视频</p>
  </div>

  <!-- 搜索框 -->
  <Card>
    <CardHeader>
      <CardTitle>搜索用户</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="flex gap-2">
        <Input
          bind:value={searchQuery}
          placeholder="输入用户名称搜索..."
          disabled={searchLoading}
          on:keydown={(e) => e.key === 'Enter' && searchUsers()}
        />
        <Button on:click={searchUsers} disabled={searchLoading}>
          {#if searchLoading}
            <Search class="mr-2 h-4 w-4 animate-spin" />
            搜索中...
          {:else}
            <Search class="mr-2 h-4 w-4" />
            搜索
          {/if}
        </Button>
      </div>
    </CardContent>
  </Card>

  <!-- 搜索结果 -->
  {#if searchResults.length > 0 && showSearchResults}
    <Card>
      <CardHeader>
        <CardTitle>搜索结果</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          {#each searchResults as user}
            <div class="flex items-center justify-between rounded-lg border p-4">
              <div class="flex items-center gap-4">
                <img
                  src={user.avatar}
                  alt={user.nickname}
                  class="h-12 w-12 rounded-full"
                />
                <div>
                  <h3 class="font-semibold">{user.nickname}</h3>
                  <p class="text-sm text-muted-foreground">
                    {user.signature || '暂无签名'}
                  </p>
                  <div class="mt-1 flex gap-4 text-xs text-muted-foreground">
                    <span>粉丝: {formatNumber(user.follower_count)}</span>
                    <span>作品: {user.aweme_count}</span>
                    <span>获赞: {formatNumber(user.total_favorited)}</span>
                  </div>
                </div>
              </div>
              <Button on:click={() => viewUserVideos(user)} variant="outline">
                查看作品
              </Button>
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>
  {/if}

  <!-- 视频列表 -->
  {#if selectedUser && !showSearchResults}
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <Button on:click={backToSearch} variant="ghost" size="sm">
              ← 返回搜索
            </Button>
            <div>
              <CardTitle>{userInfo?.nickname} 的作品</CardTitle>
              <p class="text-sm text-muted-foreground">
                共 {userVideos.length} 个作品，已选择 {selectedVideos.size} 个
              </p>
            </div>
          </div>
          <div class="flex gap-2">
            <Button on:click={selectAll} variant="outline" size="sm">
              全选
            </Button>
            <Button on:click={selectNone} variant="outline" size="sm">
              取消全选
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {#if videosLoading}
          <div class="flex items-center justify-center py-8">
            <p class="text-muted-foreground">加载中...</p>
          </div>
        {:else}
          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {#each userVideos as video}
              <div
                class="relative cursor-pointer rounded-lg border transition-colors {selectedVideos.has(video.aweme_id) ? 'border-primary bg-primary/5' : ''}"
                on:click={() => toggleVideo(video.aweme_id)}
              >
                <!-- 选中标记 -->
                {#if selectedVideos.has(video.aweme_id)}
                  <div class="absolute right-2 top-2 z-10">
                    <CheckCircle class="h-6 w-6 text-primary" />
                  </div>
                {/if}

                <!-- 封面 -->
                <div class="relative aspect-[9/16] overflow-hidden rounded-t-lg bg-gray-100">
                  {#if video.cover}
                    <img
                      src={video.cover}
                      alt={video.desc}
                      class="h-full w-full object-cover"
                    />
                  {/if}
                  
                  <!-- 类型标记 -->
                  <div class="absolute left-2 top-2">
                    {#if video.aweme_type === 68}
                      <div class="flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white">
                        <Image class="h-3 w-3" />
                        图文
                      </div>
                    {:else}
                      <div class="flex items-center gap-1 rounded bg-black/60 px-2 py-1 text-xs text-white">
                        <Video class="h-3 w-3" />
                        {formatDuration(video.duration / 1000)}
                      </div>
                    {/if}
                  </div>
                </div>

                <!-- 信息 -->
                <div class="p-3">
                  <p class="mb-2 line-clamp-2 text-sm">
                    {video.desc || '无标题'}
                  </p>
                  <div class="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{formatDate(video.create_time)}</span>
                    <div class="flex gap-2">
                      <span>❤ {formatNumber(video.statistics.digg_count)}</span>
                      <span>💬 {formatNumber(video.statistics.comment_count)}</span>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </CardContent>
    </Card>
  {/if}

  <!-- 下载设置 -->
  {#if selectedUser && userVideos.length > 0 && !showSearchResults}
    <Card>
      <CardHeader>
        <CardTitle>下载设置</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
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
                  disabled={downloadLoading}
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
          on:click={downloadSelected} 
          disabled={downloadLoading}
          class="w-full"
        >
          {#if downloadLoading}
            <Download class="mr-2 h-4 w-4 animate-spin" />
            下载中...
          {:else}
            <Download class="mr-2 h-4 w-4" />
            {selectedVideos.size > 0 
              ? `下载选中的 ${selectedVideos.size} 个作品` 
              : '下载全部作品'}
          {/if}
        </Button>
      </CardContent>
    </Card>
  {/if}

  <!-- 任务状态 -->
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