from odoo import api, fields, models


class QuanLyTaiSanDashboard(models.Model):
    _name = "quan_ly_tai_san_dashboard"
    _description = "Dashboard quản lý tài sản"
    _rec_name = "name"

    name = fields.Char(default="Dashboard quản lý tài sản")
    tong_yeu_cau = fields.Integer("Tổng yêu cầu", compute="_compute_dashboard")
    yeu_cau_cho_duyet = fields.Integer("Chờ duyệt", compute="_compute_dashboard")
    yeu_cau_da_duyet = fields.Integer("Đã duyệt", compute="_compute_dashboard")
    tong_tai_san = fields.Integer("Tổng tài sản", compute="_compute_dashboard")
    tai_san_dang_su_dung = fields.Integer("Đang sử dụng", compute="_compute_dashboard")
    tai_san_da_thanh_ly = fields.Integer("Đã thanh lý", compute="_compute_dashboard")
    tai_san_chua_khau_hao = fields.Integer("Chưa khấu hao", compute="_compute_dashboard")
    tai_san_dang_khau_hao = fields.Integer("Đang khấu hao", compute="_compute_dashboard")
    tai_san_khau_hao_xong = fields.Integer("Khấu hao xong", compute="_compute_dashboard")
    tong_dieu_chuyen = fields.Integer("Tổng điều chuyển", compute="_compute_dashboard")
    tong_thanh_ly = fields.Integer("Hồ sơ thanh lý", compute="_compute_dashboard")
    tong_nguyen_gia = fields.Float("Tổng nguyên giá", compute="_compute_dashboard")
    tong_gia_tri_dang_su_dung = fields.Float("Giá trị đang sử dụng", compute="_compute_dashboard")
    tong_gia_tri_thanh_ly = fields.Float("Tổng giá trị thanh lý", compute="_compute_dashboard")

    @api.depends()
    def _compute_dashboard(self):
        Asset = self.env["tai_san"]
        Request = self.env["yeu_cau_cap_tai_san"]
        Transfer = self.env["dieu_chuyen_tai_san"]
        Liquidation = self.env["thanh_ly_tai_san"]
        for record in self:
            all_assets = Asset.search([])
            in_use_assets = Asset.search([("trang_thai_su_dung", "=", "dang_su_dung")])
            liquidated_assets = Asset.search([("trang_thai_su_dung", "=", "thanh_ly")])
            record.tong_yeu_cau = Request.search_count([])
            record.yeu_cau_cho_duyet = Request.search_count([("trang_thai", "=", "cho_duyet")])
            record.yeu_cau_da_duyet = Request.search_count([("trang_thai", "=", "da_duyet")])
            record.tong_tai_san = len(all_assets)
            record.tai_san_dang_su_dung = len(in_use_assets)
            record.tai_san_da_thanh_ly = len(liquidated_assets)
            record.tai_san_chua_khau_hao = Asset.search_count([("trang_thai_khau_hao", "=", "chua_khau_hao")])
            record.tai_san_dang_khau_hao = Asset.search_count([("trang_thai_khau_hao", "=", "dang_khau_hao")])
            record.tai_san_khau_hao_xong = Asset.search_count([("trang_thai_khau_hao", "=", "hoan_thanh")])
            record.tong_dieu_chuyen = Transfer.search_count([])
            record.tong_thanh_ly = Liquidation.search_count([])
            record.tong_nguyen_gia = sum(all_assets.mapped("nguyen_gia"))
            record.tong_gia_tri_dang_su_dung = sum(in_use_assets.mapped("nguyen_gia"))
            record.tong_gia_tri_thanh_ly = sum(Liquidation.search([("trang_thai", "=", "da_duyet")]).mapped("gia_tri_thanh_ly"))

    def action_open_requests(self):
        return self._get_action("quan_ly_tai_san.action_yeu_cau_cap_tai_san", [])

    def action_open_pending_requests(self):
        return self._get_action("quan_ly_tai_san.action_yeu_cau_cap_tai_san", [("trang_thai", "=", "cho_duyet")])

    def action_open_assets(self):
        return self._asset_action([])

    def action_open_assets_in_use(self):
        return self._asset_action([("trang_thai_su_dung", "=", "dang_su_dung")])

    def action_open_assets_liquidated(self):
        return self._asset_action([("trang_thai_su_dung", "=", "thanh_ly")])

    def action_open_depreciating_assets(self):
        return self._asset_action([("trang_thai_khau_hao", "=", "dang_khau_hao")])

    def action_open_transfers(self):
        return self._get_action("quan_ly_tai_san.action_dieu_chuyen_tai_san", [])

    def action_open_liquidations(self):
        return self._get_action("quan_ly_tai_san.action_thanh_ly_tai_san", [])

    def _asset_action(self, domain):
        return self._get_action("quan_ly_tai_san.action_tai_san", domain)

    def _get_action(self, xml_id, domain):
        action = self.env.ref(xml_id).read()[0]
        action["domain"] = domain
        return action
