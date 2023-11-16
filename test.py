# Primero, definimos la red y la máscara nuevamente
network = "103.3.0.0"
mask = 21

# Convertimos la dirección de red en un número entero
octets = network.split('.')
network_int = (int(octets[0]) << 24) + (int(octets[1])
                                        << 16) + (int(octets[2]) << 8) + int(octets[3])

# El número de host sigue siendo 27851
host_number = 410

# Calcular la dirección IP del host sumando el número de host a la dirección de red
# Debemos tener en cuenta que la dirección de red (primer host) es 13.3.0.0, así que el host número 27851 estará después de este.
host_ip_int = network_int + host_number

# Convertir la dirección IP del host de vuelta a formato decimal con puntos
host_ip_octets = [
    (host_ip_int >> 24) & 255,
    (host_ip_int >> 16) & 255,
    (host_ip_int >> 8) & 255,
    host_ip_int & 255
]

host_ip = '.'.join(map(str, host_ip_octets))
print(host_ip)

network = ["53.0.0.0", "13.0.0.0", "131.3.0.0",
           "103.0.0.0", "194.3.0.0", "153.3.0.0"]
mask = [19, 17, 21, 21, 25, 23]
host = [[[410,4095, 7781],[1229,4095,6962]], [], [], [], [], []]

for net, mask, host in zip(network, mask, host):
