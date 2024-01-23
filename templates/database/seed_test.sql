-- Usar la base de datos
USE sql_telintec;

-- Insertar datos de prueba en la tabla product_categories
INSERT INTO
  product_categories_amc (name)
VALUES
  ('Switches'),
  ('Routers'),
  ('Firewalls'),
  ('Cables'),
  ('Computers'),
  ('Printers'),
  ('Storage'),
  ('Software'),
  ('Servers'),
  ('Access Points');

-- Insertar datos de prueba en la tabla products
INSERT INTO
  products_amc (name, description, price, stock, id_category)
VALUES
  (
    'Cisco Catalyst 2960',
    '24-Port Gigabit Switch',
    499.99,
    50,
    10,
    100,
    20,
    1
  ),
  (
    'Cisco ISR 2900 Series',
    'Enterprise Router',
    899.99,
    30,
    5,
    50,
    10,
    2
  ),
  (
    'Fortinet FortiGate 60E',
    'Security Firewall',
    799.99,
    20,
    5,
    30,
    10,
    3
  ),
  (
    'Ubiquiti UniFi AP AC Pro',
    'Wireless Access Point',
    149.99,
    40,
    10,
    80,
    15,
    4
  ),
  (
    'Cisco Catalyst 2960',
    '24-Port Gigabit Switch',
    499.99,
    50,
    10,
    100,
    20,
    1
  ),
  (
    'Cisco ISR 2900 Series',
    'Enterprise Router',
    899.99,
    30,
    5,
    50,
    10,
    2
  ),
  (
    'Fortinet FortiGate 60E',
    'Security Firewall',
    799.99,
    20,
    5,
    30,
    10,
    3
  ),
  (
    'Ubiquiti UniFi AP AC Pro',
    'Wireless Access Point',
    149.99,
    40,
    10,
    80,
    15,
    4
  ),
  (
    'Cisco Catalyst 2960',
    '24-Port Gigabit Switch',
    499.99,
    50,
    10,
    100,
    20,
    1
  ),
  (
    'Cisco ISR 2900 Series',
    'Enterprise Router',
    899.99,
    30,
    5,
    50,
    10,
    2
  );

-- Insertar datos de prueba en la tabla customers
INSERT INTO
  customers_amc (name, email, phone)
VALUES
  (
    'Empresa A',
    'empresaA@example.com',
    '123-456-7890'
  ),
  (
    'Empresa B',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa C',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa D',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa E',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa F',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa G',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa H',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa I',
    'empresaB@example.com',
    '987-654-3210'
  ),
  (
    'Empresa J',
    'empresaB@example.com',
    '987-654-3210'
  );

-- Insertar datos de prueba en la tabla customer_addresses
INSERT INTO
  customer_addresses_amc (id_customer, address, city, postal_code)
VALUES
  (1, 'Calle Principal 123', 'Ciudad A', '12345'),
  (2, 'Calle Principal 456', 'Ciudad B', '67890'),
  (3, 'Calle Principal 789', 'Ciudad C', '13579'),
  (4, 'Calle Principal 012', 'Ciudad D', '24680'),
  (5, 'Calle Principal 345', 'Ciudad E', '12345'),
  (6, 'Calle Principal 678', 'Ciudad F', '67890'),
  (7, 'Calle Principal 901', 'Ciudad G', '13579'),
  (8, 'Calle Principal 234', 'Ciudad H', '24680'),
  (9, 'Calle Principal 567', 'Ciudad I', '12345'),
  (10, 'Calle Principal 890', 'Ciudad J', '67890');

-- Insertar datos de prueba en la tabla suppliers
INSERT INTO
  suppliers_amc (name, address, phone)
VALUES
  (
    'Proveedor A',
    'Dirección Proveedor A',
    '555-1111'
  ),
  (
    'Proveedor B',
    'Dirección Proveedor B',
    '555-2222'
  ),
  (
    'Proveedor C',
    'Dirección Proveedor C',
    '555-3333'
  ),
  (
    'Proveedor D',
    'Dirección Proveedor D',
    '555-4444'
  ),
  (
    'Proveedor E',
    'Dirección Proveedor E',
    '555-5555'
  ),
  (
    'Proveedor F',
    'Dirección Proveedor F',
    '555-6666'
  ),
  (
    'Proveedor G',
    'Dirección Proveedor G',
    '555-7777'
  ),
  (
    'Proveedor H',
    'Dirección Proveedor H',
    '555-8888'
  ),
  (
    'Proveedor I',
    'Dirección Proveedor I',
    '555-9999'
  ),
  (
    'Proveedor J',
    'Dirección Proveedor J',
    '555-0000'
  );

-- Insertar datos de prueba en la tabla orders
INSERT INTO
  orders_amc (id_customer, return_status)
VALUES
  (1, 'complete'),
  (2, 'complete'),
  (3, 'complete'),
  (4, 'complete'),
  (5, 'pending'),
  (6, 'pending'),
  (7, 'pending'),
  (8, 'processing'),
  (9, 'processing'),
  (10, 'processing');

-- Insertar datos de prueba en la tabla order_details
INSERT INTO
  order_details_amc (id_order, id_product, quantity)
VALUES
  (1, 1, 5),
  (1, 3, 10),
  (2, 2, 3),
  (3, 7, 5),
  (4, 5, 6),
  (5, 9, 10),
  (6, 2, 4),
  (7, 4, 22),
  (8, 6, 15),
  (9, 8, 3),
  (10, 10, 2);

-- Insertar datos de prueba en la tabla supplier_product
INSERT INTO
  supplier_product_amc (id_supplier, id_product)
VALUES
  (1, 1),
  (2, 2),
  (3, 3),
  (4, 4),
  (5, 5),
  (6, 6),
  (7, 7),
  (8, 8),
  (9, 9),
  (10, 10);

-- Insertar movimientos de productos
INSERT INTO
  product_movements_amc (
    id_product,
    movement_type,
    quantity,
    movement_date
  )
VALUES
  (1, 'entrada', 20, '2024-01-19 11:00:00'),
  (2, 'entrada', 10, '2024-01-19 12:00:00'),
  (3, 'entrada', 15, '2024-01-19 13:00:00'),
  (4, 'entrada', 5, '2024-01-19 14:00:00'),
  (5, 'entrada', 10, '2024-01-19 15:00:00'),
  (6, 'salida', 20, '2024-01-19 16:00:00'),
  (7, 'salida', 15, '2024-01-19 17:00:00'),
  (8, 'salida', 5, '2024-01-19 18:00:00'),
  (9, 'salida', 10, '2024-01-19 19:00:00'),
  (10, 'salida', 20, '2024-01-19 20:00:00');