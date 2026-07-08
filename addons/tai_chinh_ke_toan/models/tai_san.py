from odoo import models


class TaiSan(models.Model):
    _inherit = "tai_san"

    def _auto_create_depreciation_profile(self):
        profile_model = self.env["ho_so_khau_hao"]
        profiles = profile_model
        for asset in self:
            asset_type = asset.loai_tai_san_id
            if not asset_type.tu_dong_khau_hao:
                continue
            if not asset_type.thoi_gian_khau_hao_mac_dinh:
                continue
            if asset.nguyen_gia <= 0:
                continue
            existing_profile = profile_model.search([("tai_san_id", "=", asset.id)], limit=1)
            if existing_profile:
                profiles |= existing_profile
                continue
            recovery_value = asset.nguyen_gia * asset_type.ty_le_gia_tri_thu_hoi / 100
            profile = profile_model.create({
                "tai_san_id": asset.id,
                "nguyen_gia": asset.nguyen_gia,
                "gia_tri_thu_hoi": recovery_value,
                "thoi_gian_khau_hao": asset_type.thoi_gian_khau_hao_mac_dinh,
                "ngay_bat_dau_khau_hao": asset.ngay_tao_tai_san,
            })
            profile.action_bat_dau_khau_hao()
            profiles |= profile
        return profiles

    def create(self, vals):
        asset = super().create(vals)
        asset._auto_create_depreciation_profile()
        return asset

    def write(self, vals):
        result = super().write(vals)
        if {"loai_tai_san_id", "nguyen_gia", "ngay_tao_tai_san"} & set(vals):
            self._auto_create_depreciation_profile()
        return result
