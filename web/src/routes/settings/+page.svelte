<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Settings, Save, CheckCircle, XCircle, FolderOpen } from 'lucide-svelte';
  import api from '$lib/api';

  let config = {
    cookie: '',
    save_path: '',
    proxy: ''
  };
  let cookieValid = false;
  let loading = false;
  let saveLoading = false;
  let message = '';
  let messageType: 'success' | 'error' = 'success';

  async function loadConfig() {
    try {
      const response = await api.getConfig();
      config = response.data;
      if (config.cookie) {
        await validateCookie();
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  }

  async function validateCookie() {
    if (!config.cookie) {
      cookieValid = false;
      return;
    }

    loading = true;
    try {
      const response = await api.validateCookie(config.cookie);
      cookieValid = response.data;
      if (cookieValid) {
        api.setCookie(config.cookie);
      }
    } catch (error) {
      cookieValid = false;
    } finally {
      loading = false;
    }
  }

  async function saveConfig() {
    saveLoading = true;
    message = '';

    try {
      await api.updateConfig(config);
      if (config.cookie) {
        await validateCookie();
      }
      message = '配置保存成功';
      messageType = 'success';
    } catch (error: any) {
      message = error.message || '保存失败';
      messageType = 'error';
    } finally {
      saveLoading = false;
      setTimeout(() => {
        message = '';
      }, 3000);
    }
  }

  onMount(() => {
    loadConfig();
  });
</script>

<svelte:head>
  <title>设置 - DouYin Spider</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold">设置</h1>
    <p class="text-muted-foreground">配置系统参数</p>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>Cookie 配置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="cookie" class="mb-2 block text-sm font-medium">
          抖音 Cookie
        </label>
        <div class="flex gap-2">
          <Input
            id="cookie"
            type="text"
            bind:value={config.cookie}
            placeholder="请输入抖音Cookie"
            class="flex-1"
          />
          <Button 
            on:click={validateCookie} 
            disabled={loading || !config.cookie}
            variant="outline"
          >
            {#if loading}
              验证中...
            {:else}
              验证
            {/if}
          </Button>
        </div>
        <div class="mt-2 flex items-center gap-2">
          {#if cookieValid}
            <CheckCircle class="h-4 w-4 text-green-600" />
            <span class="text-sm text-green-600">Cookie 有效</span>
          {:else if config.cookie && !loading}
            <XCircle class="h-4 w-4 text-red-600" />
            <span class="text-sm text-red-600">Cookie 无效</span>
          {/if}
        </div>
        <p class="mt-1 text-xs text-muted-foreground">
          请从浏览器开发者工具中复制完整的Cookie字符串
        </p>
      </div>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>存储设置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="save_path" class="mb-2 block text-sm font-medium">
          保存路径
        </label>
        <div class="flex gap-2">
          <Input
            id="save_path"
            type="text"
            bind:value={config.save_path}
            placeholder="例如：D:/DouYin/Downloads"
            class="flex-1"
          />
          <Button variant="outline" size="icon">
            <FolderOpen class="h-4 w-4" />
          </Button>
        </div>
        <p class="mt-1 text-xs text-muted-foreground">
          爬取的视频和图片将保存到此目录
        </p>
      </div>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle>网络设置</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="proxy" class="mb-2 block text-sm font-medium">
          代理服务器（可选）
        </label>
        <Input
          id="proxy"
          type="text"
          bind:value={config.proxy}
          placeholder="例如：http://127.0.0.1:7890"
        />
        <p class="mt-1 text-xs text-muted-foreground">
          如需使用代理，请输入代理服务器地址
        </p>
      </div>
    </CardContent>
  </Card>

  <div class="flex justify-end">
    <Button on:click={saveConfig} disabled={saveLoading}>
      {#if saveLoading}
        保存中...
      {:else}
        <Save class="mr-2 h-4 w-4" />
        保存配置
      {/if}
    </Button>
  </div>

  {#if message}
    <div class={`fixed bottom-4 right-4 rounded-lg p-4 shadow-lg ${
      messageType === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
    }`}>
      {message}
    </div>
  {/if}
</div>