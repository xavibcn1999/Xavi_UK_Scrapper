def calculate_and_send_email(self, item):
    try:
        asin = item['nkw']
        ebay_product_price = item['product_price']
        ebay_shipping_fee = item['shipping_fee']
        ebay_price = ebay_product_price + ebay_shipping_fee
        
        # Debugging information
        logging.info(f"Calculando ROI para ASIN: {asin}")
        logging.info(f"Precio del producto en eBay: {ebay_product_price}")
        logging.info(f"Costo de envío en eBay: {ebay_shipping_fee}")
        logging.info(f"Precio de eBay (producto + envío): {ebay_price}")

        amazon_item = self.collection_a.find_one({'ASIN': asin})
        
        if amazon_item:
            logging.info(f"Documento de Amazon recuperado: {amazon_item}")
            
            amazon_used_price_str = amazon_item.get('Buy Box Used: 180 days avg.', 0)
            logging.info(f"Valor extraído de 'Buy Box Used: 180 days avg': {amazon_used_price_str}")
            
            if isinstance(amazon_used_price_str, str):
                try:
                    amazon_used_price = self.convert_price(amazon_used_price_str)
                except ValueError as e:
                    logging.error(f"Error al convertir 'Buy Box Used: 180 days avg' a float: {e}")
                    amazon_used_price = 0.0
            else:
                amazon_used_price = float(amazon_used_price_str)

            fba_fee_str = amazon_item.get('FBA Fees', 0)
            if isinstance(fba_fee_str, str):
                try:
                    fba_fee = self.convert_price(fba_fee_str)
                except ValueError as e:
                    logging.error(f"Error al convertir 'FBA Fees' a float: {e}")
                    fba_fee = 0.0
            else:
                fba_fee = float(fba_fee_str)

            referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
            referral_fee = amazon_used_price * referral_fee_percentage

            # Adjusted profit calculation
            profit = amazon_used_price - ebay_price - fba_fee - referral_fee
            roi = (profit / ebay_price) * 100 if ebay_price else 0

            logging.info(f"Precio de venta en Amazon (Buy Box Used): {amazon_used_price}")
            logging.info(f"Tarifa de FBA: {fba_fee}")
            logging.info(f"Tarifa de referencia: {referral_fee}")
            logging.info(f"Ganancia: {profit}")
            logging.info(f"ROI: {roi}%")

            if roi > 50:  # Adjust the ROI threshold as needed
                ebay_url = self.collection_e.find_one({'_id': item['_id']}).get('url', '')
                self.send_email(
                    item['image_url'], ebay_url, ebay_price,
                    amazon_item.get('Image', ''), amazon_item.get('URL: Amazon', ''), amazon_used_price, roi
                )

    except Exception as e:
        logging.error(f"Error calculating ROI and sending email: {e}")

