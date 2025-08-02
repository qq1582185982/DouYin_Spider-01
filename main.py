# coding=utf-8
import json
import os
from loguru import logger

from dy_apis.douyin_api import DouyinAPI
from utils.common_util import init
from utils.data_util import handle_work_info, download_work, save_to_xlsx
from utils.download_db import get_download_db


class Data_Spider():
    def __init__(self):
        self.douyin_apis = DouyinAPI()

    def spider_work(self, auth, work_url: str, proxies=None):
        """
        爬取一个作品的信息
        :param auth : 用户认证信息
        :param work_url: 作品链接
        :return:
        """
        res_json = self.douyin_apis.get_work_info(auth, work_url)
        data = res_json['aweme_detail']

        work_info = handle_work_info(data)
        logger.info(f'爬取作品信息 {work_url}')
        return work_info

    def spider_some_work(self, auth, works: list, base_path: dict, save_choice: str, excel_name: str = '', proxies=None, force_download=False, use_database=True):
        """
        爬取一些作品的信息
        :param auth: 用户认证信息
        :param works: 作品链接列表
        :param base_path: 保存路径
        :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        :param excel_name: excel文件名
        :param force_download: 是否强制下载
        :param use_database: 是否使用数据库优化
        :return:
        """
        if (save_choice == 'all' or save_choice == 'excel') and excel_name == '':
            raise ValueError('excel_name 不能为空')
        
        work_list = []
        download_stats = {
            'total_works': 0,
            'works_downloaded': 0,
            'works_skipped': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'files_failed': 0
        }
        
        for work_url in works:
            work_info = self.spider_work(auth, work_url)
            work_list.append(work_info)
            download_stats['total_works'] += 1
            
        for work_info in work_list:
            if save_choice == 'all' or 'media' in save_choice:
                stats = download_work(work_info, base_path['media'], save_choice, force_download, use_database)
                download_stats['files_downloaded'] += stats['files_downloaded']
                download_stats['files_skipped'] += stats['files_skipped']
                download_stats['files_failed'] += stats['files_failed']
                
                if stats['files_downloaded'] > 0:
                    download_stats['works_downloaded'] += 1
                elif stats['files_skipped'] == stats['total_files']:
                    download_stats['works_skipped'] += 1
                    
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_list, file_path)
        
        logger.info(f'批量爬取完成 - 总作品: {download_stats["total_works"]}, 新下载: {download_stats["works_downloaded"]}, 跳过: {download_stats["works_skipped"]}, 文件下载: {download_stats["files_downloaded"]}, 文件跳过: {download_stats["files_skipped"]}, 文件失败: {download_stats["files_failed"]}')
        return download_stats


    def spider_user_all_work(self, auth, user_url: str, base_path: dict, save_choice: str, excel_name: str = '', proxies=None, force_download=False, use_database=True):
        """
        爬取一个用户的所有作品，支持数据库预过滤
        :param auth: 用户认证信息
        :param user_url: 用户链接
        :param base_path: 保存路径
        :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
        :param excel_name: excel文件名
        :param proxies: 代理
        :param force_download: 是否强制下载
        :param use_database: 是否使用数据库优化
        :return:
        """
        user_info = self.douyin_apis.get_user_info(auth, user_url)
        work_list = self.douyin_apis.get_user_all_work_info(auth, user_url)
        
        # 提取用户ID用于数据库查询
        user_id = user_info['user'].get('sec_uid', '')
        
        download_stats = {
            'total_works': len(work_list),
            'works_downloaded': 0,
            'works_skipped': 0,
            'works_db_skipped': 0,  # 数据库预过滤跳过的数量
            'files_downloaded': 0,
            'files_skipped': 0,
            'files_failed': 0
        }
        
        # 数据库预过滤（如果启用且不强制下载）
        db = get_download_db() if use_database else None
        works_to_process = []
        
        if db and not force_download:
            # 获取已下载的作品ID集合
            downloaded_work_ids = db.get_downloaded_work_ids(user_id)
            logger.info(f'数据库显示用户 {user_id} 已下载 {len(downloaded_work_ids)} 个作品')
            
            # 过滤出需要处理的作品
            for work_info in work_list:
                work_id = work_info.get('aweme_id', '')
                if work_id not in downloaded_work_ids:
                    works_to_process.append(work_info)
                else:
                    download_stats['works_db_skipped'] += 1
            
            logger.info(f'数据库预过滤: 总作品 {len(work_list)}, 需处理 {len(works_to_process)}, 数据库跳过 {download_stats["works_db_skipped"]}')
        else:
            works_to_process = work_list
        
        logger.info(f'用户 {user_url} 作品数量: {len(work_list)}, 需要处理: {len(works_to_process)}')
        
        if save_choice == 'all' or save_choice == 'excel':
            excel_name = user_url.split('/')[-1].split('?')[0]

        work_info_list = []
        
        # 处理需要下载的作品
        for work_info in works_to_process:
            work_info['author'].update(user_info['user'])
            work_info = handle_work_info(work_info)
            work_info_list.append(work_info)
            logger.info(f'爬取作品信息 {work_info["work_url"]}')
            
            if save_choice == 'all' or 'media' in save_choice:
                stats = download_work(work_info, base_path['media'], save_choice, force_download, use_database)
                download_stats['files_downloaded'] += stats['files_downloaded']
                download_stats['files_skipped'] += stats['files_skipped']
                download_stats['files_failed'] += stats['files_failed']
                
                if stats['files_downloaded'] > 0:
                    download_stats['works_downloaded'] += 1
                elif stats['files_skipped'] == stats['total_files']:
                    download_stats['works_skipped'] += 1
        
        # 如果需要导出Excel，包含所有作品信息（包括已下载的）
        if (save_choice == 'all' or save_choice == 'excel') and not force_download and db:
            # 为已下载作品补充信息（用于Excel导出）
            for work_info in work_list:
                work_id = work_info.get('aweme_id', '')
                if work_id in db.get_downloaded_work_ids(user_id):
                    if not any(w['work_id'] == work_id for w in work_info_list):
                        work_info['author'].update(user_info['user'])
                        processed_work = handle_work_info(work_info)
                        work_info_list.append(processed_work)
                    
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_info_list, file_path)
            
        # 调整跳过统计（包含数据库预过滤的跳过）
        download_stats['works_skipped'] += download_stats['works_db_skipped']
        
        logger.info(f'用户爬取完成 - 总作品: {download_stats["total_works"]}, 新下载: {download_stats["works_downloaded"]}, 跳过: {download_stats["works_skipped"]} (数据库预过滤: {download_stats["works_db_skipped"]}), 文件下载: {download_stats["files_downloaded"]}, 文件跳过: {download_stats["files_skipped"]}, 文件失败: {download_stats["files_failed"]}')
        return download_stats

    def spider_some_search_work(self, auth, query: str, require_num: int, base_path: dict, save_choice: str,  sort_type: str, publish_time: str, filter_duration="", search_range="", content_type="",   excel_name: str = '', proxies=None, force_download=False, use_database=True):
        """
            :param auth: DouyinAuth object.
            :param query: 搜索关键字.
            :param require_num: 搜索结果数量.
            :param base_path: 保存路径.
            :param save_choice: 保存方式 all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
            :param sort_type: 排序方式 0 综合排序, 1 最多点赞, 2 最新发布.
            :param publish_time: 发布时间 0 不限, 1 一天内, 7 一周内, 180 半年内.
            :param filter_duration: 视频时长 空字符串 不限, 0-1 一分钟内, 1-5 1-5分钟内, 5-10000 5分钟以上
            :param search_range: 搜索范围 0 不限, 1 最近看过, 2 还未看过, 3 关注的人
            :param content_type: 内容形式 0 不限, 1 视频, 2 图文
            :param excel_name: excel文件名
            :param force_download: 是否强制下载
            :param use_database: 是否使用数据库优化
        """
        work_info_list = []
        work_list = self.douyin_apis.search_some_general_work(auth, query, require_num, sort_type, publish_time, filter_duration, search_range, content_type)
        
        download_stats = {
            'total_works': len(work_list),
            'works_downloaded': 0,
            'works_skipped': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'files_failed': 0
        }
        
        logger.info(f'搜索关键词 {query} 作品数量: {len(work_list)}')
        if save_choice == 'all' or save_choice == 'excel':
            excel_name = query
            
        for work_info in work_list:
            logger.info(json.dumps(work_info))
            logger.info(f'爬取作品信息 https://www.douyin.com/video/{work_info["aweme_info"]["aweme_id"]}')
            work_info = handle_work_info(work_info['aweme_info'])
            work_info_list.append(work_info)
            
            if save_choice == 'all' or 'media' in save_choice:
                stats = download_work(work_info, base_path['media'], save_choice, force_download, use_database)
                download_stats['files_downloaded'] += stats['files_downloaded']
                download_stats['files_skipped'] += stats['files_skipped']
                download_stats['files_failed'] += stats['files_failed']
                
                if stats['files_downloaded'] > 0:
                    download_stats['works_downloaded'] += 1
                elif stats['files_skipped'] == stats['total_files']:
                    download_stats['works_skipped'] += 1
                    
        if save_choice == 'all' or save_choice == 'excel':
            file_path = os.path.abspath(os.path.join(base_path['excel'], f'{excel_name}.xlsx'))
            save_to_xlsx(work_info_list, file_path)
            
        logger.info(f'搜索爬取完成 - 总作品: {download_stats["total_works"]}, 新下载: {download_stats["works_downloaded"]}, 跳过: {download_stats["works_skipped"]}, 文件下载: {download_stats["files_downloaded"]}, 文件跳过: {download_stats["files_skipped"]}, 文件失败: {download_stats["files_failed"]}')
        return download_stats

if __name__ == '__main__':
    """
        此文件为爬虫的入口文件，可以直接运行
        dy_apis/douyin_apis.py 为爬虫的api文件，包含抖音的全部数据接口，可以继续封装
        感谢star和follow
    """

    auth, base_path = init()

    data_spider = Data_Spider()
    # save_choice: all: 保存所有的信息, media: 保存视频和图片（media-video只下载视频, media-image只下载图片，media都下载）, excel: 保存到excel
    # save_choice 为 excel 或者 all 时，excel_name 不能为空


    # 1 爬取列表的所有作品信息 作品链接 如下所示 注意此url会过期！
    works = [
        r'https://www.douyin.com/user/MS4wLjABAAAAv2Jr7Ngl7lQMjp4fw0AxtXkaHOgI_UL8aBJGGDSaU1g?from_tab_name=main&modal_id=7445533736877264178',
    ]
    data_spider.spider_some_work(auth, works, base_path, 'all', 'test')

    # 2 爬取用户的所有作品信息 用户链接 如下所示 注意此url会过期！
    user_url = 'https://www.douyin.com/user/MS4wLjABAAAAULqT-SrJDT7RqeoxeGg1hB14Ia5UI9Pm66kzKmI1ITD2Fo3bUhqYePBaztkzj7U5?from_tab_name=main&relation=0&vid=7227654252435361061'
    data_spider.spider_user_all_work(auth, user_url, base_path, 'all')

    # 3 搜索指定关键词的作品
    query = "榴莲"
    require_num = 20  # 搜索的数量
    sort_type = '0'  # 排序方式 0 综合排序, 1 最多点赞, 2 最新发布
    publish_time = '0'  # 发布时间 0 不限, 1 一天内, 7 一周内, 180 半年内
    filter_duration = ""  # 视频时长 空字符串 不限, 0-1 一分钟内, 1-5 1-5分钟内, 5-10000 5分钟以上
    search_range = "0"  # 搜索范围 0 不限, 1 最近看过, 2 还未看过, 3 关注的人
    content_type = "0"  # 内容形式 0 不限, 1 视频, 2 图文

    data_spider.spider_some_search_work(auth, query, require_num, base_path, 'all', sort_type, publish_time, filter_duration, search_range, content_type)

