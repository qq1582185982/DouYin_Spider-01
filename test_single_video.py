#!/usr/bin/env python3
# coding=utf-8

import os
from dotenv import load_dotenv
from main import Data_Spider
from builder.auth import DouyinAuth

def test_single_video_download():
    """测试单个视频下载"""
    try:
        load_dotenv()
        
        # 创建认证对象
        auth = DouyinAuth()
        cookie_str = os.getenv('DY_COOKIES', '')
        auth.perepare_auth(cookie_str, "", "")
        print("认证准备完成")
        
        # 创建爬虫对象
        data_spider = Data_Spider()
        print("爬虫对象创建完成")
        
        # 测试URL（一个作品）
        work_url = "https://www.douyin.com/video/7413703786981575962"
        
        # 设置保存路径
        base_path = {
            'media': './downloads/media',
            'excel': './downloads/excel'
        }
        
        # 确保目录存在
        os.makedirs(base_path['media'], exist_ok=True)
        os.makedirs(base_path['excel'], exist_ok=True)
        
        print(f"开始爬取作品: {work_url}")
        
        # 爬取单个作品
        work_info = data_spider.spider_work(auth, work_url)
        print(f"作品信息获取成功: {work_info['title']}")
        
        # 手动调用下载函数测试
        from utils.data_util import download_work
        download_path = download_work(work_info, base_path['media'], 'media-video')
        
        print(f"下载完成，保存路径: {download_path}")
        
        # 检查文件大小
        video_path = os.path.join(download_path, 'video.mp4')
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            print(f"视频文件大小: {file_size} bytes")
            if file_size > 1000:
                print("SUCCESS 视频下载成功!")
            else:
                print("ERROR 视频文件过小，可能下载失败")
        else:
            print("ERROR 视频文件不存在")
            
    except Exception as e:
        print(f"ERROR 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_video_download()