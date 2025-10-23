from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    visual = fields.Selection([
        ('bad', 'Bad'),
        ('ok', 'OK'),
    ], string='Visual', default='ok', tracking=True)
    diameter = fields.Float('Diameter (mm)', tracking=True)
    thick = fields.Float('Thick (mm)', tracking=True)
    rom_state = fields.Selection([
        ('bad', 'Bad'),
        ('ok', 'OK'),
    ], string='RoM State', default='ok', tracking=True)
    checked_by_id = fields.Many2one('res.users', string='Checked By')

    @api.depends('visual', 'diameter', 'thick', 'rom_state')
    def _compute_checked_by(self):
        for record in self:
            record.checked_by_id = self.env.user.id


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    visual = fields.Selection([
        ('bad', 'Bad'),
        ('ok', 'OK'),
    ], string='Visual', default='ok', tracking=True, related='move_id.visual')
    diameter = fields.Float('Diameter (mm)', tracking=True, related='move_id.diameter')
    thick = fields.Float('Thick (mm)', tracking=True, related='move_id.thick')
    rom_state = fields.Selection([
        ('bad', 'Bad'),
        ('ok', 'OK'),
    ], string='RoM State', default='ok', tracking=True, related='move_id.rom_state')
    checked_by_id = fields.Many2one('res.users', string='Checked By', related='move_id.checked_by_id')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_ids = fields.One2many('approval.request', 'picking_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count')
    state = fields.Selection(selection_add=[
        ('requested', 'Requested'), 
        ('approved', 'Approved'), 
        ('need_improvement', 'Need Improvement')
    ], ondelete={
        'requested': 'cascade',
        'approved': 'cascade',
        'need_improvement': 'cascade',
    })
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def generate_approval_request(self):
        self.ensure_one()
        category_pr = self.env.ref('receiving_material.approval_category_data_stock_picking')
        approval = self.env['approval.request'].create({
            'name': 'Request Approval for Receiving Material ' + self.name,
            'picking_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Receiving Material {self.name} from {self.user_id.name} \n Receiving Material from {self.name} is request Approval. Please review this Receiving of Material"
        })
        if approval:
            approval.action_confirm()
        self.write({ 'state': 'requested' })

    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    def action_show_rom(self):
        self.ensure_one()
        if not self.state == 'assigned':
            return
        action = self.env.ref('stock.stock_move_action').sudo().read()[0]
        action['domain'] = [('picking_id', '=', self.id)]
        return action

    def button_validate(self):
        if self.has_rom and self.state != 'approved':
            raise ValidationError('Please Request Approval Before Validate!')

        res = super(StockPicking, self).button_validate()
        # notification for qc
        if self.picking_type_id.code == 'internal' and self.location_dest_id.for_quality_check:
            assignment = self.env['assignment.task'].create({
                'department_ids': [self.env.ref('department_detail.hr_management_data_quality').id],
                'user_id': self.env.user.id,
                'employee_type_ids': [self.env.ref('department_detail.hr_contract_type_head_of_department').id, self.env.ref('department_detail.hr_contract_type_senior_staff').id],
                'assigned_to': 'department',
                'subject': f"Pemberitahuan QC Penerimaan Produk",
                'description': f"Pemberitahuan untuk departemen terkait mengenai permintaan pengecekan untuk penerimaan produk {self.origin}",
                'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
                'model': 'purchase.order',
                'res_id': self.product_id,
            })
            if not assignment:
                raise ValidationError("Can't Assignment Task! Please contact Administrator!")
            assignment.action_assign()
        return res

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })
        self.button_validate()
    
    def action_need_improvement(self):
        self.ensure_one()
        # notification to user
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Approved Receiving of Material',
            'user_id': self.user_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.user_id.name} \n Receiving Material {self.name} yang diajukan ditolak. Mohon diperbaiki dan ditinjau kembali sesuai dengan catatan yang ditinggalkan. \n Terima Kasih",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'stock.picking',
            'res_id': self.id,
        })
        notification.action_assign()
        self.write({ 'state': 'need_improvement' })

    has_rom = fields.Boolean('Has RoM', compute='_compute_has_rom')
    @api.depends('picking_type_id')
    def _compute_has_rom(self):
        for record in self:
            record.has_rom = False
            if record.picking_type_id.code == 'incoming':
                record.has_rom = True
