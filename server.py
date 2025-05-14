import socket
import threading
from tkinter import Tk, Text, Scrollbar, Label

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Chat")
        self.clients = {}  # 存储 代号: socket
        self.online_status = {}  # 存储 代号: 在线状态
        
        # 界面组件
        self.msg_text = Text(root, width=50, height=20)
        self.msg_text.pack(padx=10, pady=10)
        scroll = Scrollbar(self.msg_text, command=self.msg_text.yview)
        scroll.pack(side='right', fill='y')
        self.msg_text.configure(yscrollcommand=scroll.set)
        
        threading.Thread(target=self.start_server, daemon=True).start()
    
    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 34568))
        server.listen(5)
        self.msg_text.insert('end', "服务器启动，等待客户端连接...\n")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
    
    def handle_client(self, client_sock):
        try:
            # 接收客户端代号
            code_len_data = client_sock.recv(4)
            code_len = int.from_bytes(code_len_data, byteorder='big')
            code = client_sock.recv(code_len).decode('utf-8')
            
            self.clients[code] = client_sock
            self.online_status[code] = True
            self.broadcast_status(code, True)  # 广播上线状态
            self.msg_text.insert('end', f"客户端 {code} 连接（IP: {client_sock.getpeername()[0]}）\n")
            
            while True:
                msg_len_data = client_sock.recv(4)
                if not msg_len_data:
                    break
                msg_len = int.from_bytes(msg_len_data, byteorder='big')
                msg = client_sock.recv(msg_len).decode('utf-8')
                
                if msg.startswith("QUERY:"):
                    # 处理状态查询请求（格式：QUERY:目标代号）
                    target_code = msg.split(':', 1)[1]
                    status = self.online_status.get(target_code, 0)
                    status_msg = f"STATUS:{target_code}:{1 if status else 0}"
                    self.send_to_client(code, status_msg)
                elif ':' in msg:
                    # 解析目标代号和消息内容（格式：目标代号:消息内容）
                    target_code, content = msg.split(':', 1)
                    if target_code in self.clients:
                        self.send_to_client(target_code, f"{code}:{content}")
                        self.msg_text.insert('end', f"转发消息 [{code} -> {target_code}]: {content}\n")
                    else:
                        self.send_to_client(code, f"警告：目标 {target_code} 不在线")
                else:
                    self.msg_text.insert('end', f"无效消息格式（来自 {code}）: {msg}\n")
        except Exception as e:
            self.msg_text.insert('end', f"客户端 {code} 错误: {str(e)}\n")
        finally:
            if code in self.clients:
                del self.clients[code]
                self.online_status[code] = False
                self.broadcast_status(code, False)  # 广播下线状态
                client_sock.close()
                self.msg_text.insert('end', f"客户端 {code} 断开连接\n")
    
    def send_to_client(self, code, msg):
        """向指定代号的客户端发送消息"""
        if code in self.clients:
            msg_bytes = msg.encode('utf-8')
            len_bytes = len(msg_bytes).to_bytes(4, byteorder='big')
            try:
                self.clients[code].sendall(len_bytes + msg_bytes)
            except Exception as e:
                self.msg_text.insert('end', f"发送到 {code} 失败: {str(e)}\n")
    
    def broadcast_status(self, code, status):
        """向所有客户端广播某代号的在线状态"""
        status_msg = f"STATUS:{code}:{1 if status else 0}"
        for c in self.clients:
            self.send_to_client(c, status_msg)
    
    def log(self, msg):
        """安全更新日志"""
        self.msg_text.insert('end', msg + '\n')
        self.msg_text.see('end')

if __name__ == "__main__":
    root = Tk()
    app = ServerApp(root)
    root.title("C - 服务器端")
    root.mainloop()
