from odoo import fields, models


class LichSuKhauHao(models.Model):
    _name = "lich_su_khau_hao"
    _description = "Lịch sử khấu hao"
    _rec_name = "ho_so_khau_hao_id"
    _order = "thang desc, id desc"

    ho_so_khau_hao_id = fields.Many2one("ho_so_khau_hao", string="Hồ sơ khấu hao", required=True, ondelete="cascade")
    thang = fields.Date("Tháng", required=True)
    so_tien = fields.Float("Số tiền", required=True)
    gia_tri_con_lai = fields.Float("Giá trị còn lại")
    ngay_ghi_nhan = fields.Date("Ngày ghi nhận", required=True)

    _sql_constraints = [
        ('ho_so_thang_unique', 'unique(ho_so_khau_hao_id, thang)', 'Mỗi hồ sơ chỉ được ghi nhận một lần trong một tháng.')
    ]
