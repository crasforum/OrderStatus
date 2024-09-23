import json
import iop

def order_status_miravia(order_id, shipping_id, api_key, api_url, api_secret, access_token, payment):
    client = iop.IopClient(api_url, api_key, api_secret)

    request = iop.IopRequest('/order/items/get', 'GET')
    request.add_api_param('order_id', order_id)
    response = client.execute(request, access_token)

    orders = response.body['data']

    item = orders[0]
        
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