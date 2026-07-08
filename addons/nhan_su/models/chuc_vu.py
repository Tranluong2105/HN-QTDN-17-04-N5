from odoo import models, fields, api


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True, copy=False, readonly=True, default="New")
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    mo_ta = fields.Text("Mô tả")

    _sql_constraints = [
        ('ma_chuc_vu_unique', 'unique(ma_chuc_vu)', 'Mã chức vụ phải là duy nhất')
    ]

    @api.model
    def create(self, vals):
        if vals.get("ma_chuc_vu", "New") == "New":
            vals["ma_chuc_vu"] = self.env["ir.sequence"].next_by_code("chuc_vu") or "New"
        return super().create(vals)
