<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Plus, RefreshCw, Download, Settings, Trash2, Eye, EyeOff, Bell, Users, Video, Clock, Search } from 'lucide-svelte';
  import api from '$lib/api';
  import { showToast, handleApiError, formatNumber, cn } from '$lib/utils';
  import type { UserSearchResult } from '$lib/types';

  interface Subscription {
    id: number;
    user_id: string;
    sec_uid: string;
    nickname: string;
    avatar: string;
    signature: string;
    follower_count: number;
    aweme_count: number;
    user_url: string;
    enabled: boolean;
    auto_download: boolean;
    selected_videos?: string[];
    last_check_time?: string;
    last_video_time?: string;
    created_at: string;
    updated_at: string;
  }

  interface SubscriptionStats {
    total_subscriptions: number;
    enabled_subscriptions: number;
    total_videos: number;
    downloaded_videos: number;
    new_videos: number;
  }

  let subscriptions: Subscription[] = [];
  let stats: SubscriptionStats = {
    total_subscriptions: 0,
    enabled_subscriptions: 0,
    total_videos: 0,
    downloaded_videos: 0,
    new_videos: 0
  };
  let loading = false;
  let checkingUpdates = false;
  let selectedSubscriptions = new Set<string>();
  let showSearchModal = false;
  let searchQuery = '';
  let searchResults: UserSearchResult[] = [];
  let searching = false;

  onMount(() => {
    loadSubscriptions();
  });

  async function loadSubscriptions() {
    loading = true;
    try {
      const response = await api.getSubscriptions();
      if (response.code === 0 && response.data) {
        subscriptions = response.data.subscriptions;
        stats = response.data.stats;
      }
    } catch (error) {
      handleApiError(error);
    } finally {
      loading = false;
    }
  }

  async function searchUsers() {
    if (!searchQuery.trim()) return;
    
    searching = true;
    try {
      const response = await api.searchUsers(searchQuery, 10);
      if (response.code === 0 && response.data) {
        searchResults = response.data;
      }
    } catch (error) {
      handleApiError(error);
    } finally {
      searching = false;
    }
  }

  async function addSubscription(user: UserSearchResult) {
    try {
      const response = await api.addSubscription(user);
      if (response.code === 0) {
        showToast('订阅添加成功', 'success');
        showSearchModal = false;
        searchQuery = '';
        searchResults = [];
        await loadSubscriptions();
      }
    } catch (error) {
      handleApiError(error);
    }
  }

  async function removeSubscription(userId: string) {
    if (!confirm('确定要取消订阅吗？')) return;
    
    try {
      const response = await api.removeSubscription(userId);
      if (response.code === 0) {
        showToast('取消订阅成功', 'success');
        await loadSubscriptions();
      }
    } catch (error) {
      handleApiError(error);
    }
  }

  async function toggleSubscription(subscription: Subscription) {
    try {
      const response = await api.updateSubscription(subscription.user_id, {
        enabled: !subscription.enabled
      });
      if (response.code === 0) {
        showToast(`订阅已${!subscription.enabled ? '启用' : '禁用'}`, 'success');
        await loadSubscriptions();
      }
    } catch (error) {
      handleApiError(error);
    }
  }

  async function checkAllUpdates() {
    checkingUpdates = true;
    try {
      const response = await api.checkSubscriptionUpdates();
      if (response.code === 0) {
        showToast('开始检查订阅更新', 'success');
      } else {
        showToast(response.message || '检查更新失败', 'error');
      }
    } catch (error: any) {
      console.error('检查更新错误:', error);
      if (error?.code === 400 && error?.message?.includes('Cookie')) {
        showToast('请先在设置页面配置Cookie', 'error');
      } else {
        handleApiError(error);
      }
    } finally {
      checkingUpdates = false;
    }
  }

  async function downloadNewVideos(userId: string) {
    try {
      const response = await api.downloadSubscriptionNewVideos(userId);
      if (response.code === 0) {
        showToast('开始下载新视频', 'success');
      } else {
        showToast(response.message || '下载失败', 'error');
      }
    } catch (error: any) {
      console.error('下载新视频错误:', error);
      if (error?.code === 400 && error?.message?.includes('Cookie')) {
        showToast('请先在设置页面配置Cookie', 'error');
      } else {
        handleApiError(error);
      }
    }
  }

  function formatDate(dateStr: string) {
    if (!dateStr) return '从未';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  }
</script>

<div class="container mx-auto px-4 py-6">
  <!-- 页面标题和操作按钮 -->
  <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">订阅管理</h1>
      <p class="text-muted-foreground">管理您订阅的UP主，自动检查并下载新发布的视频</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <Button on:click={() => showSearchModal = true} class="gap-2">
        <Plus class="h-4 w-4" />
        添加订阅
      </Button>
      <Button 
        variant="outline" 
        on:click={checkAllUpdates} 
        disabled={checkingUpdates}
        class="gap-2"
      >
        {#if checkingUpdates}
          <RefreshCw class="h-4 w-4 animate-spin" />
          检查中...
        {:else}
          <RefreshCw class="h-4 w-4" />
          检查更新
        {/if}
      </Button>
    </div>
  </div>

  <!-- 统计卡片 -->
  <div class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium text-muted-foreground">
          <div class="flex items-center gap-2">
            <Bell class="h-4 w-4" />
            总订阅数
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{stats.total_subscriptions}</div>
        <p class="text-xs text-muted-foreground">已启用 {stats.enabled_subscriptions} 个</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium text-muted-foreground">
          <div class="flex items-center gap-2">
            <Video class="h-4 w-4" />
            视频统计
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{formatNumber(stats.total_videos)}</div>
        <p class="text-xs text-muted-foreground">已下载 {formatNumber(stats.downloaded_videos)} 个</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium text-muted-foreground">
          <div class="flex items-center gap-2">
            <Download class="h-4 w-4" />
            新视频
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold text-primary">{stats.new_videos}</div>
        <p class="text-xs text-muted-foreground">待下载</p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium text-muted-foreground">
          <div class="flex items-center gap-2">
            <Clock class="h-4 w-4" />
            下载进度
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">
          {stats.total_videos > 0 ? Math.round((stats.downloaded_videos / stats.total_videos) * 100) : 0}%
        </div>
        <div class="mt-1 h-2 w-full rounded-full bg-secondary">
          <div 
            class="h-full rounded-full bg-primary transition-all"
            style="width: {stats.total_videos > 0 ? (stats.downloaded_videos / stats.total_videos) * 100 : 0}%"
          />
        </div>
      </CardContent>
    </Card>
  </div>

  <!-- 订阅列表 -->
  {#if loading}
    <div class="flex h-64 items-center justify-center">
      <div class="flex flex-col items-center gap-2">
        <RefreshCw class="h-8 w-8 animate-spin text-muted-foreground" />
        <p class="text-sm text-muted-foreground">加载中...</p>
      </div>
    </div>
  {:else if subscriptions.length === 0}
    <Card class="border-dashed">
      <CardContent class="flex h-64 items-center justify-center">
        <div class="text-center">
          <Bell class="mx-auto mb-4 h-12 w-12 text-muted-foreground/50" />
          <h3 class="mb-2 text-lg font-semibold">还没有订阅任何UP主</h3>
          <p class="mb-4 text-sm text-muted-foreground">订阅您喜欢的UP主，自动获取最新视频</p>
          <Button on:click={() => showSearchModal = true} class="gap-2">
            <Plus class="h-4 w-4" />
            添加第一个订阅
          </Button>
        </div>
      </CardContent>
    </Card>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each subscriptions as subscription}
        <Card class="overflow-hidden transition-all hover:shadow-lg">
          <CardContent class="p-0">
            <!-- 用户信息 -->
            <div class="p-4">
              <div class="flex items-start gap-3">
                <img 
                  src={subscription.avatar} 
                  alt={subscription.nickname}
                  class="h-12 w-12 rounded-full object-cover ring-2 ring-background"
                />
                <div class="flex-1 space-y-1">
                  <div class="flex items-center justify-between">
                    <h3 class="font-semibold">{subscription.nickname}</h3>
                    <Badge variant={subscription.enabled ? 'default' : 'secondary'}>
                      {subscription.enabled ? '已启用' : '已禁用'}
                    </Badge>
                  </div>
                  <div class="flex items-center gap-3 text-sm text-muted-foreground">
                    <span class="flex items-center gap-1">
                      <Users class="h-3 w-3" />
                      {formatNumber(subscription.follower_count)}
                    </span>
                    <span class="flex items-center gap-1">
                      <Video class="h-3 w-3" />
                      {subscription.aweme_count}
                    </span>
                  </div>
                </div>
              </div>
              
              {#if subscription.signature}
                <p class="mt-3 line-clamp-2 text-sm text-muted-foreground">
                  {subscription.signature}
                </p>
              {/if}
              
              <div class="mt-3 text-xs text-muted-foreground">
                <div class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  上次检查: {formatDate(subscription.last_check_time)}
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="border-t bg-muted/50 p-3">
              <div class="flex items-center justify-between">
                <div class="flex gap-1">
                  <Button
                    size="sm"
                    variant={subscription.enabled ? 'ghost' : 'secondary'}
                    on:click={() => toggleSubscription(subscription)}
                    class="h-8 w-8 p-0"
                    title={subscription.enabled ? '禁用订阅' : '启用订阅'}
                  >
                    {#if subscription.enabled}
                      <Eye class="h-4 w-4" />
                    {:else}
                      <EyeOff class="h-4 w-4" />
                    {/if}
                  </Button>
                  <a 
                    href={subscription.user_url} 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      size="sm"
                      variant="ghost"
                      class="h-8 w-8 p-0"
                      title="访问主页"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </Button>
                  </a>
                </div>
                <div class="flex gap-1">
                  <Button
                    size="sm"
                    variant="default"
                    on:click={() => downloadNewVideos(subscription.user_id)}
                    class="h-8"
                    title="下载新视频"
                  >
                    <Download class="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    on:click={() => removeSubscription(subscription.user_id)}
                    class="h-8"
                    title="取消订阅"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      {/each}
    </div>
  {/if}
</div>

<!-- 搜索用户模态框 -->
{#if showSearchModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
    <Card class="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>添加订阅</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="flex gap-2">
          <Input
            type="text"
            placeholder="搜索UP主名称..."
            bind:value={searchQuery}
            on:keydown={(e) => e.key === 'Enter' && searchUsers()}
            class="flex-1"
          />
          <Button 
            on:click={searchUsers}
            disabled={searching || !searchQuery.trim()}
            class="gap-2"
          >
            {#if searching}
              <RefreshCw class="h-4 w-4 animate-spin" />
              搜索中
            {:else}
              <Search class="h-4 w-4" />
              搜索
            {/if}
          </Button>
        </div>

        {#if searchResults.length > 0}
          <div class="max-h-96 space-y-2 overflow-y-auto rounded-lg border p-2">
            {#each searchResults as user}
              <div class="flex items-center justify-between rounded-lg border bg-card p-3 transition-colors hover:bg-accent">
                <div class="flex items-center gap-3">
                  <img 
                    src={user.avatar} 
                    alt={user.nickname}
                    class="h-10 w-10 rounded-full object-cover"
                  />
                  <div>
                    <p class="font-medium">{user.nickname}</p>
                    <p class="text-sm text-muted-foreground">
                      {formatNumber(user.follower_count)} 粉丝 · {user.aweme_count} 作品
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  on:click={() => addSubscription(user)}
                  class="gap-2"
                >
                  <Plus class="h-4 w-4" />
                  订阅
                </Button>
              </div>
            {/each}
          </div>
        {/if}

        <div class="flex justify-end gap-2 pt-4">
          <Button 
            variant="outline"
            on:click={() => {
              showSearchModal = false;
              searchQuery = '';
              searchResults = [];
            }}
          >
            取消
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
{/if}