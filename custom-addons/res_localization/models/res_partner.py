from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    city = fields.Char('City')
    city_id = fields.Many2one('res.city', string='City', domain="[('state_id', '=', state_id)]", ondelete='cascade')
    subdistrict_id = fields.Many2one('res.subdistrict', string='Subdistrict', domain="[('city_id', '=', city_id)]", ondelete='cascade')
    ward_id = fields.Many2one('res.ward', string='Ward', domain="[('subdistrict_id', '=', subdistrict_id)]", ondelete='cascade')


class ResCompany(models.Model):
    _inherit = 'res.company'

    city = fields.Char('City')
    city_id = fields.Many2one('res.city', string='City', domain="[('state_id', '=', state_id)]", ondelete='cascade')
    subdistrict_id = fields.Many2one('res.subdistrict', string='Subdistrict', domain="[('city_id', '=', city_id)]", ondelete='cascade')
    ward_id = fields.Many2one('res.ward', string='Ward', domain="[('subdistrict_id', '=', subdistrict_id)]", ondelete='cascade')

