# coding=utf-8
"""
异步版本的抖音API封装
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from .douyin_api import DouyinAPI


class DouyinAsyncAPI(DouyinAPI):
    """支持异步操作的抖音API"""
    
    async def get_user_all_works(self, user_id: str, max_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        异步获取用户所有作品
        :param user_id: 用户ID
        :param max_count: 最大获取数量，None表示获取全部
        :return: 作品列表
        """
        try:
            # 构造用户主页URL
            user_url = f"https://www.douyin.com/user/{user_id}"
            
            # 使用现有的同步方法获取作品
            # 在实际应用中，这里应该改为异步HTTP请求
            loop = asyncio.get_event_loop()
            works = await loop.run_in_executor(
                None, 
                self.get_user_all_work_info,
                self.auth,
                user_url
            )
            
            # 如果指定了最大数量，只返回前N个
            if max_count and len(works) > max_count:
                works = works[:max_count]
                
            logger.info(f"获取用户 {user_id} 的 {len(works)} 个作品")
            return works
            
        except Exception as e:
            logger.error(f"获取用户 {user_id} 作品失败: {e}")
            return []