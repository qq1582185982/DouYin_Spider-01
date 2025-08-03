import json
import os
import re
import time
import openpyxl
import requests
from loguru import logger
from retry import retry
from .database import get_database


def norm_str(str):
    new_str = re.sub(r"|[\\/:*?\"<>| ]+", "", str).replace('\n', '').replace('\r', '')
    return new_str

def norm_text(text):
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    text = ILLEGAL_CHARACTERS_RE.sub(r'', text)
    return text


def timestamp_to_str(timestamp):
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt



def handle_work_info(data):
    sec_uid = data['author']['sec_uid']
    user_url = f'https://www.douyin.com/user/{sec_uid}'
    user_desc = data['author']['signature'] if 'signature' in data['author'] else '未知'
    following_count = data['author']['following_count'] if 'following_count' in data['author'] else '未知'
    follower_count = data['author']['follower_count'] if 'follower_count' in data['author'] else '未知'
    total_favorited = data['author']['total_favorited'] if 'total_favorited' in data['author'] else '未知'
    aweme_count = data['author']['aweme_count'] if 'aweme_count' in data['author'] else '未知'
    user_id = data['author']['unique_id'] if 'unique_id' in data['author'] else '未知'
    user_age = data['author']['user_age'] if 'user_age' in data['author'] else '未知'
    gender = data['author']['gender'] if 'gender' in data['author'] else '未知'
    if gender == 1:
        gender = '男'
    elif gender == 0:
        gender = '女'
    else:
        gender = '未知'
    try:
        ip_location = data['user']['ip_location']
    except:
        ip_location = '未知'
    aweme_id = data['aweme_id']
    nickname = data['author']['nickname']
    author_avatar = data['author']['avatar_thumb']['url_list'][0]
    video_cover = data['video']['cover']['url_list'][0]
    title = data['desc']
    desc = data['desc']
    admire_count = data['statistics']['admire_count'] if 'admire_count' in data['statistics'] else 0
    digg_count = data['statistics']['digg_count']
    commnet_count = data['statistics']['comment_count']
    collect_count = data['statistics']['collect_count']
    share_count = data['statistics']['share_count']
    play_count = data['statistics']['play_count'] if 'play_count' in data['statistics'] else 0
    video_addr = data['video']['play_addr']['url_list'][0]
    images = data['images']
    if not isinstance(images, list):
        images = []
    create_time = data['create_time']

    text_extra = data['text_extra'] if 'text_extra' in data else []
    text_extra = text_extra if text_extra else []
    topics = []
    for item in text_extra:
        hashtag_name = item['hashtag_name'] if 'hashtag_name' in item else ''
        if hashtag_name:
            topics.append(hashtag_name)

    work_type = '未知'
    if 'aweme_type' in data:
        if data['aweme_type'] == 68:
            work_type = '图集'
        elif data['aweme_type'] == 0:
            work_type = '视频'

    return {
        'work_id': aweme_id,
        'work_url': f'https://www.douyin.com/video/{aweme_id}',
        'work_type': work_type,
        'title': title,
        'desc': desc,
        'admire_count': admire_count,
        'digg_count': digg_count,
        'comment_count': commnet_count,
        'collect_count': collect_count,
        'share_count': share_count,
        'play_count': play_count,
        'video_addr': video_addr,
        'images': images,
        'topics': topics,
        'create_time': create_time,
        'video_cover': video_cover,
        'user_url': user_url,
        'user_id': user_id,
        'nickname': nickname,
        'author_avatar': author_avatar,
        'user_desc': user_desc,
        'following_count': following_count,
        'follower_count': follower_count,
        'total_favorited': total_favorited,
        'aweme_count': aweme_count,
        'user_age': user_age,
        'gender': gender,
        'ip_location': ip_location
    }


def save_to_xlsx(datas, file_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ['作品id', '作品url', '作品类型', '作品标题', '描述', 'admire数量', '点赞数量', '评论数量', '收藏数量', '分享数量', '播放数量', '视频地址url', '图片地址url列表', '标签', '上传时间', '视频封面url', '用户主页url', '用户id', '昵称', '头像url', '用户描述', '关注数量', '粉丝数量', '作品被赞和收藏数量', '作品数量', '用户年龄', '性别', 'ip归属地']
    ws.append(headers)
    for data in datas:
        # 确保所有值都转换为字符串，特别处理列表和字典类型
        processed_data = {}
        for k, v in data.items():
            if isinstance(v, list):
                processed_data[k] = ', '.join(str(item) for item in v)
            elif isinstance(v, dict):
                processed_data[k] = str(v)
            else:
                processed_data[k] = norm_text(str(v))
        ws.append(list(processed_data.values()))
    wb.save(file_path)
    logger.info(f'数据保存至 {file_path}')

def check_file_exists_and_valid(file_path, min_size=1024):
    """检查文件是否存在且有效"""
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        # 文件大小大于最小值认为有效
        return file_size >= min_size
    return False

def download_media(path, name, url, type, force_download=False):
    """
    下载媒体文件，支持增量下载
    :param path: 保存路径
    :param name: 文件名（不含扩展名）
    :param url: 下载URL
    :param type: 文件类型 ('image' 或 'video')
    :param force_download: 是否强制下载，忽略已存在的文件
    :return: 下载状态 ('downloaded', 'skipped', 'failed')
    """
    # 添加必要的请求头以绕过403错误
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    
    if type == 'image':
        file_path = f'{path}/{name}.jpg'
        # 检查文件是否已存在且有效
        if not force_download and check_file_exists_and_valid(file_path, min_size=500):
            logger.info(f'图片已存在，跳过下载: {file_path}')
            return 'skipped'
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(file_path, mode="wb") as f:
                    f.write(response.content)
                logger.info(f'图片下载完成: {file_path} ({len(response.content)} bytes)')
                return 'downloaded'
            else:
                logger.error(f'图片下载失败，状态码: {response.status_code}')
                return 'failed'
        except Exception as e:
            logger.error(f'图片下载异常: {e}')
            return 'failed'
            
    elif type == 'video':
        file_path = f'{path}/{name}.mp4'
        # 检查文件是否已存在且有效（视频文件最小100KB）
        if not force_download and check_file_exists_and_valid(file_path, min_size=100*1024):
            existing_size = os.path.getsize(file_path)
            logger.info(f'视频已存在，跳过下载: {file_path} ({existing_size} bytes)')
            return 'skipped'
        
        try:
            res = requests.get(url, stream=True, headers=headers, timeout=60)
            if res.status_code == 200:
                size = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                with open(file_path, mode="wb") as f:
                    for data in res.iter_content(chunk_size=chunk_size):
                        f.write(data)
                        size += len(data)
                logger.info(f'视频下载完成: {file_path} ({size} bytes)')
                return 'downloaded'
            else:
                logger.error(f'视频下载失败，状态码: {res.status_code}, URL: {url}')
                # 保存错误信息到文件以便调试
                with open(f'{path}/{name}_error.txt', mode="w", encoding="utf-8") as f:
                    f.write(f"Status Code: {res.status_code}\n")
                    f.write(f"URL: {url}\n")
                    f.write(f"Response: {res.text[:1000]}\n")
                return 'failed'
        except Exception as e:
            logger.error(f'视频下载异常: {e}')
            return 'failed'
    
    return 'failed'


def save_wrok_detail(work, path):
    with open(f'{path}/detail.txt', mode="w", encoding="utf-8") as f:
        # 逐行输出到txt里
        f.write(f"作品id: {work['work_id']}\n")
        f.write(f"作品url: {work['work_url']}\n")
        f.write(f"作品类型: {work['work_type']}\n")
        f.write(f"作品标题: {work['title']}\n")
        f.write(f"描述: {work['desc']}\n")
        f.write(f"admire数量: {work['admire_count']}\n")
        f.write(f"点赞数量: {work['digg_count']}\n")
        f.write(f"评论数量: {work['comment_count']}\n")
        f.write(f"收藏数量: {work['collect_count']}\n")
        f.write(f"分享数量: {work['share_count']}\n")
        f.write(f"播放数量: {work.get('play_count', 0)}\n")
        f.write(f"视频地址url: {work['video_addr']}\n")
        images = work['images'] if isinstance(work['images'], list) else []
        topics = work['topics'] if isinstance(work['topics'], list) else []
        # 确保images列表中的所有项都是字符串
        image_urls = []
        for img in images:
            if isinstance(img, dict):
                # 如果是字典，尝试获取URL
                if 'url_list' in img and img['url_list']:
                    image_urls.append(str(img['url_list'][0]))
                elif 'url' in img:
                    image_urls.append(str(img['url']))
                else:
                    image_urls.append(str(img))
            else:
                image_urls.append(str(img))
        # 确保topics列表中的所有项都是字符串
        topic_names = [str(topic) for topic in topics]
        f.write(f"图片地址url列表: {', '.join(image_urls)}\n")
        f.write(f"标签: {', '.join(topic_names)}\n")
        f.write(f"上传时间: {timestamp_to_str(work['create_time'])}\n")
        f.write(f"视频封面url: {work['video_cover']}\n")
        f.write(f"用户主页url: {work['user_url']}\n")
        f.write(f"用户id: {work['user_id']}\n")
        f.write(f"昵称: {work['nickname']}\n")
        f.write(f"头像url: {work['author_avatar']}\n")
        f.write(f"用户描述: {work['user_desc']}\n")
        f.write(f"关注数量: {work['following_count']}\n")
        f.write(f"粉丝数量: {work['follower_count']}\n")
        f.write(f"作品被赞和收藏数量: {work['total_favorited']}\n")
        f.write(f"作品数量: {work['aweme_count']}\n")
        f.write(f"用户年龄: {work['user_age']}\n")
        f.write(f"用户性别: {work['gender']}\n")
        f.write(f"ip归属地: {work['ip_location']}\n")


def check_work_complete(save_path, work_type, images_count=0):
    """检查作品是否已完整下载"""
    if not os.path.exists(save_path):
        return False
    
    # 检查基本文件
    required_files = ['info.json', 'detail.txt']
    for file in required_files:
        if not os.path.exists(os.path.join(save_path, file)):
            return False
    
    if work_type == '图集':
        # 检查图片文件
        for i in range(images_count):
            img_file = os.path.join(save_path, f'image_{i}.jpg')
            if not check_file_exists_and_valid(img_file, min_size=500):
                return False
    elif work_type == '视频' or work_type == '未知':
        # 检查视频和封面
        video_file = os.path.join(save_path, 'video.mp4')
        cover_file = os.path.join(save_path, 'cover.jpg')
        # 添加日志以调试
        video_exists = check_file_exists_and_valid(video_file, min_size=100*1024)
        cover_exists = check_file_exists_and_valid(cover_file, min_size=500)
        if not video_exists:
            logger.debug(f'视频文件不存在或无效: {video_file}')
        if not cover_exists:
            logger.debug(f'封面文件不存在或无效: {cover_file}')
        if not (video_exists and cover_exists):
            return False
    
    return True

@retry(tries=3, delay=1)
def download_work(work_info, path, save_choice, force_download=False, use_database=True):
    """
    下载作品，支持增量下载和数据库记录
    :param work_info: 作品信息
    :param path: 保存基础路径
    :param save_choice: 保存选择
    :param force_download: 是否强制下载
    :param use_database: 是否使用数据库记录
    :return: 包含下载统计的结果
    """
    work_id = work_info['work_id']
    user_id = work_info['user_id']
    title = work_info['title']
    title = norm_str(title)[:40]
    nickname = work_info['nickname']
    nickname = norm_str(nickname)[:20]
    if title.strip() == '':
        title = f'无标题'
    save_path = f'{path}/{nickname}_{user_id}/{title}_{work_id}'
    work_type = work_info['work_type']
    
    # 下载统计
    stats = {
        'work_id': work_id,
        'work_type': work_type,
        'save_path': save_path,
        'files_downloaded': 0,
        'files_skipped': 0,
        'files_failed': 0,
        'total_files': 0,
        'is_complete': False
    }
    
    # 计算总文件数
    if work_type == '图集':
        images_count = len(work_info.get('images', []))
        stats['total_files'] = images_count + 2  # 图片 + info.json + detail.txt
    elif work_type == '视频' or (work_type == '未知' and work_info.get('video_addr')):
        stats['total_files'] = 4  # 视频 + 封面 + info.json + detail.txt
    else:
        stats['total_files'] = 2  # 只有 info.json + detail.txt
    
    # 数据库检查（如果启用）
    db = get_database() if use_database else None
    if db and not force_download:
        if db.is_work_complete(work_id):
            logger.info(f'数据库显示作品已完整下载，跳过: {work_id} - {title}')
            stats['files_skipped'] = stats['total_files']
            stats['is_complete'] = True
            return stats
    
    # 文件系统检查（备用方案）
    if not force_download and check_work_complete(save_path, work_type, len(work_info.get('images', []))):
        logger.info(f'作品已完整下载，跳过: {work_id} - {title}')
        stats['files_skipped'] = stats['total_files']
        stats['is_complete'] = True
        
        # 如果数据库启用但没有记录，补充记录
        if db and not db.is_work_complete(work_id):
            _record_existing_work_to_db(db, work_info, save_path)
        
        return stats
    
    # 创建目录并保存基本信息
    check_and_create_path(save_path)
    
    # 保存作品信息（总是更新）
    with open(f'{save_path}/info.json', mode='w', encoding='utf-8') as f:
        f.write(json.dumps(work_info, ensure_ascii=False, indent=2) + '\n')
    
    # 保存详细信息（总是更新）
    save_wrok_detail(work_info, save_path)
    
    # 用于数据库记录的文件信息
    files_info = []
    
    # 记录基本文件
    for file_name in ['info.json', 'detail.txt']:
        file_path = os.path.join(save_path, file_name)
        if os.path.exists(file_path):
            files_info.append({
                'file_name': file_name,
                'file_type': 'info' if file_name.endswith('.json') else 'detail',
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'is_valid': True
            })
    
    # 下载媒体文件
    if work_type == '图集' and save_choice in ['media', 'media-image', 'all']:
        for img_index, img_data in enumerate(work_info['images']):
            # 从复杂的图片数据结构中提取URL
            img_url = None
            if isinstance(img_data, dict):
                # 尝试多种可能的URL字段
                if 'url_list' in img_data and img_data['url_list']:
                    img_url = img_data['url_list'][0]
                elif 'download_url_list' in img_data and img_data['download_url_list']:
                    img_url = img_data['download_url_list'][0]
                elif 'url' in img_data:
                    img_url = img_data['url']
            elif isinstance(img_data, str):
                img_url = img_data
            
            if img_url:
                result = download_media(save_path, f'image_{img_index}', img_url, 'image', force_download)
                file_path = os.path.join(save_path, f'image_{img_index}.jpg')
                
                if result == 'downloaded':
                    stats['files_downloaded'] += 1
                elif result == 'skipped':
                    stats['files_skipped'] += 1
                else:
                    stats['files_failed'] += 1
                
                # 记录文件信息（如果文件存在）
                if os.path.exists(file_path):
                    files_info.append({
                        'file_name': f'image_{img_index}.jpg',
                        'file_type': 'image',
                        'file_path': file_path,
                        'file_size': os.path.getsize(file_path),
                        'is_valid': True
                    })
            else:
                logger.warning(f'无法提取图片{img_index}的URL，数据: {img_data}')
                stats['files_failed'] += 1
                
    elif (work_type == '视频' or (work_type == '未知' and work_info.get('video_addr'))) and save_choice in ['media', 'media-video', 'all']:
        # 下载封面
        cover_result = download_media(save_path, 'cover', work_info['video_cover'], 'image', force_download)
        cover_path = os.path.join(save_path, 'cover.jpg')
        
        if cover_result == 'downloaded':
            stats['files_downloaded'] += 1
        elif cover_result == 'skipped':
            stats['files_skipped'] += 1
        else:
            stats['files_failed'] += 1
        
        if os.path.exists(cover_path):
            files_info.append({
                'file_name': 'cover.jpg',
                'file_type': 'cover',
                'file_path': cover_path,
                'file_size': os.path.getsize(cover_path),
                'is_valid': True
            })
        
        # 下载视频
        video_result = download_media(save_path, 'video', work_info['video_addr'], 'video', force_download)
        video_path = os.path.join(save_path, 'video.mp4')
        
        if video_result == 'downloaded':
            stats['files_downloaded'] += 1
        elif video_result == 'skipped':
            stats['files_skipped'] += 1
        else:
            stats['files_failed'] += 1
        
        if os.path.exists(video_path):
            files_info.append({
                'file_name': 'video.mp4',
                'file_type': 'video',
                'file_path': video_path,
                'file_size': os.path.getsize(video_path),
                'is_valid': True
            })
    
    # 检查是否完整下载
    stats['is_complete'] = check_work_complete(save_path, work_type, len(work_info.get('images', [])))
    
    # 记录到数据库
    if db and files_info:
        work_record = work_info.copy()
        work_record['save_path'] = save_path
        work_record['is_complete'] = stats['is_complete']
        db.record_work_download(work_record, files_info)
    
    # 日志统计
    if stats['files_downloaded'] > 0:
        logger.info(f'作品下载完成: {work_id} - 新下载: {stats["files_downloaded"]}, 跳过: {stats["files_skipped"]}, 失败: {stats["files_failed"]}')
    else:
        logger.info(f'作品处理完成: {work_id} - 跳过: {stats["files_skipped"]}, 失败: {stats["files_failed"]}')
    
    return stats


def _record_existing_work_to_db(db, work_info, save_path):
    """将已存在的作品记录到数据库"""
    try:
        files_info = []
        
        # 扫描目录中的文件
        if os.path.exists(save_path):
            for file_name in os.listdir(save_path):
                file_path = os.path.join(save_path, file_name)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    # 判断文件类型
                    if file_name.endswith('.mp4'):
                        file_type = 'video'
                    elif file_name.endswith('.jpg') and 'cover' in file_name:
                        file_type = 'cover'
                    elif file_name.endswith('.jpg'):
                        file_type = 'image'
                    elif file_name == 'info.json':
                        file_type = 'info'
                    elif file_name == 'detail.txt':
                        file_type = 'detail'
                    else:
                        continue
                    
                    files_info.append({
                        'file_name': file_name,
                        'file_type': file_type,
                        'file_path': file_path,
                        'file_size': file_size,
                        'is_valid': True
                    })
        
        if files_info:
            work_record = work_info.copy()
            work_record['save_path'] = save_path
            work_record['is_complete'] = True
            db.record_work_download(work_record, files_info)
            logger.info(f'已将现有作品记录到数据库: {work_info["work_id"]}')
            
    except Exception as e:
        logger.error(f'记录现有作品到数据库失败: {e}')



def check_and_create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
