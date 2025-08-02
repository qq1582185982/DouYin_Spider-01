<script lang="ts">
  import { onMount } from 'svelte';
  import { Plus, RefreshCw, Download, Settings, Trash2, Eye, EyeOff, CheckCircle } from 'lucide-svelte';
  import api from '$lib/api';
  import { showToast, handleApiError } from '$lib/utils';
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
        // 可以跳转到任务页面查看进度
      }
    } catch (error) {
      handleApiError(error);
    } finally {
      checkingUpdates = false;
    }
  }

  async function downloadNewVideos(userId: string) {
    try {
      const response = await api.downloadSubscriptionNewVideos(userId);
      if (response.code === 0) {
        showToast('开始下载新视频', 'success');
      }
    } catch (error) {
      handleApiError(error);
    }
  }

  function formatDate(dateStr: string) {
    if (!dateStr) return '从未';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  }

  function formatCount(count: number): string {
    if (count >= 10000) {
      return (count / 10000).toFixed(1) + '万';
    }
    return count.toString();
  }
</script>

<div class="container mx-auto px-4 py-8">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">订阅管理</h1>
    <div class="flex gap-2">
      <button 
        on:click={() => showSearchModal = true} 
        class="btn btn-primary gap-2"
      >
        <Plus class="w-4 h-4" />
        添加订阅
      </button>
      <button 
        on:click={checkAllUpdates} 
        class="btn btn-outline gap-2"
        disabled={checkingUpdates}
      >
        <RefreshCw class="w-4 h-4 {checkingUpdates ? 'animate-spin' : ''}" />
        检查更新
      </button>
    </div>
  </div>

  <!-- 统计信息 -->
  <div class="stats shadow w-full mb-6">
    <div class="stat">
      <div class="stat-title">总订阅数</div>
      <div class="stat-value">{stats.total_subscriptions}</div>
      <div class="stat-desc">已启用 {stats.enabled_subscriptions} 个</div>
    </div>
    <div class="stat">
      <div class="stat-title">视频统计</div>
      <div class="stat-value">{stats.total_videos}</div>
      <div class="stat-desc">已下载 {stats.downloaded_videos} 个</div>
    </div>
    <div class="stat">
      <div class="stat-title">新视频</div>
      <div class="stat-value text-primary">{stats.new_videos}</div>
      <div class="stat-desc">待下载</div>
    </div>
  </div>

  <!-- 订阅列表 -->
  {#if loading}
    <div class="flex justify-center py-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else if subscriptions.length === 0}
    <div class="text-center py-12">
      <p class="text-base-content/60 mb-4">还没有订阅任何UP主</p>
      <button on:click={() => showSearchModal = true} class="btn btn-primary">
        添加第一个订阅
      </button>
    </div>
  {:else}
    <div class="grid gap-4">
      {#each subscriptions as subscription}
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <div class="flex items-start gap-4">
              <img 
                src={subscription.avatar} 
                alt={subscription.nickname}
                class="w-16 h-16 rounded-full object-cover"
              />
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-lg font-semibold">{subscription.nickname}</h3>
                    <p class="text-sm text-base-content/60">
                      {formatCount(subscription.follower_count)} 粉丝 · 
                      {subscription.aweme_count} 作品
                    </p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      on:click={() => toggleSubscription(subscription)}
                      class="btn btn-sm {subscription.enabled ? 'btn-success' : 'btn-ghost'}"
                      title={subscription.enabled ? '点击禁用' : '点击启用'}
                    >
                      {#if subscription.enabled}
                        <Eye class="w-4 h-4" />
                      {:else}
                        <EyeOff class="w-4 h-4" />
                      {/if}
                    </button>
                    <a 
                      href={subscription.user_url} 
                      target="_blank"
                      class="btn btn-sm btn-ghost"
                      title="访问主页"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                    <button
                      on:click={() => downloadNewVideos(subscription.user_id)}
                      class="btn btn-sm btn-primary"
                      title="下载新视频"
                    >
                      <Download class="w-4 h-4" />
                    </button>
                    <button
                      on:click={() => removeSubscription(subscription.user_id)}
                      class="btn btn-sm btn-error"
                      title="取消订阅"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {#if subscription.signature}
                  <p class="text-sm text-base-content/60 mt-2 line-clamp-2">
                    {subscription.signature}
                  </p>
                {/if}
                <div class="text-xs text-base-content/40 mt-2">
                  上次检查: {formatDate(subscription.last_check_time)} · 
                  订阅时间: {formatDate(subscription.created_at)}
                </div>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- 搜索用户模态框 -->
{#if showSearchModal}
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <h3 class="font-bold text-lg mb-4">添加订阅</h3>
      
      <div class="form-control">
        <div class="input-group">
          <input
            type="text"
            placeholder="搜索UP主名称..."
            class="input input-bordered flex-1"
            bind:value={searchQuery}
            on:keydown={(e) => e.key === 'Enter' && searchUsers()}
          />
          <button 
            class="btn btn-primary"
            on:click={searchUsers}
            disabled={searching || !searchQuery.trim()}
          >
            {#if searching}
              <span class="loading loading-spinner"></span>
            {:else}
              搜索
            {/if}
          </button>
        </div>
      </div>

      {#if searchResults.length > 0}
        <div class="mt-4 space-y-2 max-h-96 overflow-y-auto">
          {#each searchResults as user}
            <div class="card bg-base-200">
              <div class="card-body p-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <img 
                      src={user.avatar} 
                      alt={user.nickname}
                      class="w-12 h-12 rounded-full object-cover"
                    />
                    <div>
                      <p class="font-medium">{user.nickname}</p>
                      <p class="text-sm text-base-content/60">
                        {formatCount(user.follower_count)} 粉丝 · 
                        {user.aweme_count} 作品
                      </p>
                    </div>
                  </div>
                  <button
                    on:click={() => addSubscription(user)}
                    class="btn btn-sm btn-primary"
                  >
                    <Plus class="w-4 h-4" />
                    订阅
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}

      <div class="modal-action">
        <button 
          class="btn" 
          on:click={() => {
            showSearchModal = false;
            searchQuery = '';
            searchResults = [];
          }}
        >
          关闭
        </button>
      </div>
    </div>
  </div>
{/if}