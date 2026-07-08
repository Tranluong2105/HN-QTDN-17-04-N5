from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class DieuChuyenTaiSan(models.Model):
    _name = "dieu_chuyen_tai_san"
    _description = "Điều chuyển tài sản"
    _rec_name = "tai_san_id"
    _order = "ngay_dieu_chuyen desc, id desc"

    tai_san_id = fields.Many2one(
        "tai_san",
        string="Tài sản",
        required=True,
        domain="[('trang_thai_su_dung', '!=', 'thanh_ly'), ('trang_thai_khau_hao', '!=', 'da_thanh_ly')]",
    )
    nhan_vien_cu_id = fields.Many2one("nhan_vien", string="Nhân viên cũ", readonly=True)
    nhan_vien_moi_id = fields.Many2one("nhan_vien", string="Nhân viên mới", required=True)
    phong_ban_cu_id = fields.Many2one("phong_ban", string="Phòng ban cũ", readonly=True)
    phong_ban_moi_id = fields.Many2one(
        "phong_ban",
        string="Phòng ban mới",
        readonly=True,
        required=True,
    )
    ly_do = fields.Text("Lý do")
    ngay_dieu_chuyen = fields.Date("Ngày điều chuyển", default=fields.Date.context_today, required=True)

    @api.onchange("tai_san_id")
    def _onchange_tai_san_id(self):
        for record in self:
            record.nhan_vien_cu_id = record.tai_san_id.nhan_vien_su_dung_id
            record.phong_ban_cu_id = record.tai_san_id.phong_ban_id

    @api.onchange("nhan_vien_moi_id")
    def _onchange_nhan_vien_moi_id(self):
        for record in self:
            record.phong_ban_moi_id = record.nhan_vien_moi_id.phong_ban_id

    @api.constrains("nhan_vien_moi_id", "phong_ban_moi_id")
    def _check_new_employee_department(self):
        for record in self:
            if record.nhan_vien_moi_id and record.phong_ban_moi_id and record.nhan_vien_moi_id.phong_ban_id != record.phong_ban_moi_id:
                raise ValidationError("Phòng ban mới phải là phòng ban của nhân viên mới.")

    @api.constrains("tai_san_id")
    def _check_asset_not_liquidated(self):
        for record in self:
            if record.tai_san_id.trang_thai_su_dung == "thanh_ly" or record.tai_san_id.trang_thai_khau_hao == "da_thanh_ly":
                raise ValidationError("Không thể điều chuyển tài sản đã thanh lý.")

    @api.model
    def create(self, vals):
        asset = self.env["tai_san"].browse(vals.get("tai_san_id"))
        if asset:
            if asset.trang_thai_su_dung == "thanh_ly" or asset.trang_thai_khau_hao == "da_thanh_ly":
                raise UserError("Không thể điều chuyển tài sản đã thanh lý.")
            vals.setdefault("nhan_vien_cu_id", asset.nhan_vien_su_dung_id.id)
            vals.setdefault("phong_ban_cu_id", asset.phong_ban_id.id)
        employee = self.env["nhan_vien"].browse(vals.get("nhan_vien_moi_id"))
        if employee:
            if not employee.phong_ban_id:
                raise UserError("Nhân viên mới chưa có phòng ban.")
            vals["phong_ban_moi_id"] = employee.phong_ban_id.id
        record = super().create(vals)
        record.tai_san_id.write({
            "nhan_vien_su_dung_id": record.nhan_vien_moi_id.id,
            "phong_ban_id": record.phong_ban_moi_id.id,
        })
        return record

    def write(self, vals):
        if vals.get("nhan_vien_moi_id"):
            employee = self.env["nhan_vien"].browse(vals["nhan_vien_moi_id"])
            if not employee.phong_ban_id:
                raise UserError("Nhân viên mới chưa có phòng ban.")
            vals["phong_ban_moi_id"] = employee.phong_ban_id.id
        result = super().write(vals)
        if "nhan_vien_moi_id" in vals or "tai_san_id" in vals:
            for record in self:
                if record.tai_san_id and record.nhan_vien_moi_id:
                    record.tai_san_id.write({
                        "nhan_vien_su_dung_id": record.nhan_vien_moi_id.id,
                        "phong_ban_id": record.phong_ban_moi_id.id,
                    })
        return result
