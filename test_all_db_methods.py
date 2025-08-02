# coding=utf-8
from utils.database import get_database
import json

print("全面测试数据库所有方法...")
db = get_database()

# 1. 测试下载记录相关方法
print("\n=== 1. 测试下载记录相关方法 ===")

# add_download_record
test_work = {
    'work_id': 'full_test_001',
    'user_id': 'test_user_001',
    'nickname': '测试用户A',
    'title': '测试视频001',
    'work_type': 'video',
    'save_path': './downloads/test',
    'file_size': 1024000,
    'work_url': 'https://test.com/001',
    'is_complete': True
}
result = db.add_download_record(test_work)
print(f"add_download_record: {'OK' if result else 'FAIL'}")

# get_work_info
work = db.get_work_info('full_test_001')
print(f"get_work_info: {'OK' if work else 'FAIL'}")

# check_work_exists
exists = db.check_work_exists('full_test_001')
print(f"check_work_exists: {'OK' if exists else 'FAIL'}")

# is_work_complete
complete = db.is_work_complete('full_test_001')
print(f"is_work_complete: {'OK' if complete else 'FAIL'}")

# get_downloaded_work_ids
work_ids = db.get_downloaded_work_ids()
print(f"get_downloaded_work_ids (all): {'OK' if len(work_ids) > 0 else 'FAIL'} ({len(work_ids)} 个)")

work_ids_user = db.get_downloaded_work_ids('test_user_001')
print(f"get_downloaded_work_ids (user): {'OK' if len(work_ids_user) > 0 else 'FAIL'} ({len(work_ids_user)} 个)")

# record_work_download
work_record = {
    'work_id': 'full_test_002',
    'user_id': 'test_user_001',
    'nickname': '测试用户A',
    'title': '测试视频002',
    'save_path': './downloads/test2'
}
files_info = [
    {'file_name': 'video.mp4', 'file_size': 5000000},
    {'file_name': 'cover.jpg', 'file_size': 100000}
]
result = db.record_work_download(work_record, files_info)
print(f"record_work_download: {'OK' if result else 'FAIL'}")

# get_recent_downloads
recent = db.get_recent_downloads(5)
print(f"get_recent_downloads: {'OK' if len(recent) > 0 else 'FAIL'} ({len(recent)} 个)")

# get_total_works_count
total = db.get_total_works_count()
print(f"get_total_works_count: {'OK' if total > 0 else 'FAIL'} ({total} 个)")

# get_download_stats
stats = db.get_download_stats()
print(f"get_download_stats: {'OK' if stats['total_works'] > 0 else 'FAIL'}")

# 2. 测试订阅相关方法
print("\n=== 2. 测试订阅相关方法 ===")

# add_subscription
user_info = {
    'user_id': 'sub_test_001',
    'nickname': '订阅测试用户',
    'avatar': 'https://test.com/avatar.jpg',
    'user_url': 'https://test.com/user/001',
    'follower_count': 10000
}
sub_id = db.add_subscription(user_info)
print(f"add_subscription: {'OK' if sub_id else 'FAIL'} (ID: {sub_id})")

# get_subscription
sub = db.get_subscription('sub_test_001')
print(f"get_subscription: {'OK' if sub else 'FAIL'}")

# update_subscription
result = db.update_subscription('sub_test_001', enabled=0, auto_download=0)
print(f"update_subscription: {'OK' if result else 'FAIL'}")

# get_all_subscriptions
subs = db.get_all_subscriptions()
print(f"get_all_subscriptions: {'OK' if len(subs) > 0 else 'FAIL'} ({len(subs)} 个)")

# add_subscription_video
if sub_id:
    video_info = {
        'aweme_id': 'video_test_001',
        'desc': '测试视频描述',
        'create_time': 1640000000,
        'duration': 30000,
        'video': {'cover': {'url_list': ['https://test.com/cover.jpg']}},
        'statistics': {'play_count': 1000, 'digg_count': 100}
    }
    result = db.add_subscription_video(sub_id, video_info)
    print(f"add_subscription_video: {'OK' if result else 'FAIL'}")
    
    # get_subscription_videos
    videos = db.get_subscription_videos(sub_id)
    print(f"get_subscription_videos: {'OK' if len(videos) > 0 else 'FAIL'} ({len(videos)} 个)")
    
    # mark_video_downloaded
    result = db.mark_video_downloaded('video_test_001')
    print(f"mark_video_downloaded: {'OK' if result else 'FAIL'}")

# get_subscription_stats
stats = db.get_subscription_stats()
print(f"get_subscription_stats: {'OK' if stats['total_subscriptions'] > 0 else 'FAIL'}")

# 3. 测试数据库维护方法
print("\n=== 3. 测试数据库维护方法 ===")

# get_database_info
info = db.get_database_info()
print(f"get_database_info: {'OK' if info['total_records'] > 0 else 'FAIL'}")
print(f"  - 数据库路径: {info['database_path']}")
print(f"  - 数据库大小: {info['database_size']} bytes")
print(f"  - 表信息: {info['tables']}")

# cleanup_invalid_records
cleaned = db.cleanup_invalid_records()
print(f"cleanup_invalid_records: OK (清理了 {cleaned} 条记录)")

# remove_subscription (放在最后测试)
result = db.remove_subscription('sub_test_001')
print(f"remove_subscription: {'OK' if result else 'FAIL'}")

print("\n所有方法测试完成！")