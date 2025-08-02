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
      config = {
        cookie: response.data.cookie || '',
        save_path: response.data.save_path || '',
        proxy: response.data.proxy || ''
      };
      if (config.cookie) {
        // 加载配置后设置Cookie到API客户端
        api.setCookie(config.cookie);
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
        // 验证成功后设置Cookie到API客户端
        api.setCookie(config.cookie);
        message = 'Cookie验证成功';
        messageType = 'success';
      } else {
        message = 'Cookie验证失败，请检查是否有效';
        messageType = 'error';
      }
    } catch (error: any) {
      cookieValid = false;
      message = error.message || 'Cookie验证失败';
      messageType = 'error';
    } finally {
      loading = false;
      // 清除消息
      if (message) {
        setTimeout(() => {
          message = '';
        }, 3000);
      }
    }
  }

  async function saveConfig() {
    saveLoading = true;
    message = '';

    try {
      await api.updateConfig(config);
      if (config.cookie) {
        // 保存后设置Cookie到API客户端
        api.setCookie(config.cookie);
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
      <p class="text-sm text-muted-foreground">
        配置抖音Cookie以访问抖音数据
      </p>
    </CardHeader>
    <CardContent class="space-y-4">
      <div>
        <label for="cookie" class="mb-2 block text-sm font-medium">
          抖音 Cookie
        </label>
        <div class="flex gap-2">
          <Input
            id="cookie"
            type="password"
            bind:value={config.cookie}
            placeholder="请输入完整的Cookie字符串"
            class="flex-1 font-mono text-xs"
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
            <span class="text-sm text-red-600">Cookie 无效或已过期</span>
          {/if}
        </div>
        
        <!-- Cookie获取指导 -->
        <div class="mt-4 rounded-lg border bg-muted/50 p-4">
          <h4 class="mb-2 text-sm font-medium">如何获取Cookie:</h4>
          <ol class="space-y-1 text-xs text-muted-foreground">
            <li>1. 用浏览器打开 <a href="https://www.douyin.com" target="_blank" class="text-blue-600 hover:underline">www.douyin.com</a></li>
            <li>2. 登录你的抖音账号</li>
            <li>3. 按 F12 打开开发者工具</li>
            <li>4. 切换到 "Network" 或"网络"标签页</li>
            <li>5. 刷新页面，找到任意请求</li>
            <li>6. 在请求头中找到 "Cookie" 字段，复制整个值</li>
            <li>7. 将Cookie粘贴到上面的输入框中</li>
          </ol>
          <div class="mt-3 text-xs text-amber-600">
            <strong>注意:</strong> Cookie包含敏感信息，请勿分享给他人。Cookie可能会过期，需要定期更新。
          </div>
        </div>
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
        <Input
          id="save_path"
          type="text"
          bind:value={config.save_path}
          placeholder="例如：D:/DouYin/Downloads"
        />
        <p class="mt-1 text-xs text-muted-foreground">
          爬取的视频和图片将保存到此目录
        </p>
        <div class="mt-2 rounded-md bg-blue-50 p-3 text-xs">
          <p class="font-medium text-blue-900 mb-1">路径格式说明：</p>
          <ul class="space-y-1 text-blue-700">
            <li>• Windows: <code class="bg-blue-100 px-1 rounded">D:/Downloads</code> 或 <code class="bg-blue-100 px-1 rounded">D:\Downloads</code></li>
            <li>• 相对路径: <code class="bg-blue-100 px-1 rounded">./downloads</code></li>
            <li>• 路径会自动创建，无需手动创建文件夹</li>
          </ul>
        </div>
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

  <Card>
    <CardHeader>
      <CardTitle>常见问题</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="space-y-3 text-sm">
        <div>
          <h4 class="font-medium text-foreground">为什么需要Cookie？</h4>
          <p class="text-muted-foreground">Cookie包含登录状态信息，用于访问抖音的数据。没有有效的Cookie无法获取用户作品和详细信息。</p>
        </div>
        
        <div>
          <h4 class="font-medium text-foreground">Cookie多久会过期？</h4>
          <p class="text-muted-foreground">抖音Cookie通常在几小时到几天后过期，具体时间取决于账号活跃度。过期后需要重新获取。</p>
        </div>
        
        <div>
          <h4 class="font-medium text-foreground">爬取失败怎么办？</h4>
          <p class="text-muted-foreground">请检查：1) Cookie是否有效；2) 网络连接是否正常；3) 目标链接是否正确；4) 是否被抖音限制访问。</p>
        </div>
        
        <div>
          <h4 class="font-medium text-foreground">文件保存在哪里？</h4>
          <p class="text-muted-foreground">默认保存在 ./downloads 目录下，视频保存在 media 文件夹，数据表格保存在 excel 文件夹。可在存储设置中修改。</p>
        </div>
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