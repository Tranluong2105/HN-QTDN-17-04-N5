from odoo import fields, models


class ButToanKeToan(models.Model):
    _name = "but_toan_ke_toan"
    _description = "Bút toán kế toán cũ"
    _rec_name = "dien_giai"
    _order = "ngay_hach_toan desc, id desc"

    ho_so_khau_hao_id = fields.Many2one("ho_so_khau_hao", string="Hồ sơ khấu hao")
    tai_san_id = fields.Many2one("tai_san", string="Tài sản")
    loai_but_toan = fields.Selection(
        [
            ("khau_hao", "Khấu hao"),
            ("thanh_ly", "Thanh lý"),
        ],
        string="Loại bút toán",
    )
    so_tien = fields.Float("Số tiền")
    ngay_hach_toan = fields.Date("Ngày hạch toán", default=fields.Date.context_today)
    dien_giai = fields.Text("Diễn giải")
