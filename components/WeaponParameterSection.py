import flet as ft
from components.SectionTitle import SectionTitle

class WeaponParameterSection(ft.Column):
    def __init__(self,
                 attack_field,
                 affinity_field,
                 bowgun_type,
                 reload_slider,
                 magazine_slider,
                 bullet_position):
        super().__init__(spacing=12)
        
        # 武器基础参数列
        base_col = ft.Column([
            attack_field,
            affinity_field,
            ft.Text("龙热特化等级"),
            bowgun_type
        ], spacing=8)
        
        # 弹药相关参数列
        ammo_col = ft.Column([
            ft.Text("装填等级"),
            reload_slider,
            ft.Text("弹匣容量"),
            magazine_slider,
            ft.Text("子弹位置"),
            bullet_position
        ], spacing=8)
        
        self.controls = [
            SectionTitle("武器参数"),
            ft.Row([base_col, ammo_col], spacing=30)
        ]
