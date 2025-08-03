# coding=utf-8
"""
扫描进度跟踪器，用于记录和管理扫描进度
支持断点续扫和新订阅优先扫描
"""
import json
import os
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ScanTracker:
    """扫描进度跟踪器"""
    
    def __init__(self, tracker_file: str = "scan_progress.json"):
        self.tracker_file = tracker_file
        self.progress_data = self._load_progress()
        
    def _load_progress(self) -> Dict:
        """加载进度数据"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载扫描进度失败: {e}")
        
        return {
            'last_scan_time': 0,  # 上次完整扫描时间
            'subscriptions': {},  # 各订阅的扫描记录
            'scan_round': 0,      # 扫描轮次
        }
    
    def _save_progress(self):
        """保存进度数据"""
        try:
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存扫描进度失败: {e}")
    
    def update_subscription_scan(self, user_id: str, last_video_time: int = 0, 
                               last_video_id: Optional[str] = None):
        """更新订阅的扫描记录"""
        if 'subscriptions' not in self.progress_data:
            self.progress_data['subscriptions'] = {}
            
        self.progress_data['subscriptions'][user_id] = {
            'last_scan_time': int(time.time()),
            'last_video_time': last_video_time,  # 最新视频的发布时间
            'last_video_id': last_video_id,      # 最新视频的ID
            'scan_count': self.progress_data['subscriptions'].get(user_id, {}).get('scan_count', 0) + 1
        }
        self._save_progress()
        
    def get_subscription_progress(self, user_id: str) -> Optional[Dict]:
        """获取订阅的扫描进度"""
        return self.progress_data.get('subscriptions', {}).get(user_id)
    
    def group_subscriptions_by_priority(self, subscriptions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        将订阅按优先级分组
        返回: (新订阅列表, 已扫描订阅列表)
        """
        new_subscriptions = []
        scanned_subscriptions = []
        
        for sub in subscriptions:
            user_id = sub['user_id']
            if user_id not in self.progress_data.get('subscriptions', {}):
                # 新订阅，优先扫描
                new_subscriptions.append(sub)
            else:
                # 已扫描过的订阅
                scanned_subscriptions.append(sub)
        
        # 对已扫描的订阅按上次扫描时间排序（最久未扫描的优先）
        scanned_subscriptions.sort(
            key=lambda x: self.progress_data['subscriptions'].get(x['user_id'], {}).get('last_scan_time', 0)
        )
        
        return new_subscriptions, scanned_subscriptions
    
    def start_new_round(self):
        """开始新一轮扫描"""
        self.progress_data['scan_round'] = self.progress_data.get('scan_round', 0) + 1
        self.progress_data['last_scan_time'] = int(time.time())
        self._save_progress()
        logger.info(f"开始第 {self.progress_data['scan_round']} 轮扫描")
    
    def get_last_scan_info(self) -> Dict:
        """获取上次扫描信息"""
        last_scan_time = self.progress_data.get('last_scan_time', 0)
        if last_scan_time:
            last_scan_datetime = datetime.fromtimestamp(last_scan_time)
            time_since_last_scan = time.time() - last_scan_time
            
            return {
                'last_scan_time': last_scan_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'time_since_last_scan': time_since_last_scan,
                'scan_round': self.progress_data.get('scan_round', 0)
            }
        else:
            return {
                'last_scan_time': '从未扫描',
                'time_since_last_scan': 0,
                'scan_round': 0
            }
    
    def should_check_new_videos(self, user_id: str, current_video_time: int) -> bool:
        """
        判断是否应该检查新视频
        基于最新视频的发布时间判断
        """
        progress = self.get_subscription_progress(user_id)
        if not progress:
            # 新订阅，需要检查
            return True
            
        last_video_time = progress.get('last_video_time', 0)
        # 如果当前视频时间比记录的更新，说明有新视频
        return current_video_time > last_video_time
    
    def cleanup_removed_subscriptions(self, active_user_ids: List[str]):
        """清理已移除订阅的进度记录"""
        if 'subscriptions' not in self.progress_data:
            return
            
        removed_count = 0
        for user_id in list(self.progress_data['subscriptions'].keys()):
            if user_id not in active_user_ids:
                del self.progress_data['subscriptions'][user_id]
                removed_count += 1
                
        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 个已移除订阅的进度记录")
            self._save_progress()
            
    def get_statistics(self) -> Dict:
        """获取扫描统计信息"""
        subs = self.progress_data.get('subscriptions', {})
        
        # 计算平均扫描间隔
        scan_intervals = []
        current_time = int(time.time())
        
        for sub_data in subs.values():
            last_scan = sub_data.get('last_scan_time', 0)
            if last_scan > 0:
                scan_intervals.append(current_time - last_scan)
                
        avg_interval = sum(scan_intervals) / len(scan_intervals) if scan_intervals else 0
        
        # 找出最久未扫描的订阅
        oldest_scan = min(
            subs.items(),
            key=lambda x: x[1].get('last_scan_time', current_time),
            default=(None, {})
        )
        
        return {
            'total_tracked': len(subs),
            'scan_round': self.progress_data.get('scan_round', 0),
            'average_scan_interval': avg_interval,
            'oldest_unscanned': {
                'user_id': oldest_scan[0],
                'time_since_scan': current_time - oldest_scan[1].get('last_scan_time', current_time)
            } if oldest_scan[0] else None
        }