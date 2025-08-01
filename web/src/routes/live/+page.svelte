<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Radio, Play, Square, MessageCircle, Gift, Heart, Users } from 'lucide-svelte';
  import api from '$lib/api';
  import { wsManager } from '$lib/ws';
  import type { LiveMessage } from '$lib/types';

  let liveUrl = '';
  let isMonitoring = false;
  let sessionId = '';
  let messages: LiveMessage[] = [];
  let unsubscribe: (() => void) | null = null;
  let autoScroll = true;
  let messagesContainer: HTMLDivElement;

  async function startMonitoring() {
    if (!liveUrl.trim()) {
      return;
    }

    try {
      const response = await api.startLiveMonitor(liveUrl);
      sessionId = response.data;
      
      // 连接WebSocket
      await wsManager.connect(sessionId);
      
      // 订阅消息
      unsubscribe = wsManager.subscribe((message) => {
        messages = [...messages, message];
        if (messages.length > 500) {
          messages = messages.slice(-500);
        }
        
        if (autoScroll && messagesContainer) {
          requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          });
        }
      });
      
      isMonitoring = true;
    } catch (error) {
      console.error('Failed to start monitoring:', error);
    }
  }

  async function stopMonitoring() {
    if (sessionId) {
      try {
        await api.stopLiveMonitor(sessionId);
      } catch (error) {
        console.error('Failed to stop monitoring:', error);
      }
    }
    
    if (unsubscribe) {
      unsubscribe();
      unsubscribe = null;
    }
    
    wsManager.disconnect();
    isMonitoring = false;
    sessionId = '';
  }

  onDestroy(() => {
    if (isMonitoring) {
      stopMonitoring();
    }
  });

  function getMessageIcon(type: string) {
    switch (type) {
      case 'gift':
        return Gift;
      case 'chat':
        return MessageCircle;
      case 'member':
        return Users;
      case 'like':
        return Heart;
      default:
        return MessageCircle;
    }
  }

  function getMessageColor(type: string) {
    switch (type) {
      case 'gift':
        return 'text-yellow-600';
      case 'like':
        return 'text-red-600';
      case 'member':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  }
</script>

<svelte:head>
  <title>直播监控 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">直播监控</h1>
    <p class="text-muted-foreground">实时监控直播间弹幕和礼物</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>监控设置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="liveUrl" class="mb-2 block text-sm font-medium">
          直播间URL
        </label>
        <div class="flex gap-2">
          <Input
            id="liveUrl"
            type="url"
            bind:value={liveUrl}
            placeholder="https://live.douyin.com/..."
            disabled={isMonitoring}
            class="flex-1"
          />
          {#if !isMonitoring}
            <Button on:click={startMonitoring} disabled={!liveUrl.trim()}>
              <Play class="mr-2 h-4 w-4" />
              开始监控
            </Button>
          {:else}
            <Button on:click={stopMonitoring} variant="destructive">
              <Square class="mr-2 h-4 w-4" />
              停止监控
            </Button>
          {/if}
        </div>
      </div>

      {#if isMonitoring}
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Radio class="h-4 w-4 animate-pulse text-red-600" />
            <span class="text-sm font-medium">正在监控中</span>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              bind:checked={autoScroll}
              class="h-4 w-4"
            />
            自动滚动
          </label>
        </div>
      {/if}
    </CardContent>
  </Card>

  {#if isMonitoring}
    <Card>
      <CardHeader>
        <CardTitle>实时消息</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          bind:this={messagesContainer}
          class="h-96 overflow-y-auto rounded border bg-gray-50 p-4 dark:bg-gray-900"
        >
          {#if messages.length === 0}
            <p class="text-center text-muted-foreground">等待消息...</p>
          {:else}
            <div class="space-y-2">
              {#each messages as message}
                <div class="flex items-start gap-2 text-sm">
                  <svelte:component
                    this={getMessageIcon(message.type)}
                    class={`mt-0.5 h-4 w-4 flex-shrink-0 ${getMessageColor(message.type)}`}
                  />
                  <div class="flex-1">
                    {#if message.type === 'gift'}
                      <span class="font-medium">{message.user?.nickname}</span>
                      送出
                      <span class="font-medium text-yellow-600">{message.gift?.name}</span>
                      x{message.gift?.count}
                    {:else if message.type === 'chat'}
                      <span class="font-medium">{message.user?.nickname}:</span>
                      {message.content}
                    {:else if message.type === 'like'}
                      <span class="font-medium">{message.user?.nickname}</span>
                      点赞了
                    {:else if message.type === 'member'}
                      <span class="font-medium">{message.user?.nickname}</span>
                      进入直播间
                    {/if}
                    <span class="ml-2 text-xs text-muted-foreground">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </CardContent>
    </Card>
  {/if}
</div>