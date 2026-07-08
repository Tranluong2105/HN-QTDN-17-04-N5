from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LoaiTaiSan(models.Model):
    _name = "loai_tai_san"
    _description = "Loại tài sản"
    _rec_name = "ten_loai_tai_san"
    _order = "ten_loai_tai_san asc"

    ma_loai_tai_san = fields.Char("Mã loại tài sản", copy=False, readonly=True, default="New")
    ten_loai_tai_san = fields.Char("Tên loại tài sản", required=True)
    tu_dong_khau_hao = fields.Boolean("Tự động khấu hao", default=True)
    thoi_gian_khau_hao_mac_dinh = fields.Integer("Thời gian khấu hao mặc định (tháng)", default=36)
    ty_le_gia_tri_thu_hoi = fields.Float("Tỷ lệ giá trị thu hồi (%)", default=5.0)
    mo_ta = fields.Text("Mô tả")

    _sql_constraints = [
        ("ten_loai_tai_san_unique", "unique(ten_loai_tai_san)", "Tên loại tài sản phải là duy nhất."),
        ("ma_loai_tai_san_unique", "unique(ma_loai_tai_san)", "Mã loại tài sản phải là duy nhất."),
    ]

    @api.model
    def create(self, vals):
        if vals.get("ma_loai_tai_san", "New") == "New":
            vals["ma_loai_tai_san"] = self.env["ir.sequence"].next_by_code("loai_tai_san") or "New"
        return super().create(vals)

    @api.constrains("thoi_gian_khau_hao_mac_dinh", "ty_le_gia_tri_thu_hoi")
    def _check_depreciation_config(self):
        for record in self:
            if record.tu_dong_khau_hao and record.thoi_gian_khau_hao_mac_dinh <= 0:
                raise ValidationError("Thời gian khấu hao mặc định phải lớn hơn 0.")
            if record.ty_le_gia_tri_thu_hoi < 0 or record.ty_le_gia_tri_thu_hoi > 100:
                raise ValidationError("Tỷ lệ giá trị thu hồi phải nằm trong khoảng 0-100%.")
