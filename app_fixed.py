# coding=utf-8
import os
import json
import uuid
import time
import threading
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
from loguru import logger

# 导入实际的爬虫和认证类
from main import Data_Spider
from builder.auth import DouyinAuth
from utils.download_db import get_download_db

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

def _get_local_cover_url(save_path):
    """获取本地封面图片URL"""
    if not save_path:
        return ''
    
    cover_file = os.path.join(save_path, 'cover.jpg')
    if os.path.exists(cover_file):
        # 将绝对路径转换为相对URL路径
        # 例如: D:\path\downloads\media\user\work\cover.jpg -> /media/user/work/cover.jpg
        relative_path = os.path.relpath(cover_file, os.path.join(os.getcwd(), 'downloads'))
        # 转换Windows路径分隔符为URL分隔符
        url_path = relative_path.replace('\\', '/')
        return f'/static/{url_path}'
    
    return ''

def _get_local_video_url(save_path):
    """获取本地视频文件URL"""
    if not save_path:
        return ''
    
    # 处理相对路径和绝对路径
    if os.path.isabs(save_path):
        # 如果是绝对路径，转换为相对路径
        base_dir = os.path.join(os.getcwd(), 'downloads')
        try:
            relative_save_path = os.path.relpath(save_path, base_dir)
        except ValueError:
            # 如果路径不在同一驱动器上，使用原始路径
            logger.warning(f"无法转换路径: {save_path}")
            return ''
    else:
        # 如果已经是相对路径，移除可能的前缀
        relative_save_path = save_path.replace('./downloads\\', '').replace('./downloads/', '')
    
    video_file = os.path.join(save_path, 'video.mp4')
    if os.path.exists(video_file):
        # 转换Windows路径分隔符为URL分隔符
        url_path = relative_save_path.replace('\\', '/')
        return f'/static/{url_path}/video.mp4'
    else:
        # 如果文件不存在，记录日志
        logger.warning(f"视频文件不存在: {video_file}")
    
    return ''

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
        
        # 规范化路径（根据操作系统）
        if 'save_path' in data and data['save_path']:
            # 使用 os.path.normpath 自动处理路径分隔符
            data['save_path'] = os.path.normpath(data['save_path'])
        
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
                        force_download=force_download,
                        use_database=True
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

@app.route('/api/works/<work_id>', methods=['GET'])
def get_work(work_id):
    """获取单个作品详情"""
    try:
        # 从数据库查找作品
        db = get_download_db()
        work = db.get_work_info(work_id)
        
        if not work:
            return jsonify({'code': 404, 'message': '作品不存在'}), 404
        
        # 加载完整作品信息
        if work['save_path']:
            info_file = os.path.join(work['save_path'], 'info.json')
            if os.path.exists(info_file):
                with open(info_file, 'r', encoding='utf-8') as f:
                    full_info = json.load(f)
                    # 构造前端期望的数据结构
                    enhanced_work = {
                        'work_id': full_info['work_id'],
                        'work_url': full_info['work_url'],
                        'work_type': full_info['work_type'],
                        'title': full_info['title'],
                        'desc': full_info['desc'],
                        'create_time': full_info['create_time'],
                        'statistics': {
                            'play_count': full_info.get('play_count', 0),
                            'digg_count': full_info['digg_count'],
                            'comment_count': full_info['comment_count'],
                            'collect_count': full_info['collect_count'],
                            'share_count': full_info['share_count'],
                            'admire_count': full_info.get('admire_count', 0)
                        },
                        'author': {
                            'nickname': full_info['nickname'],
                            'user_id': full_info['user_id'],
                            'user_url': full_info['user_url'],
                            'avatar_thumb': full_info.get('author_avatar', ''),
                            'user_desc': full_info.get('user_desc', ''),
                            'following_count': full_info.get('following_count', 0),
                            'follower_count': full_info.get('follower_count', 0)
                        },
                        'video': {
                            'cover': full_info.get('video_cover', ''),
                            'play_addr': full_info.get('video_addr', ''),
                            'local_path': _get_local_video_url(work['save_path'])
                        },
                        'images': full_info.get('images', []),
                        'topics': full_info.get('topics', []),
                        'download_time': work['download_time'],
                        'file_size': work['file_size'],
                        'is_complete': work['is_complete']
                    }
                    
                    return jsonify({
                        'code': 0,
                        'message': 'success',
                        'data': enhanced_work
                    })
        
        # 如果没有 info.json，返回基本信息
        basic_work = {
            'work_id': work['work_id'],
            'title': work['title'],
            'work_type': work['work_type'],
            'statistics': {'digg_count': 0, 'play_count': 0, 'comment_count': 0, 'collect_count': 0, 'share_count': 0},
            'author': {'nickname': work['nickname'], 'user_id': '', 'avatar_thumb': ''},
            'video': {'cover': '', 'play_addr': ''},
            'create_time': 0,
            'download_time': work['download_time'],
            'file_size': work['file_size'],
            'is_complete': work['is_complete']
        }
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': basic_work
        })
        
    except Exception as e:
        logger.error(f"获取作品详情失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/works', methods=['GET'])
def get_works():
    """获取作品列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    
    try:
        # 从数据库读取基本数据
        db = get_download_db()
        offset = (page - 1) * limit
        recent_works = db.get_recent_downloads(limit, offset)
        
        # 为每个作品加载完整信息
        enhanced_works = []
        for work in recent_works:
            try:
                # 根据work_id查找对应的info.json文件
                work_info = db.get_work_info(work['work_id'])
                if work_info and work_info['save_path']:
                    info_file = os.path.join(work_info['save_path'], 'info.json')
                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            full_info = json.load(f)
                            # 构造前端期望的数据结构
                            enhanced_work = {
                                'work_id': full_info['work_id'],
                                'work_url': full_info['work_url'],
                                'work_type': full_info['work_type'],
                                'title': full_info['title'],
                                'desc': full_info['desc'],
                                'create_time': full_info['create_time'],
                                'statistics': {
                                    'play_count': full_info.get('play_count', 0),  # 播放量可能不存在
                                    'digg_count': full_info['digg_count'],
                                    'comment_count': full_info['comment_count'],
                                    'collect_count': full_info['collect_count'],
                                    'share_count': full_info['share_count'],
                                    'admire_count': full_info.get('admire_count', 0)
                                },
                                'author': {
                                    'nickname': full_info['nickname'],
                                    'user_id': full_info['user_id'],
                                    'user_url': full_info['user_url'],
                                    'avatar_thumb': full_info.get('author_avatar', ''),
                                    'user_desc': full_info.get('user_desc', ''),
                                    'following_count': full_info.get('following_count', 0),
                                    'follower_count': full_info.get('follower_count', 0)
                                },
                                'video': {
                                    'cover': full_info.get('video_cover', ''),
                                    'play_addr': full_info.get('video_addr', '')
                                },
                                'images': full_info.get('images', []),
                                'topics': full_info.get('topics', []),
                                'download_time': work['download_time'],
                                'file_size': work['file_size'],
                                'is_complete': work['is_complete']
                            }
                            enhanced_works.append(enhanced_work)
                    else:
                        # 如果没有info.json，使用数据库中的基本信息
                        enhanced_works.append({
                            'work_id': work['work_id'],
                            'title': work['title'],
                            'work_type': work['work_type'],
                            'statistics': {'digg_count': 0, 'play_count': 0, 'comment_count': 0, 'collect_count': 0, 'share_count': 0},
                            'author': {'nickname': work['nickname'], 'user_id': '', 'avatar_thumb': ''},
                            'video': {'cover': '', 'play_addr': ''},
                            'create_time': 0,
                            'download_time': work['download_time'],
                            'file_size': work['file_size'],
                            'is_complete': work['is_complete']
                        })
            except Exception as e:
                logger.error(f"加载作品 {work['work_id']} 详细信息失败: {e}")
                # 发生错误时使用基本信息
                enhanced_works.append({
                    'work_id': work['work_id'],
                    'title': work['title'],
                    'work_type': work['work_type'],
                    'statistics': {'digg_count': 0, 'play_count': 0, 'comment_count': 0, 'collect_count': 0, 'share_count': 0},
                    'author': {'nickname': work['nickname'], 'user_id': '', 'avatar_thumb': ''},
                    'video': {'cover': '', 'play_addr': ''},
                    'create_time': 0,
                    'download_time': work['download_time'],
                    'file_size': work['file_size'],
                    'is_complete': work['is_complete']
                })
        
        # 获取总数
        total_count = db.get_total_works_count()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'items': enhanced_works,
                'total': total_count,
                'page': page,
                'limit': limit
            }
        })
    except Exception as e:
        logger.error(f"获取作品列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """获取数据库统计信息"""
    try:
        db = get_download_db()
        user_id = request.args.get('user_id')
        
        # 获取下载统计
        download_stats = db.get_download_stats(user_id)
        
        # 获取数据库基本信息
        db_info = db.get_database_info()
        
        # 获取最近下载记录
        recent_downloads = db.get_recent_downloads(10)
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'download_stats': download_stats,
                'database_info': db_info,
                'recent_downloads': recent_downloads
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/database/cleanup', methods=['POST'])
def cleanup_database():
    """清理数据库中的无效记录"""
    try:
        db = get_download_db()
        cleaned_count = db.cleanup_invalid_records()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'cleaned_count': cleaned_count,
                'message': f'已清理 {cleaned_count} 条无效记录'
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/database/rebuild', methods=['POST'])
def rebuild_database():
    """从文件系统重建数据库索引"""
    try:
        data = request.get_json()
        base_path = data.get('base_path', config.get('save_path', './downloads') + '/media')
        
        db = get_download_db()
        rebuilt_count = db.rebuild_from_filesystem(base_path)
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'rebuilt_count': rebuilt_count,
                'message': f'已重建 {rebuilt_count} 个作品的索引',
                'base_path': base_path
            }
        })
    except Exception as e:
        logger.error(f"重建数据库索引失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/video/<work_id>')
def serve_video(work_id):
    """直接提供视频文件"""
    try:
        db = get_download_db()
        work = db.get_work_info(work_id)
        
        if not work:
            return jsonify({'error': '作品不存在'}), 404
        
        save_path = work.get('save_path', '')
        video_file = os.path.join(save_path, 'video.mp4') if save_path else ''
        
        if video_file and os.path.exists(video_file):
            return send_file(
                video_file,
                mimetype='video/mp4',
                as_attachment=False,
                conditional=True
            )
        else:
            return jsonify({'error': '视频文件不存在'}), 404
            
    except Exception as e:
        logger.error(f"提供视频文件失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-file/<work_id>')
def check_file_exists(work_id):
    """检查作品文件是否存在"""
    try:
        db = get_download_db()
        work = db.get_work_info(work_id)
        
        if not work:
            return jsonify({'exists': False, 'error': '作品不存在'})
        
        save_path = work.get('save_path', '')
        video_file = os.path.join(save_path, 'video.mp4') if save_path else ''
        
        result = {
            'work_id': work_id,
            'save_path': save_path,
            'video_file': video_file,
            'exists': os.path.exists(video_file) if video_file else False,
            'file_size': os.path.getsize(video_file) if video_file and os.path.exists(video_file) else 0
        }
        
        # 列出目录中的文件（如果目录存在）
        if save_path and os.path.exists(save_path):
            result['files_in_directory'] = os.listdir(save_path)
        else:
            result['files_in_directory'] = []
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件服务"""
    try:
        # Flask会自动解码URL编码的filename，但不会解码 %23 (#)
        # 手动处理 # 符号的编码
        if '%23' in filename:
            filename = filename.replace('%23', '#')
        
        file_path = os.path.join('downloads', filename)
        
        # 添加调试日志
        logger.info(f"请求静态文件: {filename}")
        logger.info(f"文件路径: {file_path}")
        logger.info(f"文件绝对路径: {os.path.abspath(file_path)}")
        logger.info(f"文件是否存在: {os.path.exists(file_path)}")
        
        # 如果文件不存在，尝试列出目录内容以调试
        if not os.path.exists(file_path):
            parent_dir = os.path.dirname(file_path)
            if os.path.exists(parent_dir):
                logger.info(f"父目录存在: {parent_dir}")
                logger.info(f"目录内容: {os.listdir(parent_dir)}")
            else:
                logger.info(f"父目录不存在: {parent_dir}")
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # 根据文件扩展名设置正确的MIME类型
            mimetype = None
            if filename.endswith('.mp4'):
                mimetype = 'video/mp4'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif filename.endswith('.png'):
                mimetype = 'image/png'
            
            # 支持范围请求（对视频很重要）
            return send_file(
                file_path, 
                mimetype=mimetype,
                as_attachment=False,
                conditional=True  # 支持条件请求和范围请求
            )
        else:
            logger.warning(f"文件不存在: {file_path}")
            return jsonify({'error': 'File not found', 'path': filename}), 404
    except Exception as e:
        logger.error(f"提供静态文件失败: {filename}, 错误: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

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
    print(f"当前工作目录: {os.getcwd()}")
    print(f"downloads目录: {os.path.abspath('downloads')}")
    app.run(debug=True, port=8000, host='0.0.0.0')