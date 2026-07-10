from odoo import fields, models


class ThanhLyTaiSan(models.Model):
    _inherit = "thanh_ly_tai_san"

    def action_duyet(self):
        records_to_account = self.filtered(lambda record: record.trang_thai != "da_duyet")
        result = super().action_duyet()
        for record in records_to_account:
            profile = self.env["ho_so_khau_hao"].search([
                ("tai_san_id", "=", record.tai_san_id.id),
            ], limit=1)
            if profile and profile.trang_thai == "dang_khau_hao":
                profile.trang_thai = "dung"
            self.env["so_cai_ke_toan"].create({
                "ho_so_khau_hao_id": profile.id if profile else False,
                "tai_san_id": record.tai_san_id.id,
                "loai_giao_dich": "thanh_ly",
                "ngay_ghi_so": fields.Date.context_today(self),
                "tai_khoan_no": "Thanh lý tài sản",
                "tai_khoan_co": "Tài sản cố định",
                "phat_sinh_no": record.gia_tri_thanh_ly,
                "phat_sinh_co": record.gia_tri_thanh_ly,
                "dien_giai": "Ghi sổ thanh lý tài sản %s" % record.tai_san_id.display_name,
            })
        return result
