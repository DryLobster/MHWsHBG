from collections import defaultdict
from src.core.loader import GEM_DATA
import json
import platform
from pathlib import Path

def get_app_data_path() -> Path:
    """获取跨平台的应用数据目录"""
    system = platform.system()
    if system == "Windows":
        path = Path.home() / "AppData/Local/MHW_Damage_Calculator"
    elif system == "Darwin":  # macOS
        path = Path.home() / "Library/Application Support/MHW_Damage_Calculator"
    else:  # Linux
        path = Path.home() / ".local/share/MHW_Damage_Calculator"
    
    path.mkdir(parents=True, exist_ok=True)
    return path

class GemInventory:

    SAVE_FILE = get_app_data_path() / "gem_inventory.json"

    def __init__(self):
        self.weapon_gems = defaultdict(int)  # 武器镶嵌槽的珠子
        self.equip_gems = defaultdict(int)   # 装备镶嵌槽的珠子
        self.load()  # 启动时自动读取存档

    def save(self):
        """自动存档（每次操作后调用）"""
        data = {
            "weapon_gems": dict(self.weapon_gems),
            "equip_gems": dict(self.equip_gems)
        }
        with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
    def load(self):
        """读取存档"""
        try:
            if self.SAVE_FILE.exists():
                with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.weapon_gems = defaultdict(int, data.get("weapon_gems", {}))
                self.equip_gems = defaultdict(int, data.get("equip_gems", {}))
        except Exception as e:
            print(f"读取存档失败: {e}，将使用默认库存")

    def add_gem(self, gem_name: str, count: int=1):
        gem_data = GEM_DATA.get(gem_name)
        if not gem_data:
            raise ValueError(f"未知的宝珠: {gem_name}")
            
        if gem_data['type'] == 'weapon':
            self.weapon_gems[gem_name] += count
        else:
            self.equip_gems[gem_name] += count

        self.save()  # 新增
            
    def remove_gem(self, gem_name: str):
        gem_data = GEM_DATA.get(gem_name)
        if not gem_data:
            return False
        
        # 根据类型确定要操作的字典
        target_dict = self.weapon_gems if gem_data['type'] == 'weapon' else self.equip_gems
        
        if target_dict[gem_name] > 0:
            target_dict[gem_name] -= 1
            # 自动清理数量为0的条目（修复变量名）
            if target_dict[gem_name] == 0:  # 改为操作target_dict
                del target_dict[gem_name]
            self.save()  # 新增
            return True
        return False
    
    def remove_all_gems(self):
        self.weapon_gems = defaultdict(int)
        self.equip_gems = defaultdict(int)
        
        self.save()  # 新增

    def get_all_gems(self):
        """合并武器和装备的珠子"""
        combined = {}
        # 合并武器珠子
        for gem, count in self.weapon_gems.items():
            combined[gem] = combined.get(gem, 0) + count
        # 合并装备珠子
        for gem, count in self.equip_gems.items():
            combined[gem] = combined.get(gem, 0) + count
        print(f"合并后的库存数据: {combined}")  # 调试输出
        return dict(sorted(combined.items()))

    def get_count(self, gem_name: str) -> int:
        """根据珠子名称自动判断类型并返回库存数量"""
        # 先检查武器珠子库
        if gem_name in self.weapon_gems:
            return self.weapon_gems[gem_name]
        # 再检查装备珠子库
        elif gem_name in self.equip_gems:
            return self.equip_gems[gem_name]
        # 都不存在则返回0
        return 0
    
    def consume_gems(self, gem_list: list):
        temp_weapon = defaultdict(int, self.weapon_gems)
        temp_equip = defaultdict(int, self.equip_gems)
        
        for gem_name in gem_list:
            gem_data = GEM_DATA[gem_name]
            if gem_data['type'] == 'weapon':
                if temp_weapon[gem_name] <= 0:
                    return False
                temp_weapon[gem_name] -= 1
            else:
                if temp_equip[gem_name] <= 0:
                    return False
                temp_equip[gem_name] -= 1
        return True
