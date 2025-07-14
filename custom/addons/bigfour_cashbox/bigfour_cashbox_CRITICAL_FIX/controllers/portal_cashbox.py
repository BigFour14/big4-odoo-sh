from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.tools import groupby as groupbyelem
from odoo.osv.expression import OR
from collections import OrderedDict
import base64

class CashboxPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        
        # إزالة العد التلقائي لتجنب مشاكل Loading
        # values['cashbox_count'] = 0
        
        return values

    # Main Dashboard Route
    @http.route('/cashbox', type='http', auth='user', website=True)
    def cashbox_portal(self, **kw):
        """Main cashbox portal page"""
        # Get pending counts
        pending_expenses = request.env['cashier.expense'].search_count([
            ('state', '=', 'draft')
        ])
        pending_payments = request.env['cashbox.payment'].search_count([
            ('state', '=', 'draft')
        ])
        pending_collections = request.env['cashbox.collection'].search_count([
            ('state', '=', 'draft')
        ])
        pending_uninvoiced = request.env['cashbox.uninvoiced'].search_count([
            ('state', '=', 'draft')
        ])
        pending_transfers = request.env['cashbox.transfer'].search_count([
            ('state', '=', 'draft')
        ])
        
        values = {
            'page_name': 'cashbox',
            'pending_expenses': pending_expenses,
            'pending_payments': pending_payments,
            'pending_collections': pending_collections,
            'pending_uninvoiced': pending_uninvoiced,
            'pending_transfers': pending_transfers,
        }
        return request.render('bigfour_cashbox.portal_cashbox_main', values)

    # Payment Routes
    @http.route('/cashbox/payments', type='http', auth='user', website=True)
    def cashbox_payments(self, **kw):
        """Vendor payments page"""
        # Get unpaid vendor bills
        unpaid_bills = request.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])
        
        values = {
            'page_name': 'cashbox',
            'unpaid_bills': unpaid_bills,
        }
        return request.render('bigfour_cashbox.portal_payments_list', values)

    @http.route('/cashbox/payment/create/<int:bill_id>', type='http', auth='user', website=True)
    def create_payment(self, bill_id, **kw):
        """Create payment form"""
        bill = request.env['account.move'].browse(bill_id)
        if not bill.exists():
            return request.not_found()
            
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        
        values = {
            'page_name': 'cashbox',
            'bill': bill,
            'cashboxes': cashboxes,
        }
        return request.render('bigfour_cashbox.portal_payment_form', values)

    @http.route('/cashbox/payment/submit', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def submit_payment(self, **post):
        """Submit payment"""
        try:
            bill = request.env['account.move'].browse(int(post.get('bill_id')))
            cashbox = request.env['account.journal'].browse(int(post.get('cashbox_id')))
            amount = float(post.get('amount', 0))
            
            # Create cashbox payment record
            payment_vals = {
                'vendor_id': bill.partner_id.id,
                'bill_id': bill.id,
                'amount': amount,
                'cashbox_id': cashbox.id,
                'date': post.get('date'),
                'notes': post.get('notes', ''),
                'state': 'draft',
            }
            
            payment = request.env['cashbox.payment'].create(payment_vals)
            
            # Create actual account payment and reconcile with bill
            account_payment_vals = {
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': bill.partner_id.id,
                'amount': amount,
                'currency_id': bill.currency_id.id,
                'date': post.get('date'),
                'journal_id': cashbox.id,
                'reconciled_invoice_ids': [(6, 0, [bill.id])],
            }
            
            account_payment = request.env['account.payment'].create(account_payment_vals)
            account_payment.action_post()
            
            # Update payment state
            payment.write({'state': 'paid', 'payment_id': account_payment.id})
            
            return request.redirect('/cashbox/payments')
            
        except Exception as e:
            return request.render('bigfour_cashbox.portal_error', {
                'error': str(e)
            })

    # Collection Routes
    @http.route('/cashbox/collections', type='http', auth='user', website=True)
    def cashbox_collections(self, **kw):
        """Customer collections page"""
        # Get unpaid customer invoices
        unpaid_invoices = request.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])
        
        values = {
            'page_name': 'cashbox',
            'unpaid_invoices': unpaid_invoices,
        }
        return request.render('bigfour_cashbox.portal_collections_list', values)

    @http.route('/cashbox/collection/create/<int:invoice_id>', type='http', auth='user', website=True)
    def create_collection(self, invoice_id, **kw):
        """Create collection form"""
        invoice = request.env['account.move'].browse(invoice_id)
        if not invoice.exists():
            return request.not_found()
            
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        
        values = {
            'page_name': 'cashbox',
            'invoice': invoice,
            'cashboxes': cashboxes,
        }
        return request.render('bigfour_cashbox.portal_collection_form', values)

    @http.route('/cashbox/collection/submit', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def submit_collection(self, **post):
        """Submit collection"""
        try:
            invoice = request.env['account.move'].browse(int(post.get('invoice_id')))
            cashbox = request.env['account.journal'].browse(int(post.get('cashbox_id')))
            amount = float(post.get('amount', 0))
            
            # Create cashbox collection record
            collection_vals = {
                'customer_id': invoice.partner_id.id,
                'invoice_id': invoice.id,
                'amount': amount,
                'cashbox_id': cashbox.id,
                'date': post.get('date'),
                'notes': post.get('notes', ''),
                'state': 'draft',
            }
            
            collection = request.env['cashbox.collection'].create(collection_vals)
            
            # Create actual account payment and reconcile with invoice
            account_payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': amount,
                'currency_id': invoice.currency_id.id,
                'date': post.get('date'),
                'journal_id': cashbox.id,
                'reconciled_invoice_ids': [(6, 0, [invoice.id])],
            }
            
            account_payment = request.env['account.payment'].create(account_payment_vals)
            account_payment.action_post()
            
            # Update collection state
            collection.write({'state': 'collected', 'payment_id': account_payment.id})
            
            return request.redirect('/cashbox/collections')
            
        except Exception as e:
            return request.render('bigfour_cashbox.portal_error', {
                'error': str(e)
            })

    # Expense Routes
    @http.route('/cashbox/expenses', type='http', auth='user', website=True)
    def cashbox_expenses(self, **kw):
        """Cashier expenses page"""
        expenses = request.env['cashier.expense'].search([
            ('create_uid', '=', request.env.user.id)
        ])
        
        values = {
            'page_name': 'cashbox',
            'expenses': expenses,
        }
        return request.render('bigfour_cashbox.portal_expenses_list', values)

    @http.route('/cashbox/expense/create', type='http', auth='user', website=True)
    def create_expense(self, **kw):
        """Create expense form"""
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        
        values = {
            'page_name': 'cashbox',
            'cashboxes': cashboxes,
        }
        return request.render('bigfour_cashbox.portal_expense_form', values)

    @http.route('/cashbox/expense/submit', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def submit_expense(self, **post):
        """Submit expense"""
        try:
            expense_vals = {
                'expense_name': post.get('expense_name'),
                'amount': float(post.get('amount', 0)),
                'cashbox_id': int(post.get('cashbox_id')),
                'date': post.get('date'),
                'notes': post.get('notes', ''),
                'state': 'draft',
            }
            
            # Handle receipt photo upload
            if post.get('receipt_photo'):
                expense_vals['receipt_photo'] = base64.b64encode(post.get('receipt_photo').read())
            
            expense = request.env['cashier.expense'].create(expense_vals)
            
            return request.redirect('/cashbox/expenses')
            
        except Exception as e:
            return request.render('bigfour_cashbox.portal_error', {
                'error': str(e)
            })

    # Uninvoiced Revenue Routes
    @http.route('/cashbox/uninvoiced', type='http', auth='user', website=True)
    def cashbox_uninvoiced(self, **kw):
        """Uninvoiced revenue page"""
        uninvoiced = request.env['cashbox.uninvoiced'].search([
            ('create_uid', '=', request.env.user.id)
        ])
        
        values = {
            'page_name': 'cashbox',
            'uninvoiced': uninvoiced,
        }
        return request.render('bigfour_cashbox.portal_uninvoiced_list', values)

    @http.route('/cashbox/uninvoiced/create', type='http', auth='user', website=True)
    def create_uninvoiced(self, **kw):
        """Create uninvoiced revenue form"""
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        customers = request.env['res.partner'].search([
            ('is_company', '=', False),
            ('customer_rank', '>', 0)
        ])
        
        values = {
            'page_name': 'cashbox',
            'cashboxes': cashboxes,
            'customers': customers,
        }
        return request.render('bigfour_cashbox.portal_uninvoiced_form', values)

    @http.route('/cashbox/uninvoiced/submit', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def submit_uninvoiced(self, **post):
        """Submit uninvoiced revenue"""
        try:
            uninvoiced_vals = {
                'revenue_name': post.get('revenue_name'),
                'customer_id': int(post.get('customer_id')) if post.get('customer_id') else False,
                'amount': float(post.get('amount', 0)),
                'cashbox_id': int(post.get('cashbox_id')),
                'date': post.get('date'),
                'notes': post.get('notes', ''),
                'state': 'draft',
            }
            
            uninvoiced = request.env['cashbox.uninvoiced'].create(uninvoiced_vals)
            
            return request.redirect('/cashbox/uninvoiced')
            
        except Exception as e:
            return request.render('bigfour_cashbox.portal_error', {
                'error': str(e)
            })

    # Transfer Routes
    @http.route('/cashbox/transfers', type='http', auth='user', website=True)
    def cashbox_transfers(self, **kw):
        """Cashbox transfers page"""
        transfers = request.env['cashbox.transfer'].search([
            ('create_uid', '=', request.env.user.id)
        ])
        
        values = {
            'page_name': 'cashbox',
            'transfers': transfers,
        }
        return request.render('bigfour_cashbox.portal_transfers_list', values)

    @http.route('/cashbox/transfer/create', type='http', auth='user', website=True)
    def create_transfer(self, **kw):
        """Create transfer form"""
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        
        values = {
            'page_name': 'cashbox',
            'cashboxes': cashboxes,
        }
        return request.render('bigfour_cashbox.portal_transfer_form', values)

    @http.route('/cashbox/transfer/submit', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def submit_transfer(self, **post):
        """Submit transfer"""
        try:
            transfer_vals = {
                'source_cashbox_id': int(post.get('source_cashbox_id')),
                'destination_cashbox_id': int(post.get('destination_cashbox_id')),
                'amount': float(post.get('amount', 0)),
                'date': post.get('date'),
                'notes': post.get('notes', ''),
                'state': 'draft',
            }
            
            transfer = request.env['cashbox.transfer'].create(transfer_vals)
            
            return request.redirect('/cashbox/transfers')
            
        except Exception as e:
            return request.render('bigfour_cashbox.portal_error', {
                'error': str(e)
            })

    # Cashbox Report Route
    @http.route('/cashbox/report', type='http', auth='user', website=True)
    def cashbox_report(self, **kw):
        """Cashbox report page"""
        # Get all cashboxes
        cashboxes = request.env['account.journal'].search([
            ('type', '=', 'cash')
        ])
        
        report_data = []
        total_balance = 0
        
        for cashbox in cashboxes:
            # Get cashbox balance
            balance = cashbox.current_statement_id.balance_end_real if cashbox.current_statement_id else 0
            total_balance += balance
            
            # Get pending transactions
            pending_payments = request.env['cashbox.payment'].search_count([
                ('cashbox_id', '=', cashbox.id),
                ('state', '=', 'draft')
            ])
            pending_collections = request.env['cashbox.collection'].search_count([
                ('cashbox_id', '=', cashbox.id),
                ('state', '=', 'draft')
            ])
            pending_expenses = request.env['cashier.expense'].search_count([
                ('cashbox_id', '=', cashbox.id),
                ('state', '=', 'draft')
            ])
            
            # Get recent transactions
            recent_payments = request.env['cashbox.payment'].search([
                ('cashbox_id', '=', cashbox.id),
                ('state', '!=', 'draft')
            ], limit=5, order='create_date desc')
            
            recent_collections = request.env['cashbox.collection'].search([
                ('cashbox_id', '=', cashbox.id),
                ('state', '!=', 'draft')
            ], limit=5, order='create_date desc')
            
            recent_expenses = request.env['cashier.expense'].search([
                ('cashbox_id', '=', cashbox.id),
                ('state', '!=', 'draft')
            ], limit=5, order='create_date desc')
            
            report_data.append({
                'cashbox': cashbox,
                'balance': balance,
                'pending_payments': pending_payments,
                'pending_collections': pending_collections,
                'pending_expenses': pending_expenses,
                'recent_payments': recent_payments,
                'recent_collections': recent_collections,
                'recent_expenses': recent_expenses,
            })
        
        values = {
            'page_name': 'cashbox',
            'report_data': report_data,
            'total_balance': total_balance,
            'currency': request.env.company.currency_id,
        }
        return request.render('bigfour_cashbox.cashbox_report_template', values)

