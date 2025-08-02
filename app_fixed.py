# coding=utf-8
import os
import json
import uuid
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
from loguru import logger

# 导入实际的爬虫和认证类
from main import Data_Spider
from builder.auth import DouyinAuth

app = Flask(__name__)
CORS(app)

# 全局变量
tasks = {}
CONFIG_FILE = 'config.json'

# 默认配置
DEFAULT_CONFIG = {
    'cookie': '',
    'save_path': './downloads',
    'proxy': ''
}

def load_config():
    """从配置文件和环境变量加载配置"""
    config = DEFAULT_CONFIG.copy()
    
    # 首先尝试从config.json读取
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                config.update(saved_config)
                logger.info(f"从配置文件加载配置: {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
    
    # 然后从.env文件读取Cookie（如果config中没有）
    if not config.get('cookie'):
        load_dotenv()
        env_cookie = os.getenv('DY_COOKIES', '')
        if env_cookie:
            config['cookie'] = env_cookie
            logger.info("从.env文件加载Cookie")
    
    return config

def save_config(config_data):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

# 加载配置
config = load_config()

# 初始化
data_spider = None
auth = None
base_path = None

def initialize():
    global data_spider, auth, base_path
    try:
        # 创建保存目录
        save_path = config.get('save_path', './downloads')
        os.makedirs(os.path.join(save_path, 'media'), exist_ok=True)
        os.makedirs(os.path.join(save_path, 'excel'), exist_ok=True)
        
        # 初始化爬虫
        data_spider = Data_Spider()
        
        # 创建auth对象并设置Cookie
        auth = DouyinAuth()
        cookie = config.get('cookie')
        if cookie:
            auth.perepare_auth(cookie, "", "")
            logger.info("从配置文件加载Cookie到认证模块")
        else:
            logger.warning("未找到Cookie配置")
        
        base_path = {
            'media': os.path.join(save_path, 'media'),
            'excel': os.path.join(save_path, 'excel')
        }
        
        logger.info(f"系统初始化成功")
        logger.info(f"Cookie状态: {'已配置' if cookie else '未配置'}")
        logger.info(f"保存路径: {save_path}")
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        raise

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        # 统计文件数量
        media_files = 0
        excel_files = 0
        
        if os.path.exists('./downloads/media'):
            for root, dirs, files in os.walk('./downloads/media'):
                media_files += len(files)
        
        if os.path.exists('./downloads/excel'):
            excel_files = len([f for f in os.listdir('./downloads/excel') if f.endswith('.xlsx')])
        
        status = {
            'is_running': True,
            'cookie_valid': bool(config.get('cookie')),
            'total_works': media_files,
            'total_users': excel_files,
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
        
        # 简单验证
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
        
        # 更新内存中的配置
        config.update(data)
        
        # 保存配置到文件
        if not save_config(config):
            return jsonify({'code': 500, 'message': '配置保存失败'}), 500
        
        # 更新auth的cookie
        if 'cookie' in data and data['cookie']:
            global auth
            if not auth:
                auth = DouyinAuth()
            auth.perepare_auth(data['cookie'], "", "")
            logger.info("Cookie已更新到认证模块")
            
        # 创建保存目录
        if 'save_path' in data and data['save_path']:
            os.makedirs(os.path.join(data['save_path'], 'media'), exist_ok=True)
            os.makedirs(os.path.join(data['save_path'], 'excel'), exist_ok=True)
            logger.info(f"创建保存目录: {data['save_path']}")
            
        return jsonify({'code': 0, 'message': '配置保存成功'})
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/user', methods=['POST'])
def spider_user():
    """爬取用户所有作品"""
    try:
        data = request.get_json()
        user_url = data.get('user_url')
        save_choice = data.get('save_choice', 'all')
        force_download = data.get('force_download', False)
        
        if not user_url:
            raise BadRequest('user_url is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
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
                task['updated_at'] = int(time.time())
                
                print(f"开始爬取用户: {user_url}")
                
                # 使用配置的保存路径
                save_path = config.get('save_path', './downloads')
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
                # 确保目录存在
                os.makedirs(spider_base_path['media'], exist_ok=True)
                os.makedirs(spider_base_path['excel'], exist_ok=True)
                
                # 实际调用爬虫
                if data_spider and auth:
                    try:
                        # 创建简单的.env文件供爬虫使用
                        cookie_str = config.get("cookie", "")
                        if isinstance(cookie_str, dict):
                            cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_str.items()])
                        
                        with open('.env', 'w', encoding='utf-8') as f:
                            f.write(f'DY_COOKIES={cookie_str}\n')
                            f.write(f'DY_LIVE_COOKIES={cookie_str}\n')
                        
                        # 调用爬虫，注意需要传入excel_name参数
                        excel_name = user_url.split('/')[-1].split('?')[0]
                        download_stats = data_spider.spider_user_all_work(
                            auth, 
                            user_url, 
                            spider_base_path, 
                            save_choice,
                            excel_name,
                            proxies=None,
                            force_download=force_download
                        )
                        
                        task['status'] = 'completed'
                        task['progress'] = 100
                        task['total'] = download_stats['total_works']
                        task['download_stats'] = download_stats
                        logger.info(f"用户爬取完成: {user_url}")
                        logger.info(f"下载统计: 新下载{download_stats['works_downloaded']}个作品, 跳过{download_stats['works_skipped']}个作品")
                        logger.info(f"文件保存在: {spider_base_path}")
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"爬虫执行失败: {e}")
                        print(f"详细错误信息:\n{error_details}")
                        task['status'] = 'failed'
                        task['error'] = f'爬虫执行失败: {str(e)}'
                else:
                    task['status'] = 'failed'
                    task['error'] = '爬虫未初始化'
                    
            except Exception as e:
                print(f"任务执行失败: {e}")
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
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        # 使用配置的保存路径
        save_path = config.get('save_path', './downloads')
        spider_base_path = {
            'media': os.path.join(save_path, 'media'),
            'excel': os.path.join(save_path, 'excel')
        }
        
        # 调用爬虫
        if data_spider and auth:
            work_info = data_spider.spider_work(auth, work_url)
            return jsonify({'code': 0, 'message': 'success', 'data': work_info})
        else:
            return jsonify({'code': 500, 'message': '爬虫未初始化'}), 500
            
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
        force_download = data.get('force_download', False)
        
        if not query:
            raise BadRequest('query is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
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
        
        # 在后台线程中执行爬取
        def run_spider():
            try:
                task['status'] = 'running'
                task['updated_at'] = int(time.time())
                
                print(f"开始搜索: {query}")
                
                # 使用配置的保存路径
                save_path = config.get('save_path', './downloads')
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
                # 确保目录存在
                os.makedirs(spider_base_path['media'], exist_ok=True)
                os.makedirs(spider_base_path['excel'], exist_ok=True)
                
                # 调用爬虫
                if data_spider and auth:
                    options = data.get('options', {})
                    download_stats = data_spider.spider_some_search_work(
                        auth,
                        query,
                        options.get('require_num', 20),
                        spider_base_path,
                        options.get('save_choice', 'all'),
                        options.get('sort_type', '0'),
                        options.get('publish_time', '0'),
                        options.get('filter_duration', ''),
                        options.get('search_range', '0'),
                        options.get('content_type', '0'),
                        excel_name='',
                        proxies=None,
                        force_download=force_download
                    )
                    
                    task['status'] = 'completed'
                    task['progress'] = 100
                    task['total'] = download_stats['total_works']
                    task['download_stats'] = download_stats
                    logger.info(f"搜索爬取完成: {query}")
                    logger.info(f"下载统计: 新下载{download_stats['works_downloaded']}个作品, 跳过{download_stats['works_skipped']}个作品")
                else:
                    task['status'] = 'failed'
                    task['error'] = '爬虫未初始化'
                    
            except Exception as e:
                print(f"搜索任务失败: {e}")
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
    
    # 从excel目录读取数据
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
        'status': 'running',
        'cookie_configured': bool(config.get('cookie')),
        'save_path': config.get('save_path', './downloads')
    })

if __name__ == '__main__':
    initialize()
    print("DouYin Spider API Server")
    print("请先在Web界面设置Cookie")
    print("访问 http://localhost:8000")
    app.run(debug=True, port=8000, host='0.0.0.0')