from odoo import _, api, fields, models


class PopupMessageWizard(models.TransientModel):
    _name = 'popup.message.wizard'
    _description = 'Popup Message Wizard'

    def _get_default_name(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Char('Message', readonly=True, default=_get_default_name)