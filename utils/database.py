# coding=utf-8
import os
import json
import sqlite3
import time
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from loguru import logger


class Database:
    """统一的数据库管理类，包含下载记录和订阅管理功能"""
    
    def __init__(self, db_path: str = "data.sqlite"):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = self._dict_factory
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def _dict_factory(cursor, row):
        """将查询结果转换为字典"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建下载记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    nickname TEXT,
                    title TEXT,
                    work_type TEXT DEFAULT 'video',
                    download_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    save_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    is_complete INTEGER DEFAULT 1,
                    work_url TEXT,
                    video_url TEXT,
                    cover_url TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建订阅表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    sec_uid TEXT,
                    nickname TEXT,
                    avatar TEXT,
                    signature TEXT,
                    user_url TEXT,
                    follower_count INTEGER DEFAULT 0,
                    aweme_count INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    auto_download INTEGER DEFAULT 1,
                    selected_videos TEXT,
                    last_check_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建订阅视频表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER NOT NULL,
                    aweme_id TEXT NOT NULL,
                    desc TEXT,
                    create_time INTEGER,
                    duration INTEGER,
                    cover TEXT,
                    play_count INTEGER DEFAULT 0,
                    digg_count INTEGER DEFAULT 0,
                    comment_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    is_downloaded INTEGER DEFAULT 0,
                    downloaded_at TEXT,
                    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
                    UNIQUE(subscription_id, aweme_id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_work_id ON downloads(work_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_download_time ON downloads(download_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_videos_aweme_id ON subscription_videos(aweme_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription_videos_subscription_id ON subscription_videos(subscription_id)')
            
            logger.info(f"数据库初始化完成: {self.db_path}")
    
    # ========== 下载管理相关方法 ==========
    
    def add_download_record(self, work_info: Dict[str, Any]) -> bool:
        """添加下载记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 提取必要字段
                work_id = work_info.get('work_id', '')
                if not work_id:
                    logger.error("work_id不能为空")
                    return False
                
                # 准备数据
                data = {
                    'work_id': work_id,
                    'user_id': work_info.get('user_id', ''),
                    'nickname': work_info.get('nickname', ''),
                    'title': work_info.get('title', work_info.get('desc', '')),
                    'work_type': work_info.get('work_type', 'video'),
                    'save_path': work_info.get('save_path', ''),
                    'file_size': work_info.get('file_size', 0),
                    'is_complete': 1 if work_info.get('is_complete', True) else 0,
                    'work_url': work_info.get('work_url', ''),
                    'video_url': work_info.get('video_url', ''),
                    'cover_url': work_info.get('cover_url', ''),
                    'metadata': json.dumps(work_info.get('metadata', {}), ensure_ascii=False),
                    'download_time': datetime.now().isoformat()
                }
                
                # 插入或更新记录
                cursor.execute('''
                    INSERT OR REPLACE INTO downloads 
                    (work_id, user_id, nickname, title, work_type, save_path, 
                     file_size, is_complete, work_url, video_url, cover_url, 
                     metadata, download_time, updated_at)
                    VALUES 
                    (:work_id, :user_id, :nickname, :title, :work_type, :save_path,
                     :file_size, :is_complete, :work_url, :video_url, :cover_url,
                     :metadata, :download_time, CURRENT_TIMESTAMP)
                ''', data)
                
                logger.info(f"添加下载记录成功: {work_id}")
                return True
                
        except Exception as e:
            logger.error(f"添加下载记录失败: {e}")
            return False
    
    def record_work_download(self, work_record: Dict[str, Any], files_info: List[Dict[str, Any]]) -> bool:
        """记录作品下载信息（包含文件详情）"""
        try:
            # 计算总文件大小
            total_size = sum(file['file_size'] for file in files_info)
            
            # 更新作品记录
            work_info = work_record.copy()
            work_info['file_size'] = total_size
            
            # 将文件信息存储在metadata中
            if 'metadata' not in work_info:
                work_info['metadata'] = {}
            work_info['metadata']['files'] = files_info
            
            # 调用添加下载记录方法
            return self.add_download_record(work_info)
            
        except Exception as e:
            logger.error(f"记录作品下载失败: {e}")
            return False
    
    def get_work_info(self, work_id: str) -> Optional[Dict[str, Any]]:
        """获取作品信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM downloads WHERE work_id = ?', (work_id,))
                result = cursor.fetchone()
                
                if result and result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except:
                        result['metadata'] = {}
                
                return result
        except Exception as e:
            logger.error(f"获取作品信息失败: {e}")
            return None
    
    def check_work_exists(self, work_id: str) -> bool:
        """检查作品是否已存在"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM downloads WHERE work_id = ? LIMIT 1', (work_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查作品是否存在失败: {e}")
            return False
    
    def is_work_complete(self, work_id: str) -> bool:
        """检查作品是否完整下载"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_complete FROM downloads WHERE work_id = ?', (work_id,))
                result = cursor.fetchone()
                return result and result['is_complete'] == 1
        except Exception as e:
            logger.error(f"检查作品完整性失败: {e}")
            return False
    
    def get_recent_downloads(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取最近的下载记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM downloads 
                    ORDER BY download_time DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                results = cursor.fetchall()
                for result in results:
                    if result.get('metadata'):
                        try:
                            result['metadata'] = json.loads(result['metadata'])
                        except:
                            result['metadata'] = {}
                
                return results
        except Exception as e:
            logger.error(f"获取最近下载记录失败: {e}")
            return []
    
    def get_total_works_count(self) -> int:
        """获取总作品数"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM downloads')
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"获取总作品数失败: {e}")
            return 0
    
    def get_downloaded_work_ids(self, user_id: Optional[str] = None) -> set:
        """获取已下载的作品ID集合"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute('SELECT work_id FROM downloads WHERE user_id = ?', (user_id,))
                else:
                    cursor.execute('SELECT work_id FROM downloads')
                
                return {row['work_id'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"获取已下载作品ID集合失败: {e}")
            return set()
    
    def get_download_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取下载统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    # 特定用户的统计
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_works,
                            SUM(CASE WHEN is_complete = 1 THEN 1 ELSE 0 END) as completed_works,
                            SUM(file_size) as total_size,
                            COUNT(DISTINCT user_id) as total_users
                        FROM downloads
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    # 全局统计
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_works,
                            SUM(CASE WHEN is_complete = 1 THEN 1 ELSE 0 END) as completed_works,
                            SUM(file_size) as total_size,
                            COUNT(DISTINCT user_id) as total_users
                        FROM downloads
                    ''')
                
                result = cursor.fetchone()
                return {
                    'total_works': result['total_works'] or 0,
                    'completed_works': result['completed_works'] or 0,
                    'total_size': result['total_size'] or 0,
                    'total_users': result['total_users'] or 0
                }
        except Exception as e:
            logger.error(f"获取下载统计失败: {e}")
            return {
                'total_works': 0,
                'completed_works': 0,
                'total_size': 0,
                'total_users': 0
            }
    
    # ========== 订阅管理相关方法 ==========
    
    def add_subscription(self, user_info: Dict[str, Any]) -> Optional[int]:
        """添加订阅"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                user_id = user_info.get('user_id')
                if not user_id:
                    logger.error("user_id不能为空")
                    return None
                
                data = {
                    'user_id': user_id,
                    'sec_uid': user_info.get('sec_uid', ''),
                    'nickname': user_info.get('nickname', ''),
                    'avatar': user_info.get('avatar', ''),
                    'signature': user_info.get('signature', ''),
                    'user_url': user_info.get('user_url', ''),
                    'follower_count': user_info.get('follower_count', 0),
                    'aweme_count': user_info.get('aweme_count', 0)
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO subscriptions
                    (user_id, sec_uid, nickname, avatar, signature, user_url,
                     follower_count, aweme_count, updated_at)
                    VALUES
                    (:user_id, :sec_uid, :nickname, :avatar, :signature, :user_url,
                     :follower_count, :aweme_count, CURRENT_TIMESTAMP)
                ''', data)
                
                subscription_id = cursor.lastrowid
                logger.info(f"添加订阅成功: {user_info.get('nickname')} ({user_id})")
                return subscription_id
                
        except Exception as e:
            logger.error(f"添加订阅失败: {e}")
            return None
    
    def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取订阅信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                
                if result and result.get('selected_videos'):
                    try:
                        result['selected_videos'] = json.loads(result['selected_videos'])
                    except:
                        result['selected_videos'] = []
                
                return result
        except Exception as e:
            logger.error(f"获取订阅信息失败: {e}")
            return None
    
    def get_all_subscriptions(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """获取所有订阅"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if enabled_only:
                    cursor.execute('SELECT * FROM subscriptions WHERE enabled = 1 ORDER BY created_at DESC')
                else:
                    cursor.execute('SELECT * FROM subscriptions ORDER BY created_at DESC')
                
                results = cursor.fetchall()
                for result in results:
                    if result.get('selected_videos'):
                        try:
                            result['selected_videos'] = json.loads(result['selected_videos'])
                        except:
                            result['selected_videos'] = []
                
                return results
        except Exception as e:
            logger.error(f"获取订阅列表失败: {e}")
            return []
    
    def update_subscription(self, user_id: str, **kwargs) -> bool:
        """更新订阅信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                allowed_fields = ['enabled', 'auto_download', 'selected_videos', 
                                'follower_count', 'aweme_count', 'last_check_time']
                updates = []
                params = []
                
                for field in allowed_fields:
                    if field in kwargs:
                        value = kwargs[field]
                        if field == 'selected_videos' and isinstance(value, list):
                            value = json.dumps(value)
                        updates.append(f"{field} = ?")
                        params.append(value)
                
                if not updates:
                    return True
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                sql = f"UPDATE subscriptions SET {', '.join(updates)} WHERE user_id = ?"
                cursor.execute(sql, params)
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"更新订阅失败: {e}")
            return False
    
    def remove_subscription(self, user_id: str) -> bool:
        """移除订阅"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"移除订阅失败: {e}")
            return False
    
    def add_subscription_video(self, subscription_id: int, video_info: Dict[str, Any]) -> bool:
        """添加订阅的视频"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                aweme_id = video_info.get('aweme_id')
                if not aweme_id:
                    return False
                
                # 检查是否已存在
                cursor.execute('''
                    SELECT 1 FROM subscription_videos 
                    WHERE subscription_id = ? AND aweme_id = ?
                ''', (subscription_id, aweme_id))
                
                if cursor.fetchone():
                    return False  # 已存在
                
                # 插入新视频
                data = {
                    'subscription_id': subscription_id,
                    'aweme_id': aweme_id,
                    'desc': video_info.get('desc', ''),
                    'create_time': video_info.get('create_time', 0),
                    'duration': video_info.get('duration', 0),
                    'cover': video_info.get('video', {}).get('cover', {}).get('url_list', [''])[0] if video_info.get('video') else '',
                    'play_count': video_info.get('statistics', {}).get('play_count', 0),
                    'digg_count': video_info.get('statistics', {}).get('digg_count', 0),
                    'comment_count': video_info.get('statistics', {}).get('comment_count', 0),
                    'share_count': video_info.get('statistics', {}).get('share_count', 0)
                }
                
                cursor.execute('''
                    INSERT INTO subscription_videos
                    (subscription_id, aweme_id, desc, create_time, duration,
                     cover, play_count, digg_count, comment_count, share_count)
                    VALUES
                    (:subscription_id, :aweme_id, :desc, :create_time, :duration,
                     :cover, :play_count, :digg_count, :comment_count, :share_count)
                ''', data)
                
                return True
                
        except Exception as e:
            logger.error(f"添加订阅视频失败: {e}")
            return False
    
    def get_subscription_videos(self, subscription_id: int, only_new: bool = False) -> List[Dict[str, Any]]:
        """获取订阅的视频列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if only_new:
                    sql = '''
                        SELECT * FROM subscription_videos 
                        WHERE subscription_id = ? AND is_downloaded = 0
                        ORDER BY create_time DESC
                    '''
                else:
                    sql = '''
                        SELECT * FROM subscription_videos 
                        WHERE subscription_id = ?
                        ORDER BY create_time DESC
                    '''
                
                cursor.execute(sql, (subscription_id,))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"获取订阅视频列表失败: {e}")
            return []
    
    def mark_video_downloaded(self, aweme_id: str) -> bool:
        """标记视频为已下载"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE subscription_videos 
                    SET is_downloaded = 1, downloaded_at = CURRENT_TIMESTAMP
                    WHERE aweme_id = ?
                ''', (aweme_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"标记视频已下载失败: {e}")
            return False
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """获取订阅统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 订阅统计
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_subscriptions,
                        SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_subscriptions
                    FROM subscriptions
                ''')
                sub_stats = cursor.fetchone()
                
                # 视频统计
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_videos,
                        SUM(CASE WHEN is_downloaded = 1 THEN 1 ELSE 0 END) as downloaded_videos,
                        SUM(CASE WHEN is_downloaded = 0 THEN 1 ELSE 0 END) as new_videos
                    FROM subscription_videos
                ''')
                video_stats = cursor.fetchone()
                
                return {
                    'total_subscriptions': sub_stats['total_subscriptions'] or 0,
                    'enabled_subscriptions': sub_stats['enabled_subscriptions'] or 0,
                    'total_videos': video_stats['total_videos'] or 0,
                    'downloaded_videos': video_stats['downloaded_videos'] or 0,
                    'new_videos': video_stats['new_videos'] or 0
                }
                
        except Exception as e:
            logger.error(f"获取订阅统计失败: {e}")
            return {
                'total_subscriptions': 0,
                'enabled_subscriptions': 0,
                'total_videos': 0,
                'downloaded_videos': 0,
                'new_videos': 0
            }
    
    # ========== 数据库维护方法 ==========
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row['name'] for row in cursor.fetchall()]
                
                table_info = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    table_info[table] = result['count'] if result else 0
                
                return {
                    'database_path': self.db_path,
                    'database_size': db_size,
                    'tables': table_info,
                    'total_records': sum(table_info.values())
                }
                
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {
                'database_path': self.db_path,
                'database_size': 0,
                'tables': {},
                'total_records': 0
            }
    
    def cleanup_invalid_records(self) -> int:
        """清理无效记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 清理没有work_id的下载记录
                cursor.execute("DELETE FROM downloads WHERE work_id IS NULL OR work_id = ''")
                cleaned = cursor.rowcount
                
                # 清理孤立的订阅视频记录
                cursor.execute('''
                    DELETE FROM subscription_videos 
                    WHERE subscription_id NOT IN (SELECT id FROM subscriptions)
                ''')
                cleaned += cursor.rowcount
                
                logger.info(f"清理了 {cleaned} 条无效记录")
                return cleaned
                
        except Exception as e:
            logger.error(f"清理无效记录失败: {e}")
            return 0
    
    def rebuild_from_filesystem(self, base_path: str) -> int:
        """从文件系统重建数据库索引"""
        try:
            if not os.path.exists(base_path):
                logger.error(f"路径不存在: {base_path}")
                return 0
            
            rebuilt_count = 0
            
            # 遍历媒体目录
            for user_dir in os.listdir(base_path):
                user_path = os.path.join(base_path, user_dir)
                if not os.path.isdir(user_path):
                    continue
                
                for work_dir in os.listdir(user_path):
                    work_path = os.path.join(user_path, work_dir)
                    if not os.path.isdir(work_path):
                        continue
                    
                    # 查找info.json文件
                    info_file = os.path.join(work_path, 'info.json')
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                work_info = json.load(f)
                            
                            # 添加保存路径
                            work_info['save_path'] = work_path
                            
                            # 计算文件大小
                            file_size = 0
                            for file in os.listdir(work_path):
                                file_path = os.path.join(work_path, file)
                                if os.path.isfile(file_path):
                                    file_size += os.path.getsize(file_path)
                            work_info['file_size'] = file_size
                            
                            # 添加到数据库
                            if self.add_download_record(work_info):
                                rebuilt_count += 1
                                
                        except Exception as e:
                            logger.error(f"处理文件失败 {info_file}: {e}")
            
            logger.info(f"从文件系统重建了 {rebuilt_count} 个作品的索引")
            return rebuilt_count
            
        except Exception as e:
            logger.error(f"重建数据库索引失败: {e}")
            return 0


# 单例实例
_db_instance = None

def get_database() -> Database:
    """获取数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance