from odoo import _, api, fields, models


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    job_id = fields.Many2one('hr.job', string='Job Position')
    resource_ids = fields.Many2many('resource.resource', 'resource_resource_planning_role_rel', 'planning_role_id', 'resource_resource_id', 'Resources', compute='_compute_resource_ids', readonly=False, store=True)

    @api.depends('job_id')
    def _compute_resource_ids(self):
        for record in self:
            resource_ids = []
            for employee in record.job_id.employee_ids:
                resource_ids.append((4, employee.resource_id.id))
            record.resource_ids = resource_ids


class HrJob(models.Model):
    _inherit = 'hr.job'

    role_id = fields.Many2one('planning.role', string='Planning Role')
    
    def _generate_planning_role(self):
        self.ensure_one()
        role = self.env['planning.role'].create({
            'name': self.name,
            'product_ids': [(4, self.env.ref('hr_expense.product_product_no_cost_product_template').id)],
        })
        self.write({ 'role_id': role.id })