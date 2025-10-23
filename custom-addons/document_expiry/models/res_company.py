from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _domain_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id)]
    
    documents_document_settings = fields.Boolean('Documents Document Settings', default=False)
    document_folder_id = fields.Many2one('documents.folder', string='Document Workspace', domain=_domain_company, default=lambda self: self.env.ref('document_expiry.documents_document_folder', raise_if_not_found=False))
    document_tag_ids = fields.Many2many('documents.tag', 'document_tags_rel')