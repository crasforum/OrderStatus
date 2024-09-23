import json
import requests

def order_status_colizey(order_id, shipping_id, api_key, api_url, payment):
    headers = {"x-apikey": api_key}

    api_request = f"orders/{order_id}"

    response = requests.get(api_url + api_request, headers=headers)

    if response.status_code in [200, 204]:
        order = json.loads(response.text)
        
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

            items = []
            for item in order['orderLines']:
                itemDict = {
                    "sku": item['sku'],
                    "quantity": item['quantity'],
                }

                items.append(itemDict)

            data = {
                "trackingUrl": "https://correos.es",
                "trackingNumber": shipping_id,
                "shipperId": "fad84407-3d4c-4fc3-ab43-71dec6bcc1d6",
                "items": items,
            }

            request_body = json_data = json.dumps(data)
            response = requests.post(api_url + api_request, headers=headers, data=request_body)

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
