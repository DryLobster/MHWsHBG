import flet as ft

class TabCard(ft.Card):
    """统一风格的区块卡片"""
    def __init__(self, content, height):
        super().__init__(
            elevation=2,
            content=ft.Container(
                content=ft.Column([
                    content
                ], spacing=8),
                padding=10, height=height,
            )
        )
