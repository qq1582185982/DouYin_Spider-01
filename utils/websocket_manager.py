# coding=utf-8
"""
WebSocket管理器，用于实时推送通知
"""
import json
import asyncio
from typing import Set, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.connections: Set[Any] = set()  # 存储所有活跃的WebSocket连接
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket):
        """添加新的WebSocket连接"""
        async with self._lock:
            self.connections.add(websocket)
            logger.info(f"WebSocket连接已建立，当前连接数: {len(self.connections)}")
            
    async def disconnect(self, websocket):
        """移除WebSocket连接"""
        async with self._lock:
            self.connections.discard(websocket)
            logger.info(f"WebSocket连接已断开，当前连接数: {len(self.connections)}")
            
    async def send_to_connection(self, websocket, message: str):
        """发送消息到指定连接"""
        try:
            await websocket.send(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            await self.disconnect(websocket)
            
    async def broadcast(self, message: str):
        """广播消息到所有连接"""
        if not self.connections:
            return
            
        # 创建发送任务
        tasks = []
        disconnected = []
        
        async with self._lock:
            for websocket in self.connections:
                try:
                    tasks.append(asyncio.create_task(websocket.send(message)))
                except Exception as e:
                    logger.error(f"准备发送消息时出错: {e}")
                    disconnected.append(websocket)
        
        # 移除断开的连接
        for websocket in disconnected:
            await self.disconnect(websocket)
            
        # 等待所有发送任务完成
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查发送结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"广播消息失败: {result}")
                    
        logger.debug(f"广播消息到 {len(tasks)} 个连接")
        
    async def send_json(self, websocket, data: Dict[str, Any]):
        """发送JSON数据到指定连接"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            await self.send_to_connection(websocket, message)
        except Exception as e:
            logger.error(f"发送JSON数据失败: {e}")
            
    async def broadcast_json(self, data: Dict[str, Any]):
        """广播JSON数据到所有连接"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            await self.broadcast(message)
        except Exception as e:
            logger.error(f"广播JSON数据失败: {e}")
            
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connections)
        
    async def send_notification(self, notification_type: str, content: Any):
        """发送通知消息"""
        data = {
            'type': 'notification',
            'notification_type': notification_type,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast_json(data)
        
    async def send_scan_update(self, progress: Dict[str, Any]):
        """发送扫描进度更新"""
        data = {
            'type': 'scan_update',
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast_json(data)