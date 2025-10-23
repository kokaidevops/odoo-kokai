from odoo import _, api, fields, models


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    partner_id = fields.Many2one('res.partner', string='Partner')