import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta

# Función para extraer los datos de un nodo de cliente de Spartoo
def extract_spartoo_customer_info(customer_node):
    return {
        'firstname': customer_node.findtext('customers_firstname'),
        'lastname': customer_node.findtext('customers_lastname'),
        'company': customer_node.findtext('customers_company'),
        'street_address': customer_node.findtext('customers_street_address'),
        'suburb': customer_node.findtext('customers_suburb'),
        'city': customer_node.findtext('customers_city'),
        'postcode': customer_node.findtext('customers_postcode'),
        'state': customer_node.findtext('customers_state'),
        'country': customer_node.findtext('customers_country'),
        'email_address': customer_node.findtext('customers_email_address'),
        'telephone': customer_node.findtext('customers_telephone')
    }

# Función para extraer los datos de un nodo de entrega de Spartoo
def extract_spartoo_delivery_info(delivery_node):
    relay_info_node = delivery_node.find('relay_info')
    relay_info = None
    if relay_info_node is not None:
        relay_info = {
            'id': relay_info_node.findtext('relay_id'),
            'type': relay_info_node.findtext('relay_type'),
            'name': relay_info_node.findtext('relay_name'),
            'address': relay_info_node.findtext('relay_address'),
            'city': relay_info_node.findtext('relay_city'),
            'postcode': relay_info_node.findtext('relay_postcode'),
            'country_iso': relay_info_node.findtext('relay_country_iso')
        }
    
    return {
        'firstname': delivery_node.findtext('delivery_firstname'),
        'lastname': delivery_node.findtext('delivery_lastname'),
        'relay_info': relay_info,
        'company': delivery_node.findtext('delivery_company'),
        'suburb': delivery_node.findtext('delivery_suburb'),
        'street_address': delivery_node.findtext('delivery_street_address'),
        'city': delivery_node.findtext('delivery_city'),
        'postcode': delivery_node.findtext('delivery_postcode'),
        'state': delivery_node.findtext('delivery_state'),
        'country': delivery_node.findtext('delivery_country')
    }

# Función para extraer los datos de un producto de Spartoo
def extract_spartoo_product_info(product_node):
    return {
        'reference': product_node.findtext('products_reference'),
        'name': product_node.findtext('products_name'),
        'qty': int(product_node.findtext('products_qty')),
        'spartoo': int(product_node.findtext('products_spartoo')),
        'manufacturers': product_node.findtext('products_manufacturers'),
        'size': product_node.findtext('products_size'),
        'size_reference': product_node.findtext('products_size_reference'),
        'color': product_node.findtext('products_color'),
        'price_unit': float(product_node.findtext('products_price_unit')),
        'price_unit_with_reduce': float(product_node.findtext('products_price_unit_with_reduce')),
        'final_price': float(product_node.findtext('products_final_price'))
    }

# Función para extraer los datos de un pedido de Spartoo
def extract_spartoo_order_info(order_node):
    return {
        'orders_id': order_node.findtext('orders_id'),
        'customers': extract_spartoo_customer_info(order_node.find('customers')),
        'delivery': extract_spartoo_delivery_info(order_node.find('delivery')),
        'payment_method': order_node.findtext('payment_method'),
        'payment_price': float(order_node.findtext('payment_price')),
        'shipping_price': float(order_node.findtext('shipping_price')),
        'shipping_name': order_node.findtext('shipping_name'),
        'order_total': float(order_node.findtext('order_total')),
        'orders_status_name': order_node.findtext('orders_status_name'),
        'orders_status_id': int(order_node.findtext('orders_status_id')),
        'date_purchased': order_node.findtext('date_purchased'),
        'last_modified': order_node.findtext('last_modified'),
        'products': [extract_spartoo_product_info(p) for p in order_node.findall('.//product')],
        'errors': [{
            'id': int(error.findtext('id')),
            'description': error.findtext('description')
        } for error in order_node.findall('.//error')]
    }

# Función principal
def order_status_spartoo(cf_id, orders_connection, order_id, shipping_id, access_token):
    orders_start_date = datetime.now() - timedelta(days=10)

    formatted_date = orders_start_date.strftime('%Y-%m-%d:%H:%M:%S')

    params = {
        "partenaire": access_token,
        "date": formatted_date,
        "statut": '',
    }

    response = requests.get('https://sws.spartoo.es/mp/xml_export_orders.php', params=params)

    root = ET.fromstring(response)

    orders = [extract_spartoo_order_info(order) for order in root.findall('.//order')]

    pedido = {}
    val = []
    for order in orders:
        for product in order["products"]:
            order_state = order["orders_status_id"]

            if order_state in [41, 45, 47, 3]: # Igual en un futuro hay que añadir más estados alternativos en los que no se puede aceptar ni añadir el pedido
                continue

            order_line_id = f"{order['orders_id']}"

        if order['orders_id'] == order_id:
            pedido = order
            break

    match pedido['orders_status_id']:
        case 11:
            order_info = (cf_id,
                order["orders_id"],
                order["last_modified"],
                order["customers"]["city"],
                order["customers"]["country"],
                order["customers"]["firstname"],
                order["customers"]["lastname"],
                order["customers"]["telephone"],
                order["customers"]["street_address"],
                order["customers"]["suburb"],
                order["customers"]["postcode"],
                order["customers"]["email_address"],
                product["size_reference"], # qué hay que poner aquí? (mirar en la base de datos)
                order_line_id,
                order["orders_status_name"],
                product["price_unit"],
                product["name"],
                product["qty"],
                order["shipping_price"],
                product["final_price"])
        
            val.append(order_info)
            data = {
            "partenaire": access_token,
            "oID": order_id,
            "statut": '2',
            }
            response = requests.post("https://sws.spartoo.es/mp/xml_maj_orders.php", data=data)
            print(response)
            
            # Comando SQL (ignore para que solo se añadan los nuevos)
            sql = "INSERT IGNORE INTO orders_spartoo (cf_id, order_id, acceptance_decision_date, city, country, firstname, lastname, phone, street_1, street_2, zip_code, customer_notification_email, product_sku, order_line_id, order_status, price, product_title, quantity, shipping_price, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            cur = orders_connection.cursor()

            # Añadir datos nuevos
            for v in val:
                cur.execute(sql, v)

            orders_connection.commit()
            cur.close()
        case 2:
            data = {
                "partenaire": access_token,
                "oID": order_id,
                "statut": '3',
                "tracking_number": shipping_id,
            }
            response = requests.post("https://sws.spartoo.es/mp/xml_maj_orders.php", data=data)
            print(response)

            update_query = f"""
            UPDATE orders_spartoo
            SET status = 1
            WHERE marketplace_order = {order_id}
            """

            cursor = orders_connection.cursor()
            cursor.execute(update_query)
            orders_connection.commit()
            cursor.close()
            return True
        case 3:
            return True