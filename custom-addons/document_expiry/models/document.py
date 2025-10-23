from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta


class BaseDocument(models.Model):
    _name = 'base.document'
    _description = 'Base Document'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Title', required=True, tracking=True)
    number = fields.Char('Number', tracking=True)
    active = fields.Boolean('Active', default=True)
    document_type_id = fields.Many2one('base.document.type', string='Type', tracking=True)
    responsible_ids = fields.Many2many('res.users', string='Responsible')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    activate_notify = fields.Boolean('Activate Notify?', tracking=True)
    based_on = fields.Selection([
        ('employee', 'Employee'),
        ('company', 'Company'),
        ('other', 'Other'),
    ], string='Based On', default='company', required=True)
    issue_date = fields.Date('Date of Issue', default=fields.Date.today(), required=True)
    expiry_date = fields.Date('Date of Expiry', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('expiry', 'Expiry'),
        ('refused', 'Refused'),
    ], string='State', default='draft', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    description = fields.Text('Description')
    expense_ids = fields.One2many('hr.expense.sheet', 'document_id', string='Expense')
    expense_count = fields.Integer('Expense Count', compute='_compute_expense_count', store=True)

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for record in self:
            record.expense_count = len(record.expense_ids)

    def action_show_expense_sheet(self):
        action = self.env.ref('hr_expense.action_hr_expense_sheet_all').sudo().read()[0]
        action['domain'] = [('id', 'in', self.expense_ids.ids)]
        return action

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_confirmed(self):
        self.write({ 'state': 'confirmed' })

    def action_expiry(self):
        self.write({ 'state': 'expiry' })

    def action_refused(self):
        self.write({ 'state': 'refused' })

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        for record in self:
            record.activate_notify = record.document_type_id.set_notify

    def _cron_notify_expiry(self):
        documents = self.env['base.document'].search([
            ('state', '=', 'confirmed'),
            ('activity_notify', '=', True),
            ('active', '=', True),
        ])
        for document in documents:
            if not document.activate_notify:
                return
            days = document.document_type_id.value if document.document_type_id.range == 'day' else 0
            months = document.document_type_id.value if document.document_type_id.range == 'month' else 0
            years = document.document_type_id.value if document.document_type_id.range == 'year' else 0
            today = fields.Date.today() + relativedelta(days=days, months=months, years=years)
            if not today == document.expiry_date:
                return
            batch = self.env['ir.sequence'].next_by_code('assignment.activity')
            for user in document.responsible_ids:
                notification = self.env['mail.activity'].create({
                    'res_model_id': self.env.ref('document_expiry.model_base_document').id,
                    'res_id': self._origin.id,
                    'activity_type_id': self.env.ref('custom_activity.mail_act_notification').id,
                    'date_deadline': fields.Date.today(),
                    'user_id': user.id,
                    'summary': "Please renewal for this document.",
                    'batch': batch,
                    'handle_by': 'just_one',
                })
            document.write({ 'state': 'expiry' })

    def action_create_expense(self):
        expense = self.env['hr.expense.sheet'].create({
            'name': 'Renewal for %s-%s' % (self.name, self.number),
            'employee_id': self.responsible_id.employee_id.id,
            'date': fields.Date.today(),
            'document_id': self.id,
        })
        return {
            'name': 'Expense Reports',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.sheet',
            'view_mode': 'form',
            'res_id': expense.id,
            'target': 'current',
        }


class BaseDocumentType(models.Model):
    _name = 'base.document.type'
    _description = 'Base Document Type'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    set_notify = fields.Boolean('Set Notify?')
    range = fields.Selection([
        ('day', 'Day'),
        ('month', 'Month'),
        ('year', 'Year'),
    ], string='Range', default='month', required=True)
    value = fields.Float('Value', default=1.0, required=True)
    document_ids = fields.One2many('base.document', 'document_type_id', string='Documents')

    @api.onchange('set_notify')
    def _onchange_set_notify(self):
        for record in self:
            for document in record.document_ids.filtered(lambda document: document.activate_notify == record._origin.set_notify):
                document.activate_notify = record.set_notify
