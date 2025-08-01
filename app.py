# coding=utf-8
import os
import json
import uuid
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

from dy_apis.douyin_api import DouyinAPI
from utils.common_util import init
from utils.data_util import handle_work_info, download_work, save_to_xlsx
from main import Data_Spider

app = Flask(__name__)
CORS(app)

# 全局变量
auth = None
base_path = None
data_spider = None
tasks = {}
config = {
    'cookie': '',
    'save_path': '',
    'proxy': ''
}

# 初始化
def initialize():
    global auth, base_path, data_spider
    try:
        auth, base_path = init()
        data_spider = Data_Spider()
    except Exception as e:
        print(f"初始化失败: {e}")

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        # 简单的系统状态
        status = {
            'is_running': True,
            'cookie_valid': bool(config.get('cookie')),
            'total_works': 0,  # 需要实际统计
            'total_users': 0,  # 需要实际统计
            'disk_usage': {
                'used': 0,
                'total': 0
            }
        }
        return jsonify({'code': 0, 'message': 'success', 'data': status})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/system/validate-cookie', methods=['POST'])
def validate_cookie():
    """验证Cookie是否有效"""
    try:
        data = request.get_json()
        cookie = data.get('cookie', '')
        
        # 这里需要实际验证Cookie的逻辑
        # 暂时简单判断是否非空
        is_valid = bool(cookie)
        
        return jsonify({'code': 0, 'message': 'success', 'data': is_valid})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    return jsonify({'code': 0, 'message': 'success', 'data': config})

@app.route('/api/config', methods=['PUT'])
def update_config():
    """更新配置"""
    try:
        data = request.get_json()
        config.update(data)
        
        # 如果有Cookie更新，需要重新初始化auth
        if 'cookie' in data and data['cookie']:
            # 这里需要更新auth的cookie
            pass
            
        return jsonify({'code': 0, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/user', methods=['POST'])
def spider_user():
    """爬取用户所有作品"""
    try:
        data = request.get_json()
        user_url = data.get('user_url')
        save_choice = data.get('save_choice', 'all')
        
        if not user_url:
            raise BadRequest('user_url is required')
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'user',
            'status': 'pending',
            'url': user_url,
            'progress': 0,
            'total': 0,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        # 在后台线程中执行爬取
        def run_spider():
            try:
                task['status'] = 'running'
                # 这里调用实际的爬取函数
                # data_spider.spider_user_all_work(auth, user_url, base_path, save_choice)
                task['status'] = 'completed'
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
            finally:
                task['updated_at'] = int(time.time())
        
        threading.Thread(target=run_spider).start()
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/work', methods=['POST'])
def spider_work():
    """爬取单个作品"""
    try:
        data = request.get_json()
        work_url = data.get('work_url')
        
        if not work_url:
            raise BadRequest('work_url is required')
        
        # 这里调用实际的爬取函数
        # work_info = data_spider.spider_work(auth, work_url)
        work_info = {}  # 临时返回空对象
        
        return jsonify({'code': 0, 'message': 'success', 'data': work_info})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/search', methods=['POST'])
def spider_search():
    """搜索爬取"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            raise BadRequest('query is required')
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'search',
            'status': 'pending',
            'query': query,
            'progress': 0,
            'total': 0,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    task_list = list(tasks.values())
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify({'code': 0, 'message': 'success', 'data': task_list})

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': 'Task not found'}), 404
    return jsonify({'code': 0, 'message': 'success', 'data': task})

@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': 'Task not found'}), 404
    
    if task['status'] in ['completed', 'failed']:
        return jsonify({'code': 400, 'message': 'Task already finished'}), 400
    
    task['status'] = 'failed'
    task['error'] = 'Cancelled by user'
    task['updated_at'] = int(time.time())
    
    return jsonify({'code': 0, 'message': 'success'})

@app.route('/api/works', methods=['GET'])
def get_works():
    """获取作品列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    # 这里需要实际从数据库或文件系统读取
    works = []
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'items': works,
            'total': 0,
            'page': page,
            'limit': limit
        }
    })

if __name__ == '__main__':
    import time
    initialize()
    app.run(debug=True, port=8000)