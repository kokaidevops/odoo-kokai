from odoo import _, api, fields, models


class PartnerAssessmentPoint(models.Model):
    _name = 'partner.assessment.point'
    _description = 'Partner Assessment Point'
    _order = 'sequence ASC, id DESC'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')


class PartnerAssessmentLine(models.Model):
    _name = 'partner.assessment.line'
    _description = 'Partner Assessment Line'

    point_id = fields.Many2one('partner.assessment.point', string='Point')
    assessment_id = fields.Many2one('partner.assessment', string='Assessment')
    is_check = fields.Boolean('OK?')


class PartnerAssessment(models.Model):
    _name = 'partner.assessment'
    _description = 'Partner Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='Request By', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    name = fields.Char('Name', default='New')
    partner_id = fields.Many2one('res.partner', string='Partner')
    survey_id = fields.Many2one('survey.survey', string='survey')
    line_ids = fields.One2many('partner.assessment.line', 'assessment_id', string='Line')
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='partner_id.product_categ_id', store=True)
    partner_category = fields.Selection(related='partner_id.category', string='Partner Category', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('evaluate', 'Evaluate'),
        ('request', 'Request'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('obsolete', 'Obsolete'),
    ], string='State', default='draft')
    remarks = fields.Text('Remarks')
    category = fields.Selection([
        ('init_eval', 'Initial Evaluation'),
        ('re_eval', 'Re-Evaluation'),
    ], string='Category', default='init_eval')
    date = fields.Date('Submit Date', default=fields.Date.today())
    issue_date = fields.Date('Issue Date')
    expired_date = fields.Date('Expired Date')

    def _generate_survey(self):
        self.ensure_one()

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_evaluate(self):
        self.ensure_one()
        self.write({ 'state': 'evaluate' })

    def action_request(self):
        self.ensure_one()
        self.write({ 'state': 'request' })

    def action_accept(self):
        self.ensure_one()
        self.write({ 'state': 'accept' })

    def action_reject(self):
        self.ensure_one()
        self.write({ 'state': 'reject' })

    def action_obsolete(self):
        self.ensure_one()
        self.write({ 'state': 'obsolete' })


class ResPartner(models.Model):
    _inherit = 'res.partner'

    product_categ_id = fields.Many2one('product.category', string='Product Category')
    category = fields.Selection([
        ('end_supplier', 'End Supplier'),
        ('supply_chain', 'Supply Chain'),
    ], string='Category', default='supply_chain')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('evaluate', 'Evaluate'),
        ('accept', 'Validate'),
        ('reject', 'Blacklist'),
        ('obsolete', 'Obsolete'),
    ], string='State', default='draft', compute='_compute_state', store=True)
    assessment_ids = fields.One2many('partner.assessment', 'partner_id', string='Assessment')
    assessment_count = fields.Integer('Assessment Count', compute='_compute_assessment_count', store=True)
    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for record in self:
            record.assessment_count = len(record.assessment_ids)

    @api.depends('assessment_ids', 'assessment_ids.state')
    def _compute_state(self):
        for record in self:
            record.state

    def action_show_assessment(self):
        self.ensure_one()
        if self.assessment_count == 0:
            return
        action = (self.env.ref('partner_assessment.partner_assessment_action').sudo().read()[0])
        action['domain'] = [('id', 'in', self.assessment_ids.ids)]
        return action
