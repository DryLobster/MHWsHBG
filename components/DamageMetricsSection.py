import flet as ft

from components.ResultCard import ResultCard

class DamageMetricsSection(ft.ResponsiveRow):
    """主要伤害指标区块"""
    def __init__(self, 
                 result_damage,
                 result_damage_gatlin,
                 result_damage_laser):
        super().__init__(spacing=20)
        
        self.controls = [
            ResultCard("单发伤害:", result_damage),
            ResultCard("机关龙弹DPS:", result_damage_gatlin),
            ResultCard("穿甲弹DPS:", result_damage_laser)
        ]
