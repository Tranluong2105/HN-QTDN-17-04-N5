from odoo import api, fields, models


class TaiSan(models.Model):
    _name = "tai_san"
    _description = "Tài sản"
    _rec_name = "ten_tai_san"
    _order = "ma_tai_san asc"

    ma_tai_san = fields.Char("Mã tài sản", required=True, copy=False, readonly=True, default="New")
    ten_tai_san = fields.Char("Tên tài sản", required=True)
    loai_tai_san_id = fields.Many2one("loai_tai_san", string="Loại tài sản")
    loai_tai_san = fields.Char("Loại tài sản cũ")
    ngay_tao_tai_san = fields.Date("Ngày tạo tài sản", default=fields.Date.context_today, required=True)
    nguyen_gia = fields.Float("Nguyên giá", required=True)
    gia_tri_thu_hoi = fields.Float("Giá trị thu hồi")
    nhan_vien_su_dung_id = fields.Many2one("nhan_vien", string="Nhân viên sử dụng")
    nguoi_quan_ly_id = fields.Many2one("nhan_vien", string="Người quản lý tài sản")
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban")
    trang_thai_khau_hao = fields.Selection(
        [
            ("chua_khau_hao", "Chưa khấu hao"),
            ("dang_khau_hao", "Đang khấu hao"),
            ("hoan_thanh", "Khấu hao xong"),
            ("da_thanh_ly", "Đã thanh lý"),
        ],
        string="Trạng thái khấu hao",
        default="chua_khau_hao",
        required=True,
    )
    trang_thai_su_dung = fields.Selection(
        [
            ("dang_su_dung", "Đang sử dụng"),
            ("thanh_ly", "Đã thanh lý"),
        ],
        string="Trạng thái sử dụng",
        default="dang_su_dung",
        required=True,
    )
    yeu_cau_id = fields.Many2one("yeu_cau_cap_tai_san", string="Yêu cầu cấp tài sản")

    _sql_constraints = [
        ('ma_tai_san_unique', 'unique(ma_tai_san)', 'Mã tài sản phải là duy nhất')
    ]

    @api.onchange("nhan_vien_su_dung_id")
    def _onchange_nhan_vien_su_dung_id(self):
        for record in self:
            record.phong_ban_id = record.nhan_vien_su_dung_id.phong_ban_id
            if not record.nguoi_quan_ly_id:
                record.nguoi_quan_ly_id = record.nhan_vien_su_dung_id

    @api.onchange("yeu_cau_id")
    def _onchange_yeu_cau_id(self):
        for record in self:
            if not record.yeu_cau_id:
                continue
            record.ten_tai_san = record.yeu_cau_id.ten_tai_san
            record.loai_tai_san_id = record.yeu_cau_id.loai_tai_san_id
            record.loai_tai_san = record.yeu_cau_id.loai_tai_san
            record.nguyen_gia = record._get_nguyen_gia_tu_yeu_cau(record.yeu_cau_id)
            record.ngay_tao_tai_san = record.yeu_cau_id._get_ngay_tao_tai_san()
            record.nhan_vien_su_dung_id = record.yeu_cau_id.nhan_vien_yeu_cau_id
            record.nguoi_quan_ly_id = record.yeu_cau_id.nhan_vien_yeu_cau_id
            record.phong_ban_id = record.yeu_cau_id.phong_ban_id

    @api.model
    def create(self, vals):
        if vals.get("ma_tai_san", "New") == "New":
            vals["ma_tai_san"] = self.env["ir.sequence"].next_by_code("tai_san") or "New"
        self._sync_request_vals(vals)
        if vals.get("nhan_vien_su_dung_id") and not vals.get("phong_ban_id"):
            vals["phong_ban_id"] = self.env["nhan_vien"].browse(vals["nhan_vien_su_dung_id"]).phong_ban_id.id
        if vals.get("nhan_vien_su_dung_id") and not vals.get("nguoi_quan_ly_id"):
            vals["nguoi_quan_ly_id"] = vals["nhan_vien_su_dung_id"]
        self._sync_asset_type_vals(vals)
        record = super().create(vals)
        if record.yeu_cau_id and record.yeu_cau_id.trang_thai != "da_tao_tai_san":
            record.yeu_cau_id.trang_thai = "da_tao_tai_san"
        record._gui_telegram_tai_san_duoc_tao()
        return record

    def write(self, vals):
        self._sync_request_vals(vals)
        if vals.get("nhan_vien_su_dung_id") and "phong_ban_id" not in vals:
            vals["phong_ban_id"] = self.env["nhan_vien"].browse(vals["nhan_vien_su_dung_id"]).phong_ban_id.id
        if vals.get("nhan_vien_su_dung_id") and "nguoi_quan_ly_id" not in vals:
            vals["nguoi_quan_ly_id"] = vals["nhan_vien_su_dung_id"]
        self._sync_asset_type_vals(vals)
        return super().write(vals)

    def _sync_request_vals(self, vals):
        if not vals.get("yeu_cau_id"):
            return
        request = self.env["yeu_cau_cap_tai_san"].browse(vals["yeu_cau_id"])
        vals.setdefault("ten_tai_san", request.ten_tai_san)
        vals.setdefault("loai_tai_san_id", request.loai_tai_san_id.id)
        vals.setdefault("loai_tai_san", request.loai_tai_san_id.ten_loai_tai_san or request.loai_tai_san)
        vals.setdefault("nguyen_gia", self._get_nguyen_gia_tu_yeu_cau(request))
        vals.setdefault("ngay_tao_tai_san", request._get_ngay_tao_tai_san())
        vals.setdefault("nhan_vien_su_dung_id", request.nhan_vien_yeu_cau_id.id)
        vals.setdefault("nguoi_quan_ly_id", request.nhan_vien_yeu_cau_id.id)
        vals.setdefault("phong_ban_id", request.phong_ban_id.id)

    def _get_nguyen_gia_tu_yeu_cau(self, request):
        quantity = max(request.so_luong, 1)
        return request.ngan_sach / quantity if request.ngan_sach else 0

    def _sync_asset_type_vals(self, vals):
        if vals.get("loai_tai_san_id"):
            vals["loai_tai_san"] = self.env["loai_tai_san"].browse(vals["loai_tai_san_id"]).ten_loai_tai_san
        elif vals.get("loai_tai_san") and not vals.get("loai_tai_san_id"):
            asset_type = self.env["loai_tai_san"].search([("ten_loai_tai_san", "=", vals["loai_tai_san"])], limit=1)
            if not asset_type:
                asset_type = self.env["loai_tai_san"].create({"ten_loai_tai_san": vals["loai_tai_san"]})
            vals["loai_tai_san_id"] = asset_type.id

    def _gui_telegram_tai_san_duoc_tao(self):
        for record in self:
            record._gui_telegram_tai_san("TÀI SẢN ĐƯỢC TẠO")

    def _gui_telegram_tai_san_da_thanh_ly(self, liquidation=False):
        for record in self:
            record._gui_telegram_tai_san("TÀI SẢN ĐÃ THANH LÝ", liquidation=liquidation)

    def _gui_telegram_tai_san(self, tieu_de, liquidation=False):
        configs = self.env["cau_hinh_telegram_tai_san"].sudo().search([("active", "=", True)])
        if not configs:
            return
        for record in self:
            configs.gui_tin_nhan(record._get_telegram_message(tieu_de, liquidation=liquidation))

    def _get_telegram_message(self, tieu_de, liquidation=False):
        self.ensure_one()
        lines = [
            tieu_de,
            "Mã tài sản: %s" % (self.ma_tai_san or ""),
            "Tên tài sản: %s" % (self.ten_tai_san or ""),
            "Loại tài sản: %s" % (self.loai_tai_san_id.ten_loai_tai_san or self.loai_tai_san or ""),
            "Ngày tạo tài sản: %s" % (self.ngay_tao_tai_san or ""),
            "Nguyên giá: %s" % (self.nguyen_gia or 0),
            "Giá trị thu hồi: %s" % (self.gia_tri_thu_hoi or 0),
            "Nhân viên sử dụng: %s" % (self.nhan_vien_su_dung_id.ho_ten_day_du or ""),
            "Người quản lý tài sản: %s" % (self.nguoi_quan_ly_id.ho_ten_day_du or ""),
            "Phòng ban: %s" % (self.phong_ban_id.ten_phong_ban or ""),
            "Trạng thái khấu hao: %s" % dict(self._fields["trang_thai_khau_hao"].selection).get(self.trang_thai_khau_hao, ""),
            "Trạng thái sử dụng: %s" % dict(self._fields["trang_thai_su_dung"].selection).get(self.trang_thai_su_dung, ""),
        ]
        if liquidation:
            lines.extend([
                "Giá trị thanh lý: %s" % (liquidation.gia_tri_thanh_ly or 0),
                "Ngày thanh lý: %s" % (fields.Date.context_today(liquidation)),
                "Người duyệt thanh lý: %s" % (liquidation.nguoi_duyet_id.name or self.env.user.name or ""),
                "Lý do thanh lý: %s" % (liquidation.ly_do or ""),
            ])
        return "\n".join(lines)
