// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
  is_active: boolean
  allowed_zabbix_ids: number[]
  created_at: string
}

// 认证相关
export interface LoginRequest {
  username: string
  password: string
  captcha_key: string
  captcha_code: string
}

export interface LoginResponse {
  success: boolean
  token: string
  user: User
  detail?: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  captcha_key: string
  captcha_code: string
}

export interface RegisterResponse {
  success: boolean
  token?: string
  require_activation?: boolean
  detail?: string
}

// Zabbix配置
export interface ZabbixConfig {
  id: number
  name: string
  url: string
  auth_type: 'token' | 'password'
  username?: string
  is_active: boolean
  created_at: string
}

// 邮件配置
export interface EmailConfig {
  id: number
  name: string
  smtp_server: string
  smtp_port: number
  smtp_user: string
  use_ssl: boolean
  mail_from: string
  is_active: boolean
}

// 监控筛选配置
export interface ItemPattern {
  pattern: string
  match_type: 'exact' | 'fuzzy'
}

export interface MonitorFilter {
  id: number
  name: string
  description: string
  item_patterns: ItemPattern[]
  history_type: number
  is_network: boolean
  is_storage: boolean
  zabbix_config_ids: number[]
  use_regex: boolean
  regex_pattern: string | null
  created_at: string
}

// 仪表盘数据
export interface Host {
  hostid: string
  name: string
  ip: string
  groups: string
}

export interface DashboardData {
  total: number
  online_count: number
  offline_count: number
  online_hosts: Host[]
  offline_hosts: Host[]
  cached: boolean
  cached_at: string
}

// 监控数据
export interface MonitorData {
  host: string
  ip: string
  groups: string
  items: MonitorItem[]
}

export interface MonitorItem {
  name: string
  key: string
  value: string
  units: string
  lastclock: string
}

// 定时任务
export interface Task {
  id: number
  name: string
  description?: string
  cron_expression: string
  filter_ids: number[]
  monitor_filter_ids?: number[]
  zabbix_config_id: number
  email_config_id: number | null
  recipients: string[]
  time_range?: number
  email_subject?: string
  email_body?: string
  subject_suffix_config_name?: boolean
  subject_suffix_timestamp?: boolean
  email_include_device_overview?: boolean
  email_include_monitor_summary?: boolean
  email_include_alert_summary?: boolean
  include_device_overview?: boolean
  include_alert_data?: boolean
  is_active: boolean
  is_valid?: boolean
  last_run: string | null
  next_run: string | null
  created_at: string
}

export interface TaskLog {
  id: number
  task_id: number
  task_name: string
  status: string
  start_time: string
  end_time: string | null
  started_at?: string
  finished_at?: string
  message: string
  file_path: string | null
  attachment_path?: string | null
  attachment_filename?: string | null
  recipients?: string[]
}

// 告警
export interface Alert {
  eventid: string
  name: string
  severity: number
  severity_name: string
  host_name: string
  host_ip: string
  host_groups: string
  clock: number
  r_clock: number | null
  duration: number
  recovered: boolean
  acknowledged: boolean
}

// 告警导出任务
export interface AlertExportTask {
  id: number
  zabbix_config_id: number
  zabbix_config_name: string | null
  time_from: number | null
  time_till: number | null
  severity: string | null
  recovered: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_path: string | null
  filename: string | null
  error_message: string | null
  total_count: number
  created_by: number | null
  created_at: string
  completed_at: string | null
}

// 告警API响应
export interface AlertsResponse {
  total: number
  returned: number
  alerts: Alert[]
  zabbix_config_name: string
  has_more: boolean
}

// 系统日志
export interface SystemLog {
  id: number
  level: string
  logger_name: string
  message: string
  created_at: string
}

// 导出任务
export interface ExportTask {
  id: number
  status: string
  created_at: string
  completed_at: string | null
  file_path: string | null
  error: string | null
}

// API响应
export interface ApiResponse<T = any> {
  success?: boolean
  data?: T
  detail?: string
  message?: string
}
