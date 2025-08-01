# coding=utf-8
"""
详细调试脚本 - 捕获原始响应
"""
import os
import json
import requests
from dotenv import load_dotenv
from loguru import logger

# 配置日志
logger.add("debug_spider.log", rotation="10 MB", encoding='utf-8')

# 加载环境变量
load_dotenv()

def intercept_request():
    """拦截并记录HTTP请求"""
    import requests
    
    # 保存原始的get方法
    original_get = requests.get
    
    def debug_get(url, **kwargs):
        logger.info(f"HTTP GET请求: {url}")
        logger.info(f"请求参数: {kwargs.get('params', {})}")
        logger.info(f"请求头: {kwargs.get('headers', {})}")
        
        # 执行原始请求
        resp = original_get(url, **kwargs)
        
        logger.info(f"响应状态码: {resp.status_code}")
        logger.info(f"响应头: {dict(resp.headers)}")
        logger.info(f"响应内容长度: {len(resp.text)}")
        
        if resp.text:
            logger.info(f"响应内容前1000字符: {resp.text[:1000]}")
        else:
            logger.info("响应内容为空!")
            
        return resp
    
    # 替换requests.get
    requests.get = debug_get

def test_spider():
    """测试爬虫功能"""
    try:
        # 初始化
        from utils.common_util import init
        from main import Data_Spider
        
        print("正在初始化...")
        auth, base_path = init()
        spider = Data_Spider()
        
        # 拦截HTTP请求
        intercept_request()
        
        # 测试URL
        test_url = "https://www.douyin.com/user/MS4wLjABAAAA4gJZQb3WwpH2aKXBvY5HbzYO9g7i7g_h1uzeZuNbhcs"
        
        print(f"\n测试获取用户信息: {test_url}")
        
        try:
            user_info = spider.douyin_apis.get_user_info(auth, test_url)
            print(f"成功! 用户信息: {user_info}")
        except Exception as e:
            print(f"失败: {e}")
            logger.error(f"获取用户信息失败: {e}", exc_info=True)
            
        # 测试获取用户作品
        print(f"\n测试获取用户所有作品...")
        try:
            work_list = spider.douyin_apis.get_user_all_work_info(auth, test_url)
            print(f"成功! 作品数量: {len(work_list)}")
        except Exception as e:
            print(f"失败: {e}")
            logger.error(f"获取用户作品失败: {e}", exc_info=True)
            
    except Exception as e:
        print(f"初始化失败: {e}")
        logger.error(f"初始化失败: {e}", exc_info=True)

if __name__ == "__main__":
    print("=" * 60)
    print("抖音爬虫详细调试")
    print("=" * 60)
    print("日志文件: debug_spider.log")
    print("=" * 60)
    
    test_spider()
    
    print("\n请查看 debug_spider.log 文件获取详细信息")