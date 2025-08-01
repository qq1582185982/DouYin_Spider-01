#!/usr/bin/env python3
# coding=utf-8

import traceback
import sys
import os

def debug_spider():
    """调试爬虫错误"""
    try:
        # 导入必要的模块
        from main import Data_Spider
        from builder.auth import DouyinAuth
        from dotenv import load_dotenv
        
        load_dotenv()
        
        print("1. 模块导入成功")
        
        # 创建认证对象
        auth = DouyinAuth()
        cookie_str = os.getenv('DY_COOKIES', '')
        
        print(f"2. Cookie 长度: {len(cookie_str)}")
        print(f"3. Cookie 类型: {type(cookie_str)}")
        
        # 测试 auth.perepare_auth
        print("4. 开始准备认证...")
        try:
            auth.perepare_auth(cookie_str, "", "")
            print("5. 认证准备成功")
        except Exception as e:
            print(f"5. 认证准备失败: {e}")
            traceback.print_exc()
            return
        
        # 创建爬虫对象
        print("6. 创建爬虫对象...")
        try:
            data_spider = Data_Spider()
            print("7. 爬虫对象创建成功")
        except Exception as e:
            print(f"7. 爬虫对象创建失败: {e}")
            traceback.print_exc()
            return
        
        # 测试参数准备
        print("8. 准备爬虫参数...")
        try:
            user_url = "https://www.douyin.com/user/test"
            spider_base_path = {
                'media': './downloads/media',
                'excel': './downloads/excel'
            }
            save_choice = 'all'
            excel_name = user_url.split('/')[-1].split('?')[0]
            
            print(f"   user_url: {type(user_url)} = {user_url}")
            print(f"   spider_base_path: {type(spider_base_path)} = {spider_base_path}")
            print(f"   save_choice: {type(save_choice)} = {save_choice}")
            print(f"   excel_name: {type(excel_name)} = {excel_name}")
            
        except Exception as e:
            print(f"8. 参数准备失败: {e}")
            traceback.print_exc()
            return
        
        # 测试爬虫调用（但不真的执行）
        print("9. 测试爬虫函数调用...")
        try:
            # 只测试函数是否存在和可调用
            spider_func = getattr(data_spider, 'spider_user_all_work', None)
            if spider_func:
                print("10. 爬虫函数存在")
                print(f"    函数签名: {spider_func.__code__.co_varnames}")
            else:
                print("10. 爬虫函数不存在")
                
        except Exception as e:
            print(f"9. 爬虫函数测试失败: {e}")
            traceback.print_exc()
            return
            
        print("✅ 所有基本测试通过")
        
    except Exception as e:  
        print(f"❌ 调试过程中出现错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_spider()