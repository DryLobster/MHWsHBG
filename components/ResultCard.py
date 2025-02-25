import flet as ft

class ResultCard(ft.Container):
    """通用结果展示卡片"""
    def __init__(self, title, value, col_config={"sm": 6, "md": 4}):
        super().__init__(
            content=ft.Column([
                ft.Text(title, size=16),
                ft.Container(
                    content=value,
                    padding=5,
                    alignment=ft.alignment.center
                )
            ], spacing=5),
            col=col_config,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            animate=ft.Animation(300, "easeOut")
        )
