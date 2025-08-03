# coding=utf-8
"""
扫描配置管理
"""
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScanConfig:
    """扫描配置"""
    # 基本设置
    enabled: bool = True  # 是否启用自动扫描
    scan_interval: int = 3600  # 扫描间隔（秒）
    auto_download: bool = True  # 是否自动下载新视频
    
    # 高级设置
    max_videos_per_scan: int = 50  # 每个订阅每次扫描的最大视频数
    source_delay: int = 3  # 扫描不同订阅之间的延迟（秒）
    retry_on_error: bool = True  # 出错时是否重试
    max_retries: int = 3  # 最大重试次数
    
    # 通知设置
    notify_on_complete: bool = True  # 扫描完成时通知
    notify_on_new_videos: bool = True  # 发现新视频时通知
    notify_on_error: bool = True  # 出错时通知
    min_videos_for_notification: int = 1  # 触发通知的最小新视频数
    
    # 日志设置
    log_retention_days: int = 30  # 日志保留天数
    detailed_logging: bool = False  # 是否记录详细日志
    
    # 性能设置
    concurrent_downloads: int = 3  # 并发下载数
    download_timeout: int = 300  # 下载超时时间（秒）
    
    # 风控设置
    pause_on_risk_control: bool = True  # 遇到风控时暂停
    risk_control_pause_minutes: int = 30  # 风控暂停时间（分钟）


class ScanConfigManager:
    """扫描配置管理器"""
    
    def __init__(self, config_file: str = "scan_config.json"):
        self.config_file = config_file
        self._config: Optional[ScanConfig] = None
        self._load_config()
        
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = ScanConfig(**data)
                    logger.info(f"加载扫描配置: {self.config_file}")
            except Exception as e:
                logger.error(f"加载扫描配置失败: {e}")
                self._config = ScanConfig()
        else:
            # 使用默认配置
            self._config = ScanConfig()
            self._save_config()
            
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._config), f, ensure_ascii=False, indent=2)
            logger.info("扫描配置已保存")
        except Exception as e:
            logger.error(f"保存扫描配置失败: {e}")
            
    def get_config(self) -> ScanConfig:
        """获取配置"""
        if self._config is None:
            self._load_config()
        return self._config
        
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        更新配置
        :param updates: 要更新的配置项
        :return: 是否成功
        """
        try:
            if self._config is None:
                self._load_config()
                
            # 更新配置
            config_dict = asdict(self._config)
            for key, value in updates.items():
                if key in config_dict:
                    setattr(self._config, key, value)
                else:
                    logger.warning(f"未知的配置项: {key}")
                    
            # 保存配置
            self._save_config()
            return True
            
        except Exception as e:
            logger.error(f"更新扫描配置失败: {e}")
            return False
            
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = ScanConfig()
        self._save_config()
        logger.info("扫描配置已重置为默认值")
        
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        :return: 验证结果
        """
        errors = []
        warnings = []
        
        if self._config.scan_interval < 60:
            errors.append("扫描间隔不能小于60秒")
            
        if self._config.scan_interval < 300:
            warnings.append("扫描间隔小于5分钟可能触发风控")
            
        if self._config.max_videos_per_scan > 100:
            warnings.append("每次扫描视频数过多可能影响性能")
            
        if self._config.source_delay < 1:
            errors.append("订阅间延迟不能小于1秒")
            
        if self._config.concurrent_downloads > 10:
            warnings.append("并发下载数过多可能触发风控")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    def export_config(self) -> Dict[str, Any]:
        """导出配置为字典"""
        return asdict(self._config)
        
    def import_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        从字典导入配置
        :param config_dict: 配置字典
        :return: 是否成功
        """
        try:
            self._config = ScanConfig(**config_dict)
            self._save_config()
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = ScanConfigManager()


def get_scan_config() -> ScanConfig:
    """获取扫描配置"""
    return _config_manager.get_config()


def update_scan_config(updates: Dict[str, Any]) -> bool:
    """更新扫描配置"""
    return _config_manager.update_config(updates)


def get_scan_config_manager() -> ScanConfigManager:
    """获取配置管理器"""
    return _config_manager