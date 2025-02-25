import flet as ft

from components.ResultCard import ResultCard

class DetailMetricsSection(ft.ResponsiveRow):
    """详细参数区块"""
    def __init__(self, 
                 result_affinity,
                 result_crit_phys,
                 result_crit_elem,
                 result_final_attack
                 ):
        super().__init__(spacing=15)
        
        self.controls = [
            ResultCard("会心率", result_affinity, {"sm": 6, "md": 3}),
            ResultCard("物理暴击倍率", result_crit_phys, {"sm": 6, "md": 3}),
            ResultCard("属性暴击倍率", result_crit_elem, {"sm": 6, "md": 3}),
            ResultCard("最终攻击力", result_final_attack, {"sm": 6, "md": 3})
        ]
