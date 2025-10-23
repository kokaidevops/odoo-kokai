from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    minimum_wage_id = fields.Many2one('hr.minimum.wage', string='Minimum Wage')
    max_pens_cont_id = fields.Many2one('hr.minimum.wage', string='Maximal Pension Contribution Salary')
    max_health_ins_id = fields.Many2one('hr.minimum.wage', string='Maximal Health Insurance Salary')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    minimum_wage_id = fields.Many2one('hr.minimum.wage', string='Minimum Wage', related='company_id.minimum_wage_id', readonly=False)
    max_pens_cont_id = fields.Many2one('hr.minimum.wage', string='Maximal Pension Contribution Salary', related='company_id.max_pens_cont_id', readonly=False)
    max_health_ins_id = fields.Many2one('hr.minimum.wage', string='Maximal Health Insurance Salary', related='company_id.max_health_ins_id', readonly=False)