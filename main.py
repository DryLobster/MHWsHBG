import os
import flet as ft
from collections import defaultdict
from components.AmmoParameterSection import AmmoParameterSection
from components.DamageMetricsSection import DamageMetricsSection
from components.DetailMetricsSection import DetailMetricsSection
from components.MonsterParameterSection import MonsterParameterSection
from components.ResultDisplaySection import ResultDisplaySection
from components.TabCard import TabCard
from components.WeaponParameterSection import WeaponParameterSection
from components.SectionCard import SectionCard
from src.core.optimizer import GemOptimizer
from src.core.inventory import GemInventory, get_app_data_path
from pages.inventory_ui import GemInventoryUI
from src.core.models import Weapon, Ammo, Monster, Character
from src.core.calculator import DamageCalculator
import json
from src.core.loader import SKILL_DATA, BUFF_DATA, init_user_data
from src.utils.path_manager import get_data_path

class DecimalInputFilter(ft.InputFilter):
    def __init__(self):
        super().__init__(
            regex_string=r"^\d*\.?\d*$",  # 仅支持数字和小数点
            allow=True,
            replacement_string=""
        )
class CritInputFilter(ft.InputFilter):
    def __init__(self):
        super().__init__(
            regex_string=r"^\d*\-?\d*$",  # 仅支持数字和小数点
            allow=True,
            replacement_string=""
        )

init_user_data()

#* =======状态管理类=======
class AppState:
    def __init__(self):
        self.selected_skills = {}
        self.selected_buffs = set()
        self.coverages = defaultdict(float)
        self.ammo_list = self.load_ammo_data()
        self.gem_inventory = GemInventory()  # 添加这行初始化库存 
        
    @staticmethod
    def load_ammo_data():

        # 修改为动态获取路径
        data_file = get_data_path("ammo_data.json")
        with open(data_file, 'r', encoding='utf-8') as f:
        #with open('data/ammo_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)['ammo_types']

#* =======主界面组件=======
class MHWCalculator(ft.Column):

    def _show_inventory(self, e):
        self.drawer.open = True
        self.page.update()
    

    def _close_dialog(self, dlg):
        dlg.open = False
        self.page.update()
        print("弹窗已关闭")  # 调试输出

    #* =======初始化=======
    def __init__(self, page, state):
        super().__init__(
            scroll=ft.ScrollMode.AUTO,  # 自动显示滚动条
            expand=True,  # 重要！必须设置才能正确计算滚动区域
            spacing=20  # 可选：设置子控件间距
        )
        self.page = page
        self.state = state
        self.expand = True
        self.init_components()

        self.ammo_section = AmmoParameterSection(
            self.ammo_dropdown,
            self.bullet_level_slider,
            self.phys_mv,
            self.elem_mv,
            self.hit,
            self.ignore_hitzone
        )
        
        self.weapon_section = WeaponParameterSection(
            self.attack_field,
            self.affinity_field,
            self.bowgun_type,
            self.reload_slider,
            self.magazine_slider,
            self.bullet_position
        )
        
        self.monster_section = MonsterParameterSection(
            self.phys_zone,
            self.elem_zone,
            self.scar_check,
            self.enraged,
            self.enrage_multiplier,
            self.enrage_ratio,
            self.laser_multiplier,
            self.laser_hit,
            self.virus_slider
        )

        # 初始化结果展示组件
        self.damage_metrics = DamageMetricsSection(
            self.result_damage,
            self.result_damage_gatlin,
            self.result_damage_laser
        )
        
        self.detail_metrics = DetailMetricsSection(
            self.result_affinity,
            self.result_crit_phys,
            self.result_crit_elem,
            self.result_final_attack,
        )
        
        self.result_display = ResultDisplaySection(
            self.damage_metrics,
            self.detail_metrics
        )

        

        # 初始化时直接构建布局
        self.build_layout()

    #* ======更新整体布局======
    def build_layout(self):
        
        self.controls = [
            ft.Row([  # 主容器改为横向布局
                # 左边栏（BUFF + 技能）
                ft.Container(
                    content=ft.Column([
                        #self.title, 
                        self.buff_section,
                        self.skill_panel,
                        self.build_coverage_panel(),
                        self.heheboi
                    ]),
                    width=800,  # 固定左边栏宽度
                    padding=10,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=8
                ),
                
                ft.VerticalDivider(width=10),  # 左右分界线
                
                # 右边栏（参数 + 结果）
                ft.Column([
                    #* 参数区块
                    self.build_right_up_section(),
                    self.build_right_down_section()
                ], expand=True, horizontal_alignment="start")  # 右边栏自动扩展
            ], expand=True, vertical_alignment= "start")
        ]

    #* ======初始化所有子组件======
    def init_components(self):
        #self.title = ft.Text("怪物猎人荒野弩枪计算器", size=26)
        self.buff_section = self.build_buff_section()
        self.skill_panel = self.build_skill_panel()

        #嘿嘿，boi
        self.heheboi = ft.Text("本程序由挂机虫子、脱水龙虾、半挂重卡和麻将靶子共同开发，按寻思不会有人发现这里藏了字", size=16, color= ft.Colors.GREY_100)

        #* ======武器攻击力======
        self.attack_field = ft.TextField(
            label="武器攻击力",
            value="100",
            width=150,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        #* ======装填等级======
        self.reload_slider = ft.Slider(
            min=0, max=5,
            value=3,
            divisions=5,
            label="慢←【{value}】→快"
        )
        #* ======弩枪类型======
        self.bowgun_type = ft.Slider(
            min=-2, max=2, divisions=4, value= 0,
            label="子弹特化1.2倍← 【{value}】 →龙热特化1.2倍"
        )
        #* ======弹药选择======
        self.ammo_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(a["name"]) for a in self.state.ammo_list],
            value=self.state.ammo_list[0]["name"] if self.state.ammo_list else None,  # 设置默认值
            on_change=self.update_ammo_params,
            hint_text="选择弹药类型",  # 无默认值时显示提示
            width=150
        )
        #* ======子弹等级======
        self.bullet_level_slider = ft.Slider(
            min=1, max=3, divisions=2, 
            label="{value}", 
            on_change=self.update_ammo_display
        ) 
        #* ======子弹数值======
        self.phys_mv = ft.Text("15", size=18)
        self.elem_mv = ft.Text("0", size=18)
        self.hit = ft.Text("3", size=18)
        self.ignore_hitzone = ft.Checkbox(label="无视肉质", value=False, disabled=True)        
        #* ======会心率======
        self.affinity_field = ft.TextField(
            label="会心率(%)", 
            value="0",
            width=150,
            input_filter=CritInputFilter()
        )
        #* ======物理肉质/属性吸收======
        self.phys_zone = ft.TextField(
            label="物理肉质",
            value="45",
            width=150,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.elem_zone = ft.TextField(
            label="属性吸收",
            value="20",
            width=150,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        #* ======伤口/愤怒======
        self.scar_check = ft.Checkbox(label="伤口", value=False)
        self.enrage_multiplier = ft.TextField(
            label="愤怒补正", 
            value="1.1",
            width=150,
            input_filter=DecimalInputFilter(),
        )
        self.enraged = ft.Checkbox(label="生气", value=False)
        self.enrage_ratio = ft.Slider(
            min=0, max=100, value=50,divisions=100,
            label="愤怒时间占比{value}%",
        )
        #* ======穿甲弹倍率/跳数======
        self.laser_multiplier = ft.TextField(
            label="穿甲弹倍率", 
            value="2.5",
            width=150,
            input_filter=DecimalInputFilter(),
        )
        self.laser_hit = ft.TextField(
            label="穿甲弹跳数", 
            value="10",
            width=150,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        #* ======弹匣相关======
        self.magazine_slider = ft.Slider(
            min=1, max=7, value=3, divisions=6,
            label="弹匣容量 {value}",
            on_change=self.update_bullet_position
        )
        self.bullet_position = ft.Slider(
            min=1, max=7, value=1, divisions= 6,
            label="第{value}颗"
        )
        #! ======零件相关======
        self.gear_1 = ft.Dropdown(
            
        )
        self.gear_2 = ft.Dropdown(
            
        )
        #* ======宝珠相关======
        self.weapon_slot_size_1 = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(4)],  # 生成0-3的选项
            value="3",                # 设置默认值
            label="武器孔1",    # 添加标签说明
            width=100,                # 设置合适宽度
            text_size=14,             # 文字大小
            hint_text="选择孔位尺寸",  # 未选择时的提示文字
        )
        self.weapon_slot_size_2 = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(4)],  # 生成0-3的选项
            value="2",                # 设置默认值
            label="武器孔2",    # 添加标签说明 
            width=100,                # 设置合适宽度
            text_size=14,             # 文字大小
            hint_text="选择孔位尺寸",  # 未选择时的提示文字
        )
        self.weapon_slot_size_3 = ft.Dropdown(
            options=[ft.dropdown.Option(str(i)) for i in range(4)],  # 生成0-3的选项
            value="1",                # 设置默认值
            label="武器孔3",    # 添加标签说明
            width=100,                # 设置合适宽度
            text_size=14,             # 文字大小
            hint_text="选择孔位尺寸",  # 未选择时的提示文字
        )
        self.equip_slot_num_3 = ft.TextField(
            label="装备三级孔个数", 
            value="0",
            width=100,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.equip_slot_num_2 = ft.TextField(
            label="装备二级孔个数", 
            value="0",
            width=100,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.equip_slot_num_1 = ft.TextField(
            label="装备一级孔个数", 
            value="0",
            width=100,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        self.optimize_btn = ft.ElevatedButton(
            "优化配置",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self._run_optimization,
            bgcolor=ft.colors.AMBER_100
        )
        # 添加结果展示容器
        self.optimize_result = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=True,
            width=640
        )

        self.virus_slider = ft.Slider(
            min=0, max=2, value=0,divisions=2,
            label="【0】没病/【1】发病/【2】克服  当前:{value}",
        )

        #* ======计算方式======
        self.calc_mode = ft.RadioGroup(
            value="dps",
            content=ft.Row([
                ft.Radio(value="single", label="单发伤害"),
                ft.Radio(value="dps", label="DPS期望")
            ])
        )
        #* ======结果展示======
        self.result_damage = ft.Text("0.00", size=24, weight="bold")
        self.result_damage_gatlin = ft.Text("--", size=24, weight="bold")
        self.result_damage_laser = ft.Text("--", size=24, weight="bold")

        self.result_affinity = ft.Text("0%", size=24, weight="bold")
        self.result_crit_phys = ft.Text("1.25", size=24, weight="bold")
        self.result_crit_elem = ft.Text("1.00", size=24, weight="bold")
        self.result_final_attack = ft.Text("0", size=24, weight="bold")
        
        self.result_damage = ft.Text("0.00", size=24, weight="bold")
        self.detail_expander = ft.ExpansionTile(
            title=ft.Text("详细计算"),
            controls=[
                ft.Column([
                    ft.Text("会心分布加载中...")
                ])
            ]
        )
    
    #* ======构建BUFF列表======
    def build_buff_section(self):
        #* 初始化分类字典
        categories = defaultdict(list)
        for name, buff in BUFF_DATA.items():
            categories[buff.category].append(name)
        
        #* 创建横向滚动容器（适合大量分类）
        BuffRow = ft.Row(
            controls=[
                #* 每个分类的独立卡片
                ft.Container(
                    content=ft.Column(
                        controls=[
                            #* 分类标题
                            ft.Text(cat, 
                                  weight=ft.FontWeight.BOLD,
                                  size=14,
                                  color=ft.Colors.ORANGE_800),
                            #* 带滚动的BUFF列表
                            ft.Column(
                                controls=[
                                    ft.Checkbox(
                                        label=b, 
                                        on_change=self.toggle_buff,
                                    ) for b in buffs
                                ],
                                scroll=ft.ScrollMode.AUTO,  #* 启用滚动
                                height=180,  #* 固定高度
                                spacing=5    #* 紧凑间距
                            )
                        ],
                        spacing=8
                    ),
                    #* 卡片样式
                    padding=10,
                    margin=5,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    width=180  #* 固定卡片宽度
                ) for cat, buffs in categories.items()
            ],
            scroll=ft.ScrollMode.ADAPTIVE,  #* 横向滚动
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        return SectionCard(
            title="BUFF列表",
            content=ft.Container(BuffRow),
        )

    #* ======更新技能覆盖======
    def update_coverage(self, skill_name: str, value: str):
        try:
            coverage = max(0, min(100, float(value))) / 100.0
            self.state.coverages[skill_name] = coverage
        except ValueError:
            self.state.coverages[skill_name] = 1.0  # 默认值
    #* ======构建技能列表======
    def build_skill_panel(self):
        self.skill_ui_controls = {}
        
        skill_grid = ft.GridView(
            runs_count=3,
            max_extent=200,  # 缩小宽度
            child_aspect_ratio=2,
            spacing=10,
            padding=10
        )
        
        for skill in SKILL_DATA.values():
            # 创建Dropdown控件
            level_options = [ft.dropdown.Option(str(i)) for i in range(skill.max_level+1)]
            dropdown = ft.Dropdown(
                options=level_options,
                value="0",
                width=70,
                text_size=14,
                on_change=lambda e, s=skill: self.update_skill_level(s, int(e.control.value))
            )
            
            self.skill_ui_controls[skill.name] = dropdown
            
            skill_item = ft.Container(
                content=ft.Row([
                    ft.Text(f"{skill.name}:", width=80, size=12, text_align="center", weight="bold", max_lines=2),
                    dropdown
                ], spacing=5),
                padding=5,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            )
            skill_grid.controls.append(skill_item)
        
        return SectionCard(
            title="技能列表",
            content=ft.Container(skill_grid, padding=10, height=300),
        )
    #* ======更新技能等级======
    def update_skill_level(self, skill, level):
        # 统一处理方法
        self.state.selected_skills[skill.name] = level
        if skill.has_coverage:
            self.state.coverages[skill.name] = 1.0  # 默认覆盖率
    #* ======构建覆盖列表======
    def build_coverage_panel(self):
        coverage_grid = ft.GridView(
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=3,
            spacing=10,
            padding=10
        )
        
        for skill in filter(lambda s: s.has_coverage, SKILL_DATA.values()):
            item = ft.Container(
                content=ft.Row([
                    ft.Text(f"{skill.name}:", width=60, size=12, text_align="end", weight="bold"),
                    ft.TextField(
                        value="100",
                        width=50,
                        height=30,
                        suffix="%",
                        text_size=12,
                        input_filter=ft.NumbersOnlyInputFilter(),
                        on_change=lambda e, s=skill.name: self.update_coverage(s, e.control.value)
                    ),
                    ft.Text("%", width=80, size=12, text_align="start", weight="bold")
                ], spacing=8, alignment="center", vertical_alignment="center"),
                padding=5,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            )
            coverage_grid.controls.append(item)
        
        return SectionCard(
            title="技能覆盖率",
            content=ft.Container(coverage_grid, padding=10, height=180),
        )
    #* ======构建参数面板======
    def build_params_section(self):
        params = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.ammo_section,
                    ft.VerticalDivider(),
                    self.monster_section
                ], vertical_alignment= "start"),
                self.weapon_section,

            ]),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8
        )
        return params
    #* ======构建珠子面板======
    def build_gem_section(self):
        self.gem_management_tab = ft.Container(
            content=GemInventoryUI(self.page, self.state.gem_inventory),
            height=600,
            padding=10
        )
        
        return self.gem_management_tab
    #* ======构建右上面板======
    def build_right_up_section(self):
        #* ===== 标签页容器 =====
        self.tabs_right_up = ft.Tabs(
            indicator_color=ft.Colors.ORANGE_400,
            animation_duration=1,
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="参数面板",
                    content=ft.Column([
                        self.build_params_section(),
                    ])
                ),
                ft.Tab(
                    text="珠子管理",
                    content=ft.Column([
                        self.build_gem_section(),
                    ])
                ) 
            ]
        )

        return TabCard(content=self.tabs_right_up, height=600)

    #* ======构建计算面板======
    def build_calculate_section(self):
        calcu = ft.Column([
            #* 计算按钮和模式选择
            ft.Row([
                self.calc_mode,
                ft.ElevatedButton("开始计算", on_click=self.calculate)
            ], alignment=ft.MainAxisAlignment.START),
            
            #* 结果展示区
            self.result_display
        ])  # 右边栏自动扩展
        return ft.Container(
            content=calcu)
    
    #* ======构建优化面板======
    def build_optimizer_section(self):
        weapon_slots = ft.Row([
            self.weapon_slot_size_1
            , self.weapon_slot_size_2
            , self.weapon_slot_size_3
        ])

        equip_slots = ft.Row([
            self.equip_slot_num_3
            , self.equip_slot_num_2
            , self.equip_slot_num_1
        ])

        op_left = ft.Column([
            ft.Text("武器孔位"),
            weapon_slots,
            ft.Text("装备孔位"),
            equip_slots,
            self.optimize_btn
        ])

        op_right = ft.Column([
            self.optimize_result
        ])
        
        optimizer = ft.Row([
            op_left,
            op_right
        ])

        return ft.Container(
            content=optimizer, height = 270, padding=10)

    def build_right_down_section(self):
        #* ===== 标签页容器 =====
        self.tabs_right_up = ft.Tabs(
            indicator_color=ft.Colors.ORANGE_400,
            animation_duration=1,
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="伤害计算",
                    content=ft.Column([
                        self.build_calculate_section(),
                    ])
                ),
                ft.Tab(
                    text="最优技能",
                    content=ft.Column([
                        self.build_optimizer_section(),
                    ])
                ) 
            ]
        )

        return TabCard(content=self.tabs_right_up, height=360)

    #* ======刷新弹药参数======
    def update_ammo_params(self, e):
        selected = next(a for a in self.state.ammo_list 
                      if a["name"] == self.ammo_dropdown.value)
        self.bullet_level_slider.max = selected["max_level"]
        if self.bullet_level_slider.value > self.bullet_level_slider.max:
            self.bullet_level_slider.value = self.bullet_level_slider.max
        self.update_ammo_display()
    
    def update_bullet_position(self, e):
        if int(self.bullet_position.value) > int(self.magazine_slider.value):
            self.bullet_position.value = int(self.magazine_slider.value)
        self.bullet_position.max = int(self.magazine_slider.value)
        self.bullet_position.divisions = int(self.magazine_slider.value) - 1
        self.update()

    #* ======刷新弹药显示======
    def update_ammo_display(self, e=None):
        selected = next(a for a in self.state.ammo_list 
                      if a["name"] == self.ammo_dropdown.value)
        level = int(self.bullet_level_slider.value) - 1
        str_level = str(level)
        
        phys = selected["physical_mv"] * selected["physical_mv_multiplier"].get(str_level, 1)
        phys += selected["physical_mv_add"].get(str_level, 0)
        self.phys_mv.value = f"{phys}"
        
        elem = selected["element_mv"] * selected["element_mv_multiplier"].get(str_level, 1)
        elem += selected["element_mv_add"].get(str_level, 0)
        self.elem_mv.value = f"{elem}"

        hit = selected["hit"].get(str_level, 1)  # 获取命中次数
        self.hit.value = str(hit)  # 正确更新Text控件的值

        # 正确设置复选框的值（保留控件实例，只修改value属性）
        self.ignore_hitzone.value = selected.get("ignore_hitzone", False)
        self.ignore_hitzone.update()  # 触发界面刷新
        #ignore = selected["ignore_hitzone"]
        #self.ignore_hitzone = ignore
        
        self.update()
    
    #* ======点选BUFF======
    def toggle_buff(self, e):
        buff = e.control.label
        if e.control.value:
            self.state.selected_buffs.add(buff)
        else:
            self.state.selected_buffs.discard(buff)
    
    #* ======刷新技能等级======
    def update_skill_level(self, skill, level):
        self.state.selected_skills[skill.name] = level
        if skill.has_coverage:
            self.state.coverages[skill.name] = 1.0
    #* ======移除技能======
    def remove_skill(self, skill):
        del self.state.selected_skills[skill.name]
        if skill.has_coverage:
            del self.state.coverages[skill.name]
        self.update()
    #* ======计算======
    def calculate(self, e):
        try:
            #* ===== 参数校验 =====
            if not self.ammo_dropdown.value:
                raise ValueError("请选择弹药类型")
            
            #* ===== 创建弹药实例 =====
            ammo_data = next(a for a in self.state.ammo_list 
                        if a["name"] == self.ammo_dropdown.value)
            
            ammo = Ammo(
                name=ammo_data["name"],
                type=ammo_data["type"],
                physical_mv=ammo_data["physical_mv"],
                element_mv=ammo_data["element_mv"],
                physical_mv_multiplier=ammo_data["physical_mv_multiplier"],
                element_mv_multiplier=ammo_data["element_mv_multiplier"],
                hit=ammo_data["hit"],
                physical_mv_add=ammo_data["physical_mv_add"],
                element_mv_add=ammo_data["element_mv_add"],
                max_level=ammo_data["max_level"],
                recoil=ammo_data["recoil"],
                reload_level=ammo_data["reload_level"],
                ignore_hitzone=ammo_data["ignore_hitzone"]
            )

            #* ===== 创建武器实例 =====
            weapon = Weapon(
                name="自定义弩枪",
                base_attack=int(self.attack_field.value),
                affinity=int(self.affinity_field.value),
                reload_level=int(self.reload_slider.value),
                weapon_type="heavy_bowgun"
            )
            # 在武器实例化后设置值
            weapon.bowgun_type = int(self.bowgun_type.value)

            #* ===== 创建怪物实例 =====
            monster = Monster(
                name="自定义怪物",
                phys_hitzone=int(self.phys_zone.value),
                elem_hitzone=int(self.elem_zone.value),
                scar=self.scar_check.value,
                enrage_multiplier=float(self.enrage_multiplier.value),
                enraged=self.enraged.value
            )

            #* ===== 创建角色实例 =====
            level = int(self.bullet_level_slider.value)
            character = Character(
                bullet_level=level,
                magazine=int(self.magazine_slider.value),
                enrage_ratio=float(self.enrage_ratio.value)/100,
                bullet_position=int(self.bullet_position.value)
            )
            #* ===== 穿甲弹 =====
            character.laser_hit = int(self.laser_hit.value)
            character.laser_multiplier = float(self.laser_multiplier.value)

            character.virus = self.virus_slider.value

            #* ===== 应用技能和BUFF、以及覆盖率 =====
            for name, level in self.state.selected_skills.items():
                if level > 0:  # 只添加等级大于0的技能
                    character.add_skill(name, level)
                    
            for buff in self.state.selected_buffs:
                character.add_buff(buff)
            
            character.set_coverages(self.state.coverages)

            #* ===== 执行计算 =====
            calculator = DamageCalculator(
                character, weapon, ammo, monster,
                dps_mode=(self.calc_mode.value == "dps")
            )

            context = {
                "ammo_type": ammo.type,  # 直接作为顶层键
                "ignore_hitzone": ammo.ignore_hitzone,
                "weapon_type": weapon.weapon_type,
                "bullet_position": character.bullet_position,
                "monster_status": {
                    "phys_hitzone": monster.physical_hitzone,
                    "scar": monster.scar,
                    "enraged": monster.enraged
                }
            }
            # 在应用技能效果前处理覆盖率
            if not self.calc_mode.value == "dps":
                # 单发模式清空覆盖率
                character.reset_coverages()

            # 应用技能效果到角色属性
            character.apply_skill_effects(context)
            # 在calculate方法中：
            final_attack = calculator._calculate_attack()
            crit_data = calculator._calculate_crit()

            affinity = crit_data['positive_rate'] - crit_data['negative_rate']

            self.result_final_attack.value = f"{final_attack:.0f}"
            self.result_affinity.value = f"{(affinity)*100:.1f}%"
            if affinity >= 0:
                self.result_crit_phys.value = f"{crit_data['phys_multiplier'].get('positive', 1)}"
                self.result_crit_elem.value = f"{crit_data['elem_multiplier'].get('positive', 1)}"
            else:
                self.result_crit_phys.value = crit_data['phys_multiplier'].get('negative', 1)
                self.result_crit_elem.value = crit_data['elem_multiplier'].get('negative', 1)

            if self.calc_mode.value == "dps":
                damage = calculator.calculate_dps()
                dps_gatlin = calculator.calculate_dps_gatlin()
                dps_laser = calculator.calculate_dps_laser()
                total_dps = damage
                self.result_damage.value = f"{total_dps:.2f}"
                self.result_damage_gatlin.value = f"{dps_gatlin:.2f}"
                self.result_damage_laser.value = f"{dps_laser:.2f}"
            else:
                damage = calculator.calculate_damage()
                self.result_damage.value = f"{damage:.1f}"
                self.result_damage_gatlin.value = "--"
                self.result_damage_laser.value = "--"


            # ===== 显示详细数据 =====
            self.show_detail(calculator)
            self.update()
            
        except StopIteration:
            self.show_error("弹药数据加载失败")
        except ValueError as ve:
            self.show_error(f"输入错误: {str(ve)}")
        except KeyError as ke:
            self.show_error(f"数据字段缺失: {str(ke)}")
        except Exception as ex:
            self.show_error(f"计算错误: {str(ex)}")
            raise  # 开发阶段保留堆栈跟踪

    def show_error(self, message):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message, color=ft.Colors.RED_700),
            bgcolor=ft.Colors.AMBER_100
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_detail(self, calculator):
        crit_data = calculator._calculate_crit()
        content = ft.Column([
            ft.Text(f"正会心率: {crit_data['positive_rate']*100:.1f}%"),
            ft.Text(f"负会心率: {crit_data['negative_rate']*100:.1f}%"),
            ft.Text(f"物理会心倍率: {crit_data['phys_multiplier']['positive']:.2f}x")
        ])
        self.detail_expander.controls = [content]
    

    # 在GemInventoryUI类中添加优化方法
    def _run_optimization(self, e):
        try:
            #* ===== 参数校验 =====
            if not self.ammo_dropdown.value:
                raise ValueError("请选择弹药类型")
            
            #* ===== 创建弹药实例 =====
            ammo_data = next(a for a in self.state.ammo_list 
                        if a["name"] == self.ammo_dropdown.value)
            
            ammo = Ammo(
                name=ammo_data["name"],
                type=ammo_data["type"],
                physical_mv=ammo_data["physical_mv"],
                element_mv=ammo_data["element_mv"],
                physical_mv_multiplier=ammo_data["physical_mv_multiplier"],
                element_mv_multiplier=ammo_data["element_mv_multiplier"],
                hit=ammo_data["hit"],
                physical_mv_add=ammo_data["physical_mv_add"],
                element_mv_add=ammo_data["element_mv_add"],
                max_level=ammo_data["max_level"],
                recoil=ammo_data["recoil"],
                reload_level=ammo_data["reload_level"],
                ignore_hitzone=ammo_data["ignore_hitzone"]
            )

            #* ===== 创建武器实例 =====
            weapon = Weapon(
                name="自定义弩枪",
                base_attack=int(self.attack_field.value),
                affinity=int(self.affinity_field.value),
                reload_level=int(self.reload_slider.value),
                weapon_type="heavy_bowgun"
            )
            # 在武器实例化后设置值
            weapon.bowgun_type = int(self.bowgun_type.value)
            weapon.gem_size_1=int(self.weapon_slot_size_1.value)
            weapon.gem_size_2=int(self.weapon_slot_size_2.value)
            weapon.gem_size_3=int(self.weapon_slot_size_3.value)

            #* ===== 创建怪物实例 =====
            monster = Monster(
                name="自定义怪物",
                phys_hitzone=int(self.phys_zone.value),
                elem_hitzone=int(self.elem_zone.value),
                scar=self.scar_check.value,
                enrage_multiplier=float(self.enrage_multiplier.value),
                enraged=self.enraged.value
            )

            #* ===== 创建角色实例 =====
            level = int(self.bullet_level_slider.value)
            character = Character(
                bullet_level=level,
                magazine=int(self.magazine_slider.value),
                enrage_ratio=float(self.enrage_ratio.value)/100,
                bullet_position=int(self.bullet_position.value)
            )

            character.gem_num_3=int(self.equip_slot_num_3.value)
            character.gem_num_2=int(self.equip_slot_num_2.value)
            character.gem_num_1=int(self.equip_slot_num_1.value)

            #* ===== 应用狂龙病状态 =====
            character.virus = self.virus_slider.value

            #* ===== 应用技能和BUFF =====
            for name, level in self.state.selected_skills.items():
                if level > 0:  # 只添加等级大于0的技能
                    character.add_skill(name, level)
                    
            for buff in self.state.selected_buffs:
                character.add_buff(buff)

            character.set_coverages(self.state.coverages)

            self.optimize_btn.text = "重弩祈祷中..."
            self.update()
            print("开始优化...") # 调试输出
            print(f"武器孔位: {weapon.gem_size_1}, {weapon.gem_size_2}, {weapon.gem_size_3}")
            print(f"装备孔位: {character.gem_num_3}, {character.gem_num_2}, {character.gem_num_1}")
            
            # 创建优化器实例
            optimizer = GemOptimizer(
                inventory=self.state.gem_inventory,
                character=character,
                weapon=weapon,
                ammo=ammo,
                monster=monster,
            )
            print("创建GemOptimizer完成") # 调试输出
            # 获取最佳组合
            top_combos = optimizer.generate_gem_combinations()
            print("top_combos获取完成") # 调试输出
            # 显示结果
            self._display_optimize_results(top_combos)
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"优化失败: {str(ex)}", color=ft.Colors.RED_700),
                bgcolor=ft.Colors.AMBER_100
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _display_optimize_results(self, combos):
        self.optimize_result.controls.clear()
        
        self.optimize_btn.text = "优化配置"

        for i, combo in enumerate(combos):  # 修改这行
            self.optimize_result.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"第{i+1}名配置 (DPS: {combo.dps:.2f})", 
                            weight="bold", color=ft.colors.ORANGE_700),
                        ft.Text("武器孔位:", size=12),
                        self._build_gem_list(combo.weapon_gems),
                        ft.Text("装备孔位:", size=12),
                        self._build_gem_list(combo.equip_gems),
                        ft.Divider()
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    bgcolor=ft.colors.GREY_50
                )
            )
        
        self.optimize_result.visible = True
        self.page.update()

    def _build_gem_list(self, gems):
        return ft.Row(
            controls=[self._gem_chip(g) for g in gems if g],
            wrap=True,
            spacing=5
        )

    def _gem_chip(self, gem_name):
        return ft.Chip(
            label=ft.Text(gem_name),
            bgcolor=ft.colors.ORANGE_50,
            check_color=ft.colors.ORANGE_800
        )

def main(page: ft.Page):
    page.title = "MHWs超级弩枪计算器v0.1.0"
    #page.window_icon = "assets/iconHBG.ico"
    page.window_width = 1080
    page.window_height = 1920
    # 设置全局主题
    page.theme = ft.Theme(
        # 复选框主题
        checkbox_theme=ft.CheckboxTheme(
            check_color=ft.Colors.WHITE,
            fill_color={
                "selected": ft.Colors.ORANGE_600,  # 选中状态
                "": ft.Colors.GREY_400,            # 默认状态
            }
        ),
        # 单选按钮主题
        radio_theme=ft.RadioTheme(
            fill_color={
                "selected": ft.Colors.ORANGE_600,
                "": ft.Colors.GREY_400,
            }
        ),
        slider_theme=ft.SliderTheme(
            active_track_color=ft.Colors.ORANGE_600,    # 激活轨道颜色
            inactive_track_color=ft.Colors.GREY_400,  # 未激活轨道颜色
            thumb_color=ft.Colors.ORANGE_ACCENT,        # 滑块颜色
            overlay_color=ft.Colors.ORANGE_100,         # 点击时的涟漪效果颜色
            value_indicator_color=ft.Colors.ORANGE_800  # 数值指示器颜色
        )
    )
    
    state = AppState()
    calculator = MHWCalculator(page, state)
    page.add(calculator)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")