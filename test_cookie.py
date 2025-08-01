#!/usr/bin/env python3
# coding=utf-8

import os
from dotenv import load_dotenv
from builder.auth import DouyinAuth
from dy_apis.douyin_api import DouyinAPI

def test_cookie_validity():
    """测试Cookie是否有效"""
    try:
        load_dotenv()
        
        # 创建认证对象
        auth = DouyinAuth()
        cookie_str = os.getenv('DY_COOKIES', '')
        
        print(f"Cookie长度: {len(cookie_str)}")
        print(f"Cookie前100字符: {cookie_str[:100]}...")
        
        auth.perepare_auth(cookie_str, "", "")
        print("认证准备完成")
        
        # 创建API对象
        api = DouyinAPI()
        
        # 测试一个简单的用户信息获取
        test_url = "https://www.douyin.com/user/MS4wLjABAAAAgr1ldMOw26_s3hhOJJjX3MQqLbvLbWiQ1ustJjAWYgg"
        
        print("尝试获取用户信息...")
        user_info = api.get_user_info(auth, test_url)
        
        if user_info and 'user' in user_info:
            print("OK Cookie有效，用户信息获取成功")
            print(f"用户昵称: {user_info['user'].get('nickname', '未知')}")
            print(f"用户作品数: {user_info['user'].get('aweme_count', '未知')}")
        else:
            print("ERROR Cookie可能无效或已过期")
            print(f"返回数据: {user_info}")
            
    except Exception as e:
        print(f"ERROR 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cookie_validity()