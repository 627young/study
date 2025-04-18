## 打包python脚本为exe文件
### 1. 安装pyinstaller
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
### 2. 使用pyinstaller打包脚本
python -m PyInstaller --onefile --windowed --name "xxx"  --icon "xxx.ico" xxx.py --distpath "xxx" 
例如：
python -m PyInstaller --onefile --windowed --name "升级工具" --icon "./icon.jpg" main.py --distpath "./dist"

### 3. 打包后的exe文件会在distpath指定目录下