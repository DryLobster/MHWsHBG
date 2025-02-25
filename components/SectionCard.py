import flet as ft

class SectionCard(ft.Card):
    """统一风格的区块卡片"""
    def __init__(self, title, content):
        super().__init__(
            elevation=2,
            content=ft.Container(
                content=ft.Column([
                    ft.Text(title, size=16, weight="bold"),
                    ft.Divider(height=1),
                    content
                ], spacing=8),
                padding=10
            )
        )
