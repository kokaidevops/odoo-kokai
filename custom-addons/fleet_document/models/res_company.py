from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _domain_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id)]
    
    documents_vehicle_settings = fields.Boolean('Documents Vehicle Settings', default=False)
    vehicle_folder_id = fields.Many2one('documents.folder', string='Vehicle Workspace', domain=_domain_company, default=lambda self: self.env.ref('documents_fleet.documents_fleet_folder', raise_if_not_found=False))
    vehicle_tag_ids = fields.Many2many('documents.tag', 'vehicle_tags_rel')