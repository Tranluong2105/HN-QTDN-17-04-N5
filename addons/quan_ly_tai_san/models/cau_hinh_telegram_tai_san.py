import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CauHinhTelegramTaiSan(models.Model):
    _name = "cau_hinh_telegram_tai_san"
    _description = "Cấu hình Telegram tài sản"
    _rec_name = "ten_cau_hinh"
    _order = "sequence, id"

    ten_cau_hinh = fields.Char("Tên cấu hình", required=True, default="Telegram quản lý tài sản")
    bot_token = fields.Char("Bot token", required=True)
    chat_id = fields.Char("Chat ID", required=True)
    bo_qua_xac_thuc_ssl = fields.Boolean("Bỏ qua xác thực SSL", default=True)
    active = fields.Boolean("Đang sử dụng", default=True)
    sequence = fields.Integer("Thứ tự", default=10)

    def gui_tin_nhan(self, noi_dung):
        for record in self.filtered("active"):
            record._gui_tin_nhan(noi_dung)

    def _gui_tin_nhan(self, noi_dung):
        self.ensure_one()
        if not self.bot_token or not self.chat_id:
            return

        try:
            self._send_telegram_request(noi_dung)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            _logger.warning("Không thể gửi tin nhắn Telegram tài sản: %s", error)

    def action_gui_thu_telegram(self):
        for record in self:
            if not record.bot_token or not record.chat_id:
                raise UserError("Bạn cần nhập Bot token và Chat ID trước khi gửi thử.")
            try:
                record._send_telegram_request("Kiểm tra kết nối Telegram từ Odoo: thành công.")
            except urllib.error.HTTPError as error:
                error_message = error.read().decode("utf-8", errors="ignore")
                raise UserError("Telegram từ chối yêu cầu: %s" % (error_message or error)) from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                raise UserError("Không thể kết nối Telegram. Kiểm tra mạng của Odoo/server và token/chat_id. Chi tiết: %s" % error) from error
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Telegram",
                "message": "Đã gửi tin nhắn thử thành công.",
                "type": "success",
                "sticky": False,
            },
        }

    def _send_telegram_request(self, noi_dung):
        self.ensure_one()
        url = "https://api.telegram.org/bot%s/sendMessage" % self.bot_token
        payload = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": noi_dung,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        request = urllib.request.Request(url, data=payload, method="POST")
        context = ssl._create_unverified_context() if self.bo_qua_xac_thuc_ssl else None
        with urllib.request.urlopen(request, timeout=10, context=context) as response:
            return response.read()
