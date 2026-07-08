from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class YeuCauCapTaiSan(models.Model):
    _name = "yeu_cau_cap_tai_san"
    _description = "Yêu cầu cấp tài sản"
    _rec_name = "ma_yeu_cau"
    _order = "id desc"

    ma_yeu_cau = fields.Char("Mã yêu cầu", required=True, copy=False, readonly=True, default="New")
    ngay_yeu_cau = fields.Datetime("Ngày yêu cầu", default=fields.Datetime.now, required=True)
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban", required=True)
    nhan_vien_yeu_cau_id = fields.Many2one("nhan_vien", string="Nhân viên yêu cầu", required=True)
    ten_tai_san = fields.Char("Tên tài sản", required=True)
    loai_tai_san_id = fields.Many2one("loai_tai_san", string="Loại tài sản")
    loai_tai_san = fields.Char("Loại tài sản cũ")
    so_luong = fields.Integer("Số lượng", default=1, required=True)
    ngan_sach = fields.Float("Ngân sách")
    ly_do = fields.Text("Lý do")
    trang_thai = fields.Selection(
        [
            ("nhap", "Nháp"),
            ("cho_duyet", "Chờ duyệt"),
            ("da_duyet", "Đã duyệt"),
            ("tu_choi", "Từ chối"),
            ("da_tao_tai_san", "Đã tạo tài sản"),
        ],
        string="Trạng thái",
        default="nhap",
        required=True,
    )
    tai_san_ids = fields.One2many("tai_san", inverse_name="yeu_cau_id", string="Tài sản đã tạo")

    @api.onchange("nhan_vien_yeu_cau_id")
    def _onchange_nhan_vien_yeu_cau_id(self):
        for record in self:
            record.phong_ban_id = record.nhan_vien_yeu_cau_id.phong_ban_id

    @api.onchange("phong_ban_id")
    def _onchange_phong_ban_id(self):
        for record in self:
            if record.nhan_vien_yeu_cau_id and record.nhan_vien_yeu_cau_id.phong_ban_id != record.phong_ban_id:
                record.nhan_vien_yeu_cau_id = False

    @api.onchange("loai_tai_san_id")
    def _onchange_loai_tai_san_id(self):
        for record in self:
            record.loai_tai_san = record.loai_tai_san_id.ten_loai_tai_san

    @api.constrains("phong_ban_id", "nhan_vien_yeu_cau_id")
    def _check_employee_department(self):
        for record in self:
            if record.phong_ban_id and record.nhan_vien_yeu_cau_id and record.nhan_vien_yeu_cau_id.phong_ban_id != record.phong_ban_id:
                raise ValidationError("Nhân viên yêu cầu phải thuộc phòng ban đã chọn.")

    @api.model
    def create(self, vals):
        if vals.get("ma_yeu_cau", "New") == "New":
            vals["ma_yeu_cau"] = self.env["ir.sequence"].next_by_code("yeu_cau_cap_tai_san") or "New"
        if vals.get("nhan_vien_yeu_cau_id") and not vals.get("phong_ban_id"):
            vals["phong_ban_id"] = self.env["nhan_vien"].browse(vals["nhan_vien_yeu_cau_id"]).phong_ban_id.id
        self._sync_asset_type_vals(vals)
        return super().create(vals)

    def write(self, vals):
        if vals.get("nhan_vien_yeu_cau_id") and "phong_ban_id" not in vals:
            vals["phong_ban_id"] = self.env["nhan_vien"].browse(vals["nhan_vien_yeu_cau_id"]).phong_ban_id.id
        self._sync_asset_type_vals(vals)
        return super().write(vals)

    def _sync_asset_type_vals(self, vals):
        if vals.get("loai_tai_san_id"):
            vals["loai_tai_san"] = self.env["loai_tai_san"].browse(vals["loai_tai_san_id"]).ten_loai_tai_san
        elif vals.get("loai_tai_san") and not vals.get("loai_tai_san_id"):
            asset_type = self.env["loai_tai_san"].search([("ten_loai_tai_san", "=", vals["loai_tai_san"])], limit=1)
            if not asset_type:
                asset_type = self.env["loai_tai_san"].create({"ten_loai_tai_san": vals["loai_tai_san"]})
            vals["loai_tai_san_id"] = asset_type.id

    def action_gui_duyet(self):
        self.write({"trang_thai": "cho_duyet"})

    def action_tu_choi(self):
        self.write({"trang_thai": "tu_choi"})

    def action_duyet(self):
        for record in self:
            record.trang_thai = "da_duyet"
            record.action_tao_tai_san()

    def action_tao_tai_san(self):
        for record in self:
            if record.trang_thai not in ("da_duyet", "da_tao_tai_san"):
                raise UserError("Chỉ có thể tạo tài sản từ yêu cầu đã duyệt.")
            if record.tai_san_ids:
                record.trang_thai = "da_tao_tai_san"
                continue
            quantity = max(record.so_luong, 1)
            unit_value = record.ngan_sach / quantity if record.ngan_sach else 0
            asset_date = record._get_ngay_tao_tai_san()
            for index in range(quantity):
                name = record.ten_tai_san if quantity == 1 else "%s %s" % (record.ten_tai_san, index + 1)
                self.env["tai_san"].create({
                    "ten_tai_san": name,
                    "loai_tai_san_id": record.loai_tai_san_id.id,
                    "loai_tai_san": record.loai_tai_san_id.ten_loai_tai_san or record.loai_tai_san,
                    "nguyen_gia": unit_value,
                    "ngay_tao_tai_san": asset_date,
                    "nhan_vien_su_dung_id": record.nhan_vien_yeu_cau_id.id,
                    "phong_ban_id": record.phong_ban_id.id,
                    "yeu_cau_id": record.id,
                })
            record.trang_thai = "da_tao_tai_san"

    def _get_ngay_tao_tai_san(self):
        self.ensure_one()
        request_dt = fields.Datetime.to_datetime(self.ngay_yeu_cau) or fields.Datetime.now()
        now_dt = fields.Datetime.now()
        asset_date = fields.Date.to_date(request_dt)
        if now_dt > request_dt + timedelta(hours=24):
            asset_date += timedelta(days=1)
        return asset_date
