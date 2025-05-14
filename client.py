
import socket
import threading
import tkinter as tk
from tkinter import messagebox
class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Guojam is Handsome Chat OS V1.0")
        self.server_ip = "chat.guojam.xyz"  # 服务器IP
        self.port = 34568
        self.my_code = "anonymous"  # 默认代号
        self.target_code = "guojam"  # 默认目标代号
        self.server_socket = None
        self.connected = False
        self.online = False  # 目标在线状态
        self.timer = None  # 定时检测线程
        # 创建界面组件
        self._create_widgets()
        # 启动窗口关闭事件处理
        root.protocol("WM_DELETE_WINDOW", self.close_app)
    def _create_widgets(self):
        # 代号输入区
        code_frame = tk.Frame(self.root)
        tk.Label(code_frame, text="我的名字:").pack(side="left", padx=5)
        self.code_entry = tk.Entry(code_frame, width=20)
        self.code_entry.pack(side="left", padx=5)
        code_frame.pack(pady=5)
        # 目标代号输入区
        target_frame = tk.Frame(self.root)
        tk.Label(target_frame, text="目标名字:").pack(side="left", padx=5)
        self.target_entry = tk.Entry(target_frame, width=20)
        self.target_entry.pack(side="left", padx=5)
        self.target_entry.insert(0, "guojam")  # 默认值
        target_frame.pack(pady=5)
        # 保存配置按钮
        self.save_btn = tk.Button(self.root, text="保存配置并连接", command=self.save_and_connect)
        self.save_btn.pack(pady=5)
        # 状态指示灯
        status_frame = tk.Frame(self.root)
        tk.Label(status_frame, text="目标状态:").pack(side="left", padx=5)
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, bg="white")
        self.status_canvas.create_oval(5, 5, 15, 15, fill="red")  # 初始为红色（离线）
        self.status_canvas.pack(side="left", padx=5)
        status_frame.pack(pady=5)
        # 消息显示框
        self.msg_area = tk.Text(self.root, width=50, height=20)
        self.msg_area.config(state=tk.DISABLED)
        scrollbar = tk.Scrollbar(self.root, command=self.msg_area.yview)
        self.msg_area.configure(yscrollcommand=scrollbar.set)
        self.msg_area.pack(padx=10, pady=5, side="left")
        scrollbar.pack(pady=5, side="left", fill="y")
        # 消息输入区
        input_frame = tk.Frame(self.root)
        self.input_entry = tk.Entry(input_frame, width=40)
        self.send_btn = tk.Button(input_frame, text="发送", command=self.send_message)
        self.input_entry.pack(side="left", padx=5)
        self.send_btn.pack(side="left", padx=5)
        input_frame.pack(pady=10)
    def save_and_connect(self):
        """保存配置并连接服务器"""
        self.my_code = self.code_entry.get().strip() or "anonymous"
        self.target_code = self.target_entry.get().strip() or "guojam"
        # 连接服务器
        if self.connected:
            messagebox.showwarning("提示", "已连接，将更新目标代号")
            self.update_target_code()
            return
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_ip, self.port))
            self.connected = True
            # 发送客户端代号
            code_bytes = self.my_code.encode("utf-8")
            self.server_socket.sendall(len(code_bytes).to_bytes(4, byteorder="big") + code_bytes)
            messagebox.showinfo("成功", "连接服务器并保存配置")
            self.msg_area.config(state=tk.NORMAL)
            self.msg_area.insert(tk.END, "已连接到服务器\n")
            self.msg_area.config(state=tk.DISABLED)
            # 启动消息接收线程和状态检测
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.start_status_check()
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
            self.connected = False
    def start_status_check(self):
        """每5秒检测一次目标状态"""
        self.check_target_status()
        if self.connected:
            self.timer = threading.Timer(5, self.start_status_check)
            self.timer.start()
    def check_target_status(self):
        """向服务器查询目标代号状态"""
        if not self.connected:
            return
        try:
            query_msg = f"QUERY:{self.target_code}"
            query_bytes = query_msg.encode("utf-8")
            self.server_socket.sendall(len(query_bytes).to_bytes(4, byteorder="big") + query_bytes)
        except Exception as e:
            messagebox.showwarning("提示", f"状态检测失败: {str(e)}")
    def receive_messages(self):
        """接收服务器消息（包括状态和聊天内容）"""
        try:
            while self.connected:
                # 接收消息长度
                len_data = self.server_socket.recv(4)
                if not len_data:
                    break
                msg_len = int.from_bytes(len_data, byteorder="big")
                # 接收消息内容
                msg = self.server_socket.recv(msg_len).decode("utf-8")
                if msg.startswith("STATUS:"):
                    # 更新状态指示灯
                    parts = msg.split(":")
                    if len(parts) == 3 and parts[1] == self.target_code:
                        self.online = parts[2] == "1"
                        self.update_status_indicator()
                else:
                    self.msg_area.config(state=tk.NORMAL)
                    self.msg_area.insert(tk.END, msg + "\n")
                    self.msg_area.config(state=tk.DISABLED)
                    self.msg_area.see(tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"接收消息失败: {str(e)}")
            self.disconnect()
        finally:
            self.disconnect()
    def send_message(self):
        """发送消息到目标代号"""
        if not self.connected:
            messagebox.showerror("错误", "未连接到服务器")
            return
        content = self.input_entry.get().strip()
        if not content:
            messagebox.showwarning("提示", "请输入消息内容")
            return
        # 构造消息（目标代号:内容）
        msg = f"{self.target_code}:{content}"
        msg_bytes = msg.encode("utf-8")
        try:
            self.server_socket.sendall(len(msg_bytes).to_bytes(4, byteorder="big") + msg_bytes)
            self.input_entry.delete(0, tk.END)
            # 显示自己发送的消息
            self.msg_area.config(state=tk.NORMAL)
            self.msg_area.insert(tk.END, f"{self.my_code}:{content}\n")
            self.msg_area.config(state=tk.DISABLED)
            self.msg_area.see(tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"发送失败: {str(e)}")
    def update_target_code(self):
        """通知服务器更新目标代号（可选，根据协议扩展）"""
        pass
    def update_status_indicator(self):
        """更新状态指示灯颜色"""
        color = "green" if self.online else "red"
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(5, 5, 15, 15, fill=color)
    def disconnect(self):
        """断开连接"""
        if self.connected:
            self.connected = False
            self.server_socket.close()
            self.msg_area.config(state=tk.NORMAL)
            self.msg_area.insert(tk.END, "连接已断开\n")
            self.msg_area.config(state=tk.DISABLED)
            if self.timer:
                self.timer.cancel()
    def close_app(self):
        """关闭应用"""
        self.disconnect()
        self.root.destroy()
if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()

