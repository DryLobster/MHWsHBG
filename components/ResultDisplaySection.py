import flet as ft

class ResultDisplaySection(ft.Container):
    """结果展示主容器"""
    def __init__(self, 
                 damage_section,
                 detail_section):
        super().__init__(
            content=ft.Column([
                #ft.Text("计算结果", size=20, weight="bold",color=ft.Colors.ORANGE_800),
                damage_section,
                detail_section
            ], spacing=25),
            expand=True,
            padding=10,
            #bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.NONE
        )
