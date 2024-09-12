import tkinter as tk
import tkinter.filedialog as fd
import ttkbootstrap as ttk
from tkinter import messagebox

import os,time,yaml,math
import serial,serial.tools.list_ports
import threading
from queue import Queue,Empty
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES,PKCS1_OAEP

class SerialReader:
    def __init__(self):
        self.lines = []
        self.saving = False
        self.stop_event = threading.Event()

    def send_command(self, ser: serial.Serial, command: str):
        '向esp32發送命令'
        if ser.is_open:
            ser.write(command.encode('utf-8'))
        else:
            print("Serial port is not open")

    def read_serial(self) -> str:
        '讀取esp32返回的私鑰資料'
        esp32 = Methods(None).check_esp32_traget()
        ser = serial.Serial(**esp32)
        if ser is None:
            return None

        self.send_command(ser, "/getprivate")

        try:
            thread = threading.Thread(target=self._read_serial_thread, args=(ser,))
            thread.start()
            thread.join()  
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        if not self.lines:
            return None
        
        return "\n".join(self.lines)

    def _read_serial_thread(self, ser: serial.Serial):
        try:
            while not self.stop_event.is_set():
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "-----BEGIN RSA PRIVATE KEY-----" in line:
                    self.saving = True  
                if self.saving:
                    self.lines.append(line)
                if "-----END RSA PRIVATE KEY-----" in line:
                    self.stop_event.set()  
        except serial.SerialException as e:
            print(f"Serial error in thread: {e}")
            self.stop_event.set()  
        except Exception as e:
            print(f"Unexpected error in thread: {e}")
            self.stop_event.set()  

    def stop_reading(self):
        self.stop_event.set()

class Methods(ttk.Window):
    def __init__(self, master: tk.Tk) -> None:
        if master is not None:
            super().__init__(master)
            self.app_window: ttk.Window = master
            self.withdraw()
        self.__esp_chip_id = "F8CD0412CFA4"
        self.__esp_baud = 115200
        self.__timeout = 2
        self.PY_PATH = os.path.abspath(__file__)
        self.DIRECTORY = os.path.dirname(self.PY_PATH)
        self.private:bytes = None
        self.__AES_KEY_PATH = f"{self.DIRECTORY}\\AES_KEY.bin" #被RSA加密後的AES密碼
        self.password_bin = f"{self.DIRECTORY}\\Password.bin"
        self.password_yaml =  f"{self.DIRECTORY}\\Password.yaml" if self.__search_file(self.DIRECTORY, "Password.yaml") else None

    def check_esp32_traget(self,chip_id=None) -> dict :
        chip_id = chip_id or self.__esp_chip_id
        ports = serial.tools.list_ports.comports()
        for port in ports:
            try:
                with serial.Serial(port.device, self.__esp_baud,timeout=1) as ser:
                    ser.write(b'\r\n')  #喚醒裝置
                    output = ser.read(100).decode('utf-8')  
                    #print(output)
                    if chip_id in output:
                        #print(f"ESP32 with Chip ID {chip_id} found on {port.device}")
                        return {"port":port.device,"baudrate":self.__esp_baud,"timeout":self.__timeout}
            except (OSError, serial.SerialException):
                continue
        print("traget ESP32 not found.")
        return None

    def encrypt_data(self,enc_path:str,rsa_private:bytes):
        try:
            cipher_rsa = PKCS1_OAEP.new(RSA.import_key(rsa_private)) 
            with open(self.__AES_KEY_PATH,"rb") as enc_aes_key:
                dec_aes_key = cipher_rsa.decrypt(enc_aes_key.read())    
            cipher_aes = AES.new(dec_aes_key, AES.MODE_EAX)
            with open(enc_path,"rb") as plaintext:
                plaintext = plaintext.read()
            ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext)
            return b"".join([cipher_aes.nonce, tag, ciphertext])
        except:
            print(f"加密時出現錯誤,請確任參數正確")
    
    def decrypt_data(self,dec_path:str,rsa_private:bytes) -> bytes:
        with open(self.__AES_KEY_PATH,"rb") as enc_aes_key:
            cipher_rsa = PKCS1_OAEP.new(RSA.import_key(rsa_private)) 
            dec_aes_key = cipher_rsa.decrypt(enc_aes_key.read())  
        with open(dec_path,"rb") as ciphertext:
            params = {
                'nonce': ciphertext.read(16),
                'tag': ciphertext.read(16),
                'cipheredData': ciphertext.read()
            }
        cipher_aes = AES.new(dec_aes_key, AES.MODE_EAX, nonce=params["nonce"])
        plaintext = cipher_aes.decrypt_and_verify(ciphertext=params["cipheredData"],received_mac_tag=params["tag"])
        return plaintext

    def __search_file(self,directory:str, filename:str):
        """
        搜尋指定資料夾中是否存在特定檔案。

        :param directory: 資料夾路徑
        :param filename: 檔案名稱
        :return: 如果找到檔案，則回傳 True，否則回傳 False
        """
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return True
        return False

    def delete_file(self,filename:str):
        "刪除文件"
        try:
            os.remove(filename)  
            print(f"{filename} 已成功刪除")
        except FileNotFoundError:
            print(f"{filename} 並未找到")
        except PermissionError:
            print(f"權限被拒絕：無法刪除 {filename}.")
        except Exception as e:
            print(f"刪除時發生錯誤 {filename}: {e}")

    def copyClipboard(self, data):
        #print(data)
        self.clipboard_clear()
        self.clipboard_append(data)
        self.update()

    def decrypt_Yaml(self):
        "解密Yaml檔"
        data = self.decrypt_data(self.password_bin,self.private)
        yaml_str = data.decode('utf-8')
        yaml_data:dict = yaml.load(stream=yaml_str, Loader=yaml.FullLoader)
        with open(f"{self.DIRECTORY}\\Password.yaml","w") as files:
            yaml.dump(yaml_data, files, default_flow_style=False, allow_unicode=True)

    def encrypt_Yaml(self):
        "加密Yaml檔"
        with open(f"{self.password_bin}","wb") as files:
            byte_data:bytes = self.encrypt_data(f"{self.DIRECTORY}\\Password.yaml",self.private)
            files.write(byte_data)
            self.delete_file(f"{self.DIRECTORY}\\Password.yaml")

    def delete_Yaml(self):
        self.delete_file(f"{self.DIRECTORY}\\Password.yaml")


class App(ttk.Window):
    def __init__(self) -> None:
        super().__init__()
        self.methods = Methods(self)
        self.withdraw()
        self.title("密碼存儲器")
        self.icon_path = f"{self.methods.DIRECTORY}\\app.ico"
        self.resizable(False, False)
        self.screen_width,self.screen_height = self.winfo_screenwidth(),self.winfo_screenheight()
        self.style.configure(
            "Bold.Label", font=("Helvetica", 12, "bold"))
        self.style.configure(
            "Bold.TLabel", font=("Helvetica", 16, "bold"))
        self.current_window:tk.Toplevel = None

    def run(self):
        self.__login()
        self.mainloop()

    def __main_windows(self) -> None:
        "創建主窗口"
        if self.current_window:
            self.current_window.destroy()
        self.main_window = tk.Toplevel(self)
        self.main_window.iconbitmap(self.icon_path)
        self.__creatMenu(self.main_window)
        self.__createClipboard(self.main_window)
        width = self.main_window.winfo_width()
        height = self.main_window.winfo_height()
        self.__center_window(self.main_window,width,height)
        self.current_window = self.main_window
        self.main_window.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __login(self) -> None:
        "創建登入介面"
        if self.current_window:
            self.current_window.destroy()
        self.login = tk.Toplevel(self)
        self.__center_window(self.login,250,75)
        self.login.iconbitmap(self.icon_path)
        login_btn = ttk.Button(
            self.login,
            text="檢查金鑰是否插上電腦",
            command=lambda :self.__get_esp32_key()
        )
        login_btn.pack()                                                 
        self.current_window = self.login
        self.login.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __center_window(self,window:ttk.Window,width:int,height:int) -> None:
        "視窗置中"
        x = (self.screen_width - width) // 2
        y = (self.screen_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def __get_esp32_key(self) -> None:
        esp32_status = self.methods.check_esp32_traget()
        if (esp32_status):
            ser_reader = SerialReader()
            self.methods.private = ser_reader.read_serial()
            messagebox.showinfo("金鑰取得成功", "按下確認以繼續!")
            self.__main_windows()
        else:
            messagebox.showinfo("Error出現錯誤!", "請確保金鑰插到電腦!")
            self.__on_closing()
            
    def __on_closing(self):
        self.current_window.destroy()
        self.methods.destroy()
        self.destroy()
    
    def __createClipboard(self,class_:tk.Tk):
        data = self.methods.decrypt_data(self.methods.password_bin,self.methods.private)
        yaml_str = data.decode('utf-8')
        yaml_data:dict = yaml.load(stream=yaml_str, Loader=yaml.FullLoader)
        titleDict, nameDict, copyAccountDict, copyPasswordDict = {}, {}, {}, {}
        counter, title_counter = 0, 0
        for index, (key, value) in enumerate(yaml_data.items()):
            # print(f"index:{index},counter:{counter}")
            titleDict[index] = ttk.Label(
                class_,
                text=key,
                style="Bold.TLabel"
            ).grid(row=counter+title_counter, column=1, padx=10, pady=5, sticky="nsew")
            title_counter += 1
            nameDict[index], copyAccountDict[index], copyPasswordDict[index] = {}, {}, {}
            if isinstance(value, dict):
                for index_1, (key_1, value_1) in enumerate(value.items()):
                    nameDict[index][index_1] = ttk.Label(
                        class_,
                        text=key_1,
                        style="Bold.Label"
                    ).grid(row=+title_counter+counter, column=0, padx=10, pady=5, sticky="nsew")
                    # print(f"    index_1:{index_1},counter:{counter}")
                    copyAccountDict[index][index_1] = ttk.Button(
                        class_,
                        text="複製帳號",
                        command=lambda
                        data=value_1["account"]: self.methods.copyClipboard(data)
                    ).grid(row=+title_counter+counter, column=1, padx=10, pady=5, sticky="nsew")
                    copyPasswordDict[index][index_1] = ttk.Button(
                        class_,
                        text="複製密碼",
                        command=lambda
                        data=value_1["password"]: self.methods.copyClipboard(data)
                    ).grid(row=+title_counter+counter, column=2, padx=10, pady=5, sticky="nsew")
                    counter += 1
            else:
                print(f"None Value: {value}")

    def __creatMenu(self,class_:tk.Toplevel):
        menubar = ttk.Menu(class_)

        filemenu = ttk.Menu(menubar)
        menubar.add_cascade(label="檔案(F)", menu=filemenu)
        filemenu.add_command(label="生成明文", command=self.methods.decrypt_Yaml)
        filemenu.add_command(label="加密明文", command=self.methods.encrypt_Yaml)
        filemenu.add_command(label="刪除明文", command=self.methods.delete_Yaml)

        filemenu.add_separator()
        filemenu.add_command(label="退出(E)", command=self.__on_closing)

        #editmenu = ttk.Menu(menubar)
        #menubar.add_cascade(label="編輯(E)", menu=editmenu)
        #editmenu.add_command(label="尋找", command=self.methods.Find)

        #viewmenu = ttk.Menu(menubar)
        #menubar.add_cascade(label="檢視(V)", menu=viewmenu)
        #viewmenu.add_command(label="隱藏/顯示密碼", command=self.methods.Showhide)

        class_.config(menu=menubar)

if __name__ == "__main__":
    app = App()
    app.run()
    

    
