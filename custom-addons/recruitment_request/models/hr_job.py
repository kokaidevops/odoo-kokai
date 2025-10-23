from odoo import _, api, fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    no_of_recruitment = fields.Integer('Target', compute='_compute_recruitment_request', store=True)
    request_ids = fields.One2many('recruitment.request', 'job_id', string='Recruitment Request')
    request_count = fields.Integer('Recruitment Request Count', compute='_compute_recruitment_request')

    @api.depends('request_ids', 'request_ids.state')
    def _compute_recruitment_request(self):
        for record in self:
            record.request_count = len(record.request_ids.filtered(lambda request: request.state in ['approved']))
            record.no_of_recruitment = sum([request.target for request in record.request_ids.filtered(lambda rec: rec.state in ['approved'])])

    def action_show_request(self):
        self.ensure_one()
        if self.request_count == 0:
            return
        action = self.env.ref('recruitment_request.recruitment_request_action').read()[0]
        action['domain'] = [('id', 'in', self.request_ids.ids)]
        return action