import flet as ft
from src.core.loader import GEM_DATA, SKILL_DATA

class GemInventoryUI(ft.Column):
    def __init__(self, page, inventory):
        super().__init__(expand=True)
        self.page = page
        self.inventory = inventory
        self._init_components()
        self._build_ui()

    def _init_components(self):
        """初始化所有UI组件"""
        # ===== 左侧组件 =====
        # 技能选择相关
        self.skill1_dropdown = ft.Dropdown(
            label="选择技能1",
            options=[ft.dropdown.Option("任意")] + [ft.dropdown.Option(s) for s in SKILL_DATA.keys()],
            on_change=self._update_level_options,
            expand=True
        )
        
        self.level1_dropdown = ft.Dropdown(
            label="等级1",
            disabled=True,
            options=[ft.dropdown.Option(str(i)) for i in range(1, 4)],
            expand=True
        )

        self.skill2_dropdown = ft.Dropdown(
            label="选择技能2",
            options=[
                ft.dropdown.Option("任意"),
                ft.dropdown.Option("无")
            ] + [ft.dropdown.Option(s) for s in SKILL_DATA.keys()],
            on_change=self._update_level_options,
            expand=True
        )
        
        self.level2_dropdown = ft.Dropdown(
            label="等级2",
            disabled=True,
            options=[ft.dropdown.Option(str(i)) for i in range(1, 4)],
            expand=True
        )

        # 操作按钮
        self.search_btn = ft.ElevatedButton(
            "搜索珠子",
            icon=ft.Icons.SEARCH,
            on_click=self._search_gems,
            
        )

        # 结果列表
        self.results_list = ft.GridView(
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=2.5,  # 稍高的宽高比
            spacing=10,
            padding=10,
            expand=True
        )

        # ===== 右侧组件 =====
        self.inventory_list = ft.GridView(
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=3,
            spacing=10,
            padding=10,
            expand=True
        )

        # 库存操作按钮
        self.bulk_add_btn = ft.ElevatedButton(
            "老金",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self._do_bulk_add,
            tooltip="使用神奇的老金之力添加所有珠子各5个，但过多珠子会导致计算时间上升"
        )
        self.refresh_btn = ft.ElevatedButton(
            "清空",
            icon = ft.Icons.DELETE, 
            tooltip="删除所有珠子，不可恢复，谨慎点击！",
            on_click=self._do_delete_all
        )
    def _build_ui(self):
        """构建整体布局"""
        # 左侧布局（添加珠子）
        left_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Row([self.skill1_dropdown, self.level1_dropdown]),
                        ft.Row([self.skill2_dropdown, self.level2_dropdown]),
                    ]),
                    self.search_btn,
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.results_list, height= 360
                )
            ], expand=True),
            expand=True,
            padding=10
        )

        # 右侧布局（库存）
        right_panel = ft.Container(
            content=ft.Column([
                ft.Row([self.bulk_add_btn, self.refresh_btn]),
                ft.Text("当前拥有的珠子:", weight="bold"),
                ft.Container(
                    content=self.inventory_list, height= 420
                ),
                
            ], expand=True),
            expand=True,
            padding=10,
            height= 520,
            border=ft.border.all(1, ft.colors.GREY_400)
        )

        # 主布局
        self.controls = [
            ft.Row(
                controls=[left_panel, right_panel],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        ]
        
        # 初始化数据
        self.results_list.controls = [self._build_gem_item(gem) for gem in GEM_DATA]
        self.inventory_list.controls = self._build_inventory_items()
        self.page.update()

    def _build_inventory_items(self):
        """构建库存条目列表（返回控件列表而不是GridView）"""
        controls = []

        for gem_name, count in self.inventory.get_all_gems().items():
            if count <= 0:
                continue

            controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            # 左侧文本区域（上下居中靠左）
                            ft.Column(
                                controls=[
                                    ft.Text(gem_name, weight="bold", size=14),
                                    ft.Text(
                                        f"{GEM_DATA[gem_name]['type']}  等级: {GEM_DATA[gem_name]['level']}", 
                                        size=12
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,  # 垂直居中
                                horizontal_alignment=ft.CrossAxisAlignment.START,  # 水平靠左
                                expand=True  # 占据剩余空间
                            ),
                            # 右侧操作区域（按钮在右上，数量在右下）
                            ft.Column(
                                controls=[
                                    # 删除按钮右上角
                                    ft.Row(
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.REMOVE_CIRCLE,
                                                icon_color="red400",
                                                icon_size=20,
                                                tooltip="移除",
                                                on_click=lambda e, gn=gem_name: self._remove_gem(gn)
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END  # 按钮靠右
                                    ),
                                    # 数量显示右下角
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                f"×{count}", 
                                                size=18, 
                                                color=ft.Colors.ORANGE_700,
                                                width=60,
                                                text_align=ft.TextAlign.RIGHT  # 文本右对齐1
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.END  # 靠右
                                    )
                                ],
                                spacing=5,
                                width=90,  # 固定右侧宽度
                                height=90,  # 与左侧文本区域高度匹配
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # 左右两侧分开
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,  # 整体垂直居中
                        expand=True  # 填满容器宽度
                    ),
                    padding=5,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    bgcolor=ft.colors.GREY_50,
                    height=70  # 固定容器高度确保垂直居中生效
                )
            )
        
        return controls

    def _build_gem_item(self, gem_name):
        """构建网格风格的搜索结果条目"""
        gem_data = GEM_DATA[gem_name]
        return ft.Container(
            content=ft.Row([
                # 左侧信息
                ft.Column([
                    ft.Text(gem_name, weight="bold", size=14),
                    ft.Text(f"{gem_data['type']}  等级: {gem_data['level']}", size=12),
                    #ft.Text(f"", size=12)
                ], expand=True),
                
                # 右侧操作
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color="green600",
                    icon_size=24,
                    tooltip="添加到库存",
                    on_click=lambda e, gn=gem_name: self._add_gem(gn)
                )
            ], 
            alignment="spaceBetween",
            vertical_alignment="center"),
            
            # 样式设置
            padding=ft.padding.all(12),
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
            bgcolor=ft.colors.GREY_50
        )

    def _do_bulk_add(self, e):
        for gem_name in GEM_DATA:
            # 每个宝石添加5个
            for _ in range(5):
                self.inventory.add_gem(gem_name)
        self._refresh_inventory()

    def _do_delete_all(self, e):
        # 移除库存里的所有宝石
        self.inventory.remove_all_gems()
        self._refresh_inventory()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def _update_level_options(self, e):
        """更新等级下拉选项（包含禁用逻辑）"""
        skill_dropdown = e.control
        level_dropdown = self.level1_dropdown if skill_dropdown == self.skill1_dropdown else self.level2_dropdown
        
        if skill_dropdown.value in ["任意", "无"]:
            level_dropdown.disabled = True
            level_dropdown.value = None
        else:
            level_dropdown.disabled = False
            if skill_dropdown.value in SKILL_DATA:
                max_level = min(SKILL_DATA[skill_dropdown.value].max_level, 3)
                levels = [str(i) for i in range(1, max_level+1)]
                level_dropdown.options = [ft.dropdown.Option(l) for l in levels]
                level_dropdown.value = levels[-1]
        self.page.update()

    def _search_gems(self, e):
        """修改后的搜索逻辑（带调试输出）"""
        print("\n===== 开始搜索 =====")
        print(f"GEM_DATA 总条目数: {len(GEM_DATA)}")
        
        # 获取搜索条件
        s1 = self.skill1_dropdown.value
        lv1 = int(self.level1_dropdown.value) if self.level1_dropdown.value else 0
        s2 = self.skill2_dropdown.value
        lv2 = int(self.level2_dropdown.value) if self.level2_dropdown.value else 0

        print(f"搜索条件: 技能1={s1}(≥{lv1}), 技能2={s2}(≥{lv2})")

        matched_gems = []
        
        for gem_name, gem_data in GEM_DATA.items():
            skills = gem_data['skills']
            print(f"\n检查珠子: {gem_name}")
            print(f"珠子技能: {skills}")
            
            cond1 = True
            cond2 = True

            # 检查技能1条件
            if s1 and s1 not in ["任意", "无"]:
                cond1 = any(s[0] == s1 and s[1] >= lv1 for s in skills)
                print(f"技能1检查: 需要{s1}≥{lv1} -> {'满足' if cond1 else '不满足'}")
            else:
                print(f"技能1检查: 任意条件 -> 自动满足")

            # 检查技能2条件
            if s2 == "无":
                cond2 = len(skills) < 2
                print(f"技能2检查: 需要无第二技能 -> {'满足' if cond2 else '不满足'}")
            elif s2 and s2 != "任意":
                cond2 = any(s[0] == s2 and s[1] >= lv2 for s in skills)
                print(f"技能2检查: 需要{s2}≥{lv2} -> {'满足' if cond2 else '不满足'}")
            else:
                print(f"技能2检查: 任意条件 -> 自动满足")

            if cond1 and cond2:
                print("√ 符合条件")
                matched_gems.append(gem_name)
            else:
                print("× 不符合条件")

        print(f"\n匹配到 {len(matched_gems)} 个珠子: {matched_gems}")

        # 更新结果列表
        self.results_list.controls = [self._build_gem_item(gem) for gem in matched_gems]
        self.page.update()

    def _add_gem(self, gem_name):
        """添加珠子到库存"""
        self.inventory.add_gem(gem_name)
        self._refresh_inventory()
        # 替换原来的show_snack_bar调用
        snack = ft.SnackBar(
            content=ft.Text("添加完成！"),
            action="好的",
            duration=2000
        )
        self.page.snack_bar = snack
        snack.open = True
        self.page.update()

    def _remove_gem(self, gem_name):
        """从库存移除珠子"""
        self.inventory.remove_gem(gem_name)
        self._refresh_inventory()
        #self.page.show_snack_bar(
            #ft.SnackBar(ft.Text(f"{gem_name} 移除成功!"), open=True)
        #)

    def _refresh_inventory(self):
        """刷新库存显示"""
        self.inventory_list.controls = self._build_inventory_items()
        self.page.update()
