<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Label } from '$lib/components/ui/label';
	import { Input } from '$lib/components/ui/input';
	import { Switch } from '$lib/components/ui/switch';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';
	import { toast } from 'svelte-sonner';
	import { AlertCircle, Save, RotateCcw, ArrowLeft } from 'lucide-svelte';

	interface ScanConfig {
		enabled: boolean;
		scan_interval: number;
		auto_download: boolean;
		max_videos_per_scan: number;
		source_delay: number;
		retry_on_error: boolean;
		max_retries: number;
		notify_on_complete: boolean;
		notify_on_new_videos: boolean;
		notify_on_error: boolean;
		min_videos_for_notification: number;
		log_retention_days: number;
		detailed_logging: boolean;
		concurrent_downloads: number;
		download_timeout: number;
		pause_on_risk_control: boolean;
		risk_control_pause_minutes: number;
	}

	interface ValidationResult {
		valid: boolean;
		errors: string[];
		warnings: string[];
	}

	let config: ScanConfig | null = null;
	let validation: ValidationResult | null = null;
	let loading = false;
	let saving = false;
	let hasChanges = false;
	let originalConfig: string = '';

	onMount(() => {
		fetchConfig();
	});

	async function fetchConfig() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/config');
			const data = await response.json();
			
			if (data.code === 0) {
				config = data.data.config;
				validation = data.data.validation;
				originalConfig = JSON.stringify(config);
			} else {
				toast.error('获取扫描配置失败');
			}
		} catch (error) {
			toast.error('获取扫描配置失败');
		} finally {
			loading = false;
		}
	}

	async function saveConfig() {
		if (!config || !hasChanges) return;
		
		saving = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/config', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config)
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('配置已保存');
				originalConfig = JSON.stringify(config);
				hasChanges = false;
				// 重新获取配置和验证
				await fetchConfig();
			} else {
				toast.error(data.message || '保存配置失败');
			}
		} catch (error) {
			toast.error('保存配置失败');
		} finally {
			saving = false;
		}
	}

	async function resetConfig() {
		if (!confirm('确定要重置为默认配置吗？')) return;
		
		try {
			const response = await fetch('http://localhost:8000/api/scan/config/reset', {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('配置已重置');
				config = data.data;
				originalConfig = JSON.stringify(config);
				hasChanges = false;
				await fetchConfig();
			} else {
				toast.error('重置配置失败');
			}
		} catch (error) {
			toast.error('重置配置失败');
		}
	}

	function onConfigChange() {
		hasChanges = JSON.stringify(config) !== originalConfig;
	}

	function formatSeconds(seconds: number): string {
		if (seconds < 60) return `${seconds}秒`;
		if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
		return `${Math.floor(seconds / 3600)}小时`;
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-8 flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Button variant="ghost" size="icon" on:click={() => goto('/scan')}>
				<ArrowLeft class="h-4 w-4" />
			</Button>
			<div>
				<h1 class="text-3xl font-bold mb-2">扫描设置</h1>
				<p class="text-muted-foreground">配置订阅扫描的各项参数</p>
			</div>
		</div>
		
		<div class="flex gap-2">
			<Button variant="outline" on:click={resetConfig} disabled={loading}>
				<RotateCcw class="w-4 h-4 mr-2" />
				重置默认
			</Button>
			<Button on:click={saveConfig} disabled={loading || saving || !hasChanges}>
				<Save class="w-4 h-4 mr-2" />
				保存设置
			</Button>
		</div>
	</div>

	{#if validation && (!validation.valid || validation.warnings.length > 0)}
		<div class="mb-6 space-y-2">
			{#each validation.errors as error}
				<div class="flex items-center gap-2 text-red-600">
					<AlertCircle class="w-4 h-4" />
					<span class="text-sm">{error}</span>
				</div>
			{/each}
			{#each validation.warnings as warning}
				<div class="flex items-center gap-2 text-yellow-600">
					<AlertCircle class="w-4 h-4" />
					<span class="text-sm">{warning}</span>
				</div>
			{/each}
		</div>
	{/if}

	{#if loading}
		<p class="text-center py-8">加载中...</p>
	{:else if config}
		<div class="space-y-6">
			<!-- 基本设置 -->
			<Card>
				<CardHeader>
					<CardTitle>基本设置</CardTitle>
					<CardDescription>扫描任务的基本参数配置</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="flex items-center justify-between">
						<div>
							<Label for="enabled">启用自动扫描</Label>
							<p class="text-sm text-muted-foreground">开启后将按设定间隔自动扫描订阅</p>
						</div>
						<Switch
							id="enabled"
							bind:checked={config.enabled}
							on:change={onConfigChange}
						/>
					</div>
					
					<Separator />
					
					<div class="grid gap-4 md:grid-cols-2">
						<div class="space-y-2">
							<Label for="scan_interval">扫描间隔（秒）</Label>
							<Input
								id="scan_interval"
								type="number"
								min="60"
								bind:value={config.scan_interval}
								on:input={onConfigChange}
							/>
							<p class="text-xs text-muted-foreground">
								当前设置：{formatSeconds(config.scan_interval)}
							</p>
						</div>
						
						<div class="space-y-2">
							<Label for="source_delay">订阅间延迟（秒）</Label>
							<Input
								id="source_delay"
								type="number"
								min="1"
								bind:value={config.source_delay}
								on:input={onConfigChange}
							/>
							<p class="text-xs text-muted-foreground">扫描不同订阅之间的延迟</p>
						</div>
					</div>
					
					<div class="flex items-center justify-between">
						<div>
							<Label for="auto_download">自动下载新视频</Label>
							<p class="text-sm text-muted-foreground">发现新视频时自动开始下载</p>
						</div>
						<Switch
							id="auto_download"
							bind:checked={config.auto_download}
							on:change={onConfigChange}
						/>
					</div>
				</CardContent>
			</Card>

			<!-- 高级设置 -->
			<Card>
				<CardHeader>
					<CardTitle>高级设置</CardTitle>
					<CardDescription>性能和行为的详细配置</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="grid gap-4 md:grid-cols-2">
						<div class="space-y-2">
							<Label for="max_videos_per_scan">每次扫描最大视频数</Label>
							<Input
								id="max_videos_per_scan"
								type="number"
								min="1"
								max="200"
								bind:value={config.max_videos_per_scan}
								on:input={onConfigChange}
							/>
						</div>
						
						<div class="space-y-2">
							<Label for="concurrent_downloads">并发下载数</Label>
							<Input
								id="concurrent_downloads"
								type="number"
								min="1"
								max="10"
								bind:value={config.concurrent_downloads}
								on:input={onConfigChange}
							/>
						</div>
					</div>
					
					<div class="flex items-center justify-between">
						<div>
							<Label for="retry_on_error">出错时重试</Label>
							<p class="text-sm text-muted-foreground">扫描失败时自动重试</p>
						</div>
						<Switch
							id="retry_on_error"
							bind:checked={config.retry_on_error}
							on:change={onConfigChange}
						/>
					</div>
					
					{#if config.retry_on_error}
						<div class="space-y-2 pl-6">
							<Label for="max_retries">最大重试次数</Label>
							<Input
								id="max_retries"
								type="number"
								min="1"
								max="10"
								bind:value={config.max_retries}
								on:input={onConfigChange}
								class="w-32"
							/>
						</div>
					{/if}
				</CardContent>
			</Card>

			<!-- 通知设置 -->
			<Card>
				<CardHeader>
					<CardTitle>通知设置</CardTitle>
					<CardDescription>配置各种事件的通知行为</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="flex items-center justify-between">
						<Label for="notify_on_complete">扫描完成时通知</Label>
						<Switch
							id="notify_on_complete"
							bind:checked={config.notify_on_complete}
							on:change={onConfigChange}
						/>
					</div>
					
					<div class="flex items-center justify-between">
						<Label for="notify_on_new_videos">发现新视频时通知</Label>
						<Switch
							id="notify_on_new_videos"
							bind:checked={config.notify_on_new_videos}
							on:change={onConfigChange}
						/>
					</div>
					
					{#if config.notify_on_new_videos}
						<div class="space-y-2 pl-6">
							<Label for="min_videos_for_notification">触发通知的最小视频数</Label>
							<Input
								id="min_videos_for_notification"
								type="number"
								min="1"
								bind:value={config.min_videos_for_notification}
								on:input={onConfigChange}
								class="w-32"
							/>
						</div>
					{/if}
					
					<div class="flex items-center justify-between">
						<Label for="notify_on_error">出错时通知</Label>
						<Switch
							id="notify_on_error"
							bind:checked={config.notify_on_error}
							on:change={onConfigChange}
						/>
					</div>
				</CardContent>
			</Card>

			<!-- 风控设置 -->
			<Card>
				<CardHeader>
					<CardTitle>风控设置</CardTitle>
					<CardDescription>处理平台风控的策略配置</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="flex items-center justify-between">
						<div>
							<Label for="pause_on_risk_control">遇到风控时暂停</Label>
							<p class="text-sm text-muted-foreground">检测到风控时自动暂停扫描</p>
						</div>
						<Switch
							id="pause_on_risk_control"
							bind:checked={config.pause_on_risk_control}
							on:change={onConfigChange}
						/>
					</div>
					
					{#if config.pause_on_risk_control}
						<div class="space-y-2">
							<Label for="risk_control_pause_minutes">风控暂停时间（分钟）</Label>
							<Input
								id="risk_control_pause_minutes"
								type="number"
								min="5"
								max="1440"
								bind:value={config.risk_control_pause_minutes}
								on:input={onConfigChange}
							/>
							<p class="text-xs text-muted-foreground">
								暂停 {config.risk_control_pause_minutes} 分钟后自动恢复
							</p>
						</div>
					{/if}
				</CardContent>
			</Card>

			<!-- 日志设置 -->
			<Card>
				<CardHeader>
					<CardTitle>日志设置</CardTitle>
					<CardDescription>扫描日志的记录和清理配置</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="space-y-2">
						<Label for="log_retention_days">日志保留天数</Label>
						<Input
							id="log_retention_days"
							type="number"
							min="1"
							max="365"
							bind:value={config.log_retention_days}
							on:input={onConfigChange}
						/>
						<p class="text-xs text-muted-foreground">超过此天数的日志将被自动清理</p>
					</div>
					
					<div class="flex items-center justify-between">
						<div>
							<Label for="detailed_logging">详细日志</Label>
							<p class="text-sm text-muted-foreground">记录更多调试信息（可能影响性能）</p>
						</div>
						<Switch
							id="detailed_logging"
							bind:checked={config.detailed_logging}
							on:change={onConfigChange}
						/>
					</div>
				</CardContent>
			</Card>
		</div>
	{/if}
</div>