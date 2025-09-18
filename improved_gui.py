# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from improved_account_manager import ImprovedAccountManager
from datetime import datetime

class ImprovedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("天翼云多账号保活管理器 - 优化版")
        self.root.geometry("1000x700")
        
        self.manager = ImprovedAccountManager()
        
        # 设置回调
        self.manager.add_status_callback(self.on_status_change)
        self.manager.add_log_callback(self.on_log_message)
        
        self.create_widgets()
        self.refresh_accounts()
        
        
    def create_widgets(self):
        # 创建笔记本组件
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 账号管理页面
        accounts_frame = ttk.Frame(notebook)
        notebook.add(accounts_frame, text="账号管理")

        # 调度器配置页面
        scheduler_frame = ttk.Frame(notebook)
        notebook.add(scheduler_frame, text="调度器设置")

        self.create_accounts_page(accounts_frame)
        self.create_scheduler_page(scheduler_frame)
        
    def create_accounts_page(self, parent):
        """创建账号管理页面"""
        # 控制按钮
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="添加账号", command=self.add_account_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="编辑账号", command=self.edit_account_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="删除账号", command=self.delete_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="刷新列表", command=self.refresh_accounts).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(control_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(control_frame, text="开始保活", command=self.start_keepalive).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="保活选中", command=self.keepalive_selected).pack(side=tk.LEFT, padx=(0, 5))
        
        # 账号列表
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("ID", "名称", "账号", "状态", "最后保活时间", "启用")
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            
        self.accounts_tree.column("ID", width=50)
        self.accounts_tree.column("名称", width=150)
        self.accounts_tree.column("账号", width=150)
        self.accounts_tree.column("状态", width=150)
        self.accounts_tree.column("最后保活时间", width=180)
        self.accounts_tree.column("启用", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.accounts_tree.bind("<Double-1>", lambda e: self.edit_account_dialog())
        
    def create_scheduler_page(self, parent):
        """创建调度器配置页面"""
        # 调度器状态
        status_frame = ttk.LabelFrame(parent, text="调度器状态", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.scheduler_status_label = ttk.Label(status_frame, text="调度器: 未启动", font=("Microsoft YaHei", 10, "bold"))
        self.scheduler_status_label.pack(anchor=tk.W)

        # 调度器控制
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))

        self.scheduler_btn = ttk.Button(control_frame, text="启动调度器", command=self.toggle_scheduler)
        self.scheduler_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 调度器配置
        config_frame = ttk.LabelFrame(parent, text="调度器配置", padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        # 保活间隔设置
        interval_frame = ttk.Frame(config_frame)
        interval_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interval_frame, text="保活间隔:").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.manager.config['schedule']['interval_minutes']))
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=480, width=10, textvariable=self.interval_var)
        interval_spinbox.pack(side=tk.LEFT, padx=(5, 5))
        ttk.Label(interval_frame, text="分钟").pack(side=tk.LEFT)

        # 应用设置按钮
        apply_frame = ttk.Frame(config_frame)
        apply_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(apply_frame, text="应用设置", command=self.apply_scheduler_config).pack(side=tk.LEFT)

        # 详细日志
        log_frame = ttk.LabelFrame(parent, text="详细日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 日志控制按钮
        log_control = ttk.Frame(log_frame)
        log_control.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(log_control, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control, text="保存日志", command=self.save_logs).pack(side=tk.LEFT, padx=(0, 5))

        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control, text="自动滚动", variable=self.auto_scroll_var).pack(side=tk.RIGHT)

        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        
    def add_account_dialog(self):
        """添加账号对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加账号")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="账号名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        ttk.Label(frame, text="手机号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        account_var = tk.StringVar()
        ttk.Entry(frame, textvariable=account_var, width=30).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        ttk.Label(frame, text="密码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=password_var, show="*", width=30).grid(row=2, column=1, padx=(10, 0), pady=5)
        
        def save():
            name = name_var.get().strip()
            account = account_var.get().strip()
            password = password_var.get().strip()
            
            if not all([name, account, password]):
                messagebox.showerror("错误", "请填写所有字段!")
                return
                
            self.manager.add_account(name, account, password)
            self.refresh_accounts()
            dialog.destroy()
            messagebox.showinfo("成功", "账号添加成功!")
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="保存", command=save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
        
    def edit_account_dialog(self):
        """编辑账号对话框"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的账号!")
            return
            
        item = self.accounts_tree.item(selection[0])
        account_id = int(item['values'][0])
        
        account = None
        for acc in self.manager.config['accounts']:
            if acc['id'] == account_id:
                account = acc
                break
                
        if not account:
            messagebox.showerror("错误", "账号不存在!")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑账号")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="账号名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=account['name'])
        ttk.Entry(frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        ttk.Label(frame, text="手机号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        account_var = tk.StringVar(value=account['account'])
        ttk.Entry(frame, textvariable=account_var, width=30).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        ttk.Label(frame, text="密码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar(value=account['password'])
        ttk.Entry(frame, textvariable=password_var, show="*", width=30).grid(row=2, column=1, padx=(10, 0), pady=5)
        
        enabled_var = tk.BooleanVar(value=account['enabled'])
        ttk.Checkbutton(frame, text="启用此账号", variable=enabled_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        def update():
            account['name'] = name_var.get().strip()
            account['account'] = account_var.get().strip()
            account['password'] = password_var.get().strip()
            account['enabled'] = enabled_var.get()
            
            if not all([account['name'], account['account'], account['password']]):
                messagebox.showerror("错误", "请填写所有字段!")
                return
                
            self.manager.save_config()
            self.refresh_accounts()
            dialog.destroy()
            messagebox.showinfo("成功", "账号更新成功!")
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="保存", command=update).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
        
    def delete_account(self):
        """删除账号"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的账号!")
            return
            
        item = self.accounts_tree.item(selection[0])
        account_id = int(item['values'][0])
        account_name = item['values'][1]
        
        if messagebox.askyesno("确认删除", f"确定要删除账号 '{account_name}' 吗?"):
            if self.manager.remove_account(account_id):
                self.refresh_accounts()
                messagebox.showinfo("成功", "账号删除成功!")
            else:
                messagebox.showerror("错误", "删除账号失败!")
                
    def refresh_accounts(self):
        """刷新账号列表"""
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
            
        self.manager.config = self.manager.load_config()
        
        for account in self.manager.config['accounts']:
            enabled_text = "是" if account['enabled'] else "否"
            self.accounts_tree.insert("", tk.END, values=(
                account['id'],
                account['name'],
                account['account'],
                account['status'],
                account['last_keepalive'] or "从未运行",
                enabled_text
            ))
            
            
    def start_keepalive(self):
        """开始保活"""
        if messagebox.askyesno("确认", "确定要开始保活所有启用的账号吗?\n\n账号将按顺序逐个保活。"):
            threading.Thread(target=self.manager.sequential_keepalive, daemon=True).start()
            
    def keepalive_selected(self):
        """保活选中的账号"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要保活的账号!")
            return
            
        account_ids = []
        for item in selection:
            account_id = int(self.accounts_tree.item(item)['values'][0])
            account_ids.append(account_id)
            
        if messagebox.askyesno("确认", f"确定要保活选中的 {len(account_ids)} 个账号吗?\n\n账号将按顺序逐个保活。"):
            threading.Thread(target=self.manager.sequential_keepalive, args=(account_ids,), daemon=True).start()
            
    def manual_keepalive(self):
        """手动保活"""
        self.start_keepalive()
        
    def toggle_scheduler(self):
        """切换调度器"""
        if self.manager.is_scheduler_running:
            self.manager.stop_scheduler()
            self.scheduler_btn.config(text="启动调度器")
            self.scheduler_status_label.config(text="调度器: 已停止", foreground="red")
        else:
            self.manager.start_scheduler()
            self.scheduler_btn.config(text="停止调度器")
            interval = self.manager.config['schedule']['interval_minutes']
            self.scheduler_status_label.config(text=f"调度器: 运行中 (每{interval}分钟)", foreground="green")

    def apply_scheduler_config(self):
        """应用调度器配置"""
        try:
            interval = int(self.interval_var.get())
            if interval < 1:
                messagebox.showwarning("警告", "保活间隔不能少于1分钟!")
                return
            if interval > 480:
                messagebox.showwarning("警告", "保活间隔不能超过8小时(480分钟)!")
                return

            # 更新配置
            self.manager.config['schedule']['interval_minutes'] = interval
            # 设置为24小时运行
            self.manager.config['schedule']['start_time'] = "00:00"
            self.manager.config['schedule']['end_time'] = "23:59"
            self.manager.config['schedule']['weekend_enabled'] = True

            # 保存配置
            self.manager.save_config()

            # 如果调度器正在运行，重启它以应用新配置
            if self.manager.is_scheduler_running:
                self.manager.stop_scheduler()
                self.manager.start_scheduler()
                self.scheduler_status_label.config(text=f"调度器: 运行中 (每{interval}分钟)", foreground="green")

            messagebox.showinfo("成功", f"调度器配置已更新!\n保活间隔: {interval}分钟\n运行模式: 24小时")

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字!")

    def reset_scheduler_config(self):
        """重置调度器配置为默认值"""
        self.interval_var.set("30")
        self.apply_scheduler_config()
            
    def on_status_change(self, account_id, status, last_keepalive=None):
        """状态变化回调"""
        def update_ui():
            # 更新账号列表中的状态
            for item in self.accounts_tree.get_children():
                values = list(self.accounts_tree.item(item)['values'])
                if int(values[0]) == account_id:
                    values[3] = status  # 状态列
                    if last_keepalive:
                        values[4] = last_keepalive  # 最后保活时间列
                    self.accounts_tree.item(item, values=values)
                    break
                    
            
            
        self.root.after(0, update_ui)
        
    def on_log_message(self, message):
        """日志消息回调"""
        def update_ui():
            self.log_text.insert(tk.END, message + "\n")
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)

            # 优化内存管理：保持日志行数在合理范围内
            current_lines = int(self.log_text.index('end-1c').split('.')[0])

            # 当超过500行时，删除前200行，保留最新的300行
            if current_lines > 500:
                self.log_text.delete("1.0", "201.0")
                # 添加内存清理提示
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.insert("1.0", f"[{timestamp}] === 日志已清理，保留最新300行 ===\n")
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)

        self.root.after(0, update_ui)
        
            
    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空所有日志吗?"):
            self.log_text.delete("1.0", tk.END)
            
    def save_logs(self):
        """保存日志"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get("1.0", tk.END))
                messagebox.showinfo("成功", "日志保存成功!")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {str(e)}")

def main():
    root = tk.Tk()
    app = ImprovedGUI(root)
    
    def on_closing():
        if app.manager.is_scheduler_running:
            if messagebox.askokcancel("退出", "调度器正在运行，确定要退出吗?"):
                app.manager.stop_scheduler()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()