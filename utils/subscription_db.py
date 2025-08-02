# coding=utf-8
import sqlite3
import os
import json
from datetime import datetime
from loguru import logger
from typing import List, Dict, Optional, Tuple

class SubscriptionDB:
    def __init__(self, db_path='subscriptions.db'):
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            
            # 创建订阅UP主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    sec_uid TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    avatar TEXT,
                    signature TEXT,
                    follower_count INTEGER DEFAULT 0,
                    aweme_count INTEGER DEFAULT 0,
                    user_url TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    auto_download BOOLEAN DEFAULT 1,
                    selected_videos TEXT,  -- JSON格式存储选中的视频ID列表
                    last_check_time DATETIME,
                    last_video_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建视频记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    aweme_id TEXT NOT NULL UNIQUE,
                    title TEXT,
                    create_time INTEGER,
                    duration INTEGER,
                    cover TEXT,
                    is_downloaded BOOLEAN DEFAULT 0,
                    download_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_user_id ON subscriptions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_enabled ON subscriptions(enabled)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_subscription_id ON subscription_videos(subscription_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_aweme_id ON subscription_videos(aweme_id)')
            
            self.conn.commit()
            logger.info("订阅数据库初始化成功")
        except Exception as e:
            logger.error(f"初始化订阅数据库失败: {e}")
            raise
    
    def add_subscription(self, user_info: Dict) -> int:
        """添加订阅"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions 
                (user_id, sec_uid, nickname, avatar, signature, follower_count, aweme_count, user_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_info['user_id'],
                user_info['sec_uid'],
                user_info['nickname'],
                user_info.get('avatar', ''),
                user_info.get('signature', ''),
                user_info.get('follower_count', 0),
                user_info.get('aweme_count', 0),
                user_info['user_url'],
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"添加订阅失败: {e}")
            raise
    
    def remove_subscription(self, user_id: str) -> bool:
        """移除订阅"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"移除订阅失败: {e}")
            return False
    
    def update_subscription(self, user_id: str, **kwargs) -> bool:
        """更新订阅信息"""
        try:
            # 构建更新语句
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['enabled', 'auto_download', 'selected_videos', 'last_check_time', 
                          'last_video_time', 'follower_count', 'aweme_count']:
                    fields.append(f"{key} = ?")
                    if key == 'selected_videos' and isinstance(value, list):
                        value = json.dumps(value)
                    values.append(value)
            
            if not fields:
                return False
            
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(user_id)
            
            cursor = self.conn.cursor()
            cursor.execute(f'''
                UPDATE subscriptions 
                SET {', '.join(fields)}
                WHERE user_id = ?
            ''', values)
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新订阅失败: {e}")
            return False
    
    def get_subscription(self, user_id: str) -> Optional[Dict]:
        """获取单个订阅信息"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('selected_videos'):
                    result['selected_videos'] = json.loads(result['selected_videos'])
                return result
            return None
        except Exception as e:
            logger.error(f"获取订阅信息失败: {e}")
            return None
    
    def get_all_subscriptions(self, enabled_only: bool = False) -> List[Dict]:
        """获取所有订阅"""
        try:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM subscriptions'
            if enabled_only:
                query += ' WHERE enabled = 1'
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                if result.get('selected_videos'):
                    result['selected_videos'] = json.loads(result['selected_videos'])
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"获取订阅列表失败: {e}")
            return []
    
    def add_subscription_video(self, subscription_id: int, video_info: Dict) -> bool:
        """添加订阅的视频记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO subscription_videos 
                (subscription_id, aweme_id, title, create_time, duration, cover)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subscription_id,
                video_info['aweme_id'],
                video_info.get('desc', ''),
                video_info.get('create_time', 0),
                video_info.get('duration', 0),
                video_info.get('cover', '')
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"添加视频记录失败: {e}")
            return False
    
    def get_subscription_videos(self, subscription_id: int, only_new: bool = False) -> List[Dict]:
        """获取订阅的视频列表"""
        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT * FROM subscription_videos 
                WHERE subscription_id = ?
            '''
            if only_new:
                query += ' AND is_downloaded = 0'
            query += ' ORDER BY create_time DESC'
            
            cursor.execute(query, (subscription_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取视频列表失败: {e}")
            return []
    
    def mark_video_downloaded(self, aweme_id: str) -> bool:
        """标记视频为已下载"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE subscription_videos 
                SET is_downloaded = 1, download_time = ?
                WHERE aweme_id = ?
            ''', (datetime.now().isoformat(), aweme_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"标记视频已下载失败: {e}")
            return False
    
    def get_subscription_stats(self) -> Dict:
        """获取订阅统计信息"""
        try:
            cursor = self.conn.cursor()
            
            # 总订阅数
            cursor.execute('SELECT COUNT(*) FROM subscriptions')
            total_subscriptions = cursor.fetchone()[0]
            
            # 启用的订阅数
            cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE enabled = 1')
            enabled_subscriptions = cursor.fetchone()[0]
            
            # 总视频数
            cursor.execute('SELECT COUNT(*) FROM subscription_videos')
            total_videos = cursor.fetchone()[0]
            
            # 已下载视频数
            cursor.execute('SELECT COUNT(*) FROM subscription_videos WHERE is_downloaded = 1')
            downloaded_videos = cursor.fetchone()[0]
            
            return {
                'total_subscriptions': total_subscriptions,
                'enabled_subscriptions': enabled_subscriptions,
                'total_videos': total_videos,
                'downloaded_videos': downloaded_videos,
                'new_videos': total_videos - downloaded_videos
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_subscriptions': 0,
                'enabled_subscriptions': 0,
                'total_videos': 0,
                'downloaded_videos': 0,
                'new_videos': 0
            }
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

# 全局实例
_subscription_db = None

def get_subscription_db() -> SubscriptionDB:
    """获取订阅数据库实例"""
    global _subscription_db
    if _subscription_db is None:
        _subscription_db = SubscriptionDB()
    return _subscription_db