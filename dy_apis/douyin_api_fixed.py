# coding=utf-8
import json
import requests
from loguru import logger


def safe_json_loads(text, context=""):
    """
    安全地解析JSON，如果失败则打印详细错误信息
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败 {context}")
        logger.error(f"错误信息: {str(e)}")
        logger.error(f"响应内容前200字符: {text[:200] if text else 'Empty response'}")
        logger.error(f"响应长度: {len(text) if text else 0}")
        
        # 检查是否是HTML错误页面
        if text and text.strip().startswith('<'):
            logger.error("响应似乎是HTML页面，可能是错误页面或需要验证")
            # 尝试提取错误信息
            if 'error' in text.lower() or '错误' in text:
                logger.error("检测到错误页面")
            elif 'verify' in text.lower() or '验证' in text:
                logger.error("可能需要验证码或重新登录")
        
        raise e


def safe_request(url, headers=None, cookies=None, params=None, context=""):
    """
    安全地发送请求并处理响应
    """
    try:
        logger.debug(f"发送请求 {context}: {url}")
        logger.debug(f"参数: {params}")
        
        resp = requests.get(url, headers=headers, cookies=cookies, params=params, verify=False)
        
        logger.debug(f"响应状态码: {resp.status_code}")
        logger.debug(f"响应头: {dict(resp.headers)}")
        
        if resp.status_code != 200:
            logger.error(f"HTTP错误 {context}: {resp.status_code}")
            logger.error(f"响应内容: {resp.text[:500]}")
        
        return resp
    except Exception as e:
        logger.error(f"请求失败 {context}: {str(e)}")
        raise e


# Monkey patch the douyin_api module
def patch_douyin_api():
    """
    给douyin_api模块打补丁，增加错误处理
    """
    try:
        from dy_apis import douyin_api
        
        # 保存原始方法
        original_get_user_info = douyin_api.DouyinAPI.get_user_info
        original_get_work_info = douyin_api.DouyinAPI.get_work_info
        original_get_user_all_work_info = douyin_api.DouyinAPI.get_user_all_work_info
        
        # 创建包装方法
        @staticmethod
        def patched_get_user_info(auth, user_url: str) -> dict:
            try:
                logger.info(f"获取用户信息: {user_url}")
                # 调用原始方法，但使用我们自己的请求处理
                api = f"/aweme/v1/web/user/profile/other/"
                
                # 从原始代码复制参数构建逻辑
                from builder.header_builder import HeaderBuilder, HeaderType
                from builder.params_builder import Params
                
                headers = HeaderBuilder().build(HeaderType.GET)
                headers.set_referer(user_url)
                
                params = Params()
                params.add_param("device_platform", "webapp")
                params.add_param("aid", "6383")
                params.add_param("channel", "channel_pc_web")
                
                # 提取sec_uid
                if 'user' in user_url:
                    sec_user_id = user_url.split("/")[-1].split("?")[0]
                else:
                    import re
                    sec_user_id = re.findall(r'(MS4wLjABAAAA[a-zA-Z0-9_-]+)', user_url)[0]
                
                params.add_param("sec_user_id", sec_user_id)
                params.add_param("source", "channel_pc_web")
                params.add_param("pc_client_type", "1")
                params.add_param("version_code", "190500")
                params.add_param("version_name", "19.5.0")
                params.add_param("cookie_enabled", "true")
                params.add_param("browser_language", "zh-CN")
                params.add_param("browser_platform", "Win32")
                params.add_param("browser_name", "Edge")
                params.add_param("browser_version", "125.0.0.0")
                params.add_param("browser_online", "true")
                params.add_param("engine_name", "Blink")
                params.add_param("engine_version", "125.0.0.0")
                params.with_web_id(auth, user_url)
                params.add_param("verifyFp", auth.cookie.get('s_v_web_id', ''))
                params.add_param("fp", auth.cookie.get('s_v_web_id', ''))
                params.add_param("msToken", auth.msToken)
                params.with_a_bogus()
                
                url = f'{douyin_api.DouyinAPI.douyin_url}{api}'
                resp = safe_request(url, headers=headers.get(), cookies=auth.cookie, 
                                  params=params.get(), context="get_user_info")
                
                return safe_json_loads(resp.text, context=f"get_user_info({user_url})")
                
            except Exception as e:
                logger.error(f"获取用户信息失败: {str(e)}")
                raise
        
        # 应用补丁
        douyin_api.DouyinAPI.get_user_info = patched_get_user_info
        
        logger.info("DouyinAPI补丁应用成功")
        
    except Exception as e:
        logger.error(f"应用补丁失败: {str(e)}")
        raise