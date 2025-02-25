import flet as ft

class SectionTitle(ft.Column):
    """通用区块标题组件"""
    def __init__(self, title):
        super().__init__(
            controls=[
                ft.Text(title, weight="bold", size=16),
                ft.Divider(height=1)
            ],
            spacing=4
        )
