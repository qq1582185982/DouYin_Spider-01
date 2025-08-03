<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import { Calendar, Clock, Video, AlertCircle, CheckCircle, XCircle, ArrowLeft } from 'lucide-svelte';

	interface ScanLog {
		scan_id: string;
		scan_time: string;
		timestamp: number;
		total_subscriptions: number;
		scanned_subscriptions: number;
		failed_subscriptions: number;
		total_new_videos: number;
		scan_duration: number;
		subscription_results: Array<{
			user_id: string;
			nickname: string;
			new_videos_count: number;
			scan_time: number;
			error?: string;
		}>;
	}

	interface ScanStatistics {
		total_scans: number;
		total_new_videos: number;
		average_duration: number;
		success_rate: number;
		last_scan_time?: string;
	}

	let logs: ScanLog[] = [];
	let statistics: ScanStatistics | null = null;
	let loading = false;
	let selectedLog: ScanLog | null = null;

	onMount(() => {
		fetchLogs();
	});

	async function fetchLogs() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/logs?limit=50');
			const data = await response.json();
			
			if (data.code === 0) {
				logs = data.data.logs;
				statistics = data.data.statistics;
			} else {
				toast.error('获取扫描日志失败');
			}
		} catch (error) {
			toast.error('获取扫描日志失败');
		} finally {
			loading = false;
		}
	}

	async function viewLogDetail(log: ScanLog) {
		try {
			const response = await fetch(`http://localhost:8000/api/scan/logs/${log.scan_id}`);
			const data = await response.json();
			
			if (data.code === 0) {
				selectedLog = data.data;
			} else {
				toast.error('获取日志详情失败');
			}
		} catch (error) {
			toast.error('获取日志详情失败');
		}
	}

	function formatDate(dateStr: string | number): string {
		if (typeof dateStr === 'number') {
			return new Date(dateStr * 1000).toLocaleString('zh-CN');
		}
		return new Date(dateStr).toLocaleString('zh-CN');
	}

	function formatDuration(seconds: number): string {
		if (seconds < 60) return `${Math.floor(seconds)}秒`;
		if (seconds < 3600) return `${Math.floor(seconds / 60)}分${Math.floor(seconds % 60)}秒`;
		return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`;
	}

	function getStatusBadge(log: ScanLog) {
		if (log.failed_subscriptions > 0) {
			return { variant: 'destructive' as const, text: '部分失败' };
		}
		if (log.total_new_videos > 0) {
			return { variant: 'default' as const, text: '有新内容' };
		}
		return { variant: 'outline' as const, text: '无新内容' };
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-8">
		<div class="flex items-center gap-4 mb-4">
			<Button variant="ghost" size="icon" on:click={() => goto('/scan')}>
				<ArrowLeft class="h-4 w-4" />
			</Button>
			<div>
				<h1 class="text-3xl font-bold">扫描日志</h1>
				<p class="text-muted-foreground">查看历史扫描记录和统计信息</p>
			</div>
		</div>
	</div>

	{#if statistics}
		<div class="grid gap-4 md:grid-cols-4 mb-6">
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-sm font-medium">总扫描次数</CardTitle>
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{statistics.total_scans}</div>
				</CardContent>
			</Card>
			
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-sm font-medium">发现新视频</CardTitle>
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{statistics.total_new_videos}</div>
				</CardContent>
			</Card>
			
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-sm font-medium">平均耗时</CardTitle>
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{formatDuration(statistics.average_duration)}</div>
				</CardContent>
			</Card>
			
			<Card>
				<CardHeader class="pb-3">
					<CardTitle class="text-sm font-medium">成功率</CardTitle>
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{statistics.success_rate.toFixed(1)}%</div>
				</CardContent>
			</Card>
		</div>
	{/if}

	<!-- 日志列表 -->
	<Card>
		<CardHeader>
			<CardTitle>扫描历史</CardTitle>
		</CardHeader>
		<CardContent>
			{#if loading}
				<p class="text-center py-8 text-muted-foreground">加载中...</p>
			{:else if logs.length === 0}
				<p class="text-center py-8 text-muted-foreground">暂无扫描记录</p>
			{:else}
				<div class="space-y-4">
					{#each logs as log}
						<div class="border rounded-lg p-4 hover:bg-secondary/50 transition-colors cursor-pointer"
							on:click={() => viewLogDetail(log)}
							on:keydown={(e) => e.key === 'Enter' && viewLogDetail(log)}
							role="button"
							tabindex="0"
						>
							<div class="flex items-center justify-between mb-2">
								<div class="flex items-center gap-2">
									<Calendar class="w-4 h-4 text-muted-foreground" />
									<span class="text-sm">{formatDate(log.timestamp)}</span>
									<Badge {...getStatusBadge(log)}>
										{getStatusBadge(log).text}
									</Badge>
								</div>
								<div class="flex items-center gap-4 text-sm text-muted-foreground">
									<div class="flex items-center gap-1">
										<Clock class="w-4 h-4" />
										<span>{formatDuration(log.scan_duration)}</span>
									</div>
									<div class="flex items-center gap-1">
										<Video class="w-4 h-4" />
										<span>{log.total_new_videos} 新视频</span>
									</div>
								</div>
							</div>
							
							<div class="flex items-center gap-6 text-sm">
								<div class="flex items-center gap-2">
									<CheckCircle class="w-4 h-4 text-green-500" />
									<span>{log.scanned_subscriptions} 扫描成功</span>
								</div>
								{#if log.failed_subscriptions > 0}
									<div class="flex items-center gap-2">
										<XCircle class="w-4 h-4 text-red-500" />
										<span>{log.failed_subscriptions} 扫描失败</span>
									</div>
								{/if}
							</div>
							
							{#if log.subscription_results && log.subscription_results.some(r => r.new_videos_count > 0)}
								<div class="mt-2 pt-2 border-t">
									<div class="text-sm text-muted-foreground">
										新视频来源：
										{#each log.subscription_results.filter(r => r.new_videos_count > 0).slice(0, 3) as result}
											<span class="inline-block mr-2">
												{result.nickname} ({result.new_videos_count})
											</span>
										{/each}
										{#if log.subscription_results.filter(r => r.new_videos_count > 0).length > 3}
											<span>...</span>
										{/if}
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</CardContent>
	</Card>
</div>

<!-- 日志详情对话框 -->
{#if selectedLog}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		on:click={() => selectedLog = null}
		on:keydown={(e) => e.key === 'Escape' && (selectedLog = null)}
		role="button"
		tabindex="0"
	>
		<div class="bg-background rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto"
			on:click|stopPropagation
			on:keydown|stopPropagation
			role="dialog"
			tabindex="-1"
		>
			<h2 class="text-xl font-semibold mb-4">扫描详情</h2>
			
			<div class="space-y-4">
				<div>
					<p class="text-sm text-muted-foreground">扫描时间</p>
					<p>{formatDate(selectedLog.timestamp)}</p>
				</div>
				
				<div class="grid grid-cols-3 gap-4">
					<div>
						<p class="text-sm text-muted-foreground">总订阅数</p>
						<p class="font-medium">{selectedLog.total_subscriptions}</p>
					</div>
					<div>
						<p class="text-sm text-muted-foreground">扫描成功</p>
						<p class="font-medium text-green-600">{selectedLog.scanned_subscriptions}</p>
					</div>
					<div>
						<p class="text-sm text-muted-foreground">扫描失败</p>
						<p class="font-medium text-red-600">{selectedLog.failed_subscriptions}</p>
					</div>
				</div>
				
				<div>
					<p class="text-sm text-muted-foreground mb-2">订阅扫描结果</p>
					<div class="space-y-2 max-h-60 overflow-auto">
						{#each selectedLog.subscription_results as result}
							<div class="border rounded p-2">
								<div class="flex items-center justify-between">
									<span class="font-medium">{result.nickname}</span>
									{#if result.error}
										<Badge variant="destructive" class="text-xs">失败</Badge>
									{:else if result.new_videos_count > 0}
										<Badge variant="default" class="text-xs">
											{result.new_videos_count} 新视频
										</Badge>
									{:else}
										<Badge variant="outline" class="text-xs">无新内容</Badge>
									{/if}
								</div>
								{#if result.error}
									<p class="text-sm text-red-500 mt-1">{result.error}</p>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
			
			<div class="mt-6 flex justify-end">
				<Button variant="outline" on:click={() => selectedLog = null}>
					关闭
				</Button>
			</div>
		</div>
	</div>
{/if}