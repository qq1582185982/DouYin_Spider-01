import type { ApiResponse, ApiError, WorkInfo, SpiderTask, SystemStatus, UserSearchResult, UserVideosResponse } from './types';

class ApiClient {
  private baseUrl = 'http://localhost:8000/api';
  private cookie = '';

  setCookie(cookie: string) {
    this.cookie = cookie;
    // 同时保存到localStorage作为备份
    localStorage.setItem('douyin_cookie', cookie);
  }

  getCookie(): string {
    if (!this.cookie) {
      this.cookie = localStorage.getItem('douyin_cookie') || '';
    }
    return this.cookie;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');
    
    if (this.getCookie()) {
      headers.set('X-Douyin-Cookie', this.getCookie());
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers
      });

      const data = await response.json();

      if (!response.ok) {
        throw {
          code: data.code || response.status,
          message: data.message || 'Request failed',
          status: response.status
        } as ApiError;
      }

      return data;
    } catch (error) {
      if ((error as ApiError).code) {
        throw error;
      }
      throw {
        code: 0,
        message: error instanceof Error ? error.message : 'Network error',
        status: 0
      } as ApiError;
    }
  }

  // 系统相关
  async getSystemStatus(): Promise<ApiResponse<SystemStatus>> {
    return this.request<SystemStatus>('/system/status');
  }

  async validateCookie(cookie: string): Promise<ApiResponse<boolean>> {
    return this.request('/system/validate-cookie', {
      method: 'POST',
      body: JSON.stringify({ cookie })
    });
  }

  // 用户爬取
  async spiderUser(userUrl: string, saveChoice: string = 'all', forceDownload: boolean = false, selectedVideos?: string[]): Promise<ApiResponse<SpiderTask>> {
    return this.request<SpiderTask>('/spider/user', {
      method: 'POST',
      body: JSON.stringify({ 
        user_url: userUrl, 
        save_choice: saveChoice, 
        force_download: forceDownload,
        selected_videos: selectedVideos
      })
    });
  }

  // 搜索用户
  async searchUsers(query: string, num: number = 10): Promise<ApiResponse<UserSearchResult[]>> {
    return this.request<UserSearchResult[]>('/spider/search-users', {
      method: 'POST',
      body: JSON.stringify({ query, num })
    });
  }

  // 获取用户视频列表
  async getUserVideos(userUrl: string): Promise<ApiResponse<UserVideosResponse>> {
    return this.request<UserVideosResponse>('/spider/user-videos', {
      method: 'POST',
      body: JSON.stringify({ user_url: userUrl })
    });
  }

  // 作品爬取
  async spiderWork(workUrl: string, download: boolean = false): Promise<ApiResponse<WorkInfo>> {
    return this.request<WorkInfo>('/spider/work', {
      method: 'POST',
      body: JSON.stringify({ work_url: workUrl, download })
    });
  }

  // 批量下载作品
  async spiderBatchWorks(workUrls: string[], forceDownload: boolean = false): Promise<ApiResponse<SpiderTask>> {
    return this.request<SpiderTask>('/spider/batch-works', {
      method: 'POST',
      body: JSON.stringify({ work_urls: workUrls, force_download: forceDownload })
    });
  }

  // 搜索爬取
  async spiderSearch(
    query: string,
    options: {
      require_num?: number;
      sort_type?: string;
      publish_time?: string;
      filter_duration?: string;
      search_range?: string;
      content_type?: string;
      save_choice?: string;
      force_download?: boolean;
    } = {}
  ): Promise<ApiResponse<SpiderTask>> {
    return this.request<SpiderTask>('/spider/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        require_num: options.require_num || 20,
        sort_type: options.sort_type || '0',
        publish_time: options.publish_time || '0',
        filter_duration: options.filter_duration || '',
        search_range: options.search_range || '0',
        content_type: options.content_type || '0',
        save_choice: options.save_choice || 'all',
        force_download: options.force_download || false
      })
    });
  }

  // 获取作品列表
  async getWorks(page: number = 1, limit: number = 20): Promise<ApiResponse<{
    items: WorkInfo[];
    total: number;
    page: number;
    limit: number;
  }>> {
    return this.request(`/works?page=${page}&limit=${limit}`);
  }
  
  // 获取所有作者列表
  async getWorkAuthors(): Promise<ApiResponse<Array<{
    user_id: string;
    nickname: string;
  }>>> {
    return this.request('/works/authors');
  }

  // 获取单个作品详情
  async getWork(workId: string): Promise<ApiResponse<WorkInfo>> {
    return this.request<WorkInfo>(`/works/${workId}`);
  }

  // 获取任务列表
  async getTasks(): Promise<ApiResponse<SpiderTask[]>> {
    return this.request<SpiderTask[]>('/tasks');
  }

  // 获取任务详情
  async getTask(taskId: string): Promise<ApiResponse<SpiderTask>> {
    return this.request<SpiderTask>(`/tasks/${taskId}`);
  }

  // 取消任务
  async cancelTask(taskId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/tasks/${taskId}/cancel`, {
      method: 'POST'
    });
  }

  // 获取配置
  async getConfig(): Promise<ApiResponse<{
    save_path: string;
    cookie: string;
    proxy?: string;
  }>> {
    return this.request('/config');
  }

  // 更新配置
  async updateConfig(config: {
    save_path?: string;
    cookie?: string;
    proxy?: string;
  }): Promise<ApiResponse<void>> {
    return this.request<void>('/config', {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  }

  // 订阅相关
  async getSubscriptions(): Promise<ApiResponse<{
    subscriptions: Array<{
      id: number;
      user_id: string;
      sec_uid: string;
      nickname: string;
      avatar: string;
      signature: string;
      follower_count: number;
      aweme_count: number;
      user_url: string;
      enabled: boolean;
      auto_download: boolean;
      selected_videos?: string[];
      last_check_time?: string;
      last_video_time?: string;
      created_at: string;
      updated_at: string;
    }>;
    stats: {
      total_subscriptions: number;
      enabled_subscriptions: number;
      total_videos: number;
      downloaded_videos: number;
      new_videos: number;
    };
  }>> {
    return this.request('/subscriptions');
  }

  async addSubscription(userInfo: UserSearchResult): Promise<ApiResponse<{ subscription_id: number }>> {
    return this.request('/subscriptions', {
      method: 'POST',
      body: JSON.stringify({ user_info: userInfo })
    });
  }

  async removeSubscription(userId: string): Promise<ApiResponse<void>> {
    return this.request(`/subscriptions/${userId}`, {
      method: 'DELETE'
    });
  }

  async updateSubscription(userId: string, updates: {
    enabled?: boolean;
    auto_download?: boolean;
    selected_videos?: string[];
  }): Promise<ApiResponse<void>> {
    return this.request(`/subscriptions/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async checkSubscriptionUpdates(): Promise<ApiResponse<SpiderTask>> {
    return this.request('/subscriptions/check-updates', {
      method: 'POST'
    });
  }

  async getSubscriptionVideos(userId: string, onlyNew: boolean = false): Promise<ApiResponse<{
    subscription: any;
    videos: Array<{
      id: number;
      aweme_id: string;
      title: string;
      create_time: number;
      duration: number;
      cover: string;
      is_downloaded: boolean;
      download_time?: string;
    }>;
  }>> {
    return this.request(`/subscriptions/${userId}/videos?only_new=${onlyNew}`);
  }

  async downloadSubscriptionNewVideos(userId: string): Promise<ApiResponse<SpiderTask>> {
    return this.request('/subscriptions/download-new', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    });
  }

  // 扫描器相关
  async getScannerConfig(): Promise<ApiResponse<{
    interval: number;
    auto_download: boolean;
    enabled: boolean;
    is_running: boolean;
    batch_size?: number;
  }>> {
    return this.request('/subscriptions/scanner/config');
  }

  async updateScannerConfig(config: {
    interval?: number;
    auto_download?: boolean;
    enabled?: boolean;
    batch_size?: number;
  }): Promise<ApiResponse<any>> {
    return this.request('/subscriptions/scanner/config', {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  }

  async startScanner(): Promise<ApiResponse<void>> {
    return this.request('/subscriptions/scanner/start', {
      method: 'POST'
    });
  }

  async stopScanner(): Promise<ApiResponse<void>> {
    return this.request('/subscriptions/scanner/stop', {
      method: 'POST'
    });
  }

  // 添加便捷的请求方法
  async get(endpoint: string): Promise<any> {
    return this.request(endpoint);
  }

  async post(endpoint: string, data: any): Promise<any> {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint: string, data: any): Promise<any> {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
}

const apiClient = new ApiClient();

export default apiClient;
export { apiClient as api };