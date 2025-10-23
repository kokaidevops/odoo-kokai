from odoo import _, api, fields, models


class SafetyObservation(models.Model):
    _name = 'safety.observation'
    _description = 'Safety Observation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    name = fields.Char('Name', tracking=True)
    date = fields.Date('Observation Date', default=fields.Date.today(), tracking=True)
    observation_time = fields.Datetime('Observation Time', default=fields.Datetime.now(), tracking=True)
    assessor_id = fields.Many2one('res.users', string='Assessor', default=lambda self: self.env.user.id, tracking=True)
    location_id = fields.Many2one('hr.work.location', string='Location', tracking=True)
    area_id = fields.Many2one('hr.work.area', string='Area', tracking=True)
    type = fields.Selection([
        ('safe_action', 'Safe Action'),
        ('unsafe_action', 'Unsafe Action'),
        ('unsafe_condition', 'Unsafe Condition'),
    ], string='Type', tracking=True)
    description = fields.Text('Description', tracking=True)
    handling_action = fields.Text('Handling Action', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('safety.observation')
        return super(SafetyObservation, self).create(vals)

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_done(self):
        self.ensure_one()
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })
