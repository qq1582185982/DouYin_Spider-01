# coding=utf-8
"""
扫描日志管理器，记录和管理扫描历史
"""
import json
import os
import time
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import asdict
import logging

from .scan_collector import ScanSummary

logger = logging.getLogger(__name__)


class ScanLogger:
    """扫描日志管理器"""
    
    def __init__(self, log_dir: str = "scan_logs"):
        """
        初始化扫描日志管理器
        :param log_dir: 日志存储目录
        """
        self.log_dir = log_dir
        self.current_log_file = os.path.join(log_dir, "scan_history.json")
        self._ensure_log_dir()
        
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            logger.info(f"创建扫描日志目录: {self.log_dir}")
            
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载扫描历史"""
        if not os.path.exists(self.current_log_file):
            return []
            
        try:
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回列表
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'history' in data:
                    return data['history']
                else:
                    return []
        except Exception as e:
            logger.error(f"加载扫描历史失败: {e}")
            return []
            
    def _save_history(self, history: List[Dict[str, Any]]):
        """保存扫描历史"""
        try:
            # 限制历史记录数量（保留最近100条）
            if len(history) > 100:
                history = history[-100:]
                
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"保存扫描历史失败: {e}")
            
    def log_scan(self, summary: ScanSummary) -> str:
        """
        记录一次扫描
        :param summary: 扫描摘要
        :return: 扫描ID
        """
        # 生成扫描ID
        scan_id = str(uuid.uuid4())
        summary.scan_id = scan_id
        
        # 转换为字典
        scan_record = self._summary_to_dict(summary)
        scan_record['scan_id'] = scan_id
        scan_record['timestamp'] = int(time.time())
        
        # 加载历史并添加新记录
        history = self._load_history()
        history.append(scan_record)
        
        # 保存
        self._save_history(history)
        
        # 同时保存详细日志文件
        self._save_detailed_log(scan_id, summary)
        
        logger.info(f"记录扫描日志: {scan_id}")
        return scan_id
        
    def _save_detailed_log(self, scan_id: str, summary: ScanSummary):
        """保存详细的扫描日志"""
        try:
            # 使用日期组织日志文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            detail_dir = os.path.join(self.log_dir, "details", date_str)
            
            if not os.path.exists(detail_dir):
                os.makedirs(detail_dir)
                
            # 保存详细日志
            detail_file = os.path.join(detail_dir, f"{scan_id}.json")
            scan_data = self._summary_to_dict(summary)
            
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump(scan_data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"保存详细扫描日志失败: {e}")
            
    def _summary_to_dict(self, summary: ScanSummary) -> Dict[str, Any]:
        """将扫描摘要转换为字典"""
        data = asdict(summary)
        
        # 处理datetime对象
        if isinstance(data['scan_time'], datetime):
            data['scan_time'] = data['scan_time'].isoformat()
            
        # 简化订阅结果（只保留关键信息）
        simplified_results = []
        for result in data['subscription_results']:
            simplified = {
                'user_id': result['user_id'],
                'nickname': result['nickname'],
                'new_videos_count': len(result['new_videos']),
                'scan_time': result['scan_time'],
                'error': result['error']
            }
            # 只保留前3个新视频的信息
            if result['new_videos']:
                simplified['sample_videos'] = [
                    {
                        'aweme_id': v['aweme_id'],
                        'desc': v['desc'][:50] + '...' if len(v['desc']) > 50 else v['desc']
                    }
                    for v in result['new_videos'][:3]
                ]
            simplified_results.append(simplified)
            
        data['subscription_results'] = simplified_results
        return data
        
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取扫描历史
        :param limit: 返回记录数量限制
        :return: 扫描历史列表
        """
        history = self._load_history()
        
        # 按时间倒序
        history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # 限制返回数量
        return history[:limit]
        
    def get_scan_detail(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        获取扫描详情
        :param scan_id: 扫描ID
        :return: 扫描详情
        """
        # 先从历史记录中查找
        history = self._load_history()
        for record in history:
            if record.get('scan_id') == scan_id:
                # 尝试加载详细日志
                detail = self._load_detailed_log(scan_id)
                if detail:
                    return detail
                return record
                
        return None
        
    def _load_detailed_log(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """加载详细的扫描日志"""
        try:
            # 遍历所有日期目录查找
            details_dir = os.path.join(self.log_dir, "details")
            if not os.path.exists(details_dir):
                return None
                
            for date_dir in os.listdir(details_dir):
                detail_file = os.path.join(details_dir, date_dir, f"{scan_id}.json")
                if os.path.exists(detail_file):
                    with open(detail_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                        
        except Exception as e:
            logger.error(f"加载详细扫描日志失败: {e}")
            
        return None
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        history = self._load_history()
        
        if not history:
            return {
                'total_scans': 0,
                'total_new_videos': 0,
                'average_duration': 0,
                'success_rate': 0
            }
            
        total_scans = len(history)
        total_new_videos = sum(r.get('total_new_videos', 0) for r in history)
        total_duration = sum(r.get('scan_duration', 0) for r in history)
        successful_scans = sum(1 for r in history if r.get('failed_subscriptions', 0) == 0)
        
        return {
            'total_scans': total_scans,
            'total_new_videos': total_new_videos,
            'average_duration': total_duration / total_scans if total_scans > 0 else 0,
            'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            'last_scan_time': history[0].get('scan_time') if history else None
        }
        
    def cleanup_old_logs(self, days: int = 30):
        """
        清理旧日志
        :param days: 保留最近N天的日志
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            # 清理历史记录
            history = self._load_history()
            history = [r for r in history if r.get('timestamp', 0) > cutoff_time]
            self._save_history(history)
            
            # 清理详细日志文件
            details_dir = os.path.join(self.log_dir, "details")
            if os.path.exists(details_dir):
                cutoff_date = datetime.fromtimestamp(cutoff_time).strftime("%Y-%m-%d")
                
                for date_dir in os.listdir(details_dir):
                    if date_dir < cutoff_date:
                        dir_path = os.path.join(details_dir, date_dir)
                        try:
                            import shutil
                            shutil.rmtree(dir_path)
                            logger.info(f"清理旧日志目录: {dir_path}")
                        except Exception as e:
                            logger.error(f"清理日志目录失败: {e}")
                            
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")


# 全局扫描日志实例
_scan_logger = ScanLogger()


def get_scan_logger() -> ScanLogger:
    """获取全局扫描日志实例"""
    return _scan_logger