from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ThanhLyTaiSan(models.Model):
    _name = "thanh_ly_tai_san"
    _description = "Thanh lý tài sản"
    _rec_name = "tai_san_id"
    _order = "id desc"

    tai_san_id = fields.Many2one(
        "tai_san",
        string="Tài sản",
        required=True,
        domain="[('trang_thai_su_dung', '!=', 'thanh_ly'), ('trang_thai_khau_hao', '!=', 'da_thanh_ly')]",
    )
    ly_do = fields.Text("Lý do")
    gia_tri_thanh_ly = fields.Float("Giá trị thanh lý")
    nguoi_duyet_id = fields.Many2one("res.users", string="Người duyệt")
    trang_thai = fields.Selection(
        [
            ("nhap", "Nháp"),
            ("da_duyet", "Đã duyệt"),
            ("tu_choi", "Từ chối"),
        ],
        string="Trạng thái",
        default="nhap",
        required=True,
    )

    @api.onchange("tai_san_id")
    def _onchange_tai_san_id(self):
        for record in self:
            record.gia_tri_thanh_ly = record._get_gia_tri_con_lai()

    def _is_asset_liquidated(self, asset):
        return asset.trang_thai_su_dung == "thanh_ly" or asset.trang_thai_khau_hao == "da_thanh_ly"

    def _check_asset_can_be_liquidated(self, asset):
        if asset and self._is_asset_liquidated(asset):
            raise UserError("Không thể chọn tài sản đã thanh lý.")

    def _get_gia_tri_con_lai(self):
        self.ensure_one()
        if not self.tai_san_id:
            return 0
        if "ho_so_khau_hao" in self.env.registry:
            profile = self.env["ho_so_khau_hao"].search([("tai_san_id", "=", self.tai_san_id.id)], limit=1)
            if profile:
                return profile.gia_tri_con_lai
        return self.tai_san_id.nguyen_gia

    @api.constrains("tai_san_id")
    def _check_asset_not_liquidated(self):
        for record in self:
            if record._is_asset_liquidated(record.tai_san_id):
                raise ValidationError("Không thể chọn tài sản đã thanh lý.")

    @api.model
    def create(self, vals):
        self._check_asset_can_be_liquidated(self.env["tai_san"].browse(vals.get("tai_san_id")))
        record = super().create(vals)
        if not record.gia_tri_thanh_ly:
            record.gia_tri_thanh_ly = record._get_gia_tri_con_lai()
        return record

    def write(self, vals):
        if vals.get("tai_san_id"):
            self._check_asset_can_be_liquidated(self.env["tai_san"].browse(vals["tai_san_id"]))
        return super().write(vals)

    def action_duyet(self):
        records_to_approve = self.filtered(lambda record: record.trang_thai != "da_duyet")
        for record in records_to_approve:
            record._check_asset_can_be_liquidated(record.tai_san_id)
            if not record.gia_tri_thanh_ly:
                record.gia_tri_thanh_ly = record._get_gia_tri_con_lai()
            record.nguoi_duyet_id = self.env.user
            record.trang_thai = "da_duyet"
            record.tai_san_id.trang_thai_su_dung = "thanh_ly"
            record.tai_san_id.trang_thai_khau_hao = "da_thanh_ly"
            record.tai_san_id._gui_telegram_tai_san_da_thanh_ly(liquidation=record)

    def action_tu_choi(self):
        self.write({"trang_thai": "tu_choi"})
