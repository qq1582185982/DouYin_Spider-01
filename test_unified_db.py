# coding=utf-8
import os
from utils.database import get_database

print("测试统一数据库功能...")

# 删除旧的数据库文件（如果存在）
old_dbs = ['downloads.db', 'subscriptions.db']
for db_file in old_dbs:
    if os.path.exists(db_file):
        print(f"删除旧数据库: {db_file}")
        os.remove(db_file)

# 获取数据库实例
db = get_database()
print(f"数据库创建成功: {db.db_path}")

# 1. 测试下载记录功能
print("\n1. 测试下载记录功能:")
test_work = {
    'work_id': 'test123',
    'user_id': 'user456',
    'nickname': '测试用户',
    'title': '测试视频',
    'work_type': 'video',
    'save_path': './test_path',
    'file_size': 1024000,
    'work_url': 'https://test.com/work/123'
}

result = db.add_download_record(test_work)
print(f"添加下载记录: {'成功' if result else '失败'}")

# 获取作品信息
work_info = db.get_work_info('test123')
if work_info:
    print(f"获取作品信息成功: {work_info['title']}")
else:
    print("获取作品信息失败")

# 检查作品是否存在
exists = db.check_work_exists('test123')
print(f"作品是否存在: {'是' if exists else '否'}")

# 2. 测试订阅功能
print("\n2. 测试订阅功能:")
test_user = {
    'user_id': 'sub_user123',
    'sec_uid': 'sec_123',
    'nickname': '订阅测试用户',
    'avatar': 'https://test.com/avatar.jpg',
    'signature': '这是一个测试签名',
    'user_url': 'https://test.com/user/123',
    'follower_count': 10000,
    'aweme_count': 50
}

sub_id = db.add_subscription(test_user)
print(f"添加订阅: {'成功' if sub_id else '失败'} (ID: {sub_id})")

# 获取订阅信息
sub_info = db.get_subscription('sub_user123')
if sub_info:
    print(f"获取订阅信息成功: {sub_info['nickname']}")
else:
    print("获取订阅信息失败")

# 获取所有订阅
subs = db.get_all_subscriptions()
print(f"订阅列表数量: {len(subs)}")

# 3. 测试订阅视频功能
print("\n3. 测试订阅视频功能:")
test_video = {
    'aweme_id': 'video123',
    'desc': '测试视频描述',
    'create_time': 1640000000,
    'duration': 30000,
    'video': {
        'cover': {
            'url_list': ['https://test.com/cover.jpg']
        }
    },
    'statistics': {
        'play_count': 10000,
        'digg_count': 500,
        'comment_count': 100,
        'share_count': 50
    }
}

if sub_id:
    video_added = db.add_subscription_video(sub_id, test_video)
    print(f"添加订阅视频: {'成功' if video_added else '失败'}")
    
    # 获取订阅的视频
    videos = db.get_subscription_videos(sub_id)
    print(f"订阅视频数量: {len(videos)}")

# 4. 测试统计功能
print("\n4. 测试统计功能:")
download_stats = db.get_download_stats()
print(f"下载统计: {download_stats}")

sub_stats = db.get_subscription_stats()
print(f"订阅统计: {sub_stats}")

db_info = db.get_database_info()
print(f"数据库信息: {db_info}")

print("\n数据库测试完成！")