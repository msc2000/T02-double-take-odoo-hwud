from odoo import models, fields

class BusinessAI(models.Model):
    _name = 'business.ai'
    _description = 'Business AI'

    name = fields.Char(string='Name', required=True)

    # This is to select the actual product under inventory in odoo
    product_id = fields.Many2one(
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

    recommended_reorder_quantity = fields.Float(
        string='Recommended Reorder Quantity',
        compute='_compute_recommended_reorder_quantity'
    )

    stockout_risk = fields.Selection(
        [
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        string='Stockout Risk',
        compute='_compute_stockout_risk'
    )

    recommendation = fields.Text(
          string='AI Recommendation',
          compute='_compute_recommendation'
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

    '''FUNCTIONS FOR THE AI MODEL'''
    #to calculate the stock quantity of the selected product
    def _compute_stock_quantity(self):
        for record in self:
            if record.product_id:
                record.stock_quantity = sum(
                    self.env['stock.quant'].search([
                        ('product_id', '=', record.product_id.id),
                        ('location_id.usage', '=', 'internal'),
                    ]).mapped('quantity')
                )
            else:
                record.stock_quantity = 0

    # Calculate how many units of the selected product have been sold
    def _compute_units_sold(self):
        for record in self:
            if record.product_id:
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
                    # Find the earliest confirmed sale
                    sale_dates = [
                        line.order_id.date_order.date()
                        for line in sale_lines
                        if line.order_id.date_order
                    ]

                    earliest_date = min(sale_dates)
                    today = fields.Date.context_today(record)

                    # +1 means a sale made today counts as one day
                    days = max((today - earliest_date).days + 1, 1)

                    record.average_daily_sales = (
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
                record.days_until_stockout = 0

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

    #AI recommneds what to do next when product is nearly out of stock
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