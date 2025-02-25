
from abc import ABC, abstractmethod
import types
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from .models import Character  # 仅用于类型提示

class SkillEffect(ABC):
    """技能效果抽象基类"""
    @abstractmethod
    def apply_effect(self, 
                    character: 'Character',
                    context: Dict[str, Any]) -> Dict[str, float]:
        """
        参数:
            context: 包含计算上下文信息，如：
                - weapon_type: 武器类型
                - ammo_type: 弹药类型
                - attack_sequence: 攻击动作序列
                - monster_status: 怪物状态
        返回:
            需要修改的数值字典，如 {'attack_multiplier': 0.1}
        """
        pass

class Skill:
    """技能实体类"""
    def __init__(self, 
                 name: str,
                 max_level: int,
                 effects: Dict[int, SkillEffect],
                 condition: Optional['SkillCondition'] = None,
                 has_coverage: bool = False):
        self.name = name
        self.max_level = max_level
        self.effects = effects
        self.condition = condition
        self.has_coverage = has_coverage
        
        # 为每个效果添加技能名引用
        for level, effect in self.effects.items():
            effect.skill_name = name  # 动态添加属性


class SkillCondition(ABC):
    """技能触发条件抽象类"""
    @abstractmethod
    def check(self, context: Dict[str, Any]) -> bool:
        pass

# ===== 工厂函数直接放在同文件 =====
def create_effect(effect_data: dict) -> SkillEffect:
    effect_type = effect_data.pop('type')
    
    # 本地类映射（无需导入）
    effect_classes: Dict[str, types[SkillEffect]] = {
        'None': NoneEffect,
        'BuffAttackBoost': BuffAttackBoostEffect,
        'AttackBoost': AttackBoostEffect,
        'CriticalEye': CriticalEyeEffect,
        'IndependentBoost': IndependentBoostEffect,
        'CriticalBoost': CriticalBoostEffect,
        'CriticalElement': CriticalElementEffect,
        'ElementBoost': ElementBoostEffect,
        'WeaknessExploit': WeaknessExploitEffect,
        'Agitator': ChallengerEffect,
        'AttackCrit':AttckCritEffect,
        'AmmoTypeBoost': AmmoTypeBoostEffect,
        'Artillery': ArtilleryEffect,
        'FirstShot': FirstShotEffect,
        'AssaultShot': AssaultShotEffect,
        'Burst': BurstEffect,
        'Virus': VirusEffect,
        'Muga': MugaEffect,
        'ChainBlade': ChainBladeEffect,
        # 其他效果类...
    }
    
    return effect_classes[effect_type](**effect_data)

# ===== 具体效果实现样例 =====
class NoneEffect(SkillEffect):
    """无攻击效果（查表版）"""
    def __init__(self):
        return
    def apply_effect(self, character, context):
        
        return {
        }
class BuffAttackBoostEffect(SkillEffect):
    """攻击力提升效果（查表版）"""
    def __init__(self, multiplier: float, addition: int):
        self.multiplier = multiplier  # 直接存储当前等级对应的百分比加成
        self.addition = addition      # 直接存储当前等级对应的固定值加成

    def apply_effect(self, character, context):
        
        return {
            'attack_multiplier': self.multiplier,
            'attack_additions': self.addition
        }
class AttackBoostEffect(SkillEffect):
    """攻击力提升效果（查表版）"""
    def __init__(self, multiplier: float, addition: int):
        self.multiplier = multiplier  # 直接存储当前等级对应的百分比加成
        self.addition = addition      # 直接存储当前等级对应的固定值加成

    def apply_effect(self, character, context):
        # 获取覆盖率（默认为1.0）
        coverage = character.coverage_rates.get(self.skill_name, 1.0)  # 需要关联技能名
        
        return {
            'attack_multiplier': self.multiplier * coverage,
            'attack_additions': self.addition * coverage
        }

class CriticalEyeEffect(SkillEffect):
    """看破技能（查表版）"""
    def __init__(self, affinity: int):
        self.affinity = affinity  # 直接存储当前等级对应的会心率数值

    def apply_effect(self, character, context):
        # 获取覆盖率（默认为1.0）
        coverage = character.coverage_rates.get(self.skill_name, 1.0)  # 需要关联技能名
        return {'affinity_buffs': self.affinity * coverage}
    
class IndependentBoostEffect(SkillEffect):
    """独立乘区提升效果（查表版）"""
    def __init__(self, physical_boost: float, element_boost: float):
        self.physical_boost = physical_boost
        self.element_boost = element_boost

    def apply_effect(self, character, context):
        # 获取覆盖率（默认为1.0）
        coverage = character.coverage_rates.get(self.skill_name, 1.0)  # 需要关联技能名
        
        return {
            'independent_physical': self.physical_boost * coverage,
            'independent_element': self.element_boost * coverage
        }
    
class CriticalBoostEffect(SkillEffect):
    """超会心效果（直接查表版）"""
    def __init__(self, value: float):
        self.value = value  # 直接存储当前等级对应的数值
        
    def apply_effect(self, character, context):
        return {
            'crit_damage_physical_buffs': self.value,
            'crit_damage_element_buffs': 0  # 根据实际需求可调整属性加成
        }
class CriticalElementEffect(SkillEffect):
    """超会心效果（直接查表版）"""
    def __init__(self, value: float):
        self.value = value  # 直接存储当前等级对应的数值
        
    def apply_effect(self, character, context):
        return {
            'crit_damage_physical_buffs': 0,
            'crit_damage_element_buffs': self.value  # 根据实际需求可调整属性加成
        }
class ElementBoostEffect(SkillEffect):
    """属性强化效果（火/水/雷/冰/龙属性强化）"""
    def __init__(self, multiplier: float = 0.0, addition: int = 0):
        self.multiplier = multiplier  # 属性倍率加成
        self.addition = addition      # 属性值固定加成

    def apply_effect(self, character, context):
        return {
            'element_multipliers': self.multiplier,
            'element_additions': self.addition
        }
class WeaknessExploitEffect(SkillEffect):
    """弱点特效（根据肉质和伤口状态提供会心）"""
    def __init__(self, phys_affinity: int, scar_affinity: int):
        self.phys_affinity = phys_affinity  # 肉质条件提供的会心
        self.scar_affinity = scar_affinity  # 伤口条件提供的会心

    def apply_effect(self, character, context):
        monster_status = context.get('monster_status', {})
        
        affinity = 0
        # 肉质条件判断
        if monster_status.get('phys_hitzone', 0) >= 45:
            affinity += self.phys_affinity
        
        # 伤口条件判断
        if monster_status.get('scar', False):
            affinity += self.scar_affinity
            
        return {'affinity_buffs': affinity} if affinity > 0 else {}
class ChallengerEffect(SkillEffect):
    """挑战者效果（怪物生气时生效）"""
    def __init__(self, attack_add: int, affinity_add: int):
        self.attack_add = attack_add
        self.affinity_add = affinity_add
        
    def apply_effect(self, character, context):
        # 从上下文中获取怪物状态
        monster_status = context.get('monster_status', {})
        if monster_status.get('enraged', False):
            return {
                'attack_additions': self.attack_add,
                'affinity_buffs': self.affinity_add
            }
        return {}
class AttckCritEffect(SkillEffect):
    """挑战者效果（怪物生气时生效）"""
    def __init__(self, attack_add: int, affinity_add: int):
        self.attack_add = attack_add
        self.affinity_add = affinity_add
        
    def apply_effect(self, character, context):
        # 获取覆盖率（默认为1.0）
        coverage = character.coverage_rates.get(self.skill_name, 1.0)  # 需要关联技能名
        return {
            'attack_additions': self.attack_add * coverage,
            'affinity_buffs': self.affinity_add * coverage
        }

class AmmoTypeBoostEffect(SkillEffect):
    """弹药类型强化效果"""
    def __init__(self, ammo_type: str, physical_boost: float, element_boost: float):
        self.ammo_type = ammo_type
        self.physical_boost = physical_boost
        self.element_boost = element_boost
        
    def apply_effect(self, character, context):
        # 从上下文中获取当前弹药类型
        current_ammo_type = context.get('ammo_type')
        
        # 类型匹配时应用加成
        if current_ammo_type == self.ammo_type:
            return {
                'independent_physical': self.physical_boost,
                'independent_element': self.element_boost
            }
        return {}
class ArtilleryEffect(SkillEffect):
    """炮术效果"""
    def __init__(self, physical_boost: float, element_boost: float):
        self.physical_boost = physical_boost
        self.element_boost = element_boost
        
    def apply_effect(self, character, context):
        
        # 类型匹配时应用加成
        if context.get('ignore_hitzone') == True:
            return {
                'independent_physical': self.physical_boost,
                'independent_element': self.element_boost
            }
        return {}
class FirstShotEffect(SkillEffect):
    """首发射击强化效果"""
    def __init__(self, reload_boost: int, physical_boost: float, element_boost: float):
        self.reload_boost = reload_boost
        self.physical_boost = physical_boost
        self.element_boost = element_boost
        
    def apply_effect(self, character, context):
        
        # 类型匹配时应用加成
        if (context.get('bullet_position') == 1 and context.get('ammo_type') != "special"):
            return {
                'reload_reduces': self.reload_boost,
                'independent_physical': self.physical_boost,
                'independent_element': self.element_boost
            }
        return {'reload_reduces': self.reload_boost}
class AssaultShotEffect(SkillEffect):
    """强四射击强化效果"""
    def __init__(self, attack_boost: int, affinity_boost: int, amazing_boost: int):
        self.attack_boost = attack_boost
        self.affinity_boost = affinity_boost
        self.amazing_boost = amazing_boost
        
    def apply_effect(self, character, context):
        
        affinity = 0
        attack = 0

        # 类型匹配时应用加成
        if (context.get('bullet_position') >= 4 and context.get('ammo_type') != "special"):
            
            affinity += self.affinity_boost

        if ((context.get('bullet_position') == 4 or context.get('bullet_position') == 6) and context.get('ammo_type') != "special"):

            attack += self.attack_boost

        return {
            'attack_additions': attack,
            'affinity_buffs': affinity
        }
    
class BurstEffect(SkillEffect):
    """连击强化效果"""
    def __init__(self, attack_boost: int, element_boost: int):
        self.attack_boost = attack_boost
        self.element_boost = element_boost
        
    def apply_effect(self, character, context):
        coverage = character.coverage_rates.get(self.skill_name, 1.0)  # 需要关联技能名
        burst_boost_level = character.get_skill_level("连击强化")
        # 类型匹配时应用加成
        if (burst_boost_level == 1):
            self.attack_boost += 3 
        elif (burst_boost_level == 2):
            self.attack_boost += 10
        return {
            'attack_additions': self.physical_boost * coverage,
            'element_additions': self.element_boost * coverage
        }
class ChainBladeEffect(SkillEffect):
    """锁刃刺击强化效果"""
    def __init__(self, addtional_damage: int):
        self.addtional_damage = addtional_damage
        
    def apply_effect(self, character, context):
        return {

        }
    
class MugaEffect(SkillEffect):
    """无我之境强化效果"""
    def __init__(self, affinity: int):
        self.affinity = affinity
        
    def apply_effect(self, character, context):

        # 类型匹配时应用加成
        if (character.virus == "2"):
            return {
                'affinity_buffs': self.affinity
            }
        return {}
    
class VirusEffect(SkillEffect):
    """黑丝一体强化效果"""
    def __init__(self, attack_1: int, attack_2: int):
        self.attack_1 = attack_1
        self.attack_2 = attack_2
        
    def apply_effect(self, character, context):

        # 类型匹配时应用加成
        if (character.virus == "1"):
            return {
                'attack_additions': self.attack_1
            }
        if (character.virus == "2"):
            return {
                'attack_additions': self.attack_2
            }
        return {}
    
class ConditionalEffect(SkillEffect):
    """条件触发效果基类"""
    def __init__(self, base_effect: SkillEffect, condition: SkillCondition):
        self.base_effect = base_effect
        self.condition = condition

    def apply_effect(self, character, context):
        if self.condition.check(context):
            return self.base_effect.apply_effect(character, context)
        return {}

# ===== 具体条件实现样例 ===== 
class HealthCondition(SkillCondition):
    """血量条件"""
    def __init__(self, threshold: float, is_above: bool = True):
        self.threshold = threshold
        self.is_above = is_above  # True表示高于阈值触发

    def check(self, context):
        health = context.get('character_health', 1.0)
        return (health >= self.threshold) if self.is_above else (health < self.threshold)

class WeaponTypeCondition(SkillCondition):
    """武器类型条件"""
    def __init__(self, weapon_types: list):
        self.weapon_types = weapon_types

    def check(self, context):
        return context.get('weapon_type') in self.weapon_types
