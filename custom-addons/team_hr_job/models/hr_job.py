from odoo import _, api, fields, models


class HRJob(models.Model):
    _inherit = 'hr.job'

    team_ids = fields.One2many('department.team', 'job_id', string='Team')

    @api.model_create_multi
    def create(self, vals):
        res = super(HRJob, self).create(vals)
        for record in res:
            self.env['department.team'].create({
                'name': record.name,
                'department_id': record.department_id.id,
                'company_id': record.company_id.id,
                'user_id': record.department_id.manager_id.id,
                'job_id': record.id,
            })
        return res

    def generate_team(self):
        for record in self:
            self.env['department.team'].create({
                'name': record.name,
                'department_id': record.department_id.id,
                'company_id': record.company_id.id,
                'user_id': record.department_id.manager_id.id,
                'job_id': record.id,
            })



class DepartmentTeam(models.Model):
    _inherit = 'department.team'

    job_id = fields.Many2one('hr.job', string='Job Position', ondelete='cascade')
