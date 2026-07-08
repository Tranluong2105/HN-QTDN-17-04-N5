from odoo import models


class YeuCauCapTaiSan(models.Model):
    _inherit = "yeu_cau_cap_tai_san"

    def action_duyet(self):
        super().action_duyet()
        profiles = self._create_missing_depreciation_profiles()
        if profiles:
            return self._action_open_depreciation_profiles(profiles)
        return True

    def action_tao_tai_san(self):
        result = super().action_tao_tai_san()
        profiles = self._create_missing_depreciation_profiles()
        if profiles:
            return self._action_open_depreciation_profiles(profiles)
        return result

    def _create_missing_depreciation_profiles(self):
        profiles = self.env["ho_so_khau_hao"]
        for request in self:
            for asset in request.tai_san_ids:
                existing_profile = profiles.search([("tai_san_id", "=", asset.id)], limit=1)
                if existing_profile:
                    profiles |= existing_profile
                    continue
                profiles |= asset._auto_create_depreciation_profile()
        return profiles

    def _action_open_depreciation_profiles(self, profiles):
        action = self.env.ref("tai_chinh_ke_toan.action_ho_so_khau_hao").read()[0]
        if len(profiles) == 1:
            action.update({
                "view_mode": "form",
                "res_id": profiles.id,
                "views": [(False, "form")],
            })
        else:
            action["domain"] = [("id", "in", profiles.ids)]
        return action
