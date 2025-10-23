from odoo import _, api, fields, models


class NonconformingProduct(models.Model):
    _name = 'nonconforming.product'
    _description = 'Nonconforming Product'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, tracking=True)
    date = fields.Date('Date', default=fields.Date.today())

    name = fields.Char('Name', tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', tracking=True)
    product_ids = fields.Many2many('product.product', string='Product', tracking=True)
    process = fields.Char('Process', tracking=True)
    qty = fields.Integer('Qty', tracking=True)
    description = fields.Html('Description of Nonconformity', tracking=True)
    inspector_id = fields.Many2one('res.users', string='Inspector', tracking=True)
    date_submit_desc = fields.Date('Date Submit Desc', tracking=True)
    reviewed = fields.Html('Reviewed Opinion by Process Owner (Production or Purchasing)', tracking=True)
    owner_id = fields.Many2one('res.users', string='Process Owner', tracking=True)
    date_submit_reviewed = fields.Date('Date Submit Reviewed', tracking=True)
    proposed_action = fields.Selection([
        ('repair', 'Repair or rework with subsequent inspection to meet specified requirements'),
        ('regrade', 'Re-grade for alternative applications'),
        ('release', 'Release under concession'),
        ('reject', 'Reject or scrap'),
        ('return', 'Return to the suppliers'),
    ], string='Reviewed Opinion by Engineering', tracking=True)
    engineering_id = fields.Many2one('res.users', string='Engineering', tracking=True)
    date_submit_proposed = fields.Date('Date Submit by Engineering', tracking=True)
    result = fields.Text('Reviewed Result', tracking=True)
    head_id = fields.Many2one('res.users', string='Quality Dept. Head', tracking=True)
    date_submit_result = fields.Date('Date Submit Result', tracking=True)
    followed_action = fields.Text('Followed Action', tracking=True)
    inspector_followed_id = fields.Many2one('res.users', string='Inspector Followed', tracking=True)
    date_submit_followed = fields.Date('Date Submit Followed', tracking=True)
    verify_result = fields.Text('Verify Result', tracking=True)
    inspector_verify_id = fields.Many2one('res.users', string='Inspector Verify', tracking=True)
    date_submit_verify = fields.Date('Date Submit Verify', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment', tracking=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('waiting', 'Waiting for Respond'),
        ('closed', 'Closed'),
        ('cancel', 'Cancel'),
    ], string='State', default='open', required=True, tracking=True)
    closing_date = fields.Date('Closing Date')

    def action_open(self):
        self.ensure_one()
        self.write({ 'state': 'open' })

    def action_waiting(self):
        self.ensure_one()
        self.write({ 'state': 'waiting' })

    def action_closed(self):
        self.ensure_one()
        self.write({ 'state': 'closed', 'closing_date': fields.Date.today() })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })