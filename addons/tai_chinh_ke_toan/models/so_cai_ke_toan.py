from odoo import fields, models


class SoCaiKeToan(models.Model):
    _name = "so_cai_ke_toan"
    _description = "Sổ cái kế toán"
    _rec_name = "dien_giai"
    _order = "ngay_ghi_so desc, id desc"

    ho_so_khau_hao_id = fields.Many2one("ho_so_khau_hao", string="Hồ sơ khấu hao")
    tai_san_id = fields.Many2one("tai_san", string="Tài sản", required=True)
    loai_giao_dich = fields.Selection(
        [
            ("khau_hao", "Khấu hao"),
            ("thanh_ly", "Thanh lý"),
        ],
        string="Loại giao dịch",
        required=True,
    )
    ngay_ghi_so = fields.Date("Ngày ghi sổ", required=True, default=fields.Date.context_today)
    tai_khoan_no = fields.Char("Tài khoản Nợ", required=True)
    tai_khoan_co = fields.Char("Tài khoản Có", required=True)
    phat_sinh_no = fields.Float("Phát sinh Nợ", required=True)
    phat_sinh_co = fields.Float("Phát sinh Có", required=True)
    dien_giai = fields.Text("Diễn giải", required=True)
