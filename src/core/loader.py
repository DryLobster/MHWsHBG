# src/core/loader.py
import json
from pathlib import Path
import shutil
from typing import Dict, Any
from .skills import Skill, create_effect
from ..utils.path_manager import get_app_data_dir, get_base_data_dir, get_data_path  # 新增路径管理
from typing import Dict, Any
from .skills import Skill, create_effect  # 现在直接从skills导入

BUFF_DATA = {}

# 新增装填和后坐力等级对应表（放在BUFF_DATA下方）
RELOAD_LEVEL_MAP = {
    '0': 1.3,
    '1': 2.2,
    '2': 2.4,
    '3': 3.3
}

RECOIL_LEVELS = []          # 按id顺序存储的完整数据
RECOIL_NAME_TO_ID = {}      # 名称到id的映射
RECOIL_ID_TO_DATA = {}      # id到数据的快速访问

GEM_DATA = {}

def load_recoil_modifiers():
    global RECOIL_LEVELS, RECOIL_NAME_TO_ID, RECOIL_ID_TO_DATA
    
    # 修改为动态获取路径
    data_file = get_data_path("recoil_data.json")

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    #with open('data/recoil_data.json', 'r', encoding='utf-8') as f:
        #data = json.load(f)
        
        # 清空旧数据
        RECOIL_LEVELS.clear()
        RECOIL_NAME_TO_ID.clear()
        RECOIL_ID_TO_DATA.clear()
        
        # 按id排序后加载
        for entry in sorted(data['recoil_levels'], key=lambda x: x['id']):
            # 数据校验
            if entry['id'] in RECOIL_ID_TO_DATA:
                raise ValueError(f"重复的recoil id: {entry['id']}")
            if entry['name'] in RECOIL_NAME_TO_ID:
                raise ValueError(f"重复的recoil名称: {entry['name']}")
            
            # 转换数据类型
            processed = {
                'id': int(entry['id']),
                'name': str(entry['name']),
                'normal': float(entry['normal']),
                'rapid': float(entry['rapid'])
            }
            
            # 存储到全局变量
            RECOIL_LEVELS.append(processed)
            RECOIL_NAME_TO_ID[processed['name']] = processed['id']
            RECOIL_ID_TO_DATA[processed['id']] = processed
class Buff:
    def __init__(self, name, effect, category="其他增益", description=""):
        self.name = name
        self.effect = effect
        self.category = category
        self.description = description

def load_buff_data():

    global BUFF_DATA
    # 修改为动态路径
    data_file = get_data_path("buff_data.json")

    with open(data_file, 'r', encoding='utf-8') as f:
    #with open('data/buff_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        for buff in data['buffs']:
            effect = create_effect(buff['effect'])
            BUFF_DATA[buff['name']] = Buff(
                name=buff['name'],
                effect=effect,
                category=buff.get('category', '其他增益'),
                description=buff.get('description', '')
            )

def load_skill_data():
    # 修改为动态路径
    data_file = get_data_path("skills.json")

    try:
        with open(data_file, 'r', encoding='utf-8', errors='strict') as f:
        #with open('data/skills.json', 'r', encoding='utf-8', errors='strict') as f:
            data = json.load(f)
    except FileNotFoundError:
        #raise Exception("技能文件未找到，请确认data/skills.json存在")
        raise Exception(f"技能文件未找到，路径：{data_file}")
    #except UnicodeDecodeError as e:
        #raise Exception(f"文件编码错误: {str(e)}")
    
    skills = {}
    for s in data['skills']:
        effects = {
            int(level): create_effect(effect_data)
            for level, effect_data in s['effects'].items()
        }
        
        # 新增has_coverage字段解析
        has_coverage = s.get('has_coverage', False)  # 默认False
        
        skills[s['name']] = Skill(
            name=s['name'],
            max_level=s['max_level'],
            effects=effects,
            has_coverage=has_coverage  # 添加新参数
        )
    return skills

SKILL_DATA = load_skill_data()

def load_gem_data():
    global GEM_DATA

    # 修改为动态路径
    data_file = get_data_path("gem_data.json")

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
        #with open('data/gem_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            GEM_DATA.clear()
            
            for gem in data['gems']:
                # 基础校验
                if gem['type'] not in ['weapon', 'equip']:
                    raise ValueError(f"无效的宝珠类型: {gem['type']}")
                if gem['level'] < 1 or gem['level'] > 3:
                    raise ValueError(f"无效的孔位等级: {gem['level']}")
                
                # 构建技能数据（允许skill_2为空）
                skills = []
                if gem['skill_1']:
                    if gem['skill_1'] not in SKILL_DATA:
                        raise ValueError(f"未定义的技能: {gem['skill_1']}")
                    skills.append((
                        gem['skill_1'],
                        gem['skill_1_level']
                    ))
                if gem.get('skill_2'):  # 第二个技能可选
                    if gem['skill_2'] not in SKILL_DATA:
                        raise ValueError(f"未定义的技能: {gem['skill_2']}")
                    skills.append((
                        gem['skill_2'],
                        gem['skill_2_level']
                    ))
                
                # 存储到全局数据
                GEM_DATA[gem['name']] = {
                    'name': gem['name'],
                    'type': gem['type'],
                    'level': gem['level'],
                    'skills': skills
                }
                
    except FileNotFoundError:
        raise Exception(f"宝珠数据文件未找到，路径：{data_file}")
        #raise Exception("宝珠数据文件未找到，请确认data/gem_data.json存在")

# 新增：初始化用户数据目录
def init_user_data():
    """将默认数据复制到用户目录（首次运行）"""
    user_dir = get_app_data_dir()
    default_files = [
        "recoil_data.json",
        "buff_data.json",
        "skills.json",
        "gem_data.json",
        "ammo_data.json"
    ]
    
    for file_name in default_files:
        src = get_base_data_dir() / file_name
        dst = user_dir / file_name
        if not dst.exists() and src.exists():
            shutil.copy(src, dst)

# 在模块初始化时执行
init_user_data()


# 新增BUFF相关
load_buff_data()
load_gem_data()

