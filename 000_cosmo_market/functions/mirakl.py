import json
import requests

def order_status_mirakl(order_id, shipping_id, api_key, api_url, payment):
    headers = {"Authorization": api_key, "Content-Type" : "application/json"}

    api_request = f"orders"

    params = {
        'order_ids': order_id,
    }

    response = requests.get(api_url + api_request, params=params, headers=headers)

    if response.status_code in [200, 204]:
        orders_dict = json.loads(response.text)
        orders = orders_dict['orders']
        order_lines = []
        
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