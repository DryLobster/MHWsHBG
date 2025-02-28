import math


class DamageCalculator:
    def __init__(self, 
                 character, 
                 weapon, 
                 ammo, 
                 monster, 
                 dps_mode=False):  # 新增参数
        self.character = character
        self.weapon = weapon
        self.ammo = ammo
        self.monster = monster
        self.dps_mode = dps_mode  # 新增属性

    def _calculate_attack(self):
        # 乘算部分（1 + 所有百分比加成之和）
        attack_multiplier = 1.0 + sum(self.character.attack_multipliers)
        
        # 加算部分
        attack_addition = sum(self.character.attack_additions)
        
        # 最终攻击力 = (基础攻击 × 乘算系数 + 加算值) 四舍五入
        raw_attack = self.weapon.base_attack * attack_multiplier + attack_addition
        return round(raw_attack)  # 特殊舍入规则

    
    def _apply_independent_modifiers(self, base_damage, damage_type):
        """
        damage_type: 'physical' 或 'element'
        """
        # 叠加所有独立乘区（如炮术、弹道强化等）
        modifiers = self.ammo.modifiers.get(damage_type, 1.0)
        for mod in self.character.independent_modifiers[damage_type]:
            modifiers *= mod
        return base_damage * modifiers
    
    def _calculate_crit(self):
        """改进后的会心计算逻辑"""
        # 总合会心率（限制在-100%~100%）
        total_affinity = self.weapon.affinity + sum(self.character.affinity_buffs)
        affinity = max(-100, min(100, total_affinity)) / 100.0  # 转为小数形式

        # 物理会心倍率计算（包含负会心处理）
        base_phys_crit = self.character.crit_damage_physical
        phys_crit_multiplier = base_phys_crit + sum(self.character.crit_damage_physical_buffs)
        
        # 属性会心倍率计算
        base_elem_crit = self.character.crit_damage_element
        elem_crit_multiplier = base_elem_crit + sum(self.character.crit_damage_element_buffs)

        # 分解会心概率
        if affinity >= 0:
            positive_rate = affinity
            negative_rate = 0.0
        else:
            positive_rate = 0.0
            negative_rate = -affinity  # 取绝对值

        normal_rate = 1 - positive_rate - negative_rate

        return {
            'positive_rate': positive_rate,
            'negative_rate': negative_rate,
            'normal_rate': normal_rate,
            'phys_multiplier': {
                'positive': phys_crit_multiplier,
                'negative': 0.75,  # 负会心固定75%
                'normal': 1.0
            },
            'elem_multiplier': {
                'positive': elem_crit_multiplier,
                'negative': 1.0,   # 属性不受负会心影响
                'normal': 1.0
            }
        }
    
    def calculate_fire_time(self):

        ammo_reload_multiplier = 1.0 + sum(self.character.reload_reduces)
        #weapon_reload = self.weapon.reload_level
        ammo_reload = self.ammo.reload_level

        #all_reload = 5 - weapon_reload + ammo_reload
        all_reload = ammo_reload
        if all_reload > 3:
            all_reload = 3

        recoil = self.ammo.recoil
        from src.core.loader import RECOIL_ID_TO_DATA, RELOAD_LEVEL_MAP
        recoil_interval_2 = RECOIL_ID_TO_DATA.get(str(recoil), {'normal': 1.0, 'rapid': 1.33})
        recoil_interval = recoil_interval_2['normal']
        if self.ammo.type == 'normal':
            recoil_interval = recoil_interval_2['rapid']

        reload_time = RELOAD_LEVEL_MAP[str(all_reload)]

        magazine = self.character.magazine

        whole_time = magazine * recoil_interval + reload_time / ammo_reload_multiplier

        return whole_time / magazine
    
    def calculate_fire_time_gatlin(self):
        return 7.2

    def calculate_fire_time_laser(self):
        return 1.7

    def calculate_bullet_damage(self, bullet_position, enraged=False):
        """计算单发子弹的伤害"""
        # 保存当前的怪物愤怒状态
        original_enraged = self.monster.enraged
        self.monster.enraged = enraged

        # 设置子弹位置
        self.character.bullet_position = bullet_position

        # 计算伤害
        damage = self.calculate_damage()

        # 恢复怪物愤怒状态
        self.monster.enraged = original_enraged

        return damage
    
    def calculate_magazine_damage(self, enraged=False):
        """计算整个弹匣的总伤害"""
        total_damage = 0
        for bullet_position in range(1, self.character.magazine + 1):
            bullet_damage = self.calculate_bullet_damage(bullet_position, enraged)
            total_damage += bullet_damage * self.ammo.hit.get(str(self.character.bullet_level - 1), 1)
        return total_damage
    
    def calculate_all_damage_for_dps(self):
        rage = True
        total_damage = 0
        total_damage += self.calculate_magazine_damage() * (1 - self.character.enrage_ratio) + self.calculate_magazine_damage(rage) * self.character.enrage_ratio

        return total_damage
    
    def calculate_dps(self):
        total_damage = self.calculate_all_damage_for_dps()
        dps = total_damage / self.calculate_fire_time() / self.character.magazine
        return dps

    def calculate_damage(self):
        # 构建技能生效上下文
        # 修正后的上下文结构
        context = {
            "ammo_type": self.ammo.type,  # 直接作为顶层键
            "ignore_hitzone": self.ammo.ignore_hitzone,
            "weapon_type": self.weapon.weapon_type,
            "bullet_position": self.character.bullet_position,
            "monster_status": {
                "phys_hitzone": self.monster.physical_hitzone,
                "scar": self.monster.scar,
                "enraged": self.monster.enraged
            }
        }
        # 在应用技能效果前处理覆盖率
        if not self.dps_mode:
            # 单发模式清空覆盖率
            self.character.skill_coverages = {}

        # 应用技能效果到角色属性
        self.character.apply_skill_effects(context)

        # 基础数值计算
        attack = self._calculate_attack()
        crit_data = self._calculate_crit()

        # 获取弹药等级相关参数
        level = str(self.character.bullet_level - 1)  # 转为0-based索引
        phys_mv = (
            self.ammo.physical_mv * self.ammo.physical_mv_multiplier.get(level, 1.0)
            + self.ammo.physical_mv_add.get(level, 0)
        )
        # 修改后（正确）：
        elem_basic = self.ammo.element_mv * self.ammo.element_mv_multiplier.get(level, 1.0)
        elem_limit = elem_basic * 1.9

        elem_mv = ( elem_basic
            * math.prod(1 + m for m in self.character.element_multipliers)  # 使用数学乘积
        )
        if elem_mv > 0:
            elem_mv += self.ammo.element_mv_add.get(level, 0)
            
            elem_add = sum(self.character.element_additions)
            if elem_add > 35:
                elem_add = 35

            elem_mv += elem_add # 确保加法在最后

            if elem_mv > elem_limit:
                elem_mv = elem_limit

        # 肉质处理
        phys_hitzone = 100 if self.ammo.ignore_hitzone else self.monster.physical_hitzone
        elem_hitzone = self.monster.element_hitzone

        bowgun_type_multiplier = 1
        if (self.weapon.bowgun_type < 0):
            bowgun_type_multiplier -= self.weapon.bowgun_type * 0.1

        # 物理基础伤害
        base_phys = attack / 100 * phys_mv * phys_hitzone / 100 * bowgun_type_multiplier
        if self.monster.enraged == True:
            base_phys *= self.monster.enrage_multiplier
        base_phys = self._apply_independent_modifiers(base_phys, 'physical')

        # 属性基础伤害
        base_elem = attack / 100 * elem_mv * elem_hitzone / 100 * bowgun_type_multiplier
        if self.monster.enraged == True:
            base_elem *= self.monster.enrage_multiplier
        base_elem = self._apply_independent_modifiers(base_elem, 'element')

        # 三种情况的伤害计算
        # 正常伤害
        normal_phys = base_phys * crit_data['phys_multiplier']['normal']
        normal_elem = base_elem * crit_data['elem_multiplier']['normal']
        normal_total = self._round_damage(normal_phys) + self._round_damage(normal_elem)

        # 正会心伤害
        crit_phys = base_phys * crit_data['phys_multiplier']['positive']
        crit_elem = base_elem * crit_data['elem_multiplier']['positive']
        crit_total = self._round_damage(crit_phys) + self._round_damage(crit_elem)

        # 负会心伤害
        negative_phys = base_phys * crit_data['phys_multiplier']['negative']
        negative_elem = base_elem * crit_data['elem_multiplier']['negative']
        negative_total = self._round_damage(negative_phys) + self._round_damage(negative_elem)

        # 期望伤害计算
        expected_damage = (
            normal_total * crit_data['normal_rate'] +
            crit_total * crit_data['positive_rate'] +
            negative_total * crit_data['negative_rate']
        )

        return expected_damage
    
    def calculate_dps_gatlin(self):
        damage = self.calculate_damage_gatlin()
        dps = damage * ((1 + 1.2 + 1.44 + 1.728) * 8 + 2.0736 * 32) / self.calculate_fire_time_gatlin()
        return dps
    
    def calculate_dps_laser(self):
        damage = self.calculate_damage_laser()
        dps = (damage * self.character.laser_multiplier + 2) * self.character.laser_hit / 1.7
        return dps

    def calculate_damage_gatlin(self):
        # 构建技能生效上下文
        # 修正后的上下文结构
        context = {
            "ammo_type": "special",  # 直接作为顶层键
            "ignore_hitzone": False,
            "weapon_type": self.weapon.weapon_type,
            "bullet_position": self.character.bullet_position,
            "monster_status": {
                "phys_hitzone": self.monster.physical_hitzone,
                "scar": self.monster.scar,
                "enraged": self.monster.enraged
            }
        }
        # 在应用技能效果前处理覆盖率
        if not self.dps_mode:
            # 单发模式清空覆盖率
            self.character.skill_coverages = {}

        # 应用技能效果到角色属性
        self.character.apply_skill_effects(context)

        # 基础数值计算
        attack = self._calculate_attack()
        crit_data = self._calculate_crit()

        # 获取弹药等级相关参数
        phys_mv = 9
        # 修改后（正确）：
        elem_mv = 0

        # 肉质处理
        phys_hitzone = 100 if self.ammo.ignore_hitzone else self.monster.physical_hitzone
        elem_hitzone = self.monster.element_hitzone

        bowgun_type_multiplier = 1
        if (self.weapon.bowgun_type > 0):
            bowgun_type_multiplier += self.weapon.bowgun_type * 0.1

        # 物理基础伤害
        base_phys = attack / 100 * phys_mv * phys_hitzone / 100 * bowgun_type_multiplier
        if self.monster.enraged == True:
            base_phys *= self.monster.enrage_multiplier
        base_phys = self._apply_independent_modifiers(base_phys, 'physical')

        # 属性基础伤害
        base_elem = attack / 100 * elem_mv * elem_hitzone / 100 * bowgun_type_multiplier
        if self.monster.enraged == True:
            base_elem *= self.monster.enrage_multiplier
        base_elem = self._apply_independent_modifiers(base_elem, 'element')

        # 三种情况的伤害计算
        # 正常伤害
        normal_phys = base_phys * crit_data['phys_multiplier']['normal']
        normal_elem = base_elem * crit_data['elem_multiplier']['normal']
        normal_total = self._round_damage(normal_phys) + self._round_damage(normal_elem)

        # 正会心伤害
        crit_phys = base_phys * crit_data['phys_multiplier']['positive']
        crit_elem = base_elem * crit_data['elem_multiplier']['positive']
        crit_total = self._round_damage(crit_phys) + self._round_damage(crit_elem)

        # 负会心伤害
        negative_phys = base_phys * crit_data['phys_multiplier']['negative']
        negative_elem = base_elem * crit_data['elem_multiplier']['negative']
        negative_total = self._round_damage(negative_phys) + self._round_damage(negative_elem)

        # 期望伤害计算
        expected_damage = (
            normal_total * crit_data['normal_rate'] +
            crit_total * crit_data['positive_rate'] +
            negative_total * crit_data['negative_rate']
        )

        return expected_damage

    def calculate_damage_laser(self):
        # 构建技能生效上下文
        # 修正后的上下文结构
        context = {
            "ammo_type": "special",  # 直接作为顶层键
            "ignore_hitzone": False,
            "weapon_type": self.weapon.weapon_type,
            "bullet_position": self.character.bullet_position,
            "monster_status": {
                "phys_hitzone": self.monster.physical_hitzone,
                "scar": self.monster.scar,
                "enraged": self.monster.enraged
            }
        }
        # 在应用技能效果前处理覆盖率
        if not self.dps_mode:
            # 单发模式清空覆盖率
            self.character.skill_coverages = {}

        # 应用技能效果到角色属性
        self.character.apply_skill_effects(context)

        # 基础数值计算
        attack = self._calculate_attack()
        crit_data = self._calculate_crit()

        # 获取弹药等级相关参数
        phys_mv = 6
        # 修改后（正确）：
        elem_mv = 0

        # 肉质处理
        phys_hitzone = 100 if self.ammo.ignore_hitzone else self.monster.physical_hitzone
        elem_hitzone = self.monster.element_hitzone

        # 物理基础伤害
        base_phys = attack / 100 * phys_mv * phys_hitzone / 100
        if self.monster.enraged == True:
            base_phys *= self.monster.enrage_multiplier
        base_phys = self._apply_independent_modifiers(base_phys, 'physical')

        # 属性基础伤害
        base_elem = attack / 100 * elem_mv * elem_hitzone / 100
        if self.monster.enraged == True:
            base_elem *= self.monster.enrage_multiplier
        base_elem = self._apply_independent_modifiers(base_elem, 'element')

        # 三种情况的伤害计算
        # 正常伤害
        normal_phys = base_phys * crit_data['phys_multiplier']['normal']
        normal_elem = base_elem * crit_data['elem_multiplier']['normal']
        normal_total = self._round_damage(normal_phys) + self._round_damage(normal_elem)

        # 正会心伤害
        crit_phys = base_phys * crit_data['phys_multiplier']['positive']
        crit_elem = base_elem * crit_data['elem_multiplier']['positive']
        crit_total = self._round_damage(crit_phys) + self._round_damage(crit_elem)

        # 负会心伤害
        negative_phys = base_phys * crit_data['phys_multiplier']['negative']
        negative_elem = base_elem * crit_data['elem_multiplier']['negative']
        negative_total = self._round_damage(negative_phys) + self._round_damage(negative_elem)

        # 期望伤害计算
        expected_damage = (
            normal_total * crit_data['normal_rate'] +
            crit_total * crit_data['positive_rate'] +
            negative_total * crit_data['negative_rate']
        )

        return expected_damage

    def _round_damage(self, value):
            """遵循怪物猎人的特殊舍入规则"""
            return round(value, 1)  # 等效于Excel的ROUND(value-0.4, 0)
    