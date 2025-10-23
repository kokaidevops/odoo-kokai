from odoo import _, api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    parent_id = fields.Many2one('product.template', string='Parent')
    child_ids = fields.One2many('product.template', 'parent_id', string='Parts')


class BuildingStructure(models.Model):
    _name = 'building.structure'
    _description = 'Building Structure'
    _order = 'sequence ASC, id DESC'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', default=lambda self: self.env.ref('building_maintenance.maintenance_team_data_ga_team').id)
    category_id = fields.Many2one('maintenance.equipment.category', string='Category', default=lambda self: self.env.ref('building_maintenance.maintenance_equipment_category_data_building').id, required=True, readonly=True)


class WorkAreaStructure(models.Model):
    _name = 'work.area.structure'
    _description = 'Work Area Structure'

    name = fields.Char('Name', compute='_compute_name', store=True)
    area_id = fields.Many2one('hr.work.area', string='Area', ondelete='cascade')
    structure_id = fields.Many2one('building.structure', string='Structure', ondelete='cascade')
    state = fields.Selection([
        ('good', 'No Issue'),
        ('maintenance', 'Maintenance'),
        ('bad', 'Broken'),
    ], string='State', default='good', required=True, compute='_compute_state', store=True)
    maintenance_ids = fields.One2many('maintenance.request', 'area_structure_id', string='Maintenance')
    is_broken = fields.Boolean('Is Broken?')

    @api.depends('maintenance_ids', 'maintenance_ids.stage_id', 'is_broken')
    def _compute_state(self):
        for record in self:
            state = 'bad' if record.is_broken else 'good'
            record.state = 'maintenance' if len(record.equipment_id.mapped('maintenance_ids').filtered(
                lambda maintenance: maintenance.stage_id.id in [
                    self.env.ref('maintenance.stage_0').id, 
                    self.env.ref('maintenance.stage_1').id
                ]
            )) > 0 else state

    @api.depends('area_id', 'structure_id')
    def _compute_name(self):
        for record in self:
            record.name = '[%s] %s' % (record.area_id.name, record.structure_id.name)

    def request_maintenance(self):
        if self.state == 'maintenance':
            raise ValidationError("Can't request new maintenance for this building structure in maintenance state!")
        if self.is_broken:
            raise ValidationError("Can't request new maintenance for broken building!")
        return {
            'name': 'Maintenance Request',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'maintenance.request',
            'context': dict(
                self._context, 
                active_ids=self.ids, 
                default_employee_id=self.env.user.employee_id.id, 
                default_structure_id=self.structure_id.id,
                default_work_area_id=self.area_id.id,
                default_area_structure_id=self.id,
                default_category_id=self.structure_id.category_id.id,
                default_line_id=self.id,
                default_maintenance_team_id=self.structure_id.maintenance_team_id.id,
            ),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_report_malfunction(self):
        self.ensure_one()


class WorkAreaEquipment(models.Model):
    _name = 'work.area.equipment'
    _description = 'Work Area Equipment'

    name = fields.Char('Name', compute='_compute_name', store=True)
    area_id = fields.Many2one('hr.work.area', string='Area', ondelete='cascade')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number', related='equipment_id.lot_id')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', ondelete='cascade')
    qty = fields.Float('Qty', related='lot_id.product_qty', store=True)
    state = fields.Selection([
        ('good', 'No Issue'),
        ('maintenance', 'Maintenance'),
        ('bad', 'Broken'),
    ], string='State', default='good', required=True, compute='_compute_state', store=True)
    maintenance_ids = fields.One2many('maintenance.request', 'area_equipment_id', string='Maintenance')
    is_broken = fields.Boolean('Is Broken?')

    @api.depends('area_id', 'equipment_id')
    def _compute_name(self):
        for record in self:
            record.name = '[%s] %s' % (record.area_id.name, record.equipment_id.name)

    @api.depends('maintenance_ids', 'maintenance_ids.stage_id', 'is_broken')
    def _compute_state(self):
        for record in self:
            state = 'bad' if record.is_broken else 'good'
            record.state = 'maintenance' if len(record.equipment_id.mapped('maintenance_ids').filtered(
                lambda maintenance: maintenance.stage_id.id in [
                    self.env.ref('maintenance.stage_0').id, 
                    self.env.ref('maintenance.stage_1').id
                ]
            )) > 0 else state

    def request_maintenance(self):
        if self.state == 'maintenance':
            raise ValidationError("Can't request new maintenance for this equipment in maintenance state!")
        if self.is_broken:
            raise ValidationError("Can't request new maintenance for broken equipment!")
        return {
            'name': 'Maintenance Request',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'maintenance.request',
            'context': dict(
                self._context, 
                active_ids=self.ids, 
                default_employee_id=self.env.user.employee_id.id, 
                default_equipment_id=self.equipment_id.id,
                default_line_id=self.id,
                default_work_area_id=self.area_id.id,
                default_area_equipment_id=self.id,
            ),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class HrWorkArea(models.Model):
    _inherit = 'hr.work.area'

    equipment_ids = fields.One2many('work.area.equipment', 'area_id', string='Equipment')
    structure_ids = fields.One2many('work.area.structure', 'area_id', string='Structure')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    area_ids = fields.One2many('work.area.equipment', 'equipment_id', string='Area')
    part_ids = fields.One2many('maintenance.equipment.part', 'equipment_id', string='Part')


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    category_id = fields.Many2one('maintenance.equipment.category', compute='_compute_category_id', string='Category', store=True, readonly=True, related='')
    structure_id = fields.Many2one('building.structure', string='Structure')
    work_area_id = fields.Many2one('hr.work.area', string='Work Area')
    area_structure_id = fields.Many2one('work.area.structure', string='Area Structure', domain="['&', ('area_id', '=', work_area_id), ('structure_id', '=', structure_id)]")
    area_equipment_id = fields.Many2one('work.area.equipment', string='Area Equipment', domain="['&', ('area_id', '=', work_area_id), ('equipment_id', '=', equipment_id)]")
    parent_id = fields.Many2one('maintenance.request', string='Parent')
    child_ids = fields.One2many('maintenance.request', 'parent_id', string='Child')
    child_count = fields.Integer('Child Count', compute='_compute_child_count', store=True)
    approval_ids = fields.One2many('approval.request', 'maintenance_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    can_edit = fields.Boolean('Can Edit?', default=True)

    @api.depends('child_ids')
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.child_ids)

    @api.depends('equipment_id', 'equipment_id.category_id', 'structure_id', 'structure_id.category_id')
    def _compute_category_id(self):
        for record in self:
            record.category_id = record.equipment_id.category_id if record.equipment_id else record.structure_id.category_id

    def _prepare_mail_activity(self, data):
        return {
            'res_model_id': self.env.ref('maintenance.model_maintenance_request').id,
            'res_id': self._origin.id,
            'activity_type_id': data['activity_id'],
            'date_deadline': data['date_deadline'],
            'user_id': data['user_id'],
            'summary': data['summary'],
            'batch': data['batch'],
            'handle_by': 'just_one',
        }

    def _generate_mail_activity(self, date_deadline):
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        data = self._prepare_mail_activity({
            'activity_id': self.env.ref('custom_maintenance.mail_activity_type_data_maintenance').id,
            'date_deadline': date_deadline,
            'user_id': self.user_id.id,
            'summary': 'Please process the following Maintenance Request as soon as possible. Thank You!',
            'batch': batch, 
        })
        self.env['mail.activity'].create(data)

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        date_deadline = fields.Date.today() + timedelta(days=1)
        for record in res:
            record._generate_mail_activity(date_deadline)
        return res

    def archive_equipment_request(self):
        try:
            self.write({ 'stage_id': self.env.ref('custom_maintenance.maintenance_stage_data_cancel').id })
            query = "DELETE FROM mail_activity WHERE res_id=%s AND res_model_id=%s" % (self._origin.id, self.env.ref('maintenance.model_maintenance_request').id)
            self.env.cr.execute(query)
            res = super().archive_equipment_request()
            return res
        except Exception as e:
            raise ValidationError("Failed delete data: %s" % str(e))

    def reset_equipment_request(self):
        res = super().reset_equipment_request()
        date_deadline = fields.Date.today() + timedelta(days=1)
        self._generate_mail_activity(date_deadline)
        return res

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_view_approval_request(self):
        self.ensure_one()
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        action['domain'] = [('id', 'in', approvals.ids)]
        return action

    def _prepare_approval_request(self):
        return {
            'name': 'Request Approval for Maintenance ' + self.name,
            'maintenance_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': self.env.company.approval_maintenance_id.id,
            'reason': f"Request Approval for Maintenance {self.name} from {self.user.name} \n {self.description or ''}"
        }

    def action_request_approval(self):
        try:
            data = self._prepare_approval_request()
            request = self.env['approval.request'].create(data)
            query = f"UPDATE approval_approver SET user_id={self.user_id.id} WHERE request_id={request.id} AND user_id=2"
            self.env.cr.execute(query)
            request.action_confirm()
        except Exception as e:
            raise ValidationError("Can't Request Approval. Please Contact Administrator. \n%s" % str(e))

    def action_approved(self):
        self.write({ 'stage_id': self.env.ref('maintenance.stage_3').id })
        if self.area_structure_id:
            self.area_structure_id.write({ 'is_broken': False })
        if self.area_equipment_id:
            self.area_equipment_id.write({ 'is_broken': False })

    def action_scrap(self):
        try: 
            self.write({ 'stage_id': self.env.ref('maintenance.stage_4').id })
            data = self._prepare_mail_activity({
                'activity_id': self.env.ref('custom_activity.mail_act_notification').id,
                'date_deadline': fields.Date.today(),
                'user_id': self.employee_id.user_id.id,
                'summary': "Equipment has been damaged and cannot be repaired!",
                'batch': self.env['ir.sequence'].next_by_code('assignment.activity'), 
            })
            self.env['mail.activity'].create(data)
            if self.area_structure_id:
                self.area_structure_id.write({ 'is_broken': True })
            if self.area_equipment_id:
                self.area_equipment_id.write({ 'is_broken': True })
        except Exception as e:
            raise ValidationError("Can't execute this action: %s" % str(e))

    def action_refused(self, reason):
        data = self._prepare_mail_activity({
            'activity_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'), 
        })
        self.env['mail.activity'].create(data)