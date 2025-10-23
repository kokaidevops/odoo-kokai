from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)


class OHSQuestion(models.Model):
    _name = 'ohs.question'
    _description = 'OHS Question'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Detail')
    type = fields.Selection([
        ('question', 'Question'),
        ('section', 'Section'),
    ], string='Type', default='question', required=True)
    department_ids = fields.Many2many('hr.department', string='Department')

    def action_submit_nc(self):
        ctx = dict(default_patrol_id=self.env.context.get('default_patrol_id'), default_question_id=self.id, active_ids=self.ids)
        return {
            'name': _('Nonconformity'),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'res_model': 'nonconformity.patrol',
            'target': 'current',
            'context': ctx,
        }


class OHSPatrol(models.Model):
    _name = 'ohs.patrol'
    _description = 'OHS Patrol'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name')
    department_id = fields.Many2one('hr.department', string='Department')
    nonconformity_ids = fields.One2many('nonconformity.patrol', 'patrol_id', string='Nonconformity')

    def action_show_question(self):
        self.ensure_one()
        action = self.env.ref('ohs_inspection.ohs_question_action').read()[0]
        action['domain'] = ['|', ('department_ids', 'in', [self.department_id.id]), ('department_ids', '=', False)]
        action['context'] = {'default_patrol_id': self.id}
        return action

    def action_show_nonconformity(self):
        self.ensure_one()
        action = self.env.ref('ohs_inspection.nonconformity_patrol_action').read()[0]
        action['domain'] = [('patrol_id', '=', self.id)]
        return action


class NonconformityPatrol(models.Model):
    _name = 'nonconformity.patrol'
    _description = 'Nonconformity Patrol'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    patrol_id = fields.Many2one('ohs.patrol', string='Patrol')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    question_id = fields.Many2one('ohs.question', string='Question')
    date = fields.Datetime('Date', default=fields.Datetime.now())
    name = fields.Char('Note')

    report_ids = fields.One2many('ohs.nonconformity', 'nonconformity_id', string='Report')
    report_count = fields.Integer('Report', compute='_compute_report_count', store=True)

    @api.depends('report_ids')
    def _compute_report_count(self):
        for record in self:
            record.report_count = len(record.report_ids)

    def action_show_report(self):
        self.ensure_one()
        action = self.env.ref('ohs_inspection.ohs_nonconformity_action').read()[0]
        action['domain'] = [('nonconformity_id', '=', self.id)]
        return action

    def generate_nonconformity_report(self):
        self.ensure_one()
        nonconformity_id = self.env['ohs.nonconformity'].create({
            'user_id': self.user_id.id,
            'date': fields.Date.today(),
            'nonconformity_id': self.id,
            'audite_id': self.patrol_id.department_id.manager_id.user_id.id,
        })
        action = self.env.ref('ohs_inspection.ohs_nonconformity_action').read()[0]
        action['domain'] = [('nonconformity_id', '=', self.id)]
        action['views'] = [(self.env.ref('ohs_inspection.ohs_nonconformity_view_form').id, 'form')]
        action['res_id'] = nonconformity_id.id
        return action