from odoo import fields, models


class NhatKyTuDongHoa(models.Model):
    _name = "nhat_ky_tu_dong_hoa"
    _description = "Nhật ký tự động hóa và tích hợp"
    _rec_name = "ten_tac_vu"
    _order = "ngay_thuc_hien desc, id desc"

    ten_tac_vu = fields.Char("Tên tác vụ", required=True)
    loai_tac_vu = fields.Selection(
        [
            ("khau_hao", "Tự động khấu hao"),
            ("email", "External API - Email"),
            ("llm", "AI/LLM"),
            ("ocr", "OCR"),
            ("external_api", "External API khác"),
        ],
        string="Loại tác vụ",
        required=True,
    )
    model_nguon = fields.Char("Model nguồn")
    res_id_nguon = fields.Integer("ID bản ghi nguồn")
    tai_san_id = fields.Many2one("tai_san", string="Tài sản")
    ho_so_khau_hao_id = fields.Many2one("ho_so_khau_hao", string="Hồ sơ khấu hao")
    mail_id = fields.Many2one("mail.mail", string="Email liên quan")
    du_lieu_dau_vao = fields.Text("Dữ liệu đầu vào")
    thao_tac_xu_ly = fields.Text("Thao tác xử lý")
    ket_qua_dau_ra = fields.Text("Kết quả đầu ra")
    trang_thai = fields.Selection(
        [
            ("nhap", "Nháp"),
            ("cho_xu_ly", "Chờ xử lý"),
            ("thanh_cong", "Thành công"),
            ("loi", "Lỗi"),
        ],
        string="Trạng thái",
        default="nhap",
        required=True,
    )
    loi = fields.Text("Thông tin lỗi")
    ngay_thuc_hien = fields.Datetime("Ngày thực hiện", default=fields.Datetime.now, required=True)
