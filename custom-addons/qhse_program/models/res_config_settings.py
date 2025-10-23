from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qhse_manager_id = fields.Many2one('res.users', string='QHSE Manager', related='company_id.qhse_manager_id', readonly=False)