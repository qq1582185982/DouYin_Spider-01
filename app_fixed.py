# coding=utf-8
import os
import json
import uuid
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
from loguru import logger

# 导入实际的爬虫和认证类
from main import Data_Spider
from builder.auth import DouyinAuth
from utils.database import get_database
from utils.scan_scheduler import get_scanner, start_scanner, stop_scanner
from utils.notification import send_new_videos_notification
from utils.scan_logger import get_scan_logger
from utils.scan_config import get_scan_config, update_scan_config, get_scan_config_manager
import asyncio

app = Flask(__name__)
CORS(app)

# 全局变量
tasks = {}
CONFIG_FILE = 'config.json'
_scan_auth = None
_scan_data_spider = None

# 默认配置
DEFAULT_CONFIG = {
    'cookie': '',
    'save_path': './downloads',
    'proxy': ''
}

def load_config():
    """从配置文件和环境变量加载配置"""
    config = DEFAULT_CONFIG.copy()
    config_loaded = False
    
    # 首先尝试从config.json读取
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                config.update(saved_config)
                logger.info(f"从配置文件加载配置: {CONFIG_FILE}")
                config_loaded = True
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
    
    # 如果配置文件不存在或读取失败，创建默认配置文件
    if not config_loaded:
        logger.info("配置文件不存在或读取失败，创建默认配置文件")
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # 保存默认配置
            save_config(config)
            logger.info(f"已创建默认配置文件: {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
    
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
loop = None  # 事件循环

# 创建异步任务的辅助函数
def run_async(coro):
    """在Flask中运行异步任务"""
    global loop
    if loop is None:
        loop = asyncio.new_event_loop()
        threading.Thread(target=loop.run_forever, daemon=True).start()
    
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)  # 30秒超时

def initialize():
    global data_spider, auth, base_path
    try:
        # 确保下载目录存在
        ensure_download_directories()
        
        # 初始化爬虫
        data_spider = Data_Spider()
        
        # 创建auth对象并设置Cookie
        auth = DouyinAuth()
        cookie = config.get('cookie')
        if cookie:
            auth.perepare_auth(cookie, "", "")
            logger.info("从配置文件加载Cookie到认证模块")
            
            # 设置代理
            if config.get('proxy'):
                auth.proxies = {
                    'http': config.get('proxy'),
                    'https': config.get('proxy')
                }
                logger.info(f"设置代理: {config.get('proxy')}")
        else:
            logger.warning("未找到Cookie配置")
        
        # 设置基础路径
        save_path = config.get('save_path', './downloads')
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

def ensure_download_directories():
    """确保下载目录存在"""
    try:
        # 获取保存路径，如果配置中没有则使用默认路径
        save_path = config.get('save_path', './downloads')
        
        # 规范化路径
        save_path = os.path.normpath(save_path)
        
        # 创建主下载目录
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
            logger.info(f"创建下载目录: {save_path}")
        
        # 创建子目录
        media_dir = os.path.join(save_path, 'media')
        excel_dir = os.path.join(save_path, 'excel')
        
        if not os.path.exists(media_dir):
            os.makedirs(media_dir, exist_ok=True)
            logger.info(f"创建媒体目录: {media_dir}")
        
        if not os.path.exists(excel_dir):
            os.makedirs(excel_dir, exist_ok=True)
            logger.info(f"创建Excel目录: {excel_dir}")
        
        logger.info(f"下载目录检查完成: {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"创建下载目录失败: {e}")
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

@app.route('/api/spider/search-users', methods=['POST'])
def search_users():
    """搜索用户"""
    try:
        data = request.get_json()
        query = data.get('query')
        num = data.get('num', 10)
        
        if not query:
            raise BadRequest('query is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        # 确保auth已初始化
        if not auth:
            raise BadRequest('认证模块未初始化，请重新启动服务')
        
        # 调用API搜索用户
        from dy_apis.douyin_api import DouyinAPI
        user_list = DouyinAPI.search_some_user(auth, query, num)
        
        # 格式化用户信息
        formatted_users = []
        for user in user_list:
            user_info = user.get('user_info', {})
            sec_uid = user_info.get('sec_uid', '')
            user_url = f"https://www.douyin.com/user/{sec_uid}"
            
            # 获取准确的用户信息（包括作品数量）
            try:
                detailed_user_info = DouyinAPI.get_user_info(auth, user_url)
                accurate_aweme_count = detailed_user_info['user'].get('aweme_count', 0)
            except Exception as e:
                logger.warning(f"获取用户 {sec_uid} 详细信息失败: {e}")
                accurate_aweme_count = user_info.get('aweme_count', 0)
            
            formatted_users.append({
                'user_id': user_info.get('uid', ''),
                'sec_uid': sec_uid,
                'nickname': user_info.get('nickname', ''),
                'avatar': user_info.get('avatar_thumb', {}).get('url_list', [''])[0],
                'signature': user_info.get('signature', ''),
                'follower_count': user_info.get('follower_count', 0),
                'total_favorited': user_info.get('total_favorited', 0),
                'aweme_count': accurate_aweme_count,
                'user_url': user_url
            })
        
        return jsonify({'code': 0, 'message': 'success', 'data': formatted_users})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"搜索用户失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/user-videos', methods=['POST'])
def get_user_videos():
    """获取用户的视频列表（不下载）"""
    try:
        data = request.get_json()
        user_url = data.get('user_url')
        
        if not user_url:
            raise BadRequest('user_url is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        # 确保auth已初始化
        if not auth:
            raise BadRequest('认证模块未初始化，请重新启动服务')
        
        # 获取用户信息和作品列表
        from dy_apis.douyin_api import DouyinAPI
        user_info = DouyinAPI.get_user_info(auth, user_url)
        work_list = DouyinAPI.get_user_all_work_info(auth, user_url)
        
        # 格式化作品信息
        formatted_works = []
        for work in work_list:
            formatted_works.append({
                'aweme_id': work.get('aweme_id', ''),
                'desc': work.get('desc', ''),
                'create_time': work.get('create_time', 0),
                'duration': work.get('duration', 0),
                'cover': work.get('video', {}).get('cover', {}).get('url_list', [''])[0] if work.get('video') else '',
                'statistics': {
                    'digg_count': work.get('statistics', {}).get('digg_count', 0),
                    'comment_count': work.get('statistics', {}).get('comment_count', 0),
                    'share_count': work.get('statistics', {}).get('share_count', 0),
                    'play_count': work.get('statistics', {}).get('play_count', 0)
                },
                'aweme_type': work.get('aweme_type', 0)  # 0: video, 68: image
            })
        
        result = {
            'user': {
                'nickname': user_info['user'].get('nickname', ''),
                'avatar': user_info['user'].get('avatar_thumb', {}).get('url_list', [''])[0],
                'signature': user_info['user'].get('signature', ''),
                'follower_count': user_info['user'].get('follower_count', 0),
                'aweme_count': len(work_list)
            },
            'works': formatted_works
        }
        
        return jsonify({'code': 0, 'message': 'success', 'data': result})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"获取用户视频列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/user', methods=['POST'])
def spider_user():
    """爬取用户所有作品"""
    try:
        data = request.get_json()
        user_url = data.get('user_url')
        save_choice = data.get('save_choice', 'all')
        force_download = data.get('force_download', False)
        selected_videos = data.get('selected_videos', [])  # 新增：选中的视频ID列表
        
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
                
                # 确保下载目录存在
                save_path = ensure_download_directories()
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
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
                            force_download=force_download,
                            selected_videos=selected_videos
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
    """爬取单个作品（支持下载）"""
    try:
        data = request.get_json()
        work_url = data.get('work_url')
        download = data.get('download', False)  # 是否下载
        
        if not work_url:
            raise BadRequest('work_url is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        # 确保下载目录存在
        save_path = ensure_download_directories()
        spider_base_path = {
            'media': os.path.join(save_path, 'media'),
            'excel': os.path.join(save_path, 'excel')
        }
        
        # 调用爬虫
        if data_spider and auth:
            try:
                if download:
                    # 下载视频
                    download_stats = data_spider.spider_some_work(
                        auth, 
                        [work_url], 
                        spider_base_path, 
                        'media',  # 只下载媒体文件
                        excel_name='',
                        force_download=data.get('force_download', False),
                        use_database=True
                    )
                    
                    # 获取作品信息
                    proxies = None
                    if config.get('proxy'):
                        proxies = {
                            'http': config.get('proxy'),
                            'https': config.get('proxy')
                        }
                    work_info = data_spider.spider_work(auth, work_url, proxies)
                    work_info['download_stats'] = download_stats
                    
                    return jsonify({'code': 0, 'message': 'success', 'data': work_info})
                else:
                    # 只获取信息
                    proxies = None
                    if config.get('proxy'):
                        proxies = {
                            'http': config.get('proxy'),
                            'https': config.get('proxy')
                        }
                    work_info = data_spider.spider_work(auth, work_url, proxies)
                    return jsonify({'code': 0, 'message': 'success', 'data': work_info})
            except Exception as spider_error:
                logger.error(f"爬虫执行失败: {spider_error}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                raise
        else:
            return jsonify({'code': 500, 'message': '爬虫未初始化'}), 500
            
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"处理作品请求失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/spider/batch-works', methods=['POST'])
def spider_batch_works():
    """批量下载视频链接"""
    try:
        data = request.get_json()
        work_urls = data.get('work_urls', [])
        
        if not work_urls:
            raise BadRequest('work_urls is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        # 创建任务
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'batch-works',
            'status': 'pending',
            'urls': work_urls,
            'progress': 0,
            'total': len(work_urls),
            'results': [],
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        # 在后台线程中执行下载
        def run_batch_download():
            try:
                task['status'] = 'running'
                task['updated_at'] = int(time.time())
                
                # 确保下载目录存在
                save_path = ensure_download_directories()
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
                results = []
                
                for idx, url in enumerate(work_urls):
                    try:
                        # 下载单个视频
                        download_stats = data_spider.spider_some_work(
                            auth, 
                            [url], 
                            spider_base_path, 
                            'media',
                            excel_name='',
                            force_download=data.get('force_download', False),
                            use_database=True
                        )
                        
                        # 获取作品信息
                        work_info = data_spider.spider_work(auth, url)
                        work_info['download_stats'] = download_stats
                        
                        results.append({
                            'url': url,
                            'status': 'success',
                            'info': work_info
                        })
                        
                    except Exception as e:
                        logger.error(f"下载视频失败 {url}: {e}")
                        results.append({
                            'url': url,
                            'status': 'failed',
                            'error': str(e)
                        })
                    
                    # 更新进度
                    task['progress'] = idx + 1
                    task['results'] = results
                    task['updated_at'] = int(time.time())
                
                task['status'] = 'completed'
                logger.info(f"批量下载完成: {len(results)} 个视频")
                
            except Exception as e:
                logger.error(f"批量下载任务失败: {e}")
                task['status'] = 'failed'
                task['error'] = str(e)
            finally:
                task['updated_at'] = int(time.time())
        
        threading.Thread(target=run_batch_download).start()
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
        
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
                
                # 确保下载目录存在
                save_path = ensure_download_directories()
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
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
        db = get_database()
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
    search = request.args.get('search', '')
    
    try:
        # 从数据库读取基本数据
        db = get_database()
        offset = (page - 1) * limit
        recent_works = db.get_recent_downloads(limit, offset, search)
        
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
        total_count = db.get_total_works_count(search)
        
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
        db = get_database()
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
        db = get_database()
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
        
        db = get_database()
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
        db = get_database()
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
        db = get_database()
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

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """获取订阅列表"""
    try:
        db = get_database()
        subscriptions = db.get_all_subscriptions()
        stats = db.get_subscription_stats()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'subscriptions': subscriptions,
                'stats': stats
            }
        })
    except Exception as e:
        logger.error(f"获取订阅列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions', methods=['POST'])
def add_subscription():
    """添加订阅"""
    try:
        data = request.get_json()
        user_info = data.get('user_info')
        
        if not user_info or not user_info.get('user_id'):
            raise BadRequest('用户信息不完整')
        
        db = get_database()
        subscription_id = db.add_subscription(user_info)
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'subscription_id': subscription_id
            }
        })
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"添加订阅失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions/<user_id>', methods=['DELETE'])
def remove_subscription(user_id):
    """移除订阅"""
    try:
        db = get_database()
        success = db.remove_subscription(user_id)
        
        if success:
            return jsonify({'code': 0, 'message': 'success'})
        else:
            return jsonify({'code': 404, 'message': '订阅不存在'}), 404
    except Exception as e:
        logger.error(f"移除订阅失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions/<user_id>', methods=['PUT'])
def update_subscription(user_id):
    """更新订阅设置"""
    try:
        data = request.get_json()
        db = get_database()
        success = db.update_subscription(user_id, **data)
        
        if success:
            return jsonify({'code': 0, 'message': 'success'})
        else:
            return jsonify({'code': 404, 'message': '订阅不存在'}), 404
    except Exception as e:
        logger.error(f"更新订阅失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions/check-updates', methods=['POST'])
def check_subscription_updates():
    """检查订阅更新"""
    try:
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        db = get_database()
        subscriptions = db.get_all_subscriptions(enabled_only=True)
        
        # 创建检查任务
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'subscription_check',
            'status': 'pending',
            'progress': 0,
            'total': len(subscriptions),
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        # 在后台线程中执行检查
        def run_check():
            try:
                task['status'] = 'running'
                task['updated_at'] = int(time.time())
                
                from dy_apis.douyin_api import DouyinAPI
                new_videos_count = 0
                
                for idx, sub in enumerate(subscriptions):
                    try:
                        # 获取用户最新视频
                        work_list = DouyinAPI.get_user_all_work_info(auth, sub['user_url'])
                        logger.info(f"获取到 {sub['nickname']} 的 {len(work_list)} 个作品")
                        
                        # 更新用户信息
                        user_info = DouyinAPI.get_user_info(auth, sub['user_url'])
                        db.update_subscription(
                            sub['user_id'],
                            follower_count=user_info['user'].get('follower_count', 0),
                            aweme_count=len(work_list),
                            last_check_time=datetime.now().isoformat()
                        )
                        
                        # 记录新视频
                        for work in work_list:  # 检查所有视频
                            if db.add_subscription_video(sub['id'], work):
                                new_videos_count += 1
                        
                        task['progress'] = idx + 1
                        task['updated_at'] = int(time.time())
                        
                        # 避免请求过快
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"检查订阅 {sub['nickname']} 失败: {e}")
                
                task['status'] = 'completed'
                task['result'] = {
                    'checked_count': len(subscriptions),
                    'new_videos_count': new_videos_count
                }
                logger.info(f"订阅检查完成，发现 {new_videos_count} 个新视频")
                
            except Exception as e:
                logger.error(f"订阅检查任务失败: {e}")
                task['status'] = 'failed'
                task['error'] = str(e)
            finally:
                task['updated_at'] = int(time.time())
        
        threading.Thread(target=run_check).start()
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"启动订阅检查失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions/<user_id>/videos', methods=['GET'])
def get_subscription_videos(user_id):
    """获取订阅的视频列表"""
    try:
        only_new = request.args.get('only_new', 'false').lower() == 'true'
        
        db = get_database()
        subscription = db.get_subscription(user_id)
        
        if not subscription:
            return jsonify({'code': 404, 'message': '订阅不存在'}), 404
        
        videos = db.get_subscription_videos(subscription['id'], only_new=only_new)
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'subscription': subscription,
                'videos': videos
            }
        })
    except Exception as e:
        logger.error(f"获取订阅视频列表失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/subscriptions/download-new', methods=['POST'])
def download_subscription_new_videos():
    """下载订阅的新视频"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        max_count = data.get('max_count', None)  # 最大下载数量
        
        if not user_id:
            raise BadRequest('user_id is required')
        
        if not config.get('cookie'):
            raise BadRequest('请先配置Cookie')
        
        db = get_database()
        subscription = db.get_subscription(user_id)
        
        if not subscription:
            return jsonify({'code': 404, 'message': '订阅不存在'}), 404
        
        # 获取新视频
        new_videos = db.get_subscription_videos(subscription['id'], only_new=True)
        
        if not new_videos:
            return jsonify({'code': 0, 'message': '没有新视频需要下载'})
        
        logger.info(f"订阅 {subscription['nickname']} 有 {len(new_videos)} 个新视频待下载")
        
        # 如果设置了选择视频，过滤视频列表
        selected_videos = subscription.get('selected_videos', [])
        if selected_videos:
            aweme_ids = [v['aweme_id'] for v in new_videos if v['aweme_id'] in selected_videos]
        else:
            aweme_ids = [v['aweme_id'] for v in new_videos]
        
        # 如果设置了最大下载数量，限制下载数量
        if max_count and max_count > 0:
            aweme_ids = aweme_ids[:max_count]
            logger.info(f"限制下载数量为 {max_count} 个")
        
        logger.info(f"准备下载 {len(aweme_ids)} 个视频")
        
        # 创建下载任务
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'subscription_download',
            'status': 'pending',
            'url': subscription['user_url'],
            'progress': 0,
            'total': len(aweme_ids),
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        # 在后台线程中执行下载
        def run_download():
            try:
                task['status'] = 'running'
                task['updated_at'] = int(time.time())
                
                # 确保下载目录存在
                save_path = ensure_download_directories()
                spider_base_path = {
                    'media': os.path.join(save_path, 'media'),
                    'excel': os.path.join(save_path, 'excel')
                }
                
                # 调用爬虫下载指定视频
                if data_spider and auth:
                    download_stats = data_spider.spider_user_all_work(
                        auth,
                        subscription['user_url'],
                        spider_base_path,
                        'media',  # 只下载媒体文件
                        f"{subscription['nickname']}_{subscription['user_id']}",
                        proxies=None,
                        force_download=False,
                        selected_videos=aweme_ids
                    )
                    
                    # 标记视频为已下载
                    for aweme_id in aweme_ids:
                        db.mark_video_downloaded(aweme_id)
                    
                    task['status'] = 'completed'
                    task['progress'] = len(aweme_ids)
                    task['download_stats'] = download_stats
                    logger.info(f"订阅下载完成: {subscription['nickname']}")
                else:
                    task['status'] = 'failed'
                    task['error'] = '爬虫未初始化'
                    
            except Exception as e:
                logger.error(f"订阅下载任务失败: {e}")
                task['status'] = 'failed'
                task['error'] = str(e)
            finally:
                task['updated_at'] = int(time.time())
        
        threading.Thread(target=run_download).start()
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
    except BadRequest as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"启动订阅下载失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/status', methods=['GET'])
def get_scan_status():
    """获取扫描器状态"""
    try:
        scanner = get_scanner()
        status = scanner.get_status()
        
        # 获取扫描统计信息
        tracker_stats = scanner.tracker.get_statistics()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'status': status,
                'statistics': tracker_stats
            }
        })
    except Exception as e:
        logger.error(f"获取扫描状态失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """启动扫描任务"""
    try:
        global _scan_auth, _scan_data_spider
        
        data = request.get_json() or {}
        scan_interval = data.get('scan_interval', 3600)  # 默认1小时
        auto_download = data.get('auto_download', True)
        
        # 设置新视频回调
        scanner = get_scanner()
        
        # 设置认证信息
        if auth:
            scanner.set_auth(auth)
            # 保存到全局变量供回调使用
            _scan_auth = auth
            _scan_data_spider = data_spider
        else:
            return jsonify({'code': 400, 'message': '请先配置Cookie'}), 400
        
        async def new_videos_callback(user_id, videos):
            """处理新发现的视频"""
            global _scan_auth, _scan_data_spider
            
            try:
                # 获取用户信息
                db = get_database()
                user_info = db.get_subscription(user_id)
                
                # 发送通知
                await send_new_videos_notification(user_info, videos)
                
                # 如果启用了自动下载
                if auto_download and user_info.get('auto_download', True):
                    logger.info(f"开始自动下载 {user_info['nickname']} 的 {len(videos)} 个新视频")
                    
                    # 准备下载参数
                    work_urls = [f"https://www.douyin.com/video/{video['aweme_id']}" for video in videos]
                    
                    # 在后台线程中执行下载
                    def download_new_videos():
                        try:
                            save_path = ensure_download_directories()
                            spider_base_path = {
                                'media': os.path.join(save_path, 'media'),
                                'excel': os.path.join(save_path, 'excel')
                            }
                            
                            # 生成Excel文件名（使用用户昵称和时间戳）
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            excel_name = f"{user_info['nickname']}_自动下载_{timestamp}"
                            
                            # 调用爬虫下载全部内容
                            if _scan_data_spider and _scan_auth:
                                download_stats = _scan_data_spider.spider_some_work(
                                    _scan_auth,
                                    work_urls,
                                    spider_base_path,
                                    'all',  # 下载全部内容（媒体文件 + Excel）
                                    excel_name,  # Excel文件名
                                    proxies=None,
                                    use_database=True
                                )
                                
                                logger.info(f"自动下载完成 - {user_info['nickname']}: {download_stats}")
                                
                                # 标记视频为已下载
                                db = get_database()
                                for video in videos:
                                    aweme_id = video.get('aweme_id')
                                    if aweme_id:
                                        db.mark_video_downloaded(aweme_id)
                                        logger.info(f"标记视频 {aweme_id} 为已下载")
                            else:
                                logger.error("爬虫或认证信息未初始化")
                            
                        except Exception as e:
                            logger.error(f"自动下载失败 - {user_info['nickname']}: {e}")
                    
                    # 在新线程中执行下载
                    download_thread = threading.Thread(target=download_new_videos)
                    download_thread.daemon = True  # 设置为守护线程
                    download_thread.start()
                    
            except Exception as e:
                logger.error(f"处理新视频失败: {e}")
        
        scanner.set_on_new_videos_callback(new_videos_callback)
        
        # 启动扫描器
        run_async(start_scanner(scan_interval, auto_download))
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'scan_interval': scan_interval,
                'auto_download': auto_download
            }
        })
    except Exception as e:
        logger.error(f"启动扫描失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/stop', methods=['POST'])
def stop_scan():
    """停止扫描任务"""
    try:
        run_async(stop_scanner())
        
        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        logger.error(f"停止扫描失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/pause', methods=['POST'])
def pause_scan():
    """暂停扫描"""
    try:
        scanner = get_scanner()
        scanner.pause()
        
        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        logger.error(f"暂停扫描失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/resume', methods=['POST'])
def resume_scan():
    """恢复扫描"""
    try:
        scanner = get_scanner()
        scanner.resume()
        
        return jsonify({
            'code': 0,
            'message': 'success'
        })
    except Exception as e:
        logger.error(f"恢复扫描失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/once', methods=['POST'])
def scan_once():
    """执行一次扫描（手动触发）"""
    try:
        scanner = get_scanner()
        
        # 创建任务记录
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'type': 'manual_scan',
            'status': 'pending',
            'progress': 0,
            'total': 0,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
        tasks[task_id] = task
        
        # 在后台执行扫描
        def run_scan():
            try:
                task['status'] = 'running'
                task['updated_at'] = int(time.time())
                
                # 执行扫描
                summary = run_async(scanner.scan_once())
                
                task['status'] = 'completed'
                task['summary'] = summary
                logger.info("手动扫描完成")
                
            except Exception as e:
                logger.error(f"手动扫描失败: {e}")
                task['status'] = 'failed'
                task['error'] = str(e)
            finally:
                task['updated_at'] = int(time.time())
        
        threading.Thread(target=run_scan).start()
        
        return jsonify({'code': 0, 'message': 'success', 'data': task})
        
    except Exception as e:
        logger.error(f"触发手动扫描失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/progress', methods=['GET'])
def get_scan_progress():
    """获取当前扫描进度"""
    try:
        scanner = get_scanner()
        
        if not scanner.is_scanning():
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': {
                    'scanning': False,
                    'progress': None
                }
            })
        
        # 获取进度信息
        # 这里需要从scanner获取当前的collector
        # 暂时返回基本信息
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'scanning': True,
                'progress': {
                    'message': '扫描进行中...'
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取扫描进度失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/logs', methods=['GET'])
def get_scan_logs():
    """获取扫描日志"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        scan_logger = get_scan_logger()
        logs = scan_logger.get_history(limit)
        stats = scan_logger.get_statistics()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'logs': logs,
                'statistics': stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取扫描日志失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/logs/<scan_id>', methods=['GET'])
def get_scan_log_detail(scan_id):
    """获取扫描日志详情"""
    try:
        scan_logger = get_scan_logger()
        detail = scan_logger.get_scan_detail(scan_id)
        
        if not detail:
            return jsonify({'code': 404, 'message': '日志不存在'}), 404
            
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': detail
        })
        
    except Exception as e:
        logger.error(f"获取扫描日志详情失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/config', methods=['GET'])
def get_scan_configuration():
    """获取扫描配置"""
    try:
        config = get_scan_config()
        config_manager = get_scan_config_manager()
        
        # 验证配置
        validation = config_manager.validate_config()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'config': config_manager.export_config(),
                'validation': validation
            }
        })
        
    except Exception as e:
        logger.error(f"获取扫描配置失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/config', methods=['POST'])
def update_scan_configuration():
    """更新扫描配置"""
    try:
        data = request.get_json() or {}
        
        # 更新配置
        success = update_scan_config(data)
        
        if not success:
            return jsonify({'code': 400, 'message': '配置更新失败'}), 400
            
        # 如果扫描器正在运行，应用新配置
        scanner = get_scanner()
        if data.get('scan_interval'):
            scanner.scan_interval = data['scan_interval']
        if 'auto_download' in data:
            scanner.auto_download = data['auto_download']
            
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': get_scan_config_manager().export_config()
        })
        
    except Exception as e:
        logger.error(f"更新扫描配置失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/scan/config/reset', methods=['POST'])
def reset_scan_configuration():
    """重置扫描配置为默认值"""
    try:
        config_manager = get_scan_config_manager()
        config_manager.reset_to_defaults()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': config_manager.export_config()
        })
        
    except Exception as e:
        logger.error(f"重置扫描配置失败: {e}")
        return jsonify({'code': 500, 'message': str(e)}), 500

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