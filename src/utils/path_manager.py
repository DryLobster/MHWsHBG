import sys
import platform
from pathlib import Path

def get_app_data_dir() -> Path:
    """获取跨平台的应用数据目录（用户可修改数据存放处）"""
    system = platform.system()
    if system == "Windows":
        path = Path.home() / "AppData/Local/MHW_Damage_Calculator"
    elif system == "Darwin":  # macOS
        path = Path.home() / "Library/Application Support/MHW_Damage_Calculator"
    else:  # Linux
        path = Path.home() / ".local/share/MHW_Damage_Calculator"
    
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_base_data_dir() -> Path:
    """获取基础数据目录（打包后的默认数据）"""
    if getattr(sys, 'frozen', False):  # 打包环境
        return Path(sys.executable).parent / "data"
    else:  # 开发环境
        return Path(__file__).parent.parent.parent / "data"  # 根据实际结构调整

def get_data_path(file_name: str) -> Path:
    """优先返回用户修改后的数据路径"""
    user_data = get_app_data_dir() / file_name
    default_data = get_base_data_dir() / file_name
    
    # 优先使用用户自定义数据
    if user_data.exists():
        return user_data
    # 否则使用默认数据
    return default_data