from collections import defaultdict
import copy
import heapq
from venv import logger
from src.core.calculator import DamageCalculator
from src.core.inventory import GemInventory
from src.core.loader import GEM_DATA, SKILL_DATA

#* ======宝石组合类======
class GemCombination:
    def __init__(self, weapon_gems, equip_gems, dps):
        self.weapon_gems = weapon_gems  # 武器镶嵌的珠子列表
        self.equip_gems = equip_gems    # 装备镶嵌的珠子列表
        self.dps = dps                  # 组合后的DPS
#* ======珠子优化器======
class GemOptimizer:
    #* ======初始化======
    def __init__(self, inventory: GemInventory, character, weapon, ammo, monster):
        try:
            self.inventory = inventory
            self.character = character
            self.weapon = weapon
            self.ammo = ammo
            self.monster = monster
            self.base_dps = self._calculate_base_dps()
            self.all_weapon_gems = [
                g for g in GEM_DATA.values() 
                if g['type'] == 'weapon' and 
                self.inventory.get_count(g['name']) > 0
            ]
            self.all_equip_gems = [
                g for g in GEM_DATA.values() 
                if g['type'] == 'equip' and 
                self.inventory.get_count(g['name']) > 0
            ]
            print(f"初始化成功: 基础DPS: {self.base_dps}")
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            raise

    #* ======计算基本DPS======
    def _calculate_base_dps(self):
        calculator = DamageCalculator(
                character = self.character, 
                weapon = self.weapon, 
                ammo = self.ammo, 
                monster = self.monster,
                dps_mode=True
            )
        damage = calculator.calculate_dps()
        return damage

    #* ======生成武器孔位组合======
    def generate_gem_combinations(self):
        print(f"[Main] 开始生成组合 | 武器孔: {self.weapon.gem_size_1}-{self.weapon.gem_size_2}-{self.weapon.gem_size_3}")  # DEBUG-02
        print(f"[Main] 装备孔位: 3级x{self.character.gem_num_3}, 2级x{self.character.gem_num_2}, 1级x{self.character.gem_num_1}")  # DEBUG-03
        #* 预计算所有珠子的DPS增益（缓存机制）
        self._precompute_gem_effects()
        print(f"_precompute_gem_effects计算完毕")  # DEBUG-03.1
        # 使用优先队列的分支限界法
        top_combinations = []
        
        # 初始化优先队列
        pq = []
        print(f"准备创建initial_state")  # DEBUG-03.2
        #* ======创建quip_slots组，weapon的孔只有三个，但是equip的孔每个大小的数量不定，总数也不定======
        equip_slots = []
        equip_slots += [3] * self.character.gem_num_3
        equip_slots += [2] * self.character.gem_num_2
        equip_slots += [1] * self.character.gem_num_1

        #* ======初始化状态======
        initial_state = OptimizationState(
            #* ======武器的槽位======
            weapon_slots=sorted([self.weapon.gem_size_1, self.weapon.gem_size_2, 
                            self.weapon.gem_size_3], reverse=True),
            #* ======装备槽位======
            equip_slots=sorted(equip_slots, reverse=True),  # 排序装备孔
            #* ======已经使用过的珠子======
            used_gems=defaultdict(int),
            current_dps=self.base_dps,
            skill_levels=copy.deepcopy(self.character.skills),
            gem_effects_cache=self.gem_effects_cache
        )
        print(f"准备创建heapq")  # DEBUG-03.5
        #* ======通过heapq排序======
        heapq.heappush(pq, initial_state)
        print(f"[Main] 初始状态入队 | 队列大小: {len(pq)}")  # DEBUG-04
        #* ======定义一个处理了多少state的计数器======
        state_counter = 0
        #* ======分支限界处理======
        #* ======队列和前三组合小于三======
        while pq and len(top_combinations) < 3:
            #* ======当前state从队列中挤出一个最好的======
            current_state = heapq.heappop(pq)
            #* ======计数state======
            state_counter += 1
            print(f"\n[State-{state_counter}] 处理状态 | 剩余孔: W{len(current_state.weapon_slots)} E{len(current_state.equip_slots)}")  # DEBUG-05
            print(f"      当前DPS: {current_state.current_dps:.1f} | 乐观估计: {current_state.optimistic_estimate():.1f}")  # DEBUG-06
            #* ======如果这个state已经都填了孔，或者已经没有珠子可以用了======
            if current_state.is_complete():
                print(f"[Complete] 找到完整组合 | DPS: {current_state.current_dps:.1f}")  # DEBUG-07
                combo = GemCombination(
                    weapon_gems=current_state.weapon_gems,
                    equip_gems=current_state.equip_gems,
                    dps=current_state.current_dps
                )
                print("combo生成完毕")
                self._update_top_combinations(top_combinations, combo)
                print("top_combinations更新完毕")
                continue
    
            #* ======生成一个“下一个state”======
            next_states = current_state.generate_next_states(self.inventory)
            pruned_count = 0

            print(f"      生成分支: {len(next_states)} 个 | 初始可处理数")

            for next_state in next_states:
                print("进入循环")
                #* ======判断是否应该剪枝======
                if self._should_prune(next_state, top_combinations):
                    print("进入循环内判断")
                    pruned_count += 1
                    continue
                heapq.heappush(pq, next_state)
                
            print(f"      生成分支: {len(next_states)} 个 | 剪枝: {pruned_count} 个 | 队列新增: {len(next_states)-pruned_count}")  # DEBUG-08

        #print(f"\n[Result] 总处理状态数: {state_counter} | 最终队列大小: {len(pq)}")  # DEBUG-09
        print("判断完毕")
        print(f"最终三个配装的组合： {top_combinations}")
        #return [combo for _, combo in heapq.nlargest(3, top_combinations)]
        return [combo for _, _, combo in heapq.nlargest(3, top_combinations)]
    #* ======判断剪枝======
    def _should_prune(self, next_state, top_combinations):
        """ 改进版剪枝条件 """
        # 保留至少3个候选后再开始剪枝
        if len(top_combinations) < 5:
            return False
        """ 修正元组结构处理 """
        if not top_combinations:
            return False
        # 提取实际存储的combo对象（元组第二元素）
        min_dps = min(combo[1].dps for combo in top_combinations)
        return next_state.optimistic_estimate() < min_dps * 0.95
    
    
    def _update_top_combinations(self, top_combinations, new_combo):
        # 添加计数器避免比较GemCombination对象
        if not hasattr(self, '_combo_counter'):
            self._combo_counter = 0  # 初始化计数器
        
        # 标准化组合标识
        weapon_key = tuple(sorted(new_combo.weapon_gems))
        equip_key = tuple(sorted(new_combo.equip_gems))
        combo_id = (weapon_key, equip_key)

        # 检查重复（注意元组结构变化）
        existing_ids = {
            (tuple(sorted(c.weapon_gems)), tuple(sorted(c.equip_gems)))
            for _, _, c in top_combinations  # 现在元组是(dps, counter, combo)
        }
        if combo_id in existing_ids:
            return

        # 推入带计数器的元组
        self._combo_counter += 1
        heapq.heappush(top_combinations, (new_combo.dps, self._combo_counter, new_combo))
        
        # 保持最多3个元素
        if len(top_combinations) > 3:
            heapq.heappop(top_combinations)
    #* ======预计算珠子的效果======
    def _precompute_gem_effects(self):
        """预计算每个珠子对各个技能的增益效果"""
        print("\n[Precompute] 开始预计算珠子效果...")  # DEBUG-10
        self.gem_effects_cache = {}
        
        # 合并所有珠子类型
        all_gems = self.all_weapon_gems + self.all_equip_gems
        print(f"需要计算的珠子总数: {len(all_gems)}")  # DEBUG-1
        # 检查基础数据完整性
        if not SKILL_DATA:
            print("[Error] SKILL_DATA 未加载！")
            return
        
        for idx, gem in enumerate(all_gems, 1):
            try:
                print(f"\n处理第 {idx}/{len(all_gems)} 个珠子: {gem['name']}")  # DEBUG-2
                print(f"珠子类型: {gem['type']} | 等级: {gem['level']} | 技能: {gem['skills']}")
                
                # 检查技能数据完整性
                valid_skills = []
                for skill_name, level in gem['skills']:
                    if skill_name not in SKILL_DATA:
                        print(f"[Warning] 技能 {skill_name} 不存在，已跳过")
                        continue
                    valid_skills.append((skill_name, level))
                
                if not valid_skills:
                    print("该珠子没有有效技能，跳过计算")
                    self.gem_effects_cache[gem['name']] = 0
                    continue
                
                # 计算效果
                base_char = copy.deepcopy(self.character)
                effect = 0
                
                # 逐个技能计算影响
                for skill_name, level in valid_skills:
                    print(f"计算技能: {skill_name}+{level}")  # DEBUG-3
                    
                    # 获取当前等级
                    current_level = base_char.skills.get(skill_name, 0)
                    max_level = SKILL_DATA[skill_name].max_level
                    new_level = min(current_level + level, max_level)
                    
                    if current_level == new_level:
                        print(f"  技能已达上限 {current_level}/{max_level}，无增益")
                        continue
                        
                    # 计算增益
                    try:
                        print(f"  计算原始DPS（等级 {current_level}）...")
                        before = self._calculate_skill_impact(skill_name, current_level)
                        print(f"  计算新DPS（等级 {new_level}）...")
                        after = self._calculate_skill_impact(skill_name, new_level)
                        delta = after - before
                        print(f"  增益: {delta:.2f}")
                        effect += delta
                    except Exception as e:
                        print(f"  计算技能 {skill_name} 时出错: {str(e)}")
                        raise
                
                self.gem_effects_cache[gem['name']] = effect
                print(f"总增益: {effect:.2f}")  # DEBUG-4
                
            except Exception as e:
                print(f"处理珠子 {gem['name']} 时发生严重错误: {str(e)}")
                raise
        
        print("[Precompute] 预计算完成")
    #* ======计算单个技能等级对DPS的影响======
    def _calculate_skill_impact(self, skill_name, level):
        """计算单个技能等级对DPS的影响"""
        temp_char = copy.deepcopy(self.character)
        temp_char.skills[skill_name] = level
        
        try:
            calculator = DamageCalculator(
                temp_char, self.weapon, self.ammo, self.monster, dps_mode=True
            )
            result = calculator.calculate_dps()
            print(f"    计算结果: {result:.2f}")  # DEBUG-6
            return result
        except Exception as e:
            print(f"    DPS计算失败: {str(e)}")
            return 0
    
class OptimizationState:
    __slots__ = ['weapon_slots', 'equip_slots', 'used_gems', 'current_dps', 
                 'skill_levels', 'weapon_gems', 'equip_gems', 'gem_effects_cache']
    
    def __init__(self, weapon_slots, equip_slots, used_gems, current_dps, 
                 skill_levels, gem_effects_cache):
        self.weapon_slots = weapon_slots.copy()
        self.equip_slots = equip_slots.copy()
        self.used_gems = used_gems.copy()
        self.current_dps = current_dps
        self.skill_levels = skill_levels.copy()
        self.gem_effects_cache = gem_effects_cache
        self.weapon_gems = []
        self.equip_gems = []
        
    def __lt__(self, other):
        # 优先处理潜在DPS高的状态
        return self.optimistic_estimate() > other.optimistic_estimate()
    
    def optimistic_estimate(self):
        """按孔位大小分层计算最大增益"""
        estimate = self.current_dps
        # 处理剩余武器孔
        for slot in sorted(self.weapon_slots, reverse=True):
            max_effect = max( 
                (eff for gem,eff in self.gem_effects_cache.items() 
                if GEM_DATA[gem]['level'] <= slot),
                default=0
            )
            estimate += max_effect
        # 处理剩余装备孔（同上逻辑）
        for slot in sorted(self.equip_slots, reverse=True):
            max_effect = max( 
                (eff for gem,eff in self.gem_effects_cache.items() 
                if GEM_DATA[gem]['level'] <= slot),
                default=0
            )
            estimate += max_effect
        return estimate
    
    def is_complete(self):
        print("确实进行了state的判断")
        return not self.weapon_slots and not self.equip_slots
    
    def generate_next_states(self, inventory):
        """生成所有合法后续状态（修正孔位处理顺序）"""
        print("生成下一个states")
        next_states = []
        
        # 选择要处理的孔位类型（优先武器孔）
        if self.weapon_slots:
            # 深拷贝后排序以避免修改原始数据
            print("处理武器孔）")
            sorted_weapon = sorted(self.weapon_slots.copy(), reverse=True)
            current_slot = sorted_weapon[0]
            remaining_weapon = sorted_weapon[1:] + self.weapon_slots[len(sorted_weapon):]  # 保留未处理的原始孔位
            gem_type = 'weapon'
        elif self.equip_slots:
            print("处理装备孔）")
            sorted_equip = sorted(self.equip_slots.copy(), reverse=True)
            current_slot = sorted_equip[0]
            remaining_equip = sorted_equip[1:] + self.equip_slots[len(sorted_equip):]
            gem_type = 'equip'
        else:
            return []
        
        # 生成不镶嵌的分支
        no_gem_state = copy.deepcopy(self)
        print("生成不镶嵌分支")
        if gem_type == 'weapon':
            no_gem_state.weapon_slots = remaining_weapon
        else:
            no_gem_state.equip_slots = remaining_equip
        next_states.append(no_gem_state)
        
        # 生成镶嵌分支
        print("生成镶嵌分支")
        available_gems = inventory.weapon_gems if gem_type == 'weapon' else inventory.equip_gems
        print(f"可用珠子: {len(available_gems)} 个")
        for gem in available_gems:
            print(f"    镶嵌珠子: {gem}")
            if self._can_use_gem(gem, current_slot, inventory):
                new_state = self._create_gem_state(gem, current_slot, gem_type)
                if gem_type == 'weapon':
                    new_state.weapon_slots = remaining_weapon
                else:
                    new_state.equip_slots = remaining_equip
                next_states.append(new_state)
        
        print(f"生成分支: {len(next_states)} 个")
        return next_states
    
    def _can_use_gem(self, fake_gem, slot_size, inventory):
        print("检查珠子是否可用")
        
        used = self.used_gems.get(fake_gem, 0)
        print(f"已经用了 {used} 个{fake_gem}")
        total_available = inventory.get_count(fake_gem)
        print(f"已经用了 {used} 个{fake_gem}，还剩 {total_available - used} 个")
        gem = GEM_DATA[fake_gem]
        if used >= total_available:
            print("已经用完该珠子了，拒绝镶嵌")
            return False
        fail_reason = []
        if gem['level'] > slot_size:
            print("珠子等级过高，孔太小")
            fail_reason.append(f"等级过高({gem['level']}>{slot_size})")

        if self.used_gems.get(gem['name'], 0) >= inventory.get_count(gem['name']):
            print("珠子库存不足，拒绝镶嵌")
            fail_reason.append(f"库存不足({self.used_gems.get(gem['name'],0)}>={inventory.get_count(gem['name'])})")

        for skill_name, level in gem['skills']:
            current = self.skill_levels.get(skill_name, 0)
            if current >= SKILL_DATA[skill_name].max_level:
                print("技能等级已经满级，拒绝镶嵌")
                fail_reason.append(f"{skill_name}已满级({current})")
        
        if fail_reason:
            print(f"      拒绝 {gem['name']}: {'; '.join(fail_reason)}")  # DEBUG-17
            return False
            
        print("可以镶嵌")
        return True
    
    def _create_gem_state(self, fake_gem, slot_size, gem_type):
        gem = GEM_DATA[fake_gem]
        new_state = copy.deepcopy(self)
        new_state.used_gems = self.used_gems.copy()
        new_state.used_gems[gem['name']] = new_state.used_gems.get(gem['name'], 0) + 1
        
        # 更新技能等级
        for skill_name, level in gem['skills']:
            current = new_state.skill_levels.get(skill_name, 0)
            new_level = min(current + level, SKILL_DATA[skill_name].max_level)
            new_state.skill_levels[skill_name] = new_level
            
        # 更新DPS
        new_state.current_dps += self.gem_effects_cache.get(gem['name'], 0)
        
        # 记录镶嵌的珠子
        if gem_type == 'weapon':
            new_state.weapon_gems.append(gem['name'])
        else:
            new_state.equip_gems.append(gem['name'])
            
        return new_state