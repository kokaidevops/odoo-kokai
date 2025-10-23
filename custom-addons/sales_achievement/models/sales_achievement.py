from odoo import _, api, fields, models


class SalesTarget(models.Model):
    _name = 'sales.target'
    _description = 'Sales Target'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', copy=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=False, store=True)
    name = fields.Char('Name', compute='_compute_name')
    user_id = fields.Many2one('res.users', string='Salesperson')
    employee_id = fields.Many2one('hr.employee', string='Salesperson', related='user_id.employee_id')
    target = fields.Float('Salesperson Target')
    start_period = fields.Date('Start Period', default=fields.Date.today(), copy=True)
    end_period = fields.Date('End Period', default=fields.Date.today(), copy=True)
    salesperson_achieved_amount = fields.Float('Salesperson Achieved Amount', compute='_compute_salesperson_achieved_amount')
    team_id = fields.Many2one('department.team', string='Team')
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft')
    # team_achieved_amount = fields.Float('Team Achieved Amount', compute='_compute_team_achieved_amount')

    @api.depends('user_id', 'start_period', 'end_period')
    def _compute_name(self):
        for record in self:
            record.name = f"{self.user_id.name}: [{self.start_period} - {self.end_period}]"

    @api.depends('state', 'employee_id.user_id.sale_order_ids', 'employee_id.user_id.sale_order_ids.state')
    def _compute_salesperson_achieved_amount(self):
        for record in self:
            achieved_amount = 0.0
            if record.state in ['draft', 'cancel']:
                record.salesperson_achieved_amount = achieved_amount
                return
            # filtered sale_order_ids with state and period
            orders = record.employee_id.user_id.sale_order_ids.filtered(lambda order: order.state in ['sale', 'done'] and record.start_period <= order.date_order and record.end_period >= order.date_order)
            for order in orders:
                achieved_amount += order.amount_total
            record.salesperson_achieved_amount = achieved_amount

    # @api.depends('user_id.sale_order_ids')
    # def _compute_team_achieved_amount(self):
    #     for record in self:
    #         record.team_achieved_amount = 0.0

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_process(self):
        self.write({ 'state': 'process' })

    def action_done(self):
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.write({ 'state': 'cancel' })

    def action_view_sale_order(self):
        self.ensure_one()
        if len(self.employee_id.user_id.sale_order_ids) == 0:
            return
        action = (self.env.ref('sale.action_orders').sudo().read()[0])
        action['domain'] = [('id', 'in', self.employee_id.user_id.sale_order_ids.ids)]
        return action


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    salesperson_target_ids = fields.One2many('sales.target', 'employee_id', string='Salesperson Target')
    salesperson_target_count = fields.Integer('Salesperson Count', compute='_compute_salesperson_target_count')

    @api.depends('salesperson_target_ids')
    def _compute_salesperson_target_count(self):
        for record in self:
            record.salesperson_target_count = len(record.salesperson_target_ids.filtered(lambda target: target.state in ['process', 'done']))
    
    def action_view_salesperson_target(self):
        self.ensure_one()
        if len(self.salesperson_target_ids) == 0:
            return
        action = (self.env.ref('sales_achievement.sales_target_action').sudo().read()[0])
        action['domain'] = [('id', 'in', self.salesperson_target_ids.ids)]
        return action


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    salesperson_target_count = fields.Integer('Salesperson Count', related='employee_id.salesperson_target_count')