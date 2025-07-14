# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CashboxCollection(models.Model):

    def create_payment_entry(self):
        for rec in self:
            if rec.invoice_id and rec.state == 'approved':
                payment_vals = {
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': rec.partner_id.id,
                    'amount': rec.amount,
                    'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                    'journal_id': self.env['account.journal'].search([('type','=','cash')], limit=1).id,
                    'ref': rec.name,
                }
                payment = self.env['account.payment'].create(payment_vals)
                payment.action_post()
                rec.invoice_id.js_assign_outstanding_line(payment.move_id.line_ids.filtered(lambda l: l.account_id == rec.invoice_id.partner_id.property_account_receivable_id))

    _name = 'cashbox.collection'
    _description = 'Cashbox Customer Collection'
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
    customer_id = fields.Many2one(
        'res.partner', 
        string='Customer', 
        required=True,
        domain=[('customer_rank', '>', 0)],
        tracking=True
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Customer Invoice',
        domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')],
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
        string='Collection Date', 
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
        help='Upload receipt photo for this collection'
    )
    receipt_filename = fields.Char(
        string='Receipt Filename'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Relations
    cashbox_id = fields.Many2one(
        'account.journal',
        string='Cashbox',
        domain=[('type', '=', 'cash')],
        required=True
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True
    )
    
    # User tracking
    user_id = fields.Many2one(
        'res.users',
        string='Created by',
        default=lambda self: self.env.user,
        readonly=True
    )
    collected_by = fields.Many2one(
        'res.users',
        string='Collected by',
        readonly=True
    )
    collected_date = fields.Datetime(
        string='Collected Date',
        readonly=True
    )

    # Computed fields
    remaining_amount = fields.Float(
        string='Remaining Amount',
        compute='_compute_remaining_amount',
        store=True
    )

    @api.depends('invoice_id', 'invoice_id.amount_residual')
    def _compute_remaining_amount(self):
        for record in self:
            if record.invoice_id:
                record.remaining_amount = record.invoice_id.amount_residual
            else:
                record.remaining_amount = 0.0

    def write(self, vals):
        """Override write to prevent editing collected payments"""
        # منع التعديل في التحصيلات المكتملة
        for record in self:
            if record.state == 'collected' and record.payment_id:
                # السماح فقط بتغيير الحالة والملاحظات
                allowed_fields = ['state', 'description']
                if any(field not in allowed_fields for field in vals.keys()):
                    raise UserError(_('Cannot modify collected payments. Payment already posted.'))
        
        return super(CashboxCollection, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cashbox.collection') or _('New')
        return super(CashboxCollection, self).create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    @api.constrains('amount', 'invoice_id')
    def _check_collection_amount(self):
        for record in self:
            if record.invoice_id and record.amount > record.invoice_id.amount_residual:
                raise ValidationError(_('Collection amount cannot exceed the remaining invoice amount.'))

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.customer_id = self.invoice_id.partner_id
            self.amount = self.invoice_id.amount_residual
            self.currency_id = self.invoice_id.currency_id

    def action_submit(self):
        """Submit collection for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft collections can be submitted.'))
            record.state = 'submitted'
            record.message_post(
                body=_('Collection submitted for approval.'),
                message_type='notification'
            )

    def action_collect(self):
        """Process collection"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted collections can be processed.'))
            
            # Create payment
            payment_vals = record._prepare_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            
            record.write({
                'state': 'collected',
                'payment_id': payment.id,
                'collected_by': self.env.user.id,
                'collected_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Collection processed successfully.'),
                message_type='notification'
            )

    def action_cancel(self):
        """Cancel collection"""
        for record in self:
            if record.state == 'collected':
                raise UserError(_('Cannot cancel collected payments.'))
            record.state = 'cancelled'
            record.message_post(
                body=_('Collection cancelled.'),
                message_type='notification'
            )

    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            if record.payment_id:
                raise UserError(_('Cannot reset to draft. Payment already processed.'))
            record.state = 'draft'

    def _prepare_payment_vals(self):
        """Prepare payment values"""
        self.ensure_one()
        
        # الحقول الأساسية المطلوبة فقط لـ account.payment في Odoo 18
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.cashbox_id.id,
        }
        
        return payment_vals

    def action_collect(self):
        """Process collection and reconcile with invoice"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted collections can be processed.'))
            
            # Create payment
            payment_vals = record._prepare_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            
            # ربط التحصيل بالفاتورة الأصلية - استخدام move_id بدلاً من line_ids
            if record.invoice_id and payment.move_id:
                # البحث عن سطور الفاتورة والدفعة للتسوية
                invoice_lines = record.invoice_id.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
                payment_lines = payment.move_id.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
                
                # تسوية السطور
                if invoice_lines and payment_lines:
                    (invoice_lines + payment_lines).reconcile()
            
            record.write({
                'state': 'collected',
                'payment_id': payment.id,
                'collected_by': self.env.user.id,
                'collected_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Collection processed and reconciled with invoice successfully.'),
                message_type='notification'
            )

    def action_print_receipt(self):
        """Print receipt"""
        return self.env.ref('bigfour_cashbox.action_report_cashbox_collection_receipt').report_action(self)

    def unlink(self):
        for record in self:
            if record.state == 'collected':
                raise UserError(_('Cannot delete collected payments.'))
        return super(CashboxCollection, self).unlink()

