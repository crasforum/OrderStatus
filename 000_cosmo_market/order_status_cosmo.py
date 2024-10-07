import mysql.connector
from markets_credentials import *
from functions import mirakl, miravia, spartoo, colizey, hipercalzado

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

def get_tracking():
    try:
        # Conectarse a la base de datos
        cursor = conn.cursor()

        query = """
        SELECT o.marketplace_order, o.payment, o.current_state, c.shipment_code
        FROM prstshp_orders AS o
        JOIN prstshp_correos_preregister AS c ON o.id_order = c.id_order
        WHERE o.export = 0 AND o.current_state NOT IN (18, 19, 20, 21, 22, 23, 72, 74, 77, 87, 98, 99, 103, 104, 105, 106, 107, 108);
        """

        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            for order in result:
                query = f"""
                SELECT o.id_order, o.marketplace_order, o.payment, o.current_state, c.shipment_code
                FROM prstshp_orders AS o
                JOIN prstshp_correos_preregister AS c ON o.id_order = c.id_order
                WHERE o.marketplace_order = '{order[0]}'
                ORDER BY o.id_order;
                """

                cursor.execute(query)
                resultado = cursor.fetchall()

                multitienda = set()
                if len(resultado)>1:
                    for order_line in resultado:
                        if order_line[3] not in multitienda:
                            multitienda.add(order_line[3])
                            if len(multitienda) > 1:
                                pedido_elegido = resultado[(len(resultado)-1)]
                                break                            
                    if len(multitienda) == 1:
                        pedido_elegido = resultado[0]
                else:
                    pedido_elegido = resultado[0]

                id_pedido, marketplace_order, payment, current_state, shipping_number = pedido_elegido

                flag = False
                match payment:
                    case 'Miravia':
                        flag = miravia.order_status_miravia(marketplace_order, shipping_number, miravia_credentials['api_key'], miravia_credentials['api_url'], miravia_credentials['api_secret'], miravia_credentials['access_token'], payment)
                        pass
                    case 'Tradeinn':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, tradeinn_credentials['api_key'], tradeinn_credentials['api_url'], payment)
                        pass
                    case 'Decathlon':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, decathlon_credentials['api_key'], decathlon_credentials['api_url'], payment)
                        pass
                    case 'Sprinter':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, sprinter_credentials['api_key'], sprinter_credentials['api_url'], payment)
                        pass
                    case 'Carrefour':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, carrefour_credentials['api_key'], carrefour_credentials['api_url'], payment)
                        pass
                    case 'Worten':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, worten_credentials['api_key'], worten_credentials['api_url'], payment)
                        pass
                    case 'ClubeFashion':
                        flag = mirakl.order_status_mirakl(marketplace_order, shipping_number, clubefashion_credentials['api_key'], clubefashion_credentials['api_url'], payment)
                        pass
                    case 'Colizey':
                        flag = colizey.order_status_colizey(marketplace_order, shipping_number, colizey_credentials['api_key'], colizey_credentials['api_url'], payment)
                        pass
                    case 'Hipercalzado':
                        flag = hipercalzado.order_status_hipercalzado(marketplace_order, shipping_number, hipercalzado_credentials['api_key'], hipercalzado_credentials['api_url'], payment)
                        pass
                    case 'Spartoo':
                        flag = spartoo.order_status_spartoo(cf_id, orders_connection, marketplace_order, shipping_number, spartoo_credentials['api_key'])
                        pass
                    case 'Miinto':
                        flag = True
                if flag:
                    # Paso 3: Actualizar el valor de export a 1
                    print(f'Marcando pedido {marketplace_order} como estado de export a 1')
                    update_query = f"UPDATE prstshp_orders SET export = 1 WHERE marketplace_order = '{marketplace_order}'"

                    cursor.execute(update_query)
                    conn.commit()
        
    except Exception as e:
        print(f"Algo ha fallado mientras se gestionaba el tracking del pedido {marketplace_order}: ", e)
    finally:
        cursor.close()
        conn.disconnect()
        orders_connection.disconnect()

if __name__ == '__main__':
    get_tracking()