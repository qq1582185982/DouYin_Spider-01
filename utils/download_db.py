# coding=utf-8
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from loguru import logger


class DownloadDatabase:
    """下载记录数据库管理类"""
    
    def __init__(self, db_path: str = "downloads.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 创建用户表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    nickname TEXT NOT NULL,
                    user_url TEXT NOT NULL,
                    last_crawl DATETIME DEFAULT NULL,
                    total_works INTEGER DEFAULT 0,
                    crawled_works INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建作品表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS works (
                    work_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    title TEXT NOT NULL,
                    work_type TEXT NOT NULL,
                    work_url TEXT NOT NULL,
                    save_path TEXT NOT NULL,
                    file_count INTEGER NOT NULL DEFAULT 0,
                    download_time DATETIME NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    is_complete BOOLEAN DEFAULT FALSE,
                    last_check DATETIME DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建文件表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    download_time DATETIME NOT NULL,
                    is_valid BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (work_id) REFERENCES works (work_id) ON DELETE CASCADE,
                    UNIQUE(work_id, file_name)
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_works_user_id ON works (user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_works_download_time ON works (download_time)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_files_work_id ON files (work_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files (file_type)')
            
            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")
    
    def get_downloaded_work_ids(self, user_id: Optional[str] = None) -> set:
        """获取已下载的作品ID集合"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            if user_id:
                cursor = conn.execute(
                    "SELECT work_id FROM works WHERE user_id = ? AND is_complete = TRUE",
                    (user_id,)
                )
            else:
                cursor = conn.execute("SELECT work_id FROM works WHERE is_complete = TRUE")
            
            return set(row[0] for row in cursor.fetchall())
    
    def is_work_complete(self, work_id: str) -> bool:
        """检查作品是否完整下载"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            cursor = conn.execute(
                "SELECT is_complete FROM works WHERE work_id = ?",
                (work_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else False
    
    def get_work_info(self, work_id: str) -> Optional[Dict]:
        """获取作品信息"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM works WHERE work_id = ?
            ''', (work_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def record_work_download(self, work_info: Dict, files_info: List[Dict]) -> bool:
        """记录作品下载信息"""
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                now = datetime.now().isoformat()
                
                # 计算总文件大小
                total_size = sum(f.get('file_size', 0) for f in files_info)
                
                # 更新或插入作品记录
                conn.execute('''
                    INSERT OR REPLACE INTO works 
                    (work_id, user_id, nickname, title, work_type, work_url, save_path,
                     file_count, download_time, file_size, is_complete, last_check, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    work_info['work_id'],
                    work_info['user_id'],
                    work_info['nickname'],
                    work_info['title'],
                    work_info['work_type'],
                    work_info['work_url'],
                    work_info.get('save_path', ''),
                    len(files_info),
                    now,
                    total_size,
                    work_info.get('is_complete', True),
                    now,
                    now
                ))
                
                # 删除旧的文件记录
                conn.execute('DELETE FROM files WHERE work_id = ?', (work_info['work_id'],))
                
                # 插入文件记录
                for file_info in files_info:
                    conn.execute('''
                        INSERT INTO files 
                        (work_id, file_name, file_type, file_path, file_size, download_time, is_valid)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        work_info['work_id'],
                        file_info['file_name'],
                        file_info['file_type'],
                        file_info['file_path'],
                        file_info.get('file_size', 0),
                        now,
                        file_info.get('is_valid', True)
                    ))
                
                # 更新用户统计
                self._update_user_stats(conn, work_info['user_id'], work_info['nickname'], work_info.get('user_url', ''))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"记录作品下载信息失败: {e}")
            return False
    
    def _update_user_stats(self, conn, user_id: str, nickname: str, user_url: str = ''):
        """更新用户统计信息"""
        now = datetime.now().isoformat()
        
        # 获取用户作品统计
        cursor = conn.execute(
            "SELECT COUNT(*) FROM works WHERE user_id = ?",
            (user_id,)
        )
        crawled_works = cursor.fetchone()[0]
        
        # 更新或插入用户记录
        conn.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, nickname, user_url, last_crawl, crawled_works, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, nickname, user_url, now, crawled_works, now))
    
    def get_download_stats(self, user_id: Optional[str] = None) -> Dict:
        """获取下载统计信息"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            if user_id:
                # 用户统计
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_works,
                        COUNT(CASE WHEN is_complete = TRUE THEN 1 END) as complete_works,
                        SUM(file_size) as total_size,
                        SUM(file_count) as total_files
                    FROM works WHERE user_id = ?
                ''', (user_id,))
            else:
                # 全局统计
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_works,
                        COUNT(CASE WHEN is_complete = TRUE THEN 1 END) as complete_works,
                        SUM(file_size) as total_size,
                        SUM(file_count) as total_files
                    FROM works
                ''')
            
            result = cursor.fetchone()
            return {
                'total_works': result[0] or 0,
                'complete_works': result[1] or 0,
                'incomplete_works': (result[0] or 0) - (result[1] or 0),
                'total_size': result[2] or 0,
                'total_files': result[3] or 0
            }
    
    def get_recent_downloads(self, limit: int = 50) -> List[Dict]:
        """获取最近下载记录"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT work_id, nickname, title, work_type, download_time, file_size, is_complete
                FROM works 
                ORDER BY download_time DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_invalid_records(self) -> int:
        """清理无效记录（对应文件已删除）"""
        cleaned_count = 0
        
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            cursor = conn.execute("SELECT work_id, save_path FROM works")
            works = cursor.fetchall()
            
            for work_id, save_path in works:
                if not os.path.exists(save_path):
                    conn.execute("DELETE FROM works WHERE work_id = ?", (work_id,))
                    cleaned_count += 1
                    logger.info(f"清理无效记录: {work_id} - {save_path}")
            
            conn.commit()
            
        if cleaned_count > 0:
            logger.info(f"清理完成，删除了 {cleaned_count} 条无效记录")
        
        return cleaned_count
    
    def rebuild_from_filesystem(self, base_path: str) -> int:
        """从文件系统重建数据库索引"""
        rebuilt_count = 0
        
        if not os.path.exists(base_path):
            logger.warning(f"基础路径不存在: {base_path}")
            return 0
        
        logger.info(f"开始从 {base_path} 重建数据库索引...")
        
        for user_dir in os.listdir(base_path):
            user_path = os.path.join(base_path, user_dir)
            if not os.path.isdir(user_path) or '_' not in user_dir:
                continue
            
            # 解析用户信息
            try:
                nickname, user_id = user_dir.rsplit('_', 1)
                # 确保user_id不为空
                if not user_id:
                    continue
            except ValueError:
                continue
            
            for work_dir in os.listdir(user_path):
                work_path = os.path.join(user_path, work_dir)
                if not os.path.isdir(work_path):
                    continue
                
                # 解析作品信息
                try:
                    title, work_id = work_dir.rsplit('_', 1)
                except ValueError:
                    continue
                
                info_file = os.path.join(work_path, 'info.json')
                if not os.path.exists(info_file):
                    continue
                
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        work_info = json.load(f)
                    
                    # 收集文件信息
                    files_info = []
                    total_size = 0
                    
                    for file_name in os.listdir(work_path):
                        file_path = os.path.join(work_path, file_name)
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            
                            # 判断文件类型
                            if file_name.endswith('.mp4'):
                                file_type = 'video'
                            elif file_name.endswith('.jpg') and 'cover' in file_name:
                                file_type = 'cover'
                            elif file_name.endswith('.jpg'):
                                file_type = 'image'
                            elif file_name == 'info.json':
                                file_type = 'info'
                            elif file_name == 'detail.txt':
                                file_type = 'detail'
                            else:
                                continue
                            
                            files_info.append({
                                'file_name': file_name,
                                'file_type': file_type,
                                'file_path': file_path,
                                'file_size': file_size,
                                'is_valid': True
                            })
                    
                    # 构建作品信息
                    work_record = {
                        'work_id': work_id,
                        'user_id': user_id,
                        'nickname': nickname,
                        'title': title,
                        'work_type': work_info.get('work_type', '未知'),
                        'work_url': work_info.get('work_url', ''),
                        'user_url': '',
                        'save_path': work_path,
                        'is_complete': True
                    }
                    
                    # 记录到数据库
                    if self.record_work_download(work_record, files_info):
                        rebuilt_count += 1
                        
                except Exception as e:
                    logger.error(f"处理作品 {work_path} 时出错: {e}")
                    continue
        
        logger.info(f"重建完成，处理了 {rebuilt_count} 个作品")
        return rebuilt_count
    
    def get_database_info(self) -> Dict:
        """获取数据库基本信息"""
        with sqlite3.connect(self.db_path, timeout=30) as conn:
            # 获取表统计信息
            stats = {}
            for table in ['users', 'works', 'files']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # 获取数据库文件大小
            stats['db_size'] = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return stats


# 全局数据库实例
db_instance = None

def get_download_db() -> DownloadDatabase:
    """获取数据库实例（单例模式）"""
    global db_instance
    if db_instance is None:
        db_instance = DownloadDatabase()
    return db_instance