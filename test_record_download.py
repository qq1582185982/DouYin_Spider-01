# coding=utf-8
from utils.database import get_database

print("测试 record_work_download 方法...")

db = get_database()

# 准备测试数据
work_record = {
    'work_id': 'test_video_123',
    'user_id': 'test_user',
    'nickname': '测试用户',
    'title': '测试视频标题',
    'desc': '这是一个测试视频',
    'work_type': 'video',
    'save_path': './downloads/media/test_user/test_video_123',
    'work_url': 'https://test.com/video/123',
    'video_url': 'https://test.com/video/123.mp4',
    'cover_url': 'https://test.com/cover/123.jpg'
}

files_info = [
    {
        'file_name': 'video.mp4',
        'file_path': './downloads/media/test_user/test_video_123/video.mp4',
        'file_size': 5242880,  # 5MB
        'is_valid': True
    },
    {
        'file_name': 'cover.jpg',
        'file_path': './downloads/media/test_user/test_video_123/cover.jpg',
        'file_size': 102400,  # 100KB
        'is_valid': True
    },
    {
        'file_name': 'info.json',
        'file_path': './downloads/media/test_user/test_video_123/info.json',
        'file_size': 2048,  # 2KB
        'is_valid': True
    }
]

# 测试记录下载
print("\n1. 测试记录作品下载:")
result = db.record_work_download(work_record, files_info)
print(f"记录结果: {'成功' if result else '失败'}")

# 验证记录是否成功
print("\n2. 验证记录:")
work_info = db.get_work_info('test_video_123')
if work_info:
    print(f"作品标题: {work_info['title']}")
    print(f"文件大小: {work_info['file_size']} bytes")
    print(f"是否完整: {'是' if work_info['is_complete'] else '否'}")
    
    # 检查metadata中的文件信息
    if work_info.get('metadata') and 'files' in work_info['metadata']:
        print(f"文件数量: {len(work_info['metadata']['files'])}")
        for file in work_info['metadata']['files']:
            print(f"  - {file['file_name']}: {file['file_size']} bytes")
else:
    print("未找到作品记录")

print("\n测试完成！")