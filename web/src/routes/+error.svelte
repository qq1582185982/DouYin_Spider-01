<script lang="ts">
  import { page } from '$app/stores';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Home, ArrowLeft } from 'lucide-svelte';
</script>

<div class="flex min-h-[60vh] flex-col items-center justify-center">
  <div class="text-center">
    <h1 class="mb-4 text-6xl font-bold text-muted-foreground">{$page.status}</h1>
    <p class="mb-8 text-xl">
      {#if $page.status === 404}
        页面未找到
      {:else if $page.status === 500}
        服务器错误
      {:else}
        出错了
      {/if}
    </p>
    <p class="mb-8 text-muted-foreground">
      {$page.error?.message || '请求的页面不存在或已被移动'}
    </p>
    <div class="flex gap-4 justify-center">
      <Button on:click={() => history.back()} variant="outline">
        <ArrowLeft class="mr-2 h-4 w-4" />
        返回上一页
      </Button>
      <Button on:click={() => window.location.href = '/'}>
        <Home class="mr-2 h-4 w-4" />
        返回首页
      </Button>
    </div>
  </div>
</div>