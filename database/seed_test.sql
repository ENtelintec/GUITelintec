-- Usar la base de datos
USE inventory_management;
-- Insertar datos de prueba en la tabla product_categories
INSERT INTO product_categories_amc (name) VALUES
('Electrónicos'),
('Ropa'),
('Hogar'),
('Deportes'),
('Juguetes'),
('Libros'),
('Alimentos'),
('Belleza'),
('Automóviles'),
('Muebles');

-- Insertar datos de prueba en la tabla products
INSERT INTO products_amc (name, description, price, stock, id_category) VALUES
('Teléfono inteligente', 'Pantalla HD, cámara de alta resolución', 499.99, 100, 1),
('Camiseta', 'Talla L, color azul', 19.99, 200, 2),
('Aspiradora', 'Modelo de alta potencia para uso doméstico', 149.99, 50, 3),
('Balón de fútbol', 'Balón oficial de la liga', 29.99, 30, 4),
('Muñeca', 'Muñeca articulada con accesorios', 24.99, 50, 5),
('Libro "El Señor de los Anillos"', 'Edición especial con ilustraciones', 39.99, 80, 6),
('Arroz', 'Arroz blanco de grano largo', 5.99, 300, 7),
('Crema facial', 'Hidratante para piel seca', 14.99, 100, 8),
('Automóvil compacto', 'Modelo eficiente en combustible', 19999.99, 10, 9),
('Sofá', 'Sofá de tres plazas, color beige', 499.99, 20, 10);

-- Insertar datos de prueba en la tabla customers
INSERT INTO customers_amc (name, email, phone) VALUES
('Juan Pérez', 'juan@example.com', '555-1234'),
('María García', 'maria@example.com', '555-5678'),
('Carlos López', 'carlos@example.com', '555-9012'),
('Ana Rodríguez', 'ana@example.com', '555-3456'),
('Pedro Martínez', 'pedro@example.com', '555-7890'),
('Laura Sánchez', 'laura@example.com', '555-2345'),
('Javier Torres', 'javier@example.com', '555-6789'),
('Carmen Ruiz', 'carmen@example.com', '555-1234'),
('Ricardo González', 'ricardo@example.com', '555-5678'),
('Isabel Gómez', 'isabel@example.com', '555-9012');

-- Insertar datos de prueba en la tabla customer_addresses
INSERT INTO customer_addresses_amc (id_customer, address, city, postal_code) VALUES
(1, 'Calle A, 123', 'Ciudad', '12345'),
(2, 'Avenida B, 456', 'Pueblo', '67890'),
(3, 'Calle C, 789', 'Villa', '23456'),
(4, 'Avenida D, 012', 'Ciudad', '78901'),
(5, 'Calle E, 345', 'Pueblo', '23456'),
(6, 'Avenida F, 678', 'Villa', '89012'),
(7, 'Calle G, 901', 'Ciudad', '34567'),
(8, 'Avenida H, 234', 'Pueblo', '90123'),
(9, 'Calle I, 567', 'Villa', '45678'),
(10, 'Avenida J, 890', 'Ciudad', '01234');

-- Insertar datos de prueba en la tabla suppliers
INSERT INTO suppliers_amc (name, address, phone) VALUES
('Proveedor A', 'Calle X, 123', '555-1111'),
('Proveedor B', 'Avenida Y, 456', '555-2222'),
('Proveedor C', 'Calle Z, 789', '555-3333'),
('Proveedor D', 'Avenida W, 012', '555-4444'),
('Proveedor E', 'Calle V, 345', '555-5555'),
('Proveedor F', 'Avenida U, 678', '555-6666'),
('Proveedor G', 'Calle T, 901', '555-7777'),
('Proveedor H', 'Avenida S, 234', '555-8888'),
('Proveedor I', 'Calle R, 567', '555-9999'),
('Proveedor J', 'Avenida Q, 890', '555-0000');

-- Insertar datos de prueba en la tabla orders
INSERT INTO orders_amc (id_customer, return_status) VALUES
(1, 'complete'),
(2, 'pending'),
(3, 'processing'),
(4, 'complete'),
(5, 'pending'),
(6, 'processing'),
(7, 'complete'),
(8, 'pending'),
(9, 'processing'),
(10, 'complete');

-- Insertar datos de prueba en la tabla order_details
INSERT INTO order_details_amc (id_order, id_product, quantity) VALUES
(1, 1, 2),
(2, 3, 1),
(3, 5, 3),
(4, 7, 5),
(5, 9, 1),
(6, 2, 4),
(7, 4, 2),
(8, 6, 1),
(9, 8, 3),
(10, 10, 2);

-- Insertar datos de prueba en la tabla supplier_product
INSERT INTO supplier_product_amc (id_supplier, id_product) VALUES
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