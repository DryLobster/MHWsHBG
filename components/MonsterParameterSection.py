import flet as ft
from components.SectionTitle import SectionTitle

class MonsterParameterSection(ft.Column):
    def __init__(self,
                 phys_zone,
                 elem_zone,
                 scar_check,
                 enraged,
                 enrage_multiplier,
                 enrage_ratio,
                 laser_multiplier,
                 laser_hit,
                 virus_slider):
        super().__init__(spacing=12)
        
        #* 肉质参数列
        hitzone_col = ft.Column([
            phys_zone,
            elem_zone,
            scar_check
        ], spacing=8)
        
        #* 愤怒参数列
        enrage_col = ft.Column([
            enrage_multiplier,
            ft.Text("愤怒时间占比"),
            enrage_ratio,
            enraged
        ], spacing=8)

        #* 穿甲弹参数列
        laser_col = ft.Column([
            laser_multiplier,
            laser_hit,
            ft.Text("狂龙病"),
            virus_slider
        ], spacing=8)
        
        self.controls = [
            SectionTitle("标靶参数"),
            ft.Row([hitzone_col, enrage_col, laser_col], spacing=30, vertical_alignment= "start")
        ]
