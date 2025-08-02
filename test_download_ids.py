# coding=utf-8
from utils.database import get_database

print("测试 get_downloaded_work_ids 方法...")

db = get_database()

# 1. 添加一些测试数据
test_works = [
    {
        'work_id': 'work001',
        'user_id': 'user123',
        'nickname': '用户A',
        'title': '视频1'
    },
    {
        'work_id': 'work002',
        'user_id': 'user123',
        'nickname': '用户A',
        'title': '视频2'
    },
    {
        'work_id': 'work003',
        'user_id': 'user456',
        'nickname': '用户B',
        'title': '视频3'
    }
]

for work in test_works:
    db.add_download_record(work)
    print(f"添加作品: {work['work_id']}")

# 2. 测试获取所有已下载作品ID
print("\n获取所有已下载作品ID:")
all_ids = db.get_downloaded_work_ids()
print(f"所有作品ID: {all_ids}")
print(f"数量: {len(all_ids)}")

# 3. 测试获取特定用户的已下载作品ID
print("\n获取用户 user123 的已下载作品ID:")
user_ids = db.get_downloaded_work_ids('user123')
print(f"用户作品ID: {user_ids}")
print(f"数量: {len(user_ids)}")

print("\n测试完成！")