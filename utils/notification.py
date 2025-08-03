# coding=utf-8
"""
通知系统，用于发送扫描完成通知
支持WebSocket、日志等多种通知方式
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
import asyncio

from .scan_collector import ScanSummary, NewVideoInfo
from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.ws_manager = WebSocketManager()
        self.enabled_channels = {
            'websocket': True,
            'log': True,
            'file': False,  # 可以扩展文件通知
        }
        
    async def send_notification(self, notification_type: str, data: Dict):
        """发送通知到所有启用的渠道"""
        tasks = []
        
        if self.enabled_channels.get('websocket'):
            tasks.append(self._send_websocket_notification(notification_type, data))
            
        if self.enabled_channels.get('log'):
            tasks.append(self._send_log_notification(notification_type, data))
            
        if self.enabled_channels.get('file'):
            tasks.append(self._send_file_notification(notification_type, data))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _send_websocket_notification(self, notification_type: str, data: Dict):
        """发送WebSocket通知"""
        try:
            message = {
                'type': f'notification.{notification_type}',
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            await self.ws_manager.broadcast(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送WebSocket通知失败: {e}")
            
    async def _send_log_notification(self, notification_type: str, data: Dict):
        """发送日志通知"""
        try:
            if notification_type == 'scan_complete':
                summary: ScanSummary = data.get('summary')
                if summary:
                    logger.info(f"=== 扫描完成通知 ===")
                    logger.info(f"扫描时间: {summary.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"扫描订阅: {summary.scanned_subscriptions}/{summary.total_subscriptions}")
                    logger.info(f"新视频数: {summary.total_new_videos}")
                    logger.info(f"扫描耗时: {summary.scan_duration:.2f}秒")
                    
                    # 记录有新视频的订阅
                    for result in summary.subscription_results:
                        if result.new_videos:
                            logger.info(f"  - {result.nickname}: {len(result.new_videos)} 个新视频")
                            
            elif notification_type == 'new_videos':
                user_info = data.get('user')
                videos = data.get('videos', [])
                if user_info and videos:
                    logger.info(f"=== 新视频通知 ===")
                    logger.info(f"UP主: {user_info.get('nickname')} (ID: {user_info.get('user_id')})")
                    logger.info(f"新视频数量: {len(videos)}")
                    for video in videos[:5]:  # 最多显示5个
                        logger.info(f"  - {video.get('desc', '无标题')}")
                        
            elif notification_type == 'scan_error':
                error = data.get('error')
                logger.error(f"=== 扫描错误通知 ===")
                logger.error(f"错误信息: {error}")
                
        except Exception as e:
            logger.error(f"发送日志通知失败: {e}")
            
    async def _send_file_notification(self, notification_type: str, data: Dict):
        """发送文件通知（可以写入特定文件）"""
        # 预留接口，可以实现写入通知文件的功能
        pass


# 全局通知管理器实例
_notification_manager = NotificationManager()


async def send_scan_notification(summary: ScanSummary):
    """发送扫描完成通知"""
    # 构建通知数据，需要序列化ScanSummary
    summary_dict = {
        'total_subscriptions': summary.total_subscriptions,
        'scanned_subscriptions': summary.scanned_subscriptions,
        'failed_subscriptions': summary.failed_subscriptions,
        'total_new_videos': summary.total_new_videos,
        'scan_duration': summary.scan_duration,
        'scan_time': summary.scan_time.isoformat() if hasattr(summary.scan_time, 'isoformat') else str(summary.scan_time),
        'scan_id': summary.scan_id,
        'subscription_results': [
            {
                'user_id': r.user_id,
                'nickname': r.nickname,
                'new_videos_count': len(r.new_videos),
                'scan_time': r.scan_time,
                'error': r.error
            }
            for r in summary.subscription_results
        ]
    }
    
    notification_data = {
        'summary': summary_dict,
        'summary_text': _build_summary_text(summary)
    }
    
    await _notification_manager.send_notification('scan_complete', notification_data)
    

async def send_new_videos_notification(user_info: Dict, videos: List[Dict]):
    """发送新视频发现通知"""
    notification_data = {
        'user': user_info,
        'videos': videos,
        'count': len(videos)
    }
    
    await _notification_manager.send_notification('new_videos', notification_data)
    

async def send_scan_error_notification(error: str, details: Optional[Dict] = None):
    """发送扫描错误通知"""
    notification_data = {
        'error': error,
        'details': details or {},
        'timestamp': datetime.now().isoformat()
    }
    
    await _notification_manager.send_notification('scan_error', notification_data)


def _build_summary_text(summary: ScanSummary) -> str:
    """构建扫描摘要文本"""
    lines = [
        f"扫描完成时间: {summary.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"扫描订阅数: {summary.scanned_subscriptions}/{summary.total_subscriptions}",
        f"失败数: {summary.failed_subscriptions}",
        f"新视频总数: {summary.total_new_videos}",
        f"扫描耗时: {summary.scan_duration:.2f}秒"
    ]
    
    if summary.subscription_results:
        lines.append("\n订阅扫描结果:")
        for result in summary.subscription_results:
            if result.new_videos:
                lines.append(f"  • {result.nickname}: {len(result.new_videos)} 个新视频")
            elif result.error:
                lines.append(f"  • {result.nickname}: 扫描失败 - {result.error}")
                
    return "\n".join(lines)


def format_new_video_info(video: NewVideoInfo) -> Dict:
    """格式化新视频信息用于展示"""
    return {
        'aweme_id': video.aweme_id,
        'title': video.desc[:50] + '...' if len(video.desc) > 50 else video.desc,
        'author': video.nickname,
        'create_time': datetime.fromtimestamp(video.create_time).strftime('%Y-%m-%d %H:%M:%S'),
        'duration': f"{video.duration // 1000}秒" if video.duration else "未知",
        'play_count': video.play_count,
        'digg_count': video.digg_count,
        'cover_url': video.cover_url
    }