# coding=utf-8
import os
import json
import uuid
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
CORS(app)

# 全局变量
tasks = {}
config = {
    'cookie': '',
    'save_path': './downloads',
    'proxy': ''
}

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = {
            'is_running': True,
            'cookie_valid': bool(config.get('cookie')),
            'total_works': 123,  # 模拟数据
            'total_users': 45,   # 模拟数据
            'disk_usage': {
                'used': 1024 * 1024 * 500,  # 500MB
                'total': 1024 * 1024 * 1000  # 1GB
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
        
        # 模拟验证
        is_valid = len(cookie) > 10
        
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
        
        # 模拟后台爬取
        def run_spider():
            try:
                task['status'] = 'running'
                time.sleep(2)  # 模拟爬取过程
                task['progress'] = 50
                task['total'] = 100
                time.sleep(2)
                task['progress'] = 100
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

@app.route('/api/works', methods=['GET'])
def get_works():
    """获取作品列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    # 模拟数据
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

@app.route('/')
def index():
    """测试首页"""
    return jsonify({
        'message': 'DouYin Spider API Server',
        'version': '1.0.0',
        'endpoints': [
            '/api/system/status',
            '/api/config',
            '/api/spider/user',
            '/api/tasks'
        ]
    })

if __name__ == '__main__':
    print("Starting DouYin Spider API Server on http://localhost:8000")
    app.run(debug=True, port=8000, host='0.0.0.0')