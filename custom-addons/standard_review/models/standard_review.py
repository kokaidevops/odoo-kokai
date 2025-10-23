from odoo import _, api, fields, models


class StandardReview(models.Model):
    _name = 'standard.review'
    _description = 'Standard Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    name = fields.Char('Name', default='New', required=True)
    standard = fields.Char('Standard', required=True)
    affected_publication = fields.Char('Affected Publication')
    issued_date = fields.Date('Issued Date', default=fields.Date.today())
    effective_date = fields.Date('Effective Date')
    report_no = fields.Char('Report No.')
    date = fields.Date('Date')
    reported_by_id = fields.Many2one('res.users', string='Reported By')
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='state', default='draft')

    line_ids = fields.One2many('review.line', 'standard_id', string='Line')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('standard.review')
        return super(StandardReview, self).create(vals)

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_done(self):
        self.ensure_one()
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })


class ReviewLine(models.Model):
    _name = 'review.line'
    _description = 'Review Line'

    standard_id = fields.Many2one('review.line', string='Standard', required=True)
    section = fields.Char('Section')
    change = fields.Text('Change')
    affected_procedure = fields.Char('Affected Procedure')
    affected_record = fields.Char('Affected Record')
    pic_id = fields.Many2one('res.users', string='PIC')
    target_completed = fields.Char('Target Completed')
    remarks = fields.Text('Remarks')