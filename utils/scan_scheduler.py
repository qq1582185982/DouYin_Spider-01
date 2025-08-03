# coding=utf-8
"""
扫描调度器，负责定期扫描订阅并管理扫描任务
参考Bilibili项目的video_downloader设计
"""
import asyncio
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging
from loguru import logger as loguru_logger

from .scan_collector import ScanCollector, ScanSummary
from .scan_tracker import ScanTracker
from .database import get_database
from .notification import send_scan_notification
from .scan_logger import get_scan_logger
from .scan_config import get_scan_config
from dy_apis.douyin_async_api import DouyinAsyncAPI
from builder.auth import DouyinAuth

# 配置logger
logger = logging.getLogger(__name__)


class ScanController:
    """扫描控制器，用于控制扫描的暂停/恢复"""
    
    def __init__(self):
        self._is_paused = False
        self._is_scanning = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 初始状态为未暂停
        
    def pause(self):
        """暂停扫描"""
        self._is_paused = True
        self._pause_event.clear()
        logger.info("扫描已暂停")
        
    def resume(self):
        """恢复扫描"""
        self._is_paused = False
        self._pause_event.set()
        logger.info("扫描已恢复")
        
    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self._is_paused
        
    async def wait_if_paused(self):
        """如果暂停则等待"""
        await self._pause_event.wait()
        
    def set_scanning(self, scanning: bool):
        """设置扫描状态"""
        self._is_scanning = scanning
        
    def is_scanning(self) -> bool:
        """获取扫描状态"""
        return self._is_scanning


class SubscriptionScanner:
    """订阅扫描器"""
    
    def __init__(self, scan_interval: int = 3600, auto_download: bool = True):
        """
        初始化扫描器
        :param scan_interval: 扫描间隔（秒），默认1小时
        :param auto_download: 是否自动下载新视频
        """
        self.scan_interval = scan_interval
        self.auto_download = auto_download
        self.controller = ScanController()
        self.tracker = ScanTracker()
        self.api: Optional[DouyinAsyncAPI] = None  # 延迟初始化
        self._scan_task: Optional[asyncio.Task] = None
        self._on_new_videos_callback: Optional[Callable] = None
        self._auth: Optional[DouyinAuth] = None
        
    def set_on_new_videos_callback(self, callback: Callable[[str, List[Dict]], None]):
        """设置发现新视频时的回调函数"""
        self._on_new_videos_callback = callback
        
    def set_auth(self, auth: DouyinAuth):
        """设置认证信息"""
        self._auth = auth
        self.api = DouyinAsyncAPI(auth)
        
    async def start(self):
        """启动扫描任务"""
        if self._scan_task and not self._scan_task.done():
            logger.warning("扫描任务已在运行中")
            return
            
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info(f"订阅扫描任务已启动，扫描间隔: {self.scan_interval}秒")
        
    async def stop(self):
        """停止扫描任务"""
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            logger.info("订阅扫描任务已停止")
            
    def pause(self):
        """暂停扫描"""
        self.controller.pause()
        
    def resume(self):
        """恢复扫描"""
        self.controller.resume()
        
    def is_scanning(self) -> bool:
        """是否正在扫描"""
        return self.controller.is_scanning()
        
    def get_status(self) -> Dict:
        """获取扫描器状态"""
        return {
            'running': self._scan_task and not self._scan_task.done(),
            'scanning': self.controller.is_scanning(),
            'paused': self.controller.is_paused(),
            'scan_interval': self.scan_interval,
            'auto_download': self.auto_download,
            'last_scan': self.tracker.get_last_scan_info()
        }
        
    async def _scan_loop(self):
        """扫描循环主逻辑"""
        while True:
            try:
                # 检查是否暂停
                await self.controller.wait_if_paused()
                
                # 开始新一轮扫描
                await self._perform_scan()
                
                # 等待下一轮扫描
                logger.info(f"本轮扫描完成，等待 {self.scan_interval} 秒后进行下一轮扫描")
                
                # 智能等待，支持中断
                remaining_time = self.scan_interval
                check_interval = 5  # 每5秒检查一次
                
                while remaining_time > 0:
                    await self.controller.wait_if_paused()
                    
                    sleep_time = min(remaining_time, check_interval)
                    await asyncio.sleep(sleep_time)
                    remaining_time -= sleep_time
                    
                    # 可以在这里添加配置更新检查等逻辑
                    
            except asyncio.CancelledError:
                logger.info("扫描循环被取消")
                break
            except Exception as e:
                logger.error(f"扫描循环出错: {e}", exc_info=True)
                # 出错后等待一段时间再重试
                await asyncio.sleep(60)
                
    async def _perform_scan(self):
        """执行一轮扫描"""
        self.controller.set_scanning(True)
        collector = ScanCollector()
        
        try:
            # 开始新一轮扫描
            self.tracker.start_new_round()
            
            # 获取数据库连接
            db = get_database()
            
            # 获取所有启用的订阅
            subscriptions = db.get_all_subscriptions(enabled_only=True)
            
            if not subscriptions:
                logger.info("没有启用的订阅需要扫描")
                return
                
            # 设置总订阅数
            collector.set_total_subscriptions(len(subscriptions))
            
            # 清理已移除订阅的进度记录
            active_ids = [sub['user_id'] for sub in subscriptions]
            self.tracker.cleanup_removed_subscriptions(active_ids)
            
            # 按优先级分组（新订阅优先）
            new_subs, old_subs = self.tracker.group_subscriptions_by_priority(subscriptions)
            
            if new_subs:
                logger.info(f"检测到 {len(new_subs)} 个新订阅，将优先扫描")
                
            # 合并订阅列表（新订阅在前）
            ordered_subs = new_subs + old_subs
            
            # 逐个扫描订阅
            for idx, sub in enumerate(ordered_subs, 1):
                # 检查是否暂停
                await self.controller.wait_if_paused()
                
                user_id = sub['user_id']
                nickname = sub['nickname']
                
                logger.info(f"扫描订阅 {idx}/{len(ordered_subs)}: {nickname} (ID: {user_id})")
                
                # 开始扫描此订阅
                collector.start_subscription(user_id, nickname)
                
                try:
                    # 获取用户最新视频
                    new_videos = await self._scan_subscription(sub, collector)
                    
                    # 记录扫描成功
                    collector.end_subscription(user_id)
                    
                    # 如果有新视频且设置了自动下载
                    if new_videos and self.auto_download and sub.get('auto_download', True):
                        if self._on_new_videos_callback:
                            await self._on_new_videos_callback(user_id, new_videos)
                    
                    # 延迟避免风控（非第一个订阅）
                    if idx < len(ordered_subs):
                        await asyncio.sleep(3)
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"扫描订阅 {nickname} 失败: {error_msg}")
                    collector.end_subscription(user_id, error_msg)
                    
                    # 检查是否是风控错误
                    if '风控' in error_msg or 'risk' in error_msg.lower():
                        logger.error("检测到风控，停止本轮扫描")
                        break
                        
            # 生成扫描摘要
            summary = collector.generate_summary()
            
            # 记录扫描日志
            try:
                scan_logger = get_scan_logger()
                scan_id = scan_logger.log_scan(summary)
                logger.info(f"扫描日志已记录: {scan_id}")
            except Exception as e:
                logger.error(f"记录扫描日志失败: {e}")
            
            # 发送扫描通知
            try:
                await send_scan_notification(summary)
            except Exception as e:
                logger.error(f"发送扫描通知失败: {e}")
                
        finally:
            self.controller.set_scanning(False)
            
    async def _scan_subscription(self, subscription: Dict, collector: ScanCollector) -> List[Dict]:
        """
        扫描单个订阅
        返回新发现的视频列表
        """
        user_id = subscription['user_id']
        
        # 确保API已初始化
        if not self.api:
            logger.error("API未初始化，请先设置认证信息")
            return []
        
        # 获取订阅的扫描进度
        progress = self.tracker.get_subscription_progress(user_id)
        last_video_time = progress.get('last_video_time', 0) if progress else 0
        
        # 获取用户作品列表
        loguru_logger.info(f"正在获取用户 {subscription['nickname']} 的所有作品列表...")
        works = await self.api.get_user_all_works(user_id)  # 不限制数量，获取所有作品
        
        if not works:
            loguru_logger.info(f"用户 {subscription['nickname']} 没有作品")
            return []
            
        # 查找新视频
        new_videos = []
        latest_video_time = last_video_time
        latest_video_id = None
        
        # 获取已下载的视频ID集合
        db = get_database()
        downloaded_ids = db.get_downloaded_work_ids(user_id)
        
        for work in works:
            create_time = work.get('create_time', 0)
            aweme_id = work.get('aweme_id', '')
            
            # 更新最新视频时间
            if create_time > latest_video_time:
                latest_video_time = create_time
                latest_video_id = aweme_id
                
            # 检查是否是新视频（发布时间比上次扫描记录的新，且未下载）
            if create_time > last_video_time and aweme_id not in downloaded_ids:
                new_videos.append(work)
                collector.add_new_video(user_id, work)
                
        # 更新扫描进度
        if latest_video_time > last_video_time:
            self.tracker.update_subscription_scan(user_id, latest_video_time, latest_video_id)
            
        if new_videos:
            loguru_logger.info(f"发现 {subscription['nickname']} 的 {len(new_videos)} 个新视频")
        else:
            loguru_logger.info(f"{subscription['nickname']} 没有新视频")
            
        return new_videos
        
    async def scan_once(self) -> ScanSummary:
        """执行一次扫描（手动触发）"""
        logger.info("手动触发扫描")
        await self._perform_scan()
        # 返回最新的扫描摘要
        # 这里简化处理，实际应该从collector获取
        return None


# 全局扫描器实例
_scanner_instance: Optional[SubscriptionScanner] = None


def get_scanner() -> SubscriptionScanner:
    """获取全局扫描器实例"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SubscriptionScanner()
    return _scanner_instance


async def start_scanner(scan_interval: int = 3600, auto_download: bool = True):
    """启动扫描器"""
    scanner = get_scanner()
    scanner.scan_interval = scan_interval
    scanner.auto_download = auto_download
    await scanner.start()
    

async def stop_scanner():
    """停止扫描器"""
    scanner = get_scanner()
    await scanner.stop()