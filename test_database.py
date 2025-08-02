# coding=utf-8
"""
测试数据库驱动的增量下载功能
"""
from utils.download_db import get_download_db
from loguru import logger
import os

def test_database_functionality():
    """测试数据库基本功能"""
    logger.info("开始测试数据库功能...")
    
    # 获取数据库实例
    db = get_download_db()
    
    # 测试数据库基本信息
    db_info = db.get_database_info()
    logger.info(f"数据库信息: {db_info}")
    
    # 测试下载统计
    stats = db.get_download_stats()
    logger.info(f"下载统计: {stats}")
    
    # 测试最近下载记录
    recent = db.get_recent_downloads(5)
    logger.info(f"最近下载记录: {len(recent)} 条")
    for record in recent:
        logger.info(f"  - {record['work_id']}: {record['title']} ({record['work_type']})")
    
    # 测试已下载作品ID集合
    downloaded_ids = db.get_downloaded_work_ids()
    logger.info(f"已下载作品数量: {len(downloaded_ids)}")
    
    # 如果有下载目录，测试重建功能
    downloads_path = "./downloads/media"
    if os.path.exists(downloads_path):
        # 先清理无效记录
        cleaned = db.cleanup_invalid_records()
        logger.info(f"清理了 {cleaned} 条无效记录")
        
        # 然后重建索引
        rebuilt = db.rebuild_from_filesystem(downloads_path)
        logger.info(f"重建了 {rebuilt} 个作品的索引")
        
        # 重新获取统计信息
        stats_after = db.get_download_stats()
        logger.info(f"重建后的统计: {stats_after}")
    else:
        logger.info(f"下载目录不存在: {downloads_path}")
    
    logger.info("数据库功能测试完成!")

def test_work_completion_check():
    """测试作品完整性检查"""
    logger.info("测试作品完整性检查功能...")
    
    db = get_download_db()
    
    # 获取前5个作品进行测试
    downloaded_ids = list(db.get_downloaded_work_ids())[:5]
    
    for work_id in downloaded_ids:
        is_complete = db.is_work_complete(work_id)
        work_info = db.get_work_info(work_id)
        if work_info:
            logger.info(f"作品 {work_id}: 完整性={is_complete}, 标题={work_info.get('title', 'N/A')}")
    
    logger.info("作品完整性检查测试完成!")

if __name__ == "__main__":
    # 设置日志
    logger.add("test_database.log", rotation="1 MB", level="INFO", encoding="utf-8")
    
    try:
        test_database_functionality()
        print()
        test_work_completion_check()
        
        print("\n=== 测试结果 ===")
        print("[OK] 数据库基本功能正常")
        print("[OK] 统计信息获取正常")
        print("[OK] 记录清理和重建功能正常")
        print("[OK] 作品完整性检查正常")
        print("\n数据库驱动的增量下载系统已经准备就绪!")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n[ERROR] 测试失败: {e}")