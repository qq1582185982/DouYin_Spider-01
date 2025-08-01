# coding=utf-8
"""
详细的爬虫诊断测试脚本
用于调试JSON解析错误
"""
import os
import json
import traceback
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 60)
print("抖音爬虫诊断测试")
print("=" * 60)

# 测试Cookie是否配置
cookie = os.getenv('DY_COOKIES', '')
if not cookie:
    print("[ERROR] 错误：未找到Cookie配置")
    print("请创建.env文件并配置DY_COOKIES")
    exit(1)

print("[OK] Cookie已配置")
print(f"Cookie长度: {len(cookie)}")
print(f"Cookie前50字符: {cookie[:50]}...")

# 测试目录创建
try:
    os.makedirs('./test_downloads/media', exist_ok=True)
    os.makedirs('./test_downloads/excel', exist_ok=True)
    print("[OK] 测试目录创建成功")
except Exception as e:
    print(f"[ERROR] 创建目录失败: {e}")

# 测试导入
try:
    from main import Data_Spider
    from utils.common_util import init
    from builder.auth import DouyinAuth
    from dy_apis.douyin_api import DouyinAPI
    print("[OK] 模块导入成功")
except Exception as e:
    print(f"[ERROR] 模块导入失败: {e}")
    traceback.print_exc()
    exit(1)

# 测试初始化
try:
    print("\n正在初始化...")
    auth, base_path = init()
    print("[OK] 初始化成功")
    print(f"基础路径: {base_path}")
    
    # 检查auth对象
    print(f"\nAuth对象属性:")
    print(f"- msToken: {getattr(auth, 'msToken', 'Not found')}")
    print(f"- cookie类型: {type(auth.cookie)}")
    if hasattr(auth, 'cookie') and auth.cookie:
        print(f"- cookie keys: {list(auth.cookie.keys())[:5]}...")  # 只显示前5个键
except Exception as e:
    print(f"[ERROR] 初始化失败: {e}")
    traceback.print_exc()
    exit(1)

# 测试爬虫实例化
try:
    spider = Data_Spider()
    print("\n[OK] 爬虫实例化成功")
except Exception as e:
    print(f"[ERROR] 爬虫实例化失败: {e}")
    traceback.print_exc()
    exit(1)

# 测试简单的API请求
print("\n" + "=" * 40)
print("测试API请求")
print("=" * 40)

try:
    import requests
    from builder.header import HeaderBuilder, HeaderType
    
    # 测试请求抖音主页
    url = "https://www.douyin.com/"
    headers = HeaderBuilder().build(HeaderType.GET)
    
    print(f"测试请求: {url}")
    resp = requests.get(url, headers=headers.get(), cookies=auth.cookie, verify=False, timeout=10)
    
    print(f"响应状态码: {resp.status_code}")
    print(f"响应Content-Type: {resp.headers.get('Content-Type', 'Not found')}")
    print(f"响应长度: {len(resp.text)}")
    
    if resp.status_code == 200:
        print("[OK] 基本连接正常")
    else:
        print("[ERROR] 连接异常")
        
except Exception as e:
    print(f"[ERROR] 请求测试失败: {e}")
    traceback.print_exc()

# 测试用户信息获取
print("\n" + "=" * 40)
print("测试用户信息获取")
print("=" * 40)

test_user_url = "https://www.douyin.com/user/MS4wLjABAAAA4gJZQb3WwpH2aKXBvY5HbzYO9g7i7g_h1uzeZuNbhcs"

try:
    print(f"测试URL: {test_user_url}")
    
    # 使用一个包装函数来捕获JSON错误
    original_loads = json.loads
    def debug_json_loads(text):
        try:
            return original_loads(text)
        except json.JSONDecodeError as e:
            print(f"\n[ERROR] JSON解析失败!")
            print(f"错误: {str(e)}")
            print(f"响应内容前500字符: {text[:500] if text else 'Empty'}")
            if text and text.strip().startswith('<'):
                print("响应是HTML，可能需要验证或Cookie已过期")
            raise
    
    # 临时替换json.loads
    json.loads = debug_json_loads
    
    # 尝试获取用户信息
    user_info = spider.douyin_apis.get_user_info(auth, test_user_url)
    print("[OK] 获取用户信息成功!")
    if 'user' in user_info:
        print(f"用户名: {user_info['user'].get('nickname', 'Unknown')}")
        
except Exception as e:
    print(f"[ERROR] 获取用户信息失败: {e}")
    if "JSONDecodeError" not in str(e):
        traceback.print_exc()
finally:
    # 恢复原始的json.loads
    json.loads = original_loads

print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

print("\n可能的问题:")
print("1. Cookie已过期 - 请从浏览器重新获取Cookie")
print("2. 抖音API变更 - 可能需要更新爬虫代码")
print("3. IP被限制 - 尝试使用代理或等待一段时间")
print("4. 需要验证码 - 在浏览器中访问抖音完成验证")

print("\n建议操作:")
print("1. 在浏览器中登录抖音，确保能正常访问")
print("2. 重新复制完整的Cookie字符串")
print("3. 更新.env文件中的DY_COOKIES")
print("4. 重新运行测试脚本")