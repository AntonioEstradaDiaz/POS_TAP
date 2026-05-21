def aplicar_boton(boton, ticket):
    for producto in boton["productos"]:
        ticket.append(producto)

    return ticket