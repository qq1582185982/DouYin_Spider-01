#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_user_info():
    """测试获取用户信息"""
    try:
        from dy_apis.douyin_api import DouyinAPI
        from builder.auth import DouyinAuth
        
        print("导入模块成功")
        
        # 创建auth对象
        auth = DouyinAuth()
        print("创建auth对象成功")
        
        # 从配置文件读取cookie
        import json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        cookie = config.get('cookie', '')
        if cookie:
            auth.perepare_auth(cookie, "", "")
            print("设置cookie成功")
        else:
            print("未找到cookie配置")
            return
        
        # 测试获取用户信息
        test_user_url = "https://www.douyin.com/user/MS4wLjABAAAA1PK28AaTahNIbTh5knXjanhj0dP3RlLaNqaxjcSsIFY"
        print(f"测试用户URL: {test_user_url}")
        
        # 获取用户信息
        user_info = DouyinAPI.get_user_info(auth, test_user_url)
        print("获取用户信息成功")
        
        # 打印用户信息
        user = user_info.get('user', {})
        print(f"用户昵称: {user.get('nickname', 'Unknown')}")
        print(f"用户签名: {user.get('signature', 'Unknown')}")
        print(f"粉丝数量: {user.get('follower_count', 0)}")
        print(f"作品数量: {user.get('aweme_count', 0)}")
        
        # 获取用户作品列表
        print("\n开始获取用户作品列表...")
        work_list = DouyinAPI.get_user_all_work_info(auth, test_user_url)
        print(f"获取作品列表成功，实际作品数量: {len(work_list)}")
        
        # 打印前几个作品的信息
        for i, work in enumerate(work_list[:3]):
            print(f"作品 {i+1}: {work.get('desc', 'No description')[:50]}...")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_user_info() 