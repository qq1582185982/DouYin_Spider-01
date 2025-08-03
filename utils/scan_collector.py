# coding=utf-8
"""
扫描收集器，用于收集每轮扫描的统计信息
参考自Bilibili项目的scan_collector设计
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class NewVideoInfo:
    """新视频信息"""
    aweme_id: str
    desc: str
    user_id: str
    nickname: str
    create_time: int
    duration: int = 0
    play_count: int = 0
    digg_count: int = 0
    cover_url: Optional[str] = None


@dataclass
class SubscriptionScanResult:
    """订阅扫描结果"""
    user_id: str
    nickname: str
    new_videos: List[NewVideoInfo] = field(default_factory=list)
    scan_time: float = 0.0  # 扫描耗时（秒）
    error: Optional[str] = None  # 错误信息


@dataclass
class ScanSummary:
    """扫描摘要"""
    total_subscriptions: int  # 总订阅数
    scanned_subscriptions: int  # 已扫描订阅数
    failed_subscriptions: int  # 失败订阅数
    total_new_videos: int  # 新视频总数
    scan_duration: float  # 总扫描时长（秒）
    subscription_results: List[SubscriptionScanResult]  # 各订阅的扫描结果
    scan_time: datetime  # 扫描时间
    scan_id: Optional[str] = None  # 扫描ID


class ScanCollector:
    """扫描收集器，用于收集每次完整扫描的统计信息"""
    
    def __init__(self):
        self.start_time = time.time()
        self.scan_time = datetime.now()
        self.subscription_results: Dict[str, SubscriptionScanResult] = {}
        self.total_subscriptions = 0
        self.current_subscription_start: Optional[float] = None
        
    def set_total_subscriptions(self, count: int):
        """设置总订阅数"""
        self.total_subscriptions = count
        
    def start_subscription(self, user_id: str, nickname: str):
        """记录一个订阅的扫描开始"""
        self.current_subscription_start = time.time()
        result = SubscriptionScanResult(
            user_id=user_id,
            nickname=nickname,
            new_videos=[]
        )
        self.subscription_results[user_id] = result
        logger.debug(f"开始扫描订阅: {nickname} (ID: {user_id})")
        
    def end_subscription(self, user_id: str, error: Optional[str] = None):
        """记录一个订阅的扫描结束"""
        if user_id in self.subscription_results and self.current_subscription_start:
            scan_time = time.time() - self.current_subscription_start
            self.subscription_results[user_id].scan_time = scan_time
            self.subscription_results[user_id].error = error
            
            if error:
                logger.warning(f"订阅扫描失败 {user_id}: {error}")
            else:
                video_count = len(self.subscription_results[user_id].new_videos)
                logger.debug(f"订阅扫描完成 {user_id}: 发现 {video_count} 个新视频，耗时 {scan_time:.2f}秒")
        
        self.current_subscription_start = None
        
    def add_new_video(self, user_id: str, video_info: Dict):
        """添加新发现的视频"""
        if user_id not in self.subscription_results:
            logger.warning(f"添加视频时未找到订阅 {user_id}")
            return
            
        # 从视频信息中提取必要字段
        new_video = NewVideoInfo(
            aweme_id=video_info.get('aweme_id', ''),
            desc=video_info.get('desc', ''),
            user_id=user_id,
            nickname=self.subscription_results[user_id].nickname,
            create_time=video_info.get('create_time', 0),
            duration=video_info.get('duration', 0),
            play_count=video_info.get('statistics', {}).get('play_count', 0),
            digg_count=video_info.get('statistics', {}).get('digg_count', 0),
            cover_url=video_info.get('video', {}).get('cover', {}).get('url_list', [''])[0]
        )
        
        self.subscription_results[user_id].new_videos.append(new_video)
        
    def add_new_videos(self, user_id: str, videos: List[Dict]):
        """批量添加新发现的视频"""
        for video in videos:
            self.add_new_video(user_id, video)
            
    def generate_summary(self) -> ScanSummary:
        """生成扫描摘要"""
        scan_duration = time.time() - self.start_time
        
        # 统计数据
        scanned_subscriptions = len(self.subscription_results)
        failed_subscriptions = sum(1 for r in self.subscription_results.values() if r.error)
        total_new_videos = sum(len(r.new_videos) for r in self.subscription_results.values())
        
        # 按新视频数量排序结果
        sorted_results = sorted(
            self.subscription_results.values(), 
            key=lambda x: len(x.new_videos), 
            reverse=True
        )
        
        logger.info(f"扫描摘要: 总订阅数={self.total_subscriptions}, "
                   f"已扫描={scanned_subscriptions}, 失败={failed_subscriptions}, "
                   f"新视频={total_new_videos}, 耗时={scan_duration:.2f}秒")
        
        # 记录有新视频的订阅
        for result in sorted_results:
            if result.new_videos:
                logger.info(f"  - {result.nickname}: {len(result.new_videos)} 个新视频")
        
        return ScanSummary(
            total_subscriptions=self.total_subscriptions,
            scanned_subscriptions=scanned_subscriptions,
            failed_subscriptions=failed_subscriptions,
            total_new_videos=total_new_videos,
            scan_duration=scan_duration,
            subscription_results=sorted_results,
            scan_time=self.scan_time
        )
        
    def get_progress(self) -> Dict:
        """获取当前扫描进度"""
        scanned = len(self.subscription_results)
        progress = (scanned / self.total_subscriptions * 100) if self.total_subscriptions > 0 else 0
        
        return {
            'total': self.total_subscriptions,
            'scanned': scanned,
            'progress': round(progress, 2),
            'new_videos': sum(len(r.new_videos) for r in self.subscription_results.values()),
            'duration': time.time() - self.start_time
        }