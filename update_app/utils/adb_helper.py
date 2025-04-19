import subprocess

class ADBHelper:
    @staticmethod
    def execute_command(cmd):
        """执行ADB命令"""
        try:
            process = subprocess.run(
                ["adb"] + cmd,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            return process
        except Exception as e:
            raise Exception(f"ADB命令执行失败: {str(e)}")
            
    def push_file(self, src_path, dest_path):
        """推送文件到设备"""
        return self.execute_command(["push", src_path, dest_path])
        
    def pull_file(self, src_path, dest_path):
        """从设备拉取文件"""
        return self.execute_command(["pull", src_path, dest_path])
        
    def reboot(self):
        """重启设备"""
        return self.execute_command(["reboot"])