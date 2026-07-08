from odoo import api, fields, models


class PhongBan(models.Model):
    _name = "phong_ban"
    _description = "Phòng ban"
    _rec_name = "ten_phong_ban"
    _order = "ma_phong_ban asc"

    ma_phong_ban = fields.Char("Mã phòng ban", required=True, copy=False, readonly=True, default="New")
    ten_phong_ban = fields.Char("Tên phòng ban", required=True)
    mo_ta = fields.Text("Mô tả")
    nhan_vien_ids = fields.One2many("nhan_vien", inverse_name="phong_ban_id", string="Nhân viên")
    so_luong_nhan_vien = fields.Integer("Số lượng nhân viên", compute="_compute_so_luong_nhan_vien", store=True)

    _sql_constraints = [
        ('ma_phong_ban_unique', 'unique(ma_phong_ban)', 'Mã phòng ban phải là duy nhất')
    ]

    @api.depends("nhan_vien_ids")
    def _compute_so_luong_nhan_vien(self):
        for record in self:
            record.so_luong_nhan_vien = len(record.nhan_vien_ids)

    @api.model
    def create(self, vals):
        if vals.get("ma_phong_ban", "New") == "New":
            vals["ma_phong_ban"] = self.env["ir.sequence"].next_by_code("phong_ban") or "New"
        return super().create(vals)
