from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class HoSoKhauHao(models.Model):
    _name = "ho_so_khau_hao"
    _description = "Hồ sơ khấu hao"
    _rec_name = "tai_san_id"
    _order = "id desc"

    tai_san_id = fields.Many2one(
        "tai_san",
        string="Tài sản",
        required=True,
        domain="[('trang_thai_khau_hao','=','chua_khau_hao'), ('trang_thai_su_dung','=','dang_su_dung')]",
    )
    nguyen_gia = fields.Float("Nguyên giá", readonly=True)
    gia_tri_thu_hoi = fields.Float("Giá trị thu hồi")
    gia_tri_phai_khau_hao = fields.Float("Giá trị phải khấu hao", compute="_compute_gia_tri", store=True)
    thoi_gian_khau_hao = fields.Integer("Thời gian khấu hao (tháng)")
    ngay_bat_dau_khau_hao = fields.Date("Ngày bắt đầu khấu hao", required=True)
    khau_hao_hang_thang = fields.Float("Khấu hao hàng tháng", compute="_compute_gia_tri", store=True)
    khau_hao_luy_ke = fields.Float("Khấu hao lũy kế", default=0)
    gia_tri_con_lai = fields.Float("Giá trị còn lại", compute="_compute_gia_tri_con_lai", store=True)
    so_thang_da_khau_hao = fields.Integer("Số tháng đã khấu hao", compute="_compute_tien_do_khau_hao")
    so_thang_con_lai = fields.Integer("Số tháng còn lại", compute="_compute_tien_do_khau_hao")
    ngay_du_kien_hoan_thanh = fields.Date("Ngày dự kiến hoàn thành", compute="_compute_tien_do_khau_hao")
    tong_da_ghi_so = fields.Float("Tổng đã ghi sổ", compute="_compute_tong_da_ghi_so")
    trang_thai = fields.Selection(
        [
            ("chua_khau_hao", "Chưa khấu hao"),
            ("dang_khau_hao", "Đang khấu hao"),
            ("hoan_thanh", "Hoàn thành"),
            ("dung", "Dừng"),
        ],
        string="Trạng thái",
        default="chua_khau_hao",
        required=True,
    )
    lich_su_khau_hao_ids = fields.One2many("lich_su_khau_hao", inverse_name="ho_so_khau_hao_id", string="Lịch sử khấu hao")
    so_cai_ke_toan_ids = fields.One2many("so_cai_ke_toan", inverse_name="ho_so_khau_hao_id", string="Sổ cái kế toán")
    da_gui_canh_bao_30_ngay = fields.Boolean("Đã gửi cảnh báo 30 ngày", default=False)

    _sql_constraints = [
        ('tai_san_unique', 'unique(tai_san_id)', 'Mỗi tài sản chỉ có 1 hồ sơ khấu hao.'),
        ('thoi_gian_positive', 'check(thoi_gian_khau_hao IS NULL OR thoi_gian_khau_hao > 0)', 'Thời gian khấu hao phải lớn hơn 0.'),
    ]

    @api.onchange("tai_san_id")
    def _onchange_tai_san_id(self):
        for record in self:
            record.nguyen_gia = record.tai_san_id.nguyen_gia
            record.gia_tri_thu_hoi = record.tai_san_id.gia_tri_thu_hoi
            record.ngay_bat_dau_khau_hao = record.tai_san_id.ngay_tao_tai_san

    @api.depends("nguyen_gia", "gia_tri_thu_hoi", "thoi_gian_khau_hao")
    def _compute_gia_tri(self):
        for record in self:
            depreciable = record.nguyen_gia - record.gia_tri_thu_hoi
            record.gia_tri_phai_khau_hao = depreciable
            record.khau_hao_hang_thang = depreciable / record.thoi_gian_khau_hao if record.thoi_gian_khau_hao else 0

    @api.depends("nguyen_gia", "khau_hao_luy_ke")
    def _compute_gia_tri_con_lai(self):
        for record in self:
            record.gia_tri_con_lai = max(record.nguyen_gia - record.khau_hao_luy_ke, 0)

    @api.depends("lich_su_khau_hao_ids", "thoi_gian_khau_hao", "ngay_bat_dau_khau_hao")
    def _compute_tien_do_khau_hao(self):
        for record in self:
            depreciated_months = len(record.lich_su_khau_hao_ids)
            record.so_thang_da_khau_hao = depreciated_months
            record.so_thang_con_lai = max((record.thoi_gian_khau_hao or 0) - depreciated_months, 0)
            record.ngay_du_kien_hoan_thanh = (
                record.ngay_bat_dau_khau_hao + relativedelta(months=record.thoi_gian_khau_hao)
                if record.ngay_bat_dau_khau_hao and record.thoi_gian_khau_hao
                else False
            )

    @api.depends("so_cai_ke_toan_ids.phat_sinh_no", "so_cai_ke_toan_ids.loai_giao_dich")
    def _compute_tong_da_ghi_so(self):
        for record in self:
            record.tong_da_ghi_so = sum(record.so_cai_ke_toan_ids.filtered(lambda line: line.loai_giao_dich == "khau_hao").mapped("phat_sinh_no"))

    @api.constrains("gia_tri_thu_hoi", "nguyen_gia")
    def _check_gia_tri_thu_hoi(self):
        for record in self:
            if record.gia_tri_thu_hoi < 0:
                raise ValidationError("Giá trị thu hồi không được âm.")
            if record.gia_tri_thu_hoi > record.nguyen_gia:
                raise ValidationError("Giá trị thu hồi không được lớn hơn nguyên giá.")

    @api.model
    def create(self, vals):
        if vals.get("tai_san_id"):
            asset = self.env["tai_san"].browse(vals["tai_san_id"])
            vals.setdefault("nguyen_gia", asset.nguyen_gia)
            vals.setdefault("ngay_bat_dau_khau_hao", asset.ngay_tao_tai_san)
        record = super().create(vals)
        record.tai_san_id.gia_tri_thu_hoi = record.gia_tri_thu_hoi
        return record

    def action_bat_dau_khau_hao(self):
        for record in self:
            if record.trang_thai != "chua_khau_hao":
                continue
            if not record.thoi_gian_khau_hao:
                raise UserError("Vui lòng nhập thời gian khấu hao trước khi bắt đầu.")
            if record.gia_tri_thu_hoi < 0:
                raise UserError("Vui lòng nhập giá trị thu hồi hợp lệ.")
            if record.tai_san_id.trang_thai_khau_hao != "chua_khau_hao":
                raise UserError("Tài sản đã có trạng thái khấu hao khác Chưa khấu hao.")
            record.write({"trang_thai": "dang_khau_hao"})
            record.tai_san_id.trang_thai_khau_hao = "dang_khau_hao"
            record._sync_depreciation_until_today()

    def action_dung_khau_hao(self):
        for record in self:
            if record.trang_thai == "dang_khau_hao":
                record.trang_thai = "dung"

    def action_hoan_thanh(self):
        for record in self:
            record.write({"trang_thai": "hoan_thanh", "khau_hao_luy_ke": record.gia_tri_phai_khau_hao})
            record.tai_san_id.trang_thai_khau_hao = "hoan_thanh"

    def action_gui_canh_bao_30_ngay(self):
        accountants = self._get_depreciation_warning_recipients()
        if not accountants:
            raise UserError("Không tìm thấy nhân viên có chức vụ Kế toán/Trưởng phòng Kế toán và có email.")
        sent_count = 0
        for record in self:
            if not record._is_within_30_days_to_finish():
                raise UserError("Tài sản %s chưa nằm trong khoảng 30 ngày trước ngày hết khấu hao." % record.tai_san_id.display_name)
            record._send_depreciation_warning(accountants)
            record.da_gui_canh_bao_30_ngay = True
            sent_count += len(accountants)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Đã tạo email cảnh báo",
                "message": "Đã tạo %s email cảnh báo. Vào Settings > Technical > Email > Emails để xem." % sent_count,
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def cron_tao_khau_hao_hang_thang(self):
        profiles = self.search([("trang_thai", "=", "dang_khau_hao")])
        for profile in profiles:
            profile._sync_depreciation_until_today()

    def _sync_depreciation_until_today(self):
        today = fields.Date.context_today(self)
        history_model = self.env["lich_su_khau_hao"]
        ledger_model = self.env["so_cai_ke_toan"]
        for profile in self:
            if not profile.ngay_bat_dau_khau_hao or not profile.thoi_gian_khau_hao:
                continue
            due_count = profile._get_due_depreciation_count(today)
            existing_count = history_model.search_count([("ho_so_khau_hao_id", "=", profile.id)])
            target_count = min(due_count, profile.thoi_gian_khau_hao)
            while existing_count < target_count and profile.khau_hao_luy_ke < profile.gia_tri_phai_khau_hao:
                period_index = existing_count + 1
                period_date = profile.ngay_bat_dau_khau_hao + relativedelta(months=period_index)
                amount = min(profile.khau_hao_hang_thang, profile.gia_tri_phai_khau_hao - profile.khau_hao_luy_ke)
                new_accumulated = profile.khau_hao_luy_ke + amount
                remaining_value = max(profile.nguyen_gia - new_accumulated, profile.gia_tri_thu_hoi)
                history_model.create({
                    "ho_so_khau_hao_id": profile.id,
                    "thang": period_date,
                    "so_tien": amount,
                    "gia_tri_con_lai": remaining_value,
                    "ngay_ghi_nhan": period_date,
                })
                ledger_model.create({
                    "ho_so_khau_hao_id": profile.id,
                    "tai_san_id": profile.tai_san_id.id,
                    "loai_giao_dich": "khau_hao",
                    "ngay_ghi_so": period_date,
                    "tai_khoan_no": "Chi phí khấu hao",
                    "tai_khoan_co": "Hao mòn lũy kế",
                    "phat_sinh_no": amount,
                    "phat_sinh_co": amount,
                    "dien_giai": "Khấu hao kỳ %s cho tài sản %s" % (period_index, profile.tai_san_id.display_name),
                })
                profile.khau_hao_luy_ke = new_accumulated
                existing_count += 1
            if target_count >= profile.thoi_gian_khau_hao or profile.khau_hao_luy_ke >= profile.gia_tri_phai_khau_hao:
                profile.action_hoan_thanh()

    def _get_due_depreciation_count(self, today):
        self.ensure_one()
        if today < self.ngay_bat_dau_khau_hao:
            return 0
        delta = relativedelta(today, self.ngay_bat_dau_khau_hao)
        return delta.years * 12 + delta.months

    @api.model
    def cron_canh_bao_30_ngay(self):
        self.cron_tao_khau_hao_hang_thang()
        accountants = self._get_depreciation_warning_recipients()
        if not accountants:
            return
        profiles = self.search([
            ("trang_thai", "=", "dang_khau_hao"),
            ("da_gui_canh_bao_30_ngay", "=", False),
        ])
        for profile in profiles:
            if not profile._is_within_30_days_to_finish():
                continue
            profile._send_depreciation_warning(accountants)
            profile.da_gui_canh_bao_30_ngay = True

    def _get_depreciation_warning_recipients(self):
        employees = self.env["nhan_vien"].search([
            ("chuc_vu.ten_chuc_vu", "ilike", "Trưởng phòng"),
            "|",
            ("phong_ban_id.ten_phong_ban", "ilike", "Kế toán"),
            ("phong_ban_id.ten_phong_ban", "ilike", "Tài chính"),
            ("email", "!=", False),
        ])
        if not employees:
            employees = self.env["nhan_vien"].search([
                ("chuc_vu.ten_chuc_vu", "ilike", "Kế toán"),
                ("email", "!=", False),
            ])
        if not employees:
            employees = self.env["nhan_vien"].search([
                ("chuc_vu.ten_chuc_vu", "ilike", "Ke toan"),
                ("email", "!=", False),
            ])
        return employees

    def _is_within_30_days_to_finish(self):
        self.ensure_one()
        if not self.ngay_bat_dau_khau_hao or not self.thoi_gian_khau_hao:
            return False
        today = fields.Date.context_today(self)
        finish_date = self.ngay_bat_dau_khau_hao + relativedelta(months=self.thoi_gian_khau_hao)
        remaining_days = (finish_date - today).days
        return 0 <= remaining_days <= 30

    def _send_depreciation_warning(self, accountants):
        for profile in self:
            finish_date = profile.ngay_bat_dau_khau_hao + relativedelta(months=profile.thoi_gian_khau_hao)
            body = (
                "Tài sản sắp hết khấu hao trong vòng 30 ngày.<br/>"
                "Mã tài sản: %s<br/>"
                "Tên tài sản: %s<br/>"
                "Loại tài sản: %s<br/>"
                "Phòng ban: %s<br/>"
                "Nhân viên sử dụng: %s<br/>"
                "Nguyên giá: %s<br/>"
                "Giá trị thu hồi: %s<br/>"
                "Khấu hao lũy kế: %s<br/>"
                "Giá trị còn lại: %s<br/>"
                "Ngày bắt đầu khấu hao: %s<br/>"
                "Ngày dự kiến hoàn thành: %s"
            ) % (
                profile.tai_san_id.ma_tai_san,
                profile.tai_san_id.ten_tai_san,
                profile.tai_san_id.loai_tai_san_id.display_name or profile.tai_san_id.loai_tai_san or "",
                profile.tai_san_id.phong_ban_id.display_name or "",
                profile.tai_san_id.nhan_vien_su_dung_id.display_name or "",
                profile.nguyen_gia,
                profile.gia_tri_thu_hoi,
                profile.khau_hao_luy_ke,
                profile.gia_tri_con_lai,
                profile.ngay_bat_dau_khau_hao,
                finish_date,
            )
            for employee in accountants:
                mail = self.env["mail.mail"].create({
                    "subject": "Cảnh báo tài sản sắp hết khấu hao",
                    "email_to": employee.email,
                    "email_from": self.env.user.email_formatted or self.env.company.email_formatted or "odoo@example.com",
                    "body_html": body,
                    "auto_delete": False,
                })
                mail.send(raise_exception=False)
