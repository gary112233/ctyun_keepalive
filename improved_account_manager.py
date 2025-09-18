# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import threading
import queue
import schedule
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
import logging
import os
import my_captcha

class ImprovedAccountManager:
    def __init__(self, config_file="accounts_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.is_scheduler_running = False
        self.logger = self.setup_logger()
        self.status_callbacks = []  # 状态回调函数列表
        self.log_callbacks = []     # 日志回调函数列表
        
    def setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('ImprovedAccountManager')
        logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建文件处理器
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        file_handler = logging.FileHandler('logs/improved_account.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式器
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def add_status_callback(self, callback):
        """添加状态更新回调"""
        self.status_callbacks.append(callback)
        
    def add_log_callback(self, callback):
        """添加日志回调"""
        self.log_callbacks.append(callback)
        
    def notify_status_change(self, account_id, status, last_keepalive=None):
        """通知状态变化"""
        self.update_account_status(account_id, status, last_keepalive)
        for callback in self.status_callbacks:
            try:
                callback(account_id, status, last_keepalive)
            except:
                pass
                
    def notify_log(self, message, level="INFO"):
        """通知日志更新"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"

        # 写入日志文件
        getattr(self.logger, level.lower())(message)

        # 通知回调
        for callback in self.log_callbacks:
            try:
                # 确保消息能正确传递到GUI
                callback(log_message)
            except Exception as e:
                # 调试：如果回调失败，输出到控制台
                print(f"Log callback error: {e}")
                print(f"Message: {log_message}")
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_config()
            
    def create_default_config(self):
        """创建默认配置"""
        default_config = {
            "accounts": [],
            "settings": {
                "keepalive_interval": 30,
                "retry_times": 3,
                "retry_delay": 10,
                "browser_type": "edge",
                "browser_path": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "headless": False,
                "sequential_mode": True  # 顺序模式
            },
            "schedule": {
                "enabled": True,
                "interval_minutes": 30,
                "start_time": "08:00",
                "end_time": "22:00",
                "weekend_enabled": True
            }
        }
        self.save_config(default_config)
        return default_config
        
    def save_config(self, config=None):
        """保存配置文件"""
        if config is None:
            config = self.config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    def add_account(self, name, account, password):
        """添加账号"""
        account_id = len(self.config['accounts']) + 1
        new_account = {
            "id": account_id,
            "name": name,
            "account": account,
            "password": password,
            "enabled": True,
            "last_keepalive": "",
            "status": "未运行"
        }
        self.config['accounts'].append(new_account)
        self.save_config()
        self.notify_log(f"添加账号: {name} ({account})")
        return account_id
        
    def remove_account(self, account_id):
        """删除账号"""
        for i, account in enumerate(self.config['accounts']):
            if account['id'] == account_id:
                removed = self.config['accounts'].pop(i)
                self.save_config()
                self.notify_log(f"删除账号: {removed['name']}")
                return True
        return False
        
    def update_account_status(self, account_id, status, last_keepalive=None):
        """更新账号状态"""
        for account in self.config['accounts']:
            if account['id'] == account_id:
                account['status'] = status
                if last_keepalive:
                    account['last_keepalive'] = last_keepalive
                self.save_config()
                break
                
    def get_enabled_accounts(self):
        """获取启用的账号列表"""
        return [acc for acc in self.config['accounts'] if acc['enabled']]
        
    def create_driver(self):
        """创建浏览器驱动"""
        settings = self.config['settings']
        
        if settings['browser_type'] == 'edge':
            options = EdgeOptions()
        else:
            options = ChromeOptions()
            
        # 基本选项
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 无头模式
        if settings['headless']:
            options.add_argument('--headless')
            
        # 设置浏览器路径
        if settings['browser_path']:
            options.binary_location = settings['browser_path']
            
        # 创建驱动 - 优先使用本地驱动文件
        if settings['browser_type'] == 'edge':
            # 检查多个可能的Edge驱动路径
            possible_paths = [
                os.path.join(os.getcwd(), "msedgedriver.exe"),  # 工作目录
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe"),  # 脚本目录
                "msedgedriver.exe"  # 直接查找
            ]

            # 如果是打包程序，检查可执行文件目录
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的路径
                bundle_dir = os.path.dirname(sys.executable)
                possible_paths.insert(0, os.path.join(bundle_dir, "msedgedriver.exe"))

            local_driver_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    local_driver_path = path
                    self.logger.info(f"找到Edge驱动: {path}")
                    break
                else:
                    self.logger.debug(f"未找到驱动: {path}")

            if local_driver_path:
                self.logger.info(f"使用本地Edge驱动: {local_driver_path}")
                service = EdgeService(local_driver_path)
                driver = webdriver.Edge(service=service, options=options)
            else:
                self.logger.info("本地Edge驱动未找到，使用系统驱动")
                driver = webdriver.Edge(options=options)
        else:
            # Chrome驱动处理
            local_chrome_driver = os.path.join(os.getcwd(), "chromedriver.exe")
            if os.path.exists(local_chrome_driver):
                self.logger.info(f"使用本地Chrome驱动: {local_chrome_driver}")
                service = ChromeService(local_chrome_driver)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                self.logger.info("本地Chrome驱动未找到，使用系统驱动")
                driver = webdriver.Chrome(options=options)
            
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
        
    def keepalive_single_account(self, account):
        """对单个账号执行保活操作"""
        account_id = account['id']
        account_name = account['name']
        
        self.notify_log(f"开始保活账号: {account_name}")
        self.notify_status_change(account_id, "正在初始化")
        
        driver = None
        try:
            # 创建浏览器驱动
            self.notify_log(f"[{account_name}] 正在启动浏览器...")
            self.notify_status_change(account_id, "启动浏览器")
            driver = self.create_driver()
            
            # 访问登录页面
            self.notify_log(f"[{account_name}] 正在访问登录页面...")
            self.notify_status_change(account_id, "访问登录页面")
            driver.get("https://pc.ctyun.cn/#/login")
            time.sleep(3)
            
            # 登录
            self.notify_log(f"[{account_name}] 正在登录...")
            self.notify_status_change(account_id, "正在登录")
            
            # 查找并填写账号
            try:
                account_input = driver.find_element(By.CLASS_NAME, "account")
                account_input.clear()
                account_input.send_keys(account['account'])
                self.notify_log(f"[{account_name}] 账号输入完成")
            except Exception as e:
                raise Exception(f"无法找到账号输入框: {str(e)}")
            
            # 查找并填写密码
            try:
                password_input = driver.find_element(By.CLASS_NAME, "password")
                password_input.clear()
                password_input.send_keys(account['password'])
                self.notify_log(f"[{account_name}] 密码输入完成")
            except Exception as e:
                raise Exception(f"无法找到密码输入框: {str(e)}")
            
            # 点击登录
            try:
                login_btn = driver.find_element(By.CLASS_NAME, "btn-submit")
                login_btn.click()
                self.notify_log(f"[{account_name}] 已点击登录按钮")
            except Exception as e:
                raise Exception(f"无法找到登录按钮: {str(e)}")
            
            # 等待页面响应
            time.sleep(3)
            
            # 检查是否需要验证码
            captcha_retry_count = 0
            max_captcha_retries = 3
            
            while captcha_retry_count < max_captcha_retries:
                try:
                    # 检查是否有验证码输入框
                    captcha_input = driver.find_element(By.CLASS_NAME, 'code')
                    captcha_img = driver.find_element(By.CLASS_NAME, 'code-img')
                    
                    if captcha_input.get_attribute('value') == '':
                        captcha_retry_count += 1
                        self.notify_log(f"[{account_name}] 需要输入验证码 (第{captcha_retry_count}次尝试)")
                        self.notify_status_change(account_id, f"输入验证码({captcha_retry_count}/{max_captcha_retries})")
                        
                        # 保存验证码图片
                        safe_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_phone = account['account']
                        captcha_filename = f"{safe_name}_{safe_phone}_captcha.png"
                        captcha_path = f"static/{captcha_filename}"
                        
                        if not os.path.exists('static'):
                            os.makedirs('static')
                        
                        captcha_img.screenshot(captcha_path)
                        self.notify_log(f"[{account_name}] 验证码图片已保存: {captcha_path}")
                        
                        # 尝试自动识别验证码
                        try:
                            verify_code = my_captcha.captcha_pic(captcha_path)
                            if verify_code and verify_code.strip() and verify_code.strip() != 'nofoundOCR':
                                self.notify_log(f"[{account_name}] 自动识别验证码: {verify_code}")
                            else:
                                # 如果识别失败，使用默认值或者提示用户
                                verify_code = "0000"
                                self.notify_log(f"[{account_name}] 验证码识别失败，使用默认值: {verify_code}")
                        except Exception as e:
                            verify_code = "0000"
                            self.notify_log(f"[{account_name}] 验证码识别异常: {str(e)}, 使用默认值: {verify_code}")
                        
                        # 输入验证码
                        captcha_input.clear()
                        captcha_input.send_keys(verify_code)
                        self.notify_log(f"[{account_name}] 已输入验证码: {verify_code}")
                        
                        # 再次点击登录按钮
                        login_btn = driver.find_element(By.CLASS_NAME, "btn-submit")
                        login_btn.click()
                        self.notify_log(f"[{account_name}] 重新点击登录按钮")
                        
                        # 等待响应
                        time.sleep(5)
                        
                        # 检查登录结果
                        current_url = driver.current_url
                        if "desktop-list" in current_url:
                            self.notify_log(f"[{account_name}] 验证码输入成功，登录完成")
                            break
                        else:
                            self.notify_log(f"[{account_name}] 验证码可能错误，准备重试")
                            if captcha_retry_count >= max_captcha_retries:
                                raise Exception(f"验证码重试次数超过限制({max_captcha_retries})")
                            continue
                    else:
                        # 验证码输入框已有内容，说明不需要输入验证码
                        break
                        
                except Exception as captcha_e:
                    # 没有找到验证码元素，说明不需要验证码
                    self.notify_log(f"[{account_name}] 无需验证码或验证码处理完成")
                    break
            
            # 等待登录完成
            self.notify_log(f"[{account_name}] 等待登录完成...")
            time.sleep(5)
            
            current_url = driver.current_url
            self.notify_log(f"[{account_name}] 当前页面URL: {current_url}")
            
            if "desktop-list" in current_url:
                self.notify_log(f"[{account_name}] 登录成功，已进入云桌面列表")
                self.notify_status_change(account_id, "查找云桌面")
                
                # 查找云桌面进入按钮
                desktop_btn = None
                try:
                    self.notify_log(f"[{account_name}] 正在查找云桌面进入按钮...")
                    desktop_btn = driver.find_element(By.XPATH, "//span[contains(text(), '进入') and contains(@class, 'desktop-main-entry-text')]")
                    self.notify_log(f"[{account_name}] 找到云桌面进入按钮（span元素）")
                except:
                    try:
                        desktop_btn = driver.find_element(By.XPATH, "//*[contains(text(), '进入')]")
                        self.notify_log(f"[{account_name}] 找到云桌面进入按钮（通用元素）")
                    except:
                        try:
                            desktop_btn = driver.find_element(By.CLASS_NAME, "desktop-main-entry-text")
                            self.notify_log(f"[{account_name}] 找到云桌面进入按钮（class定位）")
                        except:
                            raise Exception("未找到云桌面进入按钮")
                
                if desktop_btn:
                    self.notify_log(f"[{account_name}] 正在点击进入云桌面...")
                    self.notify_status_change(account_id, "连接云桌面")
                    desktop_btn.click()
                    
                    # 等待云桌面加载
                    self.notify_log(f"[{account_name}] 等待云桌面加载...")
                    wait_count = 0
                    while wait_count < 30:
                        time.sleep(1)
                        wait_count += 1
                        current_url = driver.current_url
                        if "desktop?id=" in current_url:
                            self.notify_log(f"[{account_name}] 云桌面加载成功，URL: {current_url}")
                            break
                        elif wait_count % 5 == 0:
                            self.notify_log(f"[{account_name}] 等待云桌面加载中... ({wait_count}/30秒)")
                    
                    # 额外等待让云桌面完全加载，避免截图只显示加载中的画面
                    self.notify_log(f"[{account_name}] 等待云桌面完全加载，避免截图显示加载画面...")
                    time.sleep(20)  # 等待20秒让云桌面完全加载
                    
                    # 保存截图，使用账号名称和手机号作为文件名
                    # 清理文件名中的特殊字符
                    safe_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_phone = account['account']
                    screenshot_filename = f"{safe_name}_{safe_phone}_screenshot.png"
                    screenshot_path = f"static/{screenshot_filename}"
                    
                    try:
                        if not os.path.exists('static'):
                            os.makedirs('static')
                        driver.save_screenshot(screenshot_path)
                        self.notify_log(f"[{account_name}] 截图已保存: {screenshot_path}")
                    except Exception as e:
                        self.notify_log(f"[{account_name}] 保存截图失败: {str(e)}", "WARNING")
                    
                    # 发送保活信号
                    try:
                        driver.execute_script("console.log('keepalive signal');")
                        self.notify_log(f"[{account_name}] 保活信号发送成功")
                    except Exception as e:
                        self.notify_log(f"[{account_name}] 发送保活信号失败: {str(e)}", "WARNING")
                    
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.notify_status_change(account_id, "保活成功", current_time)
                    self.notify_log(f"[{account_name}] 保活操作成功完成")
                    
                    return True
                else:
                    raise Exception("未能获取云桌面进入按钮")
            else:
                raise Exception(f"登录后页面异常，当前URL: {current_url}")
                
        except Exception as e:
            error_msg = str(e)
            self.notify_log(f"[{account_name}] 保活失败: {error_msg}", "ERROR")
            self.notify_status_change(account_id, f"失败: {error_msg}")
            
            # 保存错误页面截图
            if driver:
                try:
                    # 使用账号名称和手机号作为错误截图文件名
                    safe_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_phone = account['account']
                    error_screenshot_filename = f"{safe_name}_{safe_phone}_error.png"
                    error_screenshot_path = f"static/{error_screenshot_filename}"
                    if not os.path.exists('static'):
                        os.makedirs('static')
                    driver.save_screenshot(error_screenshot_path)
                    self.notify_log(f"[{account_name}] 错误截图已保存: {error_screenshot_path}")
                except:
                    pass
            
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                    self.notify_log(f"[{account_name}] 浏览器已关闭")
                except:
                    pass
                    
    def sequential_keepalive(self, account_ids=None):
        """顺序保活（一个接一个）"""
        if account_ids is None:
            accounts = self.get_enabled_accounts()
        else:
            accounts = [acc for acc in self.config['accounts'] if acc['id'] in account_ids and acc['enabled']]
        
        if not accounts:
            self.notify_log("没有可保活的账号", "WARNING")
            return
            
        start_time = datetime.now()
        self.notify_log(f"[保活任务] 开始顺序保活，共 {len(accounts)} 个账号 - {start_time.strftime('%H:%M:%S')}")

        success_count = 0
        failed_accounts = []

        for i, account in enumerate(accounts, 1):
            account_start_time = datetime.now()
            self.notify_log(f"[保活任务] 处理第 {i}/{len(accounts)} 个账号: {account['name']} ({account['account']}) - {account_start_time.strftime('%H:%M:%S')}")

            try:
                result = self.keepalive_single_account(account)
                account_end_time = datetime.now()
                duration = (account_end_time - account_start_time).total_seconds()

                if result:
                    success_count += 1
                    self.notify_log(f"[保活任务] ✓ 账号 {account['name']} 保活成功 - 耗时: {duration:.1f}秒")
                else:
                    failed_accounts.append(account['name'])
                    self.notify_log(f"[保活任务] ✗ 账号 {account['name']} 保活失败 - 耗时: {duration:.1f}秒")

            except Exception as e:
                failed_accounts.append(account['name'])
                account_end_time = datetime.now()
                duration = (account_end_time - account_start_time).total_seconds()
                self.notify_log(f"[保活任务] ✗ 账号 {account['name']} 发生异常: {str(e)} - 耗时: {duration:.1f}秒", "ERROR")

            # 账号之间的间隔
            if i < len(accounts):
                self.notify_log(f"[保活任务] 等待 5 秒后处理下一个账号...")
                time.sleep(5)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        self.notify_log(f"[保活任务] 顺序保活完成 - 成功: {success_count}/{len(accounts)}, "
                       f"总耗时: {total_duration:.1f}秒, 完成时间: {end_time.strftime('%H:%M:%S')}")

        if failed_accounts:
            self.notify_log(f"[保活任务] 失败账号: {', '.join(failed_accounts)}")
        
    def start_scheduler(self):
        """启动定时调度器"""
        if self.is_scheduler_running:
            return
            
        schedule_config = self.config['schedule']
        if not schedule_config['enabled']:
            self.notify_log("定时调度已禁用")
            return
            
        # 设置定时任务
        interval = schedule_config['interval_minutes']
        schedule.every(interval).minutes.do(self.scheduled_keepalive)
        
        self.is_scheduler_running = True
        schedule_config = self.config['schedule']
        self.notify_log(f"[调度器] 定时调度器已启动")
        self.notify_log(f"[调度器] 配置详情 - 间隔: {interval}分钟, "
                       f"时间范围: {schedule_config['start_time']}-{schedule_config['end_time']}, "
                       f"周末保活: {'启用' if schedule_config['weekend_enabled'] else '禁用'}")

        # 立即执行第一次保活任务
        self.notify_log(f"[调度器] 立即执行首次保活任务")
        threading.Thread(target=self.scheduled_keepalive, daemon=True).start()

        self.notify_log(f"[调度器] 下次执行时间: {datetime.now() + timedelta(minutes=interval)}")
        
        def run_scheduler():
            last_check_time = time.time()
            while self.is_scheduler_running:
                current_time = time.time()
                # 每10分钟输出一次调度器状态
                if current_time - last_check_time >= 600:  # 10分钟
                    current_dt = datetime.now()
                    schedule_config = self.config['schedule']
                    self.notify_log(f"[调度器] 运行中 - 当前时间: {current_dt.strftime('%H:%M:%S')}, "
                                  f"间隔: {schedule_config['interval_minutes']}分钟, "
                                  f"时间范围: {schedule_config['start_time']}-{schedule_config['end_time']}")
                    last_check_time = current_time

                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
    def stop_scheduler(self):
        """停止定时调度器"""
        self.is_scheduler_running = False
        schedule.clear()
        self.notify_log(f"[调度器] 定时调度器已停止 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def scheduled_keepalive(self):
        """定时保活任务"""
        schedule_config = self.config['schedule']
        current_time = datetime.now()

        self.notify_log(f"[调度器] 触发定时保活任务 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 检查时间范围 (支持24小时模式)
        start_time = datetime.strptime(schedule_config['start_time'], "%H:%M").time()
        end_time = datetime.strptime(schedule_config['end_time'], "%H:%M").time()

        # 24小时模式检查 (00:00-23:59)
        is_24hour_mode = (start_time.hour == 0 and start_time.minute == 0 and
                         end_time.hour == 23 and end_time.minute == 59)

        self.notify_log(f"[调度器] 时间检查 - 当前: {current_time.strftime('%H:%M')}, "
                       f"范围: {schedule_config['start_time']}-{schedule_config['end_time']}, "
                       f"24小时模式: {'是' if is_24hour_mode else '否'}")

        if not is_24hour_mode:
            if not (start_time <= current_time.time() <= end_time):
                self.notify_log(f"[调度器] 跳过执行 - 当前时间不在保活时间范围内")
                return

            # 检查是否启用周末
            weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            current_weekday = weekday_names[current_time.weekday()]
            is_weekend = current_time.weekday() >= 5

            self.notify_log(f"[调度器] 周末检查 - 今天: {current_weekday}, "
                           f"是否周末: {'是' if is_weekend else '否'}, "
                           f"周末保活: {'启用' if schedule_config['weekend_enabled'] else '禁用'}")

            if not schedule_config['weekend_enabled'] and is_weekend:
                self.notify_log(f"[调度器] 跳过执行 - 周末保活已禁用")
                return

        # 获取启用的账号数量
        enabled_accounts = self.get_enabled_accounts()
        self.notify_log(f"[调度器] 准备执行保活 - 启用账号数: {len(enabled_accounts)}")

        if not enabled_accounts:
            self.notify_log(f"[调度器] 跳过执行 - 没有启用的账号")
            return

        self.notify_log(f"[调度器] 开始执行定时保活任务")
        threading.Thread(target=self.sequential_keepalive, daemon=True).start()
        
    def get_status_summary(self):
        """获取状态摘要"""
        accounts = self.config['accounts']
        enabled_count = len([acc for acc in accounts if acc['enabled']])
        
        status_counts = {}
        for account in accounts:
            status = account['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            'total_accounts': len(accounts),
            'enabled_accounts': enabled_count,
            'status_counts': status_counts,
            'scheduler_running': self.is_scheduler_running
        }

# 示例使用
if __name__ == "__main__":
    manager = ImprovedAccountManager()
    
    # 添加日志回调
    def log_callback(message):
        print(message)
    manager.add_log_callback(log_callback)
    
    # 启动定时调度器
    manager.start_scheduler()
    
    # 手动执行一次保活
    manager.sequential_keepalive()
    
    # 保持程序运行
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        manager.stop_scheduler()
        print("程序已停止")