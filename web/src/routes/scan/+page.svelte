<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { toast } from 'svelte-sonner';
	import { Play, Pause, RotateCw, Settings, FileText } from 'lucide-svelte';
	
	// 导入子页面组件
	import ScanLogs from './logs/+page.svelte';
	import ScanSettings from './settings/+page.svelte';

	interface ScanStatus {
		running: boolean;
		scanning: boolean;
		paused: boolean;
		scan_interval: number;
		auto_download: boolean;
		last_scan: {
			last_scan_time: string;
			time_since_last_scan: number;
			scan_round: number;
		};
	}

	interface ScanStatistics {
		total_tracked: number;
		scan_round: number;
		average_scan_interval: number;
		oldest_unscanned: {
			user_id: string;
			time_since_scan: number;
		} | null;
	}

	let scanStatus: ScanStatus | null = null;
	let scanStatistics: ScanStatistics | null = null;
	let loading = false;
	let statusInterval: ReturnType<typeof setInterval>;
	
	// 根据URL参数决定显示哪个视图
	$: view = $page.url.searchParams.get('view') || 'main';

	onMount(() => {
		fetchScanStatus();
		// 每5秒更新一次状态
		statusInterval = setInterval(fetchScanStatus, 5000);
	});

	onDestroy(() => {
		if (statusInterval) {
			clearInterval(statusInterval);
		}
	});

	async function fetchScanStatus() {
		try {
			const response = await fetch('http://localhost:8000/api/scan/status');
			const data = await response.json();
			
			if (data.code === 0) {
				scanStatus = data.data.status;
				scanStatistics = data.data.statistics;
			}
		} catch (error) {
			console.error('获取扫描状态失败:', error);
		}
	}

	async function startScan() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/start', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					scan_interval: 3600,
					auto_download: true
				})
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('扫描任务已启动');
				await fetchScanStatus();
			} else {
				toast.error(data.message || '启动扫描失败');
			}
		} catch (error) {
			toast.error('启动扫描失败');
		} finally {
			loading = false;
		}
	}

	async function stopScan() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/stop', {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('扫描任务已停止');
				await fetchScanStatus();
			} else {
				toast.error(data.message || '停止扫描失败');
			}
		} catch (error) {
			toast.error('停止扫描失败');
		} finally {
			loading = false;
		}
	}

	async function pauseScan() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/pause', {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('扫描已暂停');
				await fetchScanStatus();
			} else {
				toast.error(data.message || '暂停扫描失败');
			}
		} catch (error) {
			toast.error('暂停扫描失败');
		} finally {
			loading = false;
		}
	}

	async function resumeScan() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/resume', {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('扫描已恢复');
				await fetchScanStatus();
			} else {
				toast.error(data.message || '恢复扫描失败');
			}
		} catch (error) {
			toast.error('恢复扫描失败');
		} finally {
			loading = false;
		}
	}

	async function manualScan() {
		loading = true;
		try {
			const response = await fetch('http://localhost:8000/api/scan/once', {
				method: 'POST'
			});
			
			const data = await response.json();
			if (data.code === 0) {
				toast.success('手动扫描已触发');
				// 可以跟踪任务状态
			} else {
				toast.error(data.message || '触发扫描失败');
			}
		} catch (error) {
			toast.error('触发扫描失败');
		} finally {
			loading = false;
		}
	}

	function formatDuration(seconds: number): string {
		if (seconds < 60) return `${Math.floor(seconds)}秒`;
		if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
		if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`;
		return `${Math.floor(seconds / 86400)}天`;
	}
</script>

{#if view === 'logs'}
	<ScanLogs />
{:else if view === 'settings'}
	<ScanSettings />
{:else}
	<div class="container mx-auto px-4 py-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold mb-2">订阅扫描管理</h1>
		<p class="text-muted-foreground">管理订阅的自动扫描任务，及时发现新视频</p>
	</div>

	<div class="grid gap-6 md:grid-cols-2">
		<!-- 扫描状态卡片 -->
		<Card class="p-6">
			<h2 class="text-xl font-semibold mb-4">扫描状态</h2>
			
			{#if scanStatus}
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<span>运行状态</span>
						<Badge variant={scanStatus.running ? 'default' : 'secondary'}>
							{scanStatus.running ? '运行中' : '已停止'}
						</Badge>
					</div>
					
					{#if scanStatus.running}
						<div class="flex items-center justify-between">
							<span>当前状态</span>
							<Badge variant={scanStatus.scanning ? 'default' : 'outline'}>
								{scanStatus.scanning ? '扫描中' : (scanStatus.paused ? '已暂停' : '等待中')}
							</Badge>
						</div>
					{/if}
					
					<div class="flex items-center justify-between">
						<span>扫描间隔</span>
						<span class="text-muted-foreground">{formatDuration(scanStatus.scan_interval)}</span>
					</div>
					
					<div class="flex items-center justify-between">
						<span>自动下载</span>
						<Badge variant={scanStatus.auto_download ? 'default' : 'outline'}>
							{scanStatus.auto_download ? '开启' : '关闭'}
						</Badge>
					</div>
					
					{#if scanStatus.last_scan.last_scan_time !== '从未扫描'}
						<div class="pt-2 border-t">
							<div class="flex items-center justify-between">
								<span>上次扫描</span>
								<span class="text-sm text-muted-foreground">{scanStatus.last_scan.last_scan_time}</span>
							</div>
							<div class="flex items-center justify-between">
								<span>扫描轮次</span>
								<span class="text-sm text-muted-foreground">第 {scanStatus.last_scan.scan_round} 轮</span>
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<p class="text-muted-foreground">加载中...</p>
			{/if}
		</Card>

		<!-- 扫描统计卡片 -->
		<Card class="p-6">
			<h2 class="text-xl font-semibold mb-4">扫描统计</h2>
			
			{#if scanStatistics}
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<span>跟踪订阅数</span>
						<span class="font-medium">{scanStatistics.total_tracked}</span>
					</div>
					
					<div class="flex items-center justify-between">
						<span>总扫描轮次</span>
						<span class="font-medium">{scanStatistics.scan_round}</span>
					</div>
					
					<div class="flex items-center justify-between">
						<span>平均扫描间隔</span>
						<span class="text-muted-foreground">{formatDuration(scanStatistics.average_scan_interval)}</span>
					</div>
					
					{#if scanStatistics.oldest_unscanned}
						<div class="pt-2 border-t">
							<p class="text-sm text-muted-foreground">
								最久未扫描: {formatDuration(scanStatistics.oldest_unscanned.time_since_scan)}前
							</p>
						</div>
					{/if}
				</div>
			{:else}
				<p class="text-muted-foreground">加载中...</p>
			{/if}
		</Card>
	</div>

	<!-- 控制按钮 -->
	<Card class="mt-6 p-6">
		<h2 class="text-xl font-semibold mb-4">扫描控制</h2>
		
		<div class="flex flex-wrap gap-4">
			{#if scanStatus?.running}
				<Button 
					variant="destructive" 
					on:click={stopScan} 
					disabled={loading}
				>
					<Play class="w-4 h-4 mr-2" />
					停止扫描
				</Button>
				
				{#if scanStatus.paused}
					<Button 
						on:click={resumeScan} 
						disabled={loading}
					>
						<Play class="w-4 h-4 mr-2" />
						恢复扫描
					</Button>
				{:else}
					<Button 
						variant="outline"
						on:click={pauseScan} 
						disabled={loading || scanStatus.scanning}
					>
						<Pause class="w-4 h-4 mr-2" />
						暂停扫描
					</Button>
				{/if}
			{:else}
				<Button 
					on:click={startScan} 
					disabled={loading}
				>
					<Play class="w-4 h-4 mr-2" />
					启动扫描
				</Button>
			{/if}
			
			<Button 
				variant="outline"
				on:click={manualScan} 
				disabled={loading || scanStatus?.scanning}
			>
				<RotateCw class="w-4 h-4 mr-2" />
				手动扫描一次
			</Button>
			
			<Button variant="outline" on:click={() => goto('/scan?view=settings')}>
				<Settings class="w-4 h-4 mr-2" />
				扫描设置
			</Button>
		</div>
	</Card>

	<!-- 扫描日志 -->
	<Card class="mt-6 p-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-xl font-semibold">最近扫描</h2>
			<Button variant="outline" size="sm" on:click={() => goto('/scan?view=logs')}>
				查看全部
			</Button>
		</div>
		<div class="text-sm text-muted-foreground">
			<p>查看 <a href="/scan?view=logs" class="text-primary hover:underline">扫描日志</a> 了解详细的扫描历史记录</p>
		</div>
	</Card>
</div>
{/if}