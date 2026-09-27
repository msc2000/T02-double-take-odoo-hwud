from odoo import models, fields
import os
import requests

from dotenv import load_dotenv
load_dotenv()

'''Odoo concept:
The compute='...' is a computed field, odoo uses named method to calculate values 
rather than reading a manually entered value. (i.e., rather than the user finding answers, the functions created give answers for each field) '''

#Two Odoo Models created using models.Model for this project: BusinessAI model and BusinessDashboard model
class BusinessAI(models.Model):
    _name = 'business.ai'
    _description = 'Business AI'

    name = fields.Char(string='Name', required=True)#name field creates a text field

    # This is to select the actual product under inventory in odoo
    product_id = fields.Many2one( #Many2one means this record points to one record from another Odoo model
        'product.product',
        string='Product'
    )

    #This is to get current stock
    stock_quantity = fields.Float(
        string='Current Stock',
        compute='_compute_stock_quantity'
    )

    #This is to get units sold
    units_sold = fields.Float(
        string='Units Sold',
        compute='_compute_units_sold'
    )

    #This gets the average daily sales
    average_daily_sales = fields.Float(
        string='Average Daily Sales',
        compute='_compute_average_daily_sales'
    )

    #Number of days until stock runs out
    days_until_stockout = fields.Float(
        string='Days Until Stockout',
        compute='_compute_days_until_stockout'
    )

    #calculates the number of units the business should order to bring inventory back to approx. 7 days of stock
    recommended_reorder_quantity = fields.Float(
        string='Recommended Reorder Quantity',
        compute='_compute_recommended_reorder_quantity'
    )

    #Stockout risk calculated based on these conditions: ≤ 3 days  → High | ≤ 7 days  → Medium | > 7 days  → Low
    stockout_risk = fields.Selection( 
        [
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        string='Stockout Risk',
        compute='_compute_stockout_risk'
    )

    #checking whether the stock we have is too much and is not selling, so its a waste of inventory
    overstock_risk = fields.Selection(
    [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ],
    string='Overstock Risk',
    compute='_compute_overstock_risk'
    )

    recommendation = fields.Text(
          string='AI Recommendation',
          compute='_compute_recommendation'
    )

    risk_explanation = fields.Text(
    string='Risk Explanation',
    compute='_compute_risk_explanation'
    )

    ai_insight = fields.Text(
    string='AI Business Insight'
    )

    high_risk_count = fields.Integer(
        string='High Risk Products',
        compute='_compute_risk_counts'
    )

    medium_risk_count = fields.Integer(
        string='Medium Risk Products',
        compute='_compute_risk_counts'
    )

    low_risk_count = fields.Integer(
        string='Low Risk Products',
        compute='_compute_risk_counts'
    )

    '''ODOOPULSE BUSINESS LOGIC'''
    #to calculate the stock quantity of the selected product
    def _compute_stock_quantity(self):
        for record in self: #self can represent one or many businessAI records (an odoo concept)
            if record.product_id:
                record.stock_quantity = sum(
                    #searching stock of a product by equating product id with selected product from records and summing up all available stock in multiple internal locations of a warehouse
                    self.env['stock.quant'].search([
                        ('product_id', '=', record.product_id.id),
                        ('location_id.usage', '=', 'internal'),
                    ]).mapped('quantity')
                )
            else:
                record.stock_quantity = 0 #if no such product with a product id exists, stock is zero

    # Calculate how many units of the selected product have been sold
    def _compute_units_sold(self):
        for record in self:
            if record.product_id:
                #sale.order.line represents individual sales orders
                sale_lines = self.env['sale.order.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('order_id.state', '=', 'sale'), #only counting confirmed sales orders, rather than draft/quotation orders
                ])

                record.units_sold = sum(
                    sale_lines.mapped('product_uom_qty')
                )
            else:
                record.units_sold = 0

    # Calculate average number of units sold per day
    def _compute_average_daily_sales(self):
        for record in self:
            if record.product_id:
                sale_lines = self.env['sale.order.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('order_id.state', '=', 'sale'),
                ])

                if sale_lines:
                    # Finding dates of confirmed orders
                    sale_dates = [
                        line.order_id.date_order.date()
                        for line in sale_lines
                        if line.order_id.date_order
                    ]

                    #finding earliest sale
                    earliest_date = min(sale_dates)
                    today = fields.Date.context_today(record)

                    # +1 means a sale made today counts as one day
                    days = max((today - earliest_date).days + 1, 1)

                    record.average_daily_sales = ( # this is the sales velocity
                        record.units_sold / days
                    )
                else:
                    record.average_daily_sales = 0
            else:
                record.average_daily_sales = 0

    # Predict how many days until the product runs out of stock
    def _compute_days_until_stockout(self):
        for record in self:
            if record.average_daily_sales > 0:
                record.days_until_stockout = (
                    record.stock_quantity / record.average_daily_sales
                )
            else:
                record.days_until_stockout = 999 #The placeholder value 999 is used when no sales have been made for a product so we are unable to predict when the product will be out of stock

    #Predict how much to reorder when stock is running out based on average daily sales
    def _compute_recommended_reorder_quantity(self):
        for record in self:
            target_stock = record.average_daily_sales * 7
            record.recommended_reorder_quantity = max(target_stock - record.stock_quantity, 0)
    
    # Classify the stockout risk based on predicted days remaining
    def _compute_stockout_risk(self):
        for record in self:
            if record.days_until_stockout <= 3:
                record.stockout_risk = 'high'
            elif record.days_until_stockout <= 7:
                record.stockout_risk = 'medium'
            else:
                record.stockout_risk = 'low'

    def _compute_overstock_risk(self):
        for record in self:
            if record.average_daily_sales == 0:
                if record.stock_quantity >= 20:
                    record.overstock_risk = 'high'
                elif record.stock_quantity > 0:
                    record.overstock_risk = 'medium'
                else:
                    record.overstock_risk = 'low'

            else:
                days_of_stock = (
                    record.stock_quantity / record.average_daily_sales
                )

                if days_of_stock >= 30:
                    record.overstock_risk = 'high'
                elif days_of_stock >= 14:
                    record.overstock_risk = 'medium'
                else:
                    record.overstock_risk = 'low'
                    
    #Python function recommends what to do next when product is nearly out of stock
    def _compute_recommendation(self):
        for record in self:
            if record.stockout_risk == 'high':
                record.recommendation = (
                    f'High stockout risk. '
                    f'Estimated stock remaining: '
                    f'{record.days_until_stockout:.1f} days. '
                    f'Reorder stock soon.'
                )
            elif record.stockout_risk == 'medium':
                record.recommendation = (
                    f'Medium stockout risk. '
                    f'Estimated stock remaining: '
                    f'{record.days_until_stockout:.1f} days. '
                    f'Consider reordering stock.'
                )
            else:
                record.recommendation = (
                    f'Low stockout risk. '
                    f'Estimated stock remaining: '
                    f'{record.days_until_stockout:.1f} days. '
                    f'No immediate action required.'
                )

    def _compute_risk_explanation(self):
        for record in self:
            if not record.product_id:
                record.risk_explanation = 'No product selected.'
                continue

            if record.average_daily_sales > 0:
                record.risk_explanation = (
                    f'{record.product_id.display_name} currently has '
                    f'{record.stock_quantity:.0f} units in stock and is selling '
                    f'an average of {record.average_daily_sales:.1f} units per day. '
                    f'At the current sales rate, available stock is expected to '
                    f'last approximately {record.days_until_stockout:.1f} days. '
                    f'OdooPulse recommends replenishing '
                    f'{record.recommended_reorder_quantity:.0f} units to maintain '
                    f'approximately 7 days of stock.'
                )
            else:
                record.risk_explanation = (
                    f'{record.product_id.display_name} currently has '
                    f'{record.stock_quantity:.0f} units in stock but no confirmed '
                    f'sales activity. OdooPulse cannot estimate a stockout based '
                    f'on sales velocity, so no immediate replenishment is recommended.'
                )
    
    # Generate an AI business insight using the calculated OdooPulse metrics
    def action_generate_ai_insight(self):
        self.ensure_one()

        if not self.product_id:
            return False

        prompt = f"""
        You are an AI business assistant for a small business.

        Analyze this inventory situation and provide a short business insight.

        Product: {self.product_id.display_name}
        Current stock: {self.stock_quantity:.0f} units
        Average daily sales: {self.average_daily_sales:.1f} units/day
        Days until stockout: {self.days_until_stockout:.1f} days
        Stockout risk: {self.stockout_risk}
        Overstock risk: {self.overstock_risk}
        Recommended reorder quantity: {self.recommended_reorder_quantity:.0f} units

        Give:
        1. A brief explanation of the situation.
        2. The most important business action.

        Keep the response under 100 words.
        """

        api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            self.ai_insight = 'GROQ_API_KEY is not configured.'
            return False

        response = requests.post('https://api.groq.com/openai/v1/responses',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            json={
                'model': 'openai/gpt-oss-20b',
                'input': prompt,
            },
            timeout=30,
        )

        if response.status_code != 200:
            self.ai_insight = (f'AI request failed: {response.status_code}')
            return False

        data = response.json()

        output = data.get('output', [])

        if output:
            for item in output:
                if item.get('type') == 'message':
                    content = item.get('content', [])

                    for content_item in content:
                        if content_item.get('type') == 'output_text':
                            self.ai_insight = content_item.get(
                                'text',
                                'AI returned no response.'
                            )
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'reload',
                            }

        self.ai_insight = 'AI returned no response.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # Create an Odoo Purchase Order based on the recommended reorder quantity
    def action_create_purchase_order(self):
        self.ensure_one()

        if not self.product_id:
            return False

        if self.recommended_reorder_quantity <= 0:
            return False

        # Find a vendor for the selected product
        seller = self.product_id.seller_ids[:1]

        if not seller:
            return False

        # Create the Purchase Order
        purchase_order = self.env['purchase.order'].create({
            'partner_id': seller.partner_id.id,
        })

        # Add the product to the Purchase Order
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': self.product_id.id,
            'product_qty': self.recommended_reorder_quantity,
            'price_unit': seller.price,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            'target': 'current',
        }

    def _compute_risk_counts(self):
        analyses = self.search([])

        high_count = len(
            analyses.filtered(
                lambda record: record.stockout_risk == 'high'
            )
        )

        medium_count = len(
            analyses.filtered(
                lambda record: record.stockout_risk == 'medium'
            )
        )

        low_count = len(
            analyses.filtered(
                lambda record: record.stockout_risk == 'low'
            )
        )

        for record in self:
            record.high_risk_count = high_count
            record.medium_risk_count = medium_count
            record.low_risk_count = low_count


'''BUSINESS DASHBOARD MODEL to display information'''
class BusinessDashboard(models.Model):
    _name = 'business.dashboard'
    _description = 'OdooPulse Business Dashboard'

    name = fields.Char(
        string='Name',
        default='OdooPulse Dashboard'
    )

    high_risk_count = fields.Integer(
        string='High Risk Products',
        compute='_compute_risk_counts'
    )

    medium_risk_count = fields.Integer(
        string='Medium Risk Products',
        compute='_compute_risk_counts'
    )

    low_risk_count = fields.Integer(
        string='Low Risk Products',
        compute='_compute_risk_counts'
    )

    overstock_high_count = fields.Integer(
    string='High Overstock Risk',
    compute='_compute_overstock_count'
    )

    overstock_medium_count = fields.Integer(
        string='Medium Overstock Risk',
        compute='_compute_overstock_count'
    )

    overstock_message = fields.Text(
    string='Overstock Details',
    compute='_compute_overstock_message'    
    )

    priority_message = fields.Text(
    string='Priority Actions',
    compute='_compute_priority_message'
    )

    def _compute_risk_counts(self):
        analyses = self.env['business.ai'].search([])
        high_count = len(
            analyses.filtered(lambda record: record.stockout_risk == 'high')
        )
        medium_count = len(
            analyses.filtered(lambda record: record.stockout_risk == 'medium')
        )
        low_count = len(
            analyses.filtered(lambda record: record.stockout_risk == 'low')
        )

        for record in self:
            record.high_risk_count = high_count
            record.medium_risk_count = medium_count
            record.low_risk_count = low_count

    def _compute_overstock_count(self):
        analyses = self.env['business.ai'].search([])
        high_count = len(
            analyses.filtered(
                lambda record: record.overstock_risk == 'high'
            )
        )
        medium_count = len(
            analyses.filtered(
                lambda record: record.overstock_risk == 'medium'
            )
        )
        for record in self:
            record.overstock_high_count = high_count
            record.overstock_medium_count = medium_count

    def _compute_overstock_message(self):
        analyses = self.env['business.ai'].search([])

        overstock_products = analyses.filtered(
            lambda record: record.overstock_risk in ['high', 'medium']
        )

        overstock_products = overstock_products.sorted(
            key=lambda record: record.stock_quantity,
            reverse=True
        )

        for record in self:
            if not overstock_products:
                record.overstock_message = ('No significant overstock risks detected.')
                continue

            messages = []

            for analysis in overstock_products[:5]:
                product_name = analysis.product_id.display_name

                if analysis.overstock_risk == 'high':
                    if analysis.average_daily_sales == 0:
                        details = (
                            f'{product_name}: '
                            f'{analysis.stock_quantity:.0f} units in stock '
                            f'with no confirmed sales.'
                        )
                    else:
                        days_of_stock = (analysis.stock_quantity / analysis.average_daily_sales)

                        details = (
                            f'{product_name}: approximately '
                            f'{days_of_stock:.0f} days of stock remaining.'
                        )

                    messages.append(
                        f'HIGH: {details}'
                    )

                else:
                    if analysis.average_daily_sales > 0:
                        days_of_stock = (analysis.stock_quantity / analysis.average_daily_sales)

                        messages.append(
                            f'MEDIUM: {product_name} has approximately '
                            f'{days_of_stock:.0f} days of stock remaining.'
                        )
                    else:
                        messages.append(
                            f'MEDIUM: {product_name} has '
                            f'{analysis.stock_quantity:.0f} units in stock '
                            f'with limited sales activity.'
                        )

            record.overstock_message = '\n'.join(messages)
                
    def _compute_priority_message(self):
        analyses = self.env['business.ai'].search([])

        analyses = analyses.filtered(
            lambda record: record.stockout_risk in ['high', 'medium']
        )

        analyses = analyses.sorted(
            key=lambda record: record.days_until_stockout
        )

        for record in self:
            if not analyses:
                record.priority_message = (
                    'No immediate inventory actions required.'
                )
                continue

            messages = []

            for analysis in analyses[:5]:
                product_name = analysis.product_id.display_name

                if analysis.stockout_risk == 'high':
                    action = (
                        f'URGENT: {product_name} is expected to run out '
                        f'in {analysis.days_until_stockout:.1f} days. '
                        f'Reorder {analysis.recommended_reorder_quantity:.0f} units.'
                    )
                else:
                    action = (
                        f'WATCH: {product_name} is expected to run out '
                        f'in {analysis.days_until_stockout:.1f} days. '
                        f'Consider reordering '
                        f'{analysis.recommended_reorder_quantity:.0f} units.'
                    )

                messages.append(action)

            record.priority_message = '\n'.join(messages)