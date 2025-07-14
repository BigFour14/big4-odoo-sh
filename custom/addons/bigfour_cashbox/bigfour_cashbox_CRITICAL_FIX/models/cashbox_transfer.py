# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CashboxTransfer(models.Model):
    _name = 'cashbox.transfer'
    _description = 'Cashbox Transfer'
    _order = 'date desc, id desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference', 
        required=True, 
        copy=False,
        readonly=True, 
        default=lambda self: _('New'),
        tracking=True
    )
    amount = fields.Float(
        string='Amount', 
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    date = fields.Date(
        string='Transfer Date', 
        default=fields.Date.today, 
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Notes',
        translate=True
    )
    receipt_image = fields.Binary(
        string='Receipt Photo',
        help='Upload receipt photo for this transfer'
    )
    receipt_filename = fields.Char(
        string='Receipt Filename'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    # Relations
    source_cashbox_id = fields.Many2one(
        'account.journal',
        string='Source Cashbox',
        domain=[('type', '=', 'cash')],
        required=True,
        tracking=True
    )
    destination_cashbox_id = fields.Many2one(
        'account.journal',
        string='Destination Cashbox',
        domain=[('type', '=', 'cash')],
        required=True,
        tracking=True
    )
    account_move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True
    )
    
    # User tracking
    user_id = fields.Many2one(
        'res.users',
        string='Created by',
        default=lambda self: self.env.user,
        readonly=True
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved by',
        readonly=True
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cashbox.transfer') or _('New')
        return super(CashboxTransfer, self).create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    @api.constrains('source_cashbox_id', 'destination_cashbox_id')
    def _check_cashboxes(self):
        for record in self:
            if record.source_cashbox_id == record.destination_cashbox_id:
                raise ValidationError(_('Source and destination cashboxes must be different.'))

    def action_submit(self):
        """Submit transfer for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft transfers can be submitted.'))
            record.state = 'submitted'
            record.message_post(
                body=_('Transfer submitted for approval.'),
                message_type='notification'
            )

    def action_approve(self):
        """Approve transfer and create journal entry"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted transfers can be approved.'))
            
            # Create journal entry
            move_vals = record._prepare_move_vals()
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            
            record.write({
                'state': 'approved',
                'account_move_id': move.id,
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Transfer approved and journal entry created.'),
                message_type='notification'
            )

    def action_reject(self):
        """Reject transfer"""
        for record in self:
            if record.state not in ['submitted']:
                raise UserError(_('Only submitted transfers can be rejected.'))
            record.state = 'rejected'
            record.message_post(
                body=_('Transfer rejected.'),
                message_type='notification'
            )

    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            if record.account_move_id:
                raise UserError(_('Cannot reset to draft. Journal entry already created.'))
            record.state = 'draft'

    def _prepare_move_vals(self):
        """Prepare journal entry values"""
        self.ensure_one()
        
        move_lines = []
        
        # Credit line (source cashbox)
        move_lines.append((0, 0, {
            'name': _('Transfer to %s') % self.destination_cashbox_id.name,
            'account_id': self.source_cashbox_id.default_account_id.id,
            'debit': 0.0,
            'credit': self.amount,
            'currency_id': self.currency_id.id,
        }))
        
        # Debit line (destination cashbox)
        move_lines.append((0, 0, {
            'name': _('Transfer from %s') % self.source_cashbox_id.name,
            'account_id': self.destination_cashbox_id.default_account_id.id,
            'debit': self.amount,
            'credit': 0.0,
            'currency_id': self.currency_id.id,
        }))
        
        return {
            'journal_id': self.source_cashbox_id.id,
            'date': self.date,
            'ref': self.name,
            'line_ids': move_lines,
            'currency_id': self.currency_id.id,
        }

    def action_print_receipt(self):
        """Print receipt"""
        return self.env.ref('bigfour_cashbox.action_report_cashbox_transfer_receipt').report_action(self)

    def unlink(self):
        for record in self:
            if record.state == 'approved':
                raise UserError(_('Cannot delete approved transfers.'))
        return super(CashboxTransfer, self).unlink()

