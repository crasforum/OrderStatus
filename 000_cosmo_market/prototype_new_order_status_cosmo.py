import mysql.connector
from markets_credentials import *
import json
import requests
import iop
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

cf_id = '10000'

conn = mysql.connector.connect(
    host="185.18.197.49",
    user="cf_logistica_cosmo_market",
    password="Cf232323#",
    database="cf_logistica_cosmo_market"
)

orders_connection = mysql.connector.connect(
    host="185.23.119.190",
    port = 3306,
    user="alejandro",
    password="AlejandroCF2023!",
    database="crasforumdata",
)

def doRequest(request, params, request_type):
    if request_type == "GET":
        response = requests.get(request, params=params)
    elif request_type == "POST":
        response = requests.post(request, data=params)
    elif request_type == "PUT":
        response = requests.put(request, data=params)

    if response.status_code != 200:
        print(f"Error en la solicitud. Código de respuesta: {response.status_code}")
        print(response.text)

    return response.text

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


def get_tracking():
    try:
        # Conectarse a la base de datos
        cursor = conn.cursor()

        query = """
        SELECT o.marketplace_order, o.payment, o.current_state, c.shipment_code
        FROM prstshp_orders AS o
        JOIN prstshp_correos_preregister AS c ON o.id_order = c.id_order
        WHERE o.export = 0;
        """

        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()

        if result:
            for order in result:
                marketplace_order, payment, current_state, shipping_number = order
                flag = False
                if current_state not in [18, 19, 20, 21, 22, 23, 72, 74, 77, 87, 98, 99, 103, 104, 105, 106, 107, 108]:
                    match payment:
                        case 'Miravia':
                            flag = order_status_miravia(marketplace_order, shipping_number, miravia_credentials['api_key'], miravia_credentials['api_url'], miravia_credentials['api_secret'], miravia_credentials['access_token'], payment)
                            pass
                        case 'Tradeinn':
                            flag = order_status_mirakl(marketplace_order, shipping_number, tradeinn_credentials['api_key'], tradeinn_credentials['api_url'], payment)
                            pass
                        case 'Decathlon':
                            flag = order_status_mirakl(marketplace_order, shipping_number, decathlon_credentials['api_key'], decathlon_credentials['api_url'], payment)
                            pass
                        case 'Sprinter':
                            flag = order_status_mirakl(marketplace_order, shipping_number, sprinter_credentials['api_key'], sprinter_credentials['api_url'], payment)
                            pass
                        case 'Carrefour':
                            flag = order_status_mirakl(marketplace_order, shipping_number, carrefour_credentials['api_key'], carrefour_credentials['api_url'], payment)
                            pass
                        case 'Worten':
                            flag = order_status_mirakl(marketplace_order, shipping_number, worten_credentials['api_key'], worten_credentials['api_url'], payment)
                            pass
                        case 'Colizey':
                            flag = order_status_colizey(marketplace_order, shipping_number, colizey_credentials['api_key'], colizey_credentials['api_url'], payment)
                            pass
                        case 'Hipercalzado':
                            flag = order_status_hipercalzado(marketplace_order, shipping_number, hipercalzado_credentials['api_key'], hipercalzado_credentials['api_url'], payment)
                            pass
                        case 'Spartoo':
                            flag = order_status_spartoo(marketplace_order, shipping_number, spartoo_credentials['api_key'])
                            pass                        
                else:
                    flag = True
                if flag:
                    # Paso 3: Actualizar el valor de export a 1
                    print(f'Marcando pedido {marketplace_order} como estado de export a 1')
                    update_query = f"UPDATE prstshp_orders SET export = 1 WHERE marketplace_order = '{marketplace_order}'"

                    cursor = conn.cursor()
                    cursor.execute(update_query)
                    conn.commit()
                    cursor.close()
        
    except Exception as e:
        print(f"Algo ha fallado mientras se gestionaba el tracking del pedido {marketplace_order}: ", e)
    finally:
        conn.disconnect()
        orders_connection.disconnect()

def order_status_miravia(order_id, shipping_id, api_key, api_url, api_secret, access_token, payment):
    client = iop.IopClient(api_url, api_key, api_secret)

    request = iop.IopRequest('/order/items/get', 'GET')
    request.add_api_param('order_id', order_id)
    response = client.execute(request, access_token)

    if len(response.body['data']) > 1:
        all_products = []
        orders = response.body['data']
        for order_line in orders:
            if order_line['status'] == 'shipped' or order_line['status'] == 'delivered' or order_line['status'] == 'canceled' or order_line['status'] == 'returned':
                all_products.append(order_line)
        if len(all_products) == len(response.body['data']):
            return True
        print('PEDIDO MULTIPLE: ', order_id)
        return False
    for item in response.body['data']:
        package_id = item['package_id']

        if item['tracking_code'] != shipping_id:
            # Añadir Tracking
            params = {
                "update_packages":[
                    {
                        "tracking_number": shipping_id,
                        "package_id": package_id,
                        "shipment_provider_code": "DBSSP100000308"
                    }
                ]
            }

            params = json.dumps(params)
            request = iop.IopRequest('/order/package/tracking/update', 'POST')
            request.add_api_param('updateTrackingInfoReq', params)
            response = client.execute(request, access_token)

            if response.body["code"] not in ['0', '200']:
                print(f"Algo ha fallado con el pedido {order_id}. Código de error: {response.body['code']}. Mensaje: {response.body['message']}")
            else:
                print(f"Tracking añadido: {package_id}")

        if item['status'] == 'packed':
            # Marcar ready_to_ship
            params = {
                "packages":[
                    {
                        "package_id": package_id,
                    }
                ]
            }

            params = json.dumps(params)
            request = iop.IopRequest('/order/package/rts', 'POST')
            request.add_api_param('readyToShipReq', params)
            response = client.execute(request, access_token)

            if response.body["code"] not in ['0', '200']:
                print(f"No se ha podido marcar el pedido {order_id} como ready_to_ship correctamente:")
                print(f"respuesta: {response}")
            else:
                print(f'Pedido {order_id} de Miravia marcado como Ready To Ship')

            return False

        if item['status'] == 'ready_to_ship':
            # Marcar como enviado
            params = {
                "packages":[
                    {
                        "package_id": package_id,
                    }
                ]
            }
            
            params = json.dumps(params)
            request = iop.IopRequest('/order/package/sof/confirm/collected', 'POST')
            request.add_api_param('dbsCollectedReq', params)
            response = client.execute(request, access_token)

            if response.body["code"] not in ['0', '200']:
                print("No se ha podido marcar el pedido como enviado correctamente:")
                print(f"respuesta: {response}")
                return False
            else:
                print(f"Pedido de {payment} marcado como enviado: {order_id}")
                return True
            
        if item['status'] in ['delivered', 'canceled', 'shipped']:
            return True

def order_status_mirakl(order_id, shipping_id, api_key, api_url, payment):
    headers = {"Authorization": api_key, "Content-Type" : "application/json"}

    api_request = f"orders"

    params = {
        'order_ids': order_id,
    }

    response = requests.get(api_url + api_request, headers=headers, params=params)

    if response.status_code in [200, 204]:
        orders_dict = json.loads(response.text)
        orders = orders_dict['orders']
        order_lines = []

        if len(orders[0]['order_lines']) > 1:
            all_products = []
            for order_line in orders[0]['order_lines']:
                if order_line['order_line_state'] == 'SHIPPED' or order_line['order_line_state'] == 'SHIPPING' or order_line['order_line_state'] == 'DELIVERED' or order_line['order_line_state'] == 'REFUNDED' or order_line['order_line_state'] == 'RECEIVED' or order_line['refunds'] != []:
                    all_products.append(order_line)
            if len(all_products) == len(orders[0]['order_lines']):
                return True
            print('PEDIDO MULTIPLE: ', order_id)
            return False
        
        if orders[0]['order_state'] == 'WAITING_ACCEPTANCE':
            for order_line in orders[0]['order_lines']:
                order_lines.append({
                    "accepted": True,
                    "id": order_line["order_line_id"]
                })

            api_request = f"orders/{order_id}/accept"

            data = {
                "order_lines": order_lines
            }

            json_data = json.dumps(data, indent=4)
            response = requests.put(api_url + api_request, headers=headers, data=json_data)

            if response.status_code in [200, 204]:
                print("PEDIDO ACEPTADO: ", orders[0]['order_id'])
            else:
                print(f"ERROR AL ACEPTAR EL PEDIDO {orders[0]['order_id']} {response.text}")

        # Verifica la respuesta del servidor
        if orders[0]['order_state'] == 'SHIPPING':
            # Añadir Tracking
            api_request = f"orders/{order_id}/tracking"

            data = {
                #"carrier_code": "CORREOS-EXPRESS",
                "carrier_name": "Correos",
                "carrier_url": "https://correos.es",
                "tracking_number": shipping_id,
            }

            request_body = json_data = json.dumps(data, indent=4)
            response = requests.put(api_url + api_request, headers=headers, data=request_body)

            # Verifica la respuesta del servidor
            if response.status_code not in [200, 204]:
                # La solicitud fue un fracaso
                print("ADVERTENCIA_TRACKER: " + response.text)
            else:
                # Validar tracking
                api_request = f"orders/{order_id}/ship"

                response = requests.put(api_url + api_request, headers=headers)

                # Verifica la respuesta del servidor
                if response.status_code not in [200, 204]:
                    # La solicitud fue un fracaso
                    print("ADVERTENCIA_VALIDAR_TRACKER: " + response.text)
                if response.status_code in [200, 204]:
                    # La solicitud fue un fracaso
                    print(f"Pedido de {payment} marcado como enviado: {order_id}")
                    return True
        if orders[0]['order_state'] == 'SHIPPED' or orders[0]['order_state'] == 'CLOSED':
            return True
    else:
        print(f"No se ha encontrado el pedido con order_id: {order_id}")

def order_status_spartoo(order_id, shipping_id, access_token):
    orders_start_date = datetime.now() - timedelta(days=10)

    formatted_date = orders_start_date.strftime('%Y-%m-%d:%H:%M:%S')

    params = {
        "partenaire": access_token,
        "date": formatted_date,
        "statut": '',
    }

    response = doRequest('https://sws.spartoo.es/mp/xml_export_orders.php', params, 'GET')

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
            params = {
            "partenaire": access_token,
            "oID": order_id,
            "statut": '2',
            }
            response = doRequest("https://sws.spartoo.es/mp/xml_maj_orders.php", params, "POST")
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
            params = {
                "partenaire": access_token,
                "oID": order_id,
                "statut": '3',
                "tracking_number": shipping_id,
            }
            response = doRequest("https://sws.spartoo.es/mp/xml_maj_orders.php", params, "POST")
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

def order_status_colizey(order_id, shipping_id, api_key, api_url, payment):
    headers = {"x-apikey": api_key}

    api_request = f"orders/{order_id}"

    response = requests.get(api_url + api_request, headers=headers)

    if response.status_code in [200, 204]:
        order = json.loads(response.text)

        if len(order['orderLines']) > 1:
            all_products = []
            for order_line in order['orderLines']:
                if order_line['status'] == 5:
                    all_products.append(order_line)
            if len(all_products) == len(order['orderLines']):
                return True
            print('PEDIDO MULTIPLE: ', order_id)
            return False
        
        # Si el pedido está pagado
        if order['status'] == 1:
            # Aceptar un pedido
            api_request = f"orders/{order_id}/accept"
            response = requests.put(api_url + api_request, headers=headers, data=json_data)

            if response.status_code in [200, 204]:
                print("PEDIDO ACEPTADO: ", order['order_id'])
            else:
                print(f"ERROR AL ACEPTAR EL PEDIDO {order['order_id']} {response.text}")

        # Si el pedido está aceptado
        if order['status'] == 2:
            # Añadir Tracking
            api_request = f"orders/{order_id}/ship"

            data = {
                "trackingUrl": "https://correos.es",
                "trackingNumber": shipping_id,
            }

            request_body = json_data = json.dumps(data)
            response = requests.put(api_url + api_request, headers=headers, data=request_body)

            # Verifica la respuesta del servidor
            if response.status_code not in [200, 204]:
                # La solicitud fue un fracaso
                print("ADVERTENCIA_TRACKER: " + response.text)
            else:
                # La solicitud fue un exito
                print(f"Pedido de {payment} marcado como enviado: {order_id}")
                return True

        if order['status'] == 3 or order['status'] == 4 or order['status'] == 6:
            return True
    else:
        print(f"No se ha encontrado el pedido con order_id: {order_id}")

def order_status_hipercalzado(order_id, shipping_id, api_key, api_url, payment):
    headers = {"Authorization": api_key, "Content-Type" : "application/json"}

    api_request = f"orders"

    params = {
        'order_ids': order_id,
    }

    response = requests.get(api_url + api_request, headers=headers, params=params)

    if response.status_code in [200, 204]:
        orders_dict = json.loads(response.text)
        orders = orders_dict['orders']
        order_lines = []

        if len(orders[0]['order_lines']) > 1:
            print('PEDIDO MULTIPLE: ', order_id)
            return False
        
        if orders[0]['order_state'] == 'ORDER_WAITING_ACCEPTANCE':
            for order_line in orders[0]['order_lines']:
                order_lines.append({
                    "accept": True,
                    "id": order_line["order_line_id"]
                })

            api_request = f"orders/{order_id}/accept"

            data = {
                "order_lines": order_lines
            }

            json_data = json.dumps(data, indent=4)
            response = requests.put(api_url + api_request, headers=headers, data=json_data)

            if response.status_code in [200, 204]:
                print('PEDIDO ACEPTADO: ', orders[0]['order_id'])
            else:
                print(f"ERROR AL ACEPTAR EL PEDIDO {orders[0]['order_id']} {response.text}")

        # Verifica la respuesta del servidor
        if orders[0]['order_state'] == 'ORDER_SHIPPING':
            # Añadir Tracking
            api_request = f"orders/{order_id}/tracking"

            data = {
                #"carrier_code": "CORREOS-EXPRESS",
                "carrier_name": "Correos",
                "carrier_url": "https://correos.es",
                "tracking_number": shipping_id,
            }

            request_body = json_data = json.dumps(data, indent=4)
            response = requests.put(api_url + api_request, headers=headers, data=request_body)

            # Verifica la respuesta del servidor
            if response.status_code not in [200, 204]:
                # La solicitud fue un fracaso
                print("ADVERTENCIA_TRACKER: " + response.text)
            else:
                # Validar tracking
                api_request = f"orders/{order_id}/ship"

                response = requests.put(api_url + api_request, headers=headers)

                # Verifica la respuesta del servidor
                if response.status_code not in [200, 204]:
                    # La solicitud fue un fracaso
                    print("ADVERTENCIA_VALIDAR_TRACKER: " + response.text)
                if response.status_code in [200, 204]:
                    # La solicitud fue un fracaso
                    print(f"Pedido de {payment} marcado como enviado: {order_id}")
                    return True
        if orders[0]['order_state'] == 'ORDER_SHIPPED' or orders[0]['order_state'] == 'ORDER_DELIVERED':
            return True
    else:
        print(f"No se ha encontrado el pedido con order_id: {order_id}")

if __name__ == '__main__':
    get_tracking()