
from ast import Dict
from collections import defaultdict
from venv import logger

class Character:
    def __init__(self,
                 bullet_level, 
                 magazine, 
                 enrage_ratio,
                 bullet_position=1, 
                 ):
        self.skills: Dict[str, int] = {}  # 技能名到等级的映射
        # 攻击力计算
        self.attack_multipliers = []  # 改为列表存储各乘算因子
        self.attack_additions = []    # 改为列表存储各加算值
        
        # 属性计算
        self.element_multipliers = []
        self.element_additions = []
        
        # 会心系统
        self.affinity_buffs = []      # 存储所有会心率加成来源
        self.crit_damage_physical_buffs = []
        self.crit_damage_element_buffs = []
        self.crit_damage_physical = 1.25  # 物理会心倍率基准
        self.crit_damage_element = 1.0    # 属性会心倍率基准

        # 子弹等级
        self.bullet_level = bullet_level
        self.magazine = magazine
        self.bullet_position = bullet_position
        self.enrage_ratio = enrage_ratio

        self.reload_reduces = []
        self.recoil_reduces = []

        self.laser_hit = 10
        self.laser_multiplier = 1

        self.gem_num_3 = 0
        self.gem_num_2 = 0
        self.gem_num_1 = 0

        self.virus = "0"

        # 独立乘区系统
        self.independent_modifiers = {
            'physical': [],
            'element': []
        }

        self.active_buffs = set()  # 新增：存储激活的BUFF名称

        self.coverage_rates = {}  # 新增：存储技能覆盖率 {技能名: 覆盖率}

    def set_coverages(self, coverages: dict):
        """设置技能覆盖率（DPS计算时调用）"""
        self.coverage_rates = coverages

    def reset_coverages(self):
        """重置技能覆盖率（单发计算时调用）"""
        self.coverage_rates = {}
    
    def add_buff(self, buff_name: str):
        """添加BUFF"""
        self.active_buffs.add(buff_name)
        
    def remove_buff(self, buff_name: str):
        """移除BUFF"""
        self.active_buffs.discard(buff_name)

    def get_buff_effects(self, context: dict) -> dict:
        """获取BUFF效果（与技能效果结构相同）"""
        from .loader import BUFF_DATA
        effects = defaultdict(list)
        for buff_name in self.active_buffs:
            buff = BUFF_DATA.get(buff_name)  # 获取Buff对象
            if buff:
                # 关键修改：调用buff.effect的apply_effect
                effect_values = buff.effect.apply_effect(self, context)
                for k, v in effect_values.items():
                    effects[k].append(v)
        return effects


    def add_skill(self, skill_name: str, level: int):
        from .loader import SKILL_DATA  # 延迟导入
        max_level = SKILL_DATA[skill_name].max_level
        self.skills[skill_name] = min(level, max_level)

    def get_skill_level(self, skill_name: str):
        return self.skills.get(skill_name, 0)

    def get_active_effects(self, context: dict) -> dict:
        from .loader import SKILL_DATA  # 延迟导入
        effects = defaultdict(list)
        for skill_name, level in self.skills.items():
            # 新增等级检查
            if level <= 0:  # 包含0和负数的情况
                continue
                
            skill = SKILL_DATA[skill_name]
            effect = skill.effects.get(level)
            
            # 防御性编程：处理等级超出技能定义的情况
            if not effect:
                continue
                
            effect_values = effect.apply_effect(self, context)
            for k, v in effect_values.items():
                effects[k].append(v)
        return effects

    def apply_skill_effects(self, context: dict):
        """修改后的方法：同时应用技能和BUFF"""
        # 清空旧加成
        self._reset_bonuses()
        
        # 应用技能效果
        skill_effects = self.get_active_effects(context)
        self._apply_effects(skill_effects)
        
        # 应用BUFF效果
        buff_effects = self.get_buff_effects(context)
        self._apply_effects(buff_effects)

    def _reset_bonuses(self):
        """重置所有加成（保留键结构）"""
        self.attack_multipliers.clear()
        self.attack_additions.clear()
        self.element_multipliers.clear()
        self.element_additions.clear()
        self.affinity_buffs.clear()
        self.crit_damage_physical_buffs.clear()
        self.crit_damage_element_buffs.clear()
        self.recoil_reduces.clear()
        self.reload_reduces.clear()
        
        # 仅清空列表内容，保留键
        self.independent_modifiers['physical'].clear()
        self.independent_modifiers['element'].clear()

        
    def _apply_effects(self, effects: dict):
        """带防御性编程的最终版"""
        # 类型检查确保输入合法
        if not isinstance(effects, dict):
            raise TypeError(f"Effects must be dict, got {type(effects)}")
        
        # 调试日志记录原始效果
        logger.debug(f"Applying effects: {effects}")

        # 策略处理器（实际项目可提取为类常量）
        EFFECT_HANDLERS = {
            'attack_multiplier': self._handle_attack_multiplier,
            'attack_additions': self._handle_attack_addition,
            'element_multipliers': self._handle_element_multiplier,
            'element_additions': self._handle_element_addition,
            'affinity_buffs': self._handle_affinity_buff,
            'crit_damage_physical_buffs': self._handle_crit_physical,
            'crit_damage_element_buffs': self._handle_crit_element,
            'recoil_reduces': self._handle_recoil_reduce,
            'reload_reduces': self._handle_reload_reduce,
            'independent_physical': self._handle_independent_physical,
            'independent_element': self._handle_independent_element
        }

        for effect_type, values in effects.items():
            # 跳过无效类型
            if effect_type not in EFFECT_HANDLERS:
                logger.warning(f"Unknown effect type: {effect_type}")
                continue
                
            # 跳过空值
            if not isinstance(values, (list, tuple)) or len(values) == 0:
                continue
                
            # 调用处理器
            try:
                EFFECT_HANDLERS[effect_type](values)
            except Exception as e:
                logger.error(f"Error applying {effect_type}: {str(e)}")
                raise

    # 具体处理器方法（在Character类内部）
    def _handle_attack_multiplier(self, values):
        self.attack_multipliers.extend(float(v) for v in values)

    def _handle_attack_addition(self, values):
        self.attack_additions.extend(int(v) for v in values)

    def _handle_element_multiplier(self, values):
        self.element_multipliers.extend(float(v) for v in values)

    def _handle_element_addition(self, values):
        self.element_additions.extend(int(v) for v in values)

    def _handle_affinity_buff(self, values):
        self.affinity_buffs.extend(int(v) for v in values)

    def _handle_crit_physical(self, values):
        self.crit_damage_physical_buffs.extend(float(v) for v in values)

    def _handle_crit_element(self, values):
        self.crit_damage_element_buffs.extend(float(v) for v in values)

    def _handle_recoil_reduce(self, values):
        self.recoil_reduces.extend(float(v) for v in values)

    def _handle_reload_reduce(self, values):
        self.reload_reduces.extend(float(v) for v in values)

    def _handle_independent_physical(self, values):
        self.independent_modifiers['physical'].extend(float(v) for v in values)

    def _handle_independent_element(self, values):
        self.independent_modifiers['element'].extend(float(v) for v in values)
    


class Weapon:
    def __init__(self, name, base_attack, affinity, reload_level, weapon_type="heavy_bowgun"):
        self.name = name
        self.base_attack = base_attack  # 应包含武器基础+客制化加成
        self.affinity = affinity        # 会心率(-30表示-30%)
        self.weapon_type = weapon_type  # 新增武器类型标识
        self.reload_level = reload_level  # 新增武器重载等级
        
        self.bowgun_type:int

        self.gear_1 = ""
        self.gear_2 = ""

        self.gem_size_1 = 3
        self.gem_size_2 = 2
        self.gem_size_3 = 1
        
class Ammo:
    def __init__(self, 
                name: str,
                type:str,
                physical_mv, 
                element_mv, 
                physical_mv_multiplier: dict, 
                element_mv_multiplier: dict,
                hit: dict,
                physical_mv_add: dict,
                element_mv_add: dict,
                max_level: int, 
                recoil,
                reload_level: int,
                ignore_hitzone=False,
                modifiers: dict = None   # 独立乘区改为统一字段
                ):
        self.name = name
        self.type = type
        self.physical_mv = physical_mv  # 物理动作值 
        self.element_mv = element_mv    # 属性动作值
        self.physical_mv_multiplier = physical_mv_multiplier # 物理动作值乘数
        self.element_mv_multiplier = element_mv_multiplier # 属性动作值乘数
        self.physical_mv_add = physical_mv_add # 物理动作值乘数
        self.element_mv_add = element_mv_add # 属性动作值乘数
        self.hit = hit # 伤害次数
        self.max_level = max_level     # 最大等级
        self.recoil = recoil
        self.reload_level = reload_level
        self.ignore_hitzone = ignore_hitzone  # 是否无视肉质
        self.modifiers = modifiers or {
            'physical': 1.0,
            'element': 1.0
        }

class Monster:
    def __init__(self, 
                 name, 
                 phys_hitzone, 
                 elem_hitzone, 
                 scar:bool,
                 enrage_multiplier,
                 enraged: bool = False  # 新增生气状态标识
                 ):
        self.name = name
        self.physical_hitzone = phys_hitzone
        self.element_hitzone = elem_hitzone
        self.scar = scar
        self.enrage_multiplier = enrage_multiplier
        self.enraged = enraged  # 当前是否处于生气状态

