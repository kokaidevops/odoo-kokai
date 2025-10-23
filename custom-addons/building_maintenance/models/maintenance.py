from odoo import _, api, fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class EquipmentPartStock(models.Model):
    _name = 'equipment.part.stock'
    _description = 'Equipment Part Stock'
    _order = 'date DESC, id DESC'

    name = fields.Char('Name', related='part_id.name')
    part_id = fields.Many2one('maintenance.equipment.part', string='Part', ondelete='cascade')
    service_id = fields.Many2one('maintenance.request.service', string='Service', ondelete='restrict')
    init_qty = fields.Float('Init Qty')
    final_qty = fields.Float('Current Qty')
    date = fields.Datetime('Date', default=fields.Datetime.now())


class MaintenanceEquipmentPart(models.Model):
    _name = 'maintenance.equipment.part'
    _description = 'Maintenance Equipment Part'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', ondelete='restrict')
    name = fields.Char('Name', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float('Qty', compute='_compute_qty', store=True)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    state = fields.Selection([
        ('good', 'Good')
    ], string='State', default='good', required=True)
    service_ids = fields.One2many('maintenance.request.service', 'part_id', string='Service')
    stock_ids = fields.One2many('equipment.part.stock', 'part_id', string='Stock')

    @api.depends('stock_ids', 'stock_ids.final_qty')
    def _compute_qty(self):
        for record in self:
            record.qty = record.stock_ids[0].final_qty if record.stock_ids else 0

    def action_show_stock(self):
        self.ensure_one()
        action = self.env.ref('building_maintenance.equipment_part_stock_action').read()[0]
        action['domain'] = [('id', 'in', self.stock_ids.ids)]
        return action

    def action_show_service(self):
        self.ensure_one()
        action = self.env.ref('building_maintenance.equipment_part_stock_action').read()[0]
        action['domain'] = [('id', 'in', self.service_ids.ids)]
        return action


class MaintenanceService(models.Model):
    _name = 'maintenance.service'
    _description = 'Maintenance Service'

    name = fields.Char('Name')
    impact = fields.Selection([
        ('none', 'None'),
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
        ('replace', 'Replace'),
    ], string='Impact to Qty', default='none', required=True)


class MaintenanceRequestService(models.Model):
    _name = 'maintenance.request.service'
    _description = 'Maintenance Request Service'

    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance', ondelete='restrict', required=True)
    service_id = fields.Many2one('maintenance.service', string='Service', ondelete='restrict', required=True)
    date = fields.Datetime('Date', default=fields.Datetime.now())
    part_id = fields.Many2one('maintenance.equipment.part', string='Part', ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float('Qty')
    uom_id = fields.Many2one('uom.uom', string='UoM')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True)


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    def action_show_all_equipment(self):
        self.ensure_one()
        equipment_ids = []
        action = self.env.ref('maintenance.hr_equipment_action').read()[0]
        equipment_ids.append(self.equipment_id.id)
        for pack in self.equipment_id.lot_id.pack_ids:
            for lot in pack.lot_ids:
                equipment_ids.append(lot.equipment_id.id)
        action['domain'] = [('id', 'in', equipment_ids)]
        return action
