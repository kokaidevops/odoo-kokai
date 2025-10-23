
from werkzeug import urls
import werkzeug.exceptions
from werkzeug.urls import url_parse

from odoo import http, tools, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, MissingError, UserError, ValidationError
from odoo.http import content_disposition, Controller, request, route
from datetime import datetime

try:
    import qrcode
except ImportError:
    qrcode = None
from io import BytesIO

import logging

_logger = logging.getLogger(__name__)


class ApprovalPortal(Controller):

    def _generate_data_approval(self, proof):
        return {
            'user': proof.user_id.name,
            'date': proof.date.strftime('%d %B %Y'),
            'position': proof.position_id.name,
            'name': proof.request_id.name,
            'request_by': proof.request_id.request_owner_id.name,
            'category': proof.request_id.category_id.name,
        }

    @route(['/approval'], type='http', auth='public', website=True)
    def approval(self, **kwargs):
        id = kwargs.get('proof')
        proof = request.env['approval.approver'].search([
            ('id', '=', id),
            ('status', '=', 'approved'),
        ])
        data = { 'status': False }
        if proof:
            data = self._generate_data_approval(proof)
            data['status'] = True
        return request.render('approvals_portal.approval_page', data)

    def _generate_data_requested(self, approval):
        return {
            'user': approval.request_owner_id.name,
            'category': approval.category_id.name,
            'name': approval.name,
            'date': approval.request_date.strftime('%d %B %Y'),
            'state': dict(approval._fields['request_status'].selection).get(approval.request_status)
        }

    @route(['/requested'], type='http', auth='public', website=True)
    def requested(self, **kwargs):
        id = kwargs.get('requested')
        approval = request.env['approval.request'].search([ ('id', '=', id) ])
        data = { 'status': False }
        if approval:
            data = self._generate_data_requested(approval)
            data['status'] = True
        return request.render('approvals_portal.requested_page', data)

    @route(['/api/qrcode'], type='http', auth='public')
    def generate_qrcode(self, **kwargs):
        text = kwargs.get('text')
        
        img = qrcode.make(text)
        buffer = BytesIO()
        img.save(buffer, format='png')
        buffer.seek(0)

        response = request.make_response(buffer.getvalue(), headers=[('Content-Type', 'image/png')])
        return response