from odoo import _, api, fields, models


class SurveyCategory(models.Model):
    _name = 'survey.category'
    _description = 'Survey Category'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    value = fields.Float('Value')
    range = fields.Selection([
        ('hour', 'Hour(s)'),
        ('day', 'Day(s)'),
        ('month', 'Month(s)'),
        ('year', 'Year(s)'),
    ], string='Range', default='month')


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    category_id = fields.Many2one('survey.category', string='Category')