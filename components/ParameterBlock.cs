import flet as ft

class ParameterBlock(ft.Column):
    """参数区块模板"""
    def __init__(self, title, *controls):
        super().__init__(
            controls=[
                ft.Text(title, weight="bold", size=16),
                ft.Divider(height=1),
                *controls
            ],
            spacing=8
        )