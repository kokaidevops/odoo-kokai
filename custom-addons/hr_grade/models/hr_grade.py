from odoo import _, api, fields, models


class HrGrade(models.Model):
    _name = 'hr.grade'
    _description = 'Hr Grade'

    name = fields.Char('Grade')
    description = fields.Text('Description')


class HrJobGrade(models.Model):
    _name = 'hr.job.grade'
    _description = 'Hr Job Grade'

    job_id = fields.Many2one('hr.job', string='Job')
    grade_id = fields.Many2one('hr.grade', string='Grade')


class HrJob(models.Model):
    _inherit = 'hr.job'

    grade_ids = fields.One2many('hr.job.grade', 'job_id', string='Grade')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    grade_id = fields.Many2one('hr.grade', string='Grade')
