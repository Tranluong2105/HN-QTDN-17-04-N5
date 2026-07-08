from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_ten_day_du'
    _order = 'ten asc, tuoi desc'

    ma_nhan_vien = fields.Char("Mã nhân viên", required=True, copy=False, readonly=True, default="New")
    ma_dinh_danh = fields.Char("Mã định danh")

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_ten_day_du = fields.Char("Họ và tên đầy đủ", compute="_compute_ho_ten_day_du", store=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_ten_day_du", store=True)

    chuc_vu = fields.Many2one("chuc_vu", string="Chức vụ")
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban")
    user_id = fields.Many2one("res.users", string="Người dùng hệ thống")

    ngay_sinh = fields.Date("Ngày sinh")
    gioi_tinh = fields.Selection(
        [
            ("nam", "Nam"),
            ("nu", "Nữ"),
            ("khac", "Khác"),
        ],
        string="Giới tính",
    )
    que_quan = fields.Char("Quê quán")
    so_dien_thoai = fields.Char("Số điện thoại")
    email = fields.Char("Email")
    dia_chi = fields.Char("Địa chỉ")
    trang_thai = fields.Selection(
        [
            ("dang_lam", "Đang làm"),
            ("nghi_viec", "Nghỉ việc"),
        ],
        string="Trạng thái",
        default="dang_lam",
        required=True,
    )
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", 
                                        compute="_compute_so_nguoi_bang_tuoi",
                                        store=True
                                        )
    
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['nhan_vien'].search(
                    [
                        ('tuoi', '=', record.tuoi),
                        ('id', '!=', record.id)
                    ]
                )
                record.so_nguoi_bang_tuoi = len(records)
            else:
                record.so_nguoi_bang_tuoi = 0

    _sql_constraints = [
        ('ma_nhan_vien_unique', 'unique(ma_nhan_vien)', 'Mã nhân viên phải là duy nhất'),
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_ten_day_du(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                full_name = record.ho_ten_dem + ' ' + record.ten
            else:
                full_name = False
            record.ho_ten_day_du = full_name
            record.ho_va_ten = full_name
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year
            else:
                record.tuoi = 0

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.ngay_sinh and record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")

    @api.model
    def create(self, vals):
        if vals.get("ma_nhan_vien", "New") == "New":
            vals["ma_nhan_vien"] = self.env["ir.sequence"].next_by_code("nhan_vien") or "New"
        return super().create(vals)
