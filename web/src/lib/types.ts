export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface ApiError {
  code: number;
  message: string;
  status: number;
}

export interface WorkInfo {
  work_id: string;
  work_url: string;
  work_type: string;
  title: string;
  desc: string;
  create_time: number;
  author: AuthorInfo;
  video?: VideoInfo;
  images?: string[];
  topics?: string[];
  statistics: Statistics;
  download_time?: string;
  file_size?: number;
  is_complete?: number;
}

export interface AuthorInfo {
  user_id: string;
  user_url: string;
  nickname: string;
  avatar_thumb: string;
  user_desc: string;
  follower_count: number;
  following_count: number;
}

export interface VideoInfo {
  play_addr: string;
  cover: string;
  width: number;
  height: number;
  duration: number;
}

export interface Statistics {
  comment_count: number;
  digg_count: number;
  collect_count: number;
  share_count: number;
  play_count: number;
  admire_count: number;
}

export interface SpiderTask {
  id: string;
  type: 'user' | 'work' | 'search' | 'batch-works';
  status: 'pending' | 'running' | 'completed' | 'failed';
  url?: string;
  urls?: string[];
  query?: string;
  progress: number;
  total: number;
  result?: any;
  results?: Array<{
    url: string;
    status: 'success' | 'failed';
    info?: any;
    error?: string;
  }>;
  error?: string;
  created_at: number;
  updated_at: number;
}

export interface SystemStatus {
  is_running: boolean;
  cookie_valid: boolean;
  total_works: number;
  total_users: number;
  disk_usage: {
    used: number;
    total: number;
  };
}

export interface UserSearchResult {
  user_id: string;
  sec_uid: string;
  nickname: string;
  avatar: string;
  signature: string;
  follower_count: number;
  total_favorited: number;
  aweme_count: number;
  user_url: string;
}

export interface UserVideo {
  aweme_id: string;
  desc: string;
  create_time: number;
  duration: number;
  cover: string;
  statistics: {
    digg_count: number;
    comment_count: number;
    share_count: number;
    play_count: number;
  };
  aweme_type: number; // 0: video, 68: image
}

export interface UserVideosResponse {
  user: {
    nickname: string;
    avatar: string;
    signature: string;
    follower_count: number;
    aweme_count: number;
  };
  works: UserVideo[];
}