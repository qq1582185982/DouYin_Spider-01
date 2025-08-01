#!/usr/bin/env python3
# coding=utf-8

import traceback
import sys
import os
from dotenv import load_dotenv

def test_spider_execution():
    """直接测试爬虫执行，捕获详细错误"""
    try:
        load_dotenv()
        
        # 导入模块
        from main import Data_Spider
        from builder.auth import DouyinAuth
        
        print("1. 模块导入成功")
        
        # 创建认证对象
        auth = DouyinAuth()
        cookie_str = os.getenv('DY_COOKIES', '')
        
        print(f"2. 准备认证，Cookie长度: {len(cookie_str)}")
        auth.perepare_auth(cookie_str, "", "")
        print("3. 认证准备完成")
        
        # 创建爬虫对象
        data_spider = Data_Spider()
        print("4. 爬虫对象创建完成")
        
        # 准备参数
        user_url = "https://www.douyin.com/user/MS4wLjABAAAAgr1ldMOw26_s3hhOJJjX3MQqLbvLbWiQ1ustJjAWYgg"
        spider_base_path = {
            'media': './downloads/media',
            'excel': './downloads/excel'
        }
        save_choice = 'all'
        excel_name = user_url.split('/')[-1].split('?')[0]
        
        print("5. 参数准备完成")
        print(f"   user_url: {user_url}")
        print(f"   excel_name: {excel_name}")
        
        # 确保目录存在
        os.makedirs(spider_base_path['media'], exist_ok=True)
        os.makedirs(spider_base_path['excel'], exist_ok=True)
        print("6. 目录创建完成")
        
        # 尝试调用爬虫
        print("7. 开始调用爬虫...")
        try:
            data_spider.spider_user_all_work(
                auth, 
                user_url, 
                spider_base_path, 
                save_choice,
                excel_name
            )
            print("8. 爬虫执行完成")
        except Exception as spider_error:
            print(f"8. 爬虫执行失败: {spider_error}")
            print("详细错误信息:")
            traceback.print_exc()
            
            # 尝试更详细的分析
            print("\n=== 错误分析 ===")
            error_str = str(spider_error)
            if "sequence item 0: expected str instance, dict found" in error_str:
                print("这是join()操作的类型错误")
                print("可能的原因:")
                print("1. 某个地方传递了字典给join()操作")
                print("2. 列表中包含了字典而不是字符串")
                
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_spider_execution()