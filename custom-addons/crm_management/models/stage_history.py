from odoo import _, api, fields, models

class StageHistory(models.Model):
    _name = 'stage.history'
    _description = 'History of Change Stage Lead'

    opportunity_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    old_stage_id = fields.Many2one('crm.stage', string='Old Stage')
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True)
    reason = fields.Text('Reason')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    date = fields.Datetime('Date')