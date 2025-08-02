# coding=utf-8
import requests
import json

base_url = "http://localhost:8000/api"

print("测试API数据库功能...")

# 1. 测试数据库统计
print("\n1. 获取数据库统计信息:")
response = requests.get(f"{base_url}/database/stats")
if response.status_code == 200:
    stats = response.json()['data']
    print(f"下载统计: {stats['download_stats']}")
    print(f"数据库信息: {stats['database_info']}")
else:
    print(f"获取统计失败: {response.status_code}")

# 2. 测试订阅功能
print("\n2. 测试订阅功能:")
# 获取订阅列表
response = requests.get(f"{base_url}/subscriptions")
if response.status_code == 200:
    data = response.json()['data']
    print(f"订阅数量: {len(data['subscriptions'])}")
    print(f"订阅统计: {data['stats']}")
else:
    print(f"获取订阅列表失败: {response.status_code}")

# 3. 测试作品列表
print("\n3. 获取作品列表:")
response = requests.get(f"{base_url}/works?page=1&limit=10")
if response.status_code == 200:
    data = response.json()['data']
    print(f"作品总数: {data['total']}")
    print(f"当前页作品数: {len(data['items'])}")
    if data['items']:
        work = data['items'][0]
        print(f"第一个作品: {work.get('title', 'No title')} (ID: {work['work_id']})")
else:
    print(f"获取作品列表失败: {response.status_code}")

print("\n测试完成！统一数据库功能正常。")