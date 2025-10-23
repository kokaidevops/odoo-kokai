from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATE_POSITION = {
    'parking': 'out',
    'out': 'come',
}


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    state = fields.Selection([
        ('parking', 'Parking'),
        ('usage', 'In Use'),
    ], string='Status', default='parking')

    usage_ids = fields.One2many('fleet.usage', 'fleet_id', string='Usage')
    usage_count = fields.Integer('Usage Count', compute='_compute_usage_count')
    @api.depends('usage_ids')
    def _compute_usage_count(self):
        for record in self:
            record.usage_count = len(record.usage_ids)
    
    def action_show_fleet_usage(self):
        self.ensure_one()
        if self.usage_count == 0:
            return
        action = self.env.ref('fleet_usage.fleet_usage_action').sudo().read()[0]
        action['domain'] = [('id', 'in', self.usage_ids.ids)]
        return action


class FleetUsage(models.Model):
    _name = 'fleet.usage'
    _description = 'Fleet Usage'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default='New Request')
    date = fields.Date('Date', default=fields.Date.today(), required=True, tracking=True)
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True)
    destination = fields.Char('Destination')
    usage_time = fields.Datetime('Usage Time')
    start_odometer = fields.Float('Start Odometer')
    start_tank = fields.Float('Start Tank')
    end_time = fields.Date('End Time')
    end_odometer = fields.Float('End Odometer')
    end_tank = fields.Float('End Tank')
    description = fields.Text('Description')
    driver_id = fields.Many2one('res.users', string='Driver', default=lambda self: self.env.user.id)
    passenger_ids = fields.Many2many('res.users', string='Passenger')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, default='draft')
    position = fields.Selection([
        ('parking', 'Parking'),
        ('out', 'Out'),
    ], string='Position', default='parking')

    equipment_ids = fields.One2many('fleet.equipment.usage', 'usage_id', string='Equipment')
    condition_ids = fields.One2many('fleet.condition.usage', 'usage_id', string='Condition')
    
    approval_ids = fields.One2many(comodel_name='approval.request', inverse_name='fleet_usage_id', string='Approval Request', readonly=True, copy=False, tracking=True)
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', readonly=True)
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.mapped('approval_ids'))

    def action_view_approval_request(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        action['domain'] = [('id', 'in', approvals.ids)]
        return action

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('fleet.usage')
        return super(FleetUsage, self).create(vals)

    @api.constrains('start_tank')
    def _check_start_tank_value(self):
        for record in self:
            if record.start_tank < 0 and record.start_tank > 1:
                raise ValidationError("The value of 'Start Tank' must be between 0 and 1")

    @api.constrains('end_tank')
    def _check_end_tank_value(self):
        for record in self:
            if record.end_tank < 0 and record.end_tank > 1:
                raise ValidationError("The value of 'End Tank' must be between 0 and 1")

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_requested(self):
        self.ensure_one()
        category_pr = self.env.company.approval_fleet_usage_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'fleet_usage_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Usage {self.fleet_id.name} for {self.driver_id.name} \n Fleet Usage for {self.description}"
        }
        approval = self.env['approval.request'].create(vals)
        if not approval:
            raise ValidationError("Can't Request Approval. Please Contact Administrator")
        request = self.approval_ids[self.approval_count-1]
        query = f"UPDATE approval_approver SET user_id={self.driver_id.department_id.manager_id.user_id.id} WHERE request_id={request.id} AND user_id=2"
        self.env.cr.execute(query)
        approval.action_confirm()
        self.write({ 'state': 'requested' })
        self.generate_equipment()

    def action_approved(self):
        self.ensure_one()
        # TODO needed notification to User?
        self.write({ 'state': 'approved' })

    def action_refused(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('fleet_usage.model_fleet_usage').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.driver_id.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'refused' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    def generate_equipment(self):
        self.ensure_one()
        for line in self.fleet_id.equipment_ids:
            self.env['fleet.equipment.usage'].create({
                'usage_id': self.id,
                'equipment_id': line.equipment_id.id,
                'remark': f"Equipment - {line.qty} {line.uom_id.name} ({line._fields['condition'].get(line.condition)})",
            })


class FleetEquipmentUsage(models.Model):
    _name = 'fleet.equipment.usage'
    _description = 'Fleet Equipment Usage'

    usage_id = fields.Many2one('fleet.usage', string='Usage', required=True)
    equipment_id = fields.Many2one('product.product', string='Equipment')
    remark = fields.Char('Remark')
    checked_ids = fields.One2many('fleet.checked', 'equipment_id', string='Checked')

    def action_good_checking(self):
        self.ensure_one()
        self.env['fleet.checked'].create({
            'equipment_id': self.id,
            'user_id': self.env.user.id,
            'remark': 'Equipment in Good Condition',
            'state': STATE_POSITION[self.usage_id.position],
            'condition': 'good',
        })

    def action_bad_checking(self):
        self.ensure_one()
        ctx = dict(default_equipment_id=self.id)
        return {
            'name': _('Bad Checking'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fleet.checked.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_show_history_checked(self):
        self.ensure_one()
        action = self.env.ref('fleet_usage.fleet_checked_action').read()[0]
        action['domain'] = [('usage_id', '=', self.usage_id), ('equipment_id', '=', self.equipment_id)]
        return action


class FleetConditionUsage(models.Model):
    _name = 'fleet.condition.usage'
    _description = 'Fleet Condition Usage'

    usage_id = fields.Many2one('fleet.usage', string='Usage', required=True)
    part = fields.Selection([
        ('right', 'Right'),
        ('front', 'Front'),
        ('left', 'Left'),
        ('back', 'Back'),
    ], string='Part', required=True)
    checked_ids = fields.One2many('fleet.checked', 'condition_id', string='Checked')

    def action_good_checking(self):
        self.ensure_one()
        self.env['fleet.checked'].create({
            'condition_id': self.id,
            'user_id': self.env.user.id,
            'remark': 'Part in Good Condition',
            'state': STATE_POSITION[self.usage_id.position],
            'condition': 'good',
        })

    def action_bad_checking(self):
        self.ensure_one()
        ctx = dict(default_condition_id=self.id)
        return {
            'name': _('Bad Checking'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fleet.checked.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_show_history_checked(self):
        self.ensure_one()
        action = self.env.ref('fleet_usage.fleet_checked_action').read()[0]
        action['domain'] = [('usage_id', '=', self.usage_id), ('equipment_id', '=', self.equipment_id)]
        return action


class FleetChecked(models.Model):
    _name = 'fleet.checked'
    _description = 'Fleet Checked'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    equipment_id = fields.Many2one('fleet.equipment.usage', string='Equipment')
    condition_id = fields.Many2one('fleet.condition.usage', string='Condition')
    user_id = fields.Many2one('res.users', string='Checked By', tracking=True)
    remark = fields.Char('Remark')
    state = fields.Selection([
        ('out', 'Out'),
        ('come', 'Come'),
    ], string='State', default='out', tracking=True)
    checked_date = fields.Datetime('Checked Date', default=fields.Datetime.now(), tracking=True)
    condition = fields.Selection([
        ('bad', 'Bad'),
        ('good', 'Good'),
    ], string='Condition', default='good')


class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_show_fleet_usage(self):
        self.ensure_one()
        action = self.env.ref('fleet_usage.fleet_usage_action').read()[0]
        action['domain'] = [
            '|',
            ('driver_id', '=', self.env.user.id),
            ('passenger_ids', 'in', [self.env.user.id])
        ]
        return action