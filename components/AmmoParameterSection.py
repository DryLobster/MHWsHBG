import flet as ft
from components.SectionTitle import SectionTitle

class AmmoParameterSection(ft.Column):
    def __init__(self, 
                 ammo_dropdown,
                 bullet_level_slider,
                 phys_mv,
                 elem_mv,
                 hit,
                 ignore_hitzone):
        super().__init__(spacing=10)
        
        # 左侧列（弹药选择）
        left_col = ft.Column([
            ammo_dropdown,
            ft.Text("子弹等级"),
            bullet_level_slider
        ], spacing=8)

        # 右侧列（动作值）
        right_col = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("物理动作值"),
                    phys_mv,
                ]),
                ft.Column([
                    ft.Text("属性动作值"),
                    elem_mv,
                ]),     
            ]),
            ft.Row([
                ft.Column([
                    ft.Text("伤害次数"),
                    hit
                ]),
                ignore_hitzone
            ])
        ], spacing=20)
        
        self.controls = [
            SectionTitle("弹药参数"),
            ft.Row([left_col, right_col], spacing=30)
        ]
