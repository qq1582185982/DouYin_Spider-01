# coding=utf-8
"""
测试订阅扫描功能
"""
import asyncio
import json
from datetime import datetime
from builder.auth import DouyinAuth
from utils.scan_scheduler import SubscriptionScanner
from utils.database import get_database
from utils.notification import send_scan_notification
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_scan():
    """测试扫描功能"""
    print("=== 测试订阅扫描功能 ===\n")
    
    # 1. 初始化认证
    print("1. 初始化认证...")
    try:
        # 从config.json读取cookie
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        if not config.get('cookie'):
            print("错误：请先在config.json中配置Cookie")
            return
            
        auth = DouyinAuth(config['cookie'])
        print("✓ 认证初始化成功")
    except Exception as e:
        print(f"✗ 认证初始化失败: {e}")
        return
    
    # 2. 获取订阅列表
    print("\n2. 获取订阅列表...")
    db = get_database()
    subscriptions = db.get_all_subscriptions(enabled_only=True)
    
    if not subscriptions:
        print("✗ 没有启用的订阅")
        return
        
    print(f"✓ 找到 {len(subscriptions)} 个启用的订阅:")
    for sub in subscriptions[:3]:  # 只显示前3个
        print(f"   - {sub['nickname']} (ID: {sub['user_id']})")
    if len(subscriptions) > 3:
        print(f"   ... 还有 {len(subscriptions) - 3} 个订阅")
    
    # 3. 创建扫描器
    print("\n3. 创建扫描器...")
    scanner = SubscriptionScanner(scan_interval=3600, auto_download=False)
    scanner.set_auth(auth)
    
    # 设置新视频回调
    async def on_new_videos(user_id, videos):
        print(f"\n[新视频] 用户 {user_id} 有 {len(videos)} 个新视频")
        for video in videos[:3]:
            print(f"   - {video.get('desc', '无标题')[:50]}...")
    
    scanner.set_on_new_videos_callback(on_new_videos)
    print("✓ 扫描器创建成功")
    
    # 4. 执行一次扫描
    print("\n4. 执行扫描（只扫描第一个订阅作为测试）...")
    print("=" * 50)
    
    try:
        # 临时修改订阅列表，只扫描第一个
        original_get_all = db.get_all_subscriptions
        db.get_all_subscriptions = lambda enabled_only=False: [subscriptions[0]]
        
        # 执行扫描
        await scanner.scan_once()
        
        # 恢复原始方法
        db.get_all_subscriptions = original_get_all
        
        print("✓ 扫描完成")
        
    except Exception as e:
        print(f"✗ 扫描失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")

async def test_continuous_scan():
    """测试连续扫描"""
    print("=== 测试连续扫描功能 ===\n")
    
    # 初始化
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        auth = DouyinAuth(config['cookie'])
        scanner = SubscriptionScanner(scan_interval=60, auto_download=False)  # 1分钟扫描一次
        scanner.set_auth(auth)
        
        print("✓ 初始化成功")
        
        # 启动扫描
        print("\n启动连续扫描（每60秒扫描一次）...")
        print("按 Ctrl+C 停止\n")
        
        await scanner.start()
        
        # 等待扫描运行
        try:
            await asyncio.sleep(300)  # 运行5分钟
        except KeyboardInterrupt:
            print("\n正在停止扫描...")
            
        await scanner.stop()
        print("✓ 扫描已停止")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 单次扫描测试")
    print("2. 连续扫描测试")
    
    choice = input("\n请输入选择 (1/2): ").strip()
    
    if choice == '1':
        asyncio.run(test_scan())
    elif choice == '2':
        asyncio.run(test_continuous_scan())
    else:
        print("无效选择")