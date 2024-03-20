-- -- Verificar si la base de datos existe y eliminarla si es necesario
-- DROP DATABASE IF EXISTS sql_telintec;
-- -- Crear la base de datos
-- CREATE DATABASE sql_telintec;
-- Usar la base de datos
USE sql_telintec;

-- Crear tabla de categorías de productos
CREATE TABLE IF NOT EXISTS product_categories_amc (
    id_category INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS products_amc (
    id_product INT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    udm VARCHAR(20) NOT NULL,
    -- price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL,
    minStock INT,
    maxStock INT,
    reorderPoint INT,
    id_category INT,
    FOREIGN KEY (id_category) REFERENCES product_categories_amc(id_category) ON DELETE
    SET
        NULL ON UPDATE CASCADE,
        INDEX idx_category (id_category),
        INDEX idx_sku (sku)
);

-- Crear tabla de clientes
CREATE TABLE IF NOT EXISTS customers_amc (
    id_customer INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    rfc VARCHAR(20),
    address VARCHAR(255),
    INDEX idx_name (name)
);

-- Crear tabla de proveedores
CREATE TABLE IF NOT EXISTS suppliers_amc (
    id_supplier INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    seller_name VARCHAR(100),
    seller_email VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(255),
    web_url VARCHAR(255),
    type ENUM('materiales', 'EPP', 'linea') DEFAULT 'materiales',
    INDEX idx_name (name)
);

-- Crear tabla de órdenes
CREATE TABLE IF NOT EXISTS orders_amc (
    id_order INT PRIMARY KEY AUTO_INCREMENT,
    id_customer INT,
    order_date VARCHAR(100),
    sm_code VARCHAR(100),
    contract VARCHAR(100),
    order_number VARCHAR(100),
    operation_plant VARCHAR(100),
    ubication VARCHAR(100),
    requester VARCHAR(100),
    personal VARCHAR(100),
    estimated_date VARCHAR(100),
    status ENUM('pending', 'urgent', 'processing', 'complete') DEFAULT 'pending',
    FOREIGN KEY (id_customer) REFERENCES customers_amc(id_customer) ON DELETE
    SET
        NULL ON UPDATE CASCADE,
        INDEX idx_customer (id_customer)
);

-- Crear tabla de detalles de órdenes
CREATE TABLE IF NOT EXISTS order_details_amc (
    id_order_detail INT PRIMARY KEY AUTO_INCREMENT,
    id_order INT,
    id_product INT,
    quantity INT NOT NULL,
    description VARCHAR(255),
    FOREIGN KEY (id_order) REFERENCES orders_amc(id_order) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products_amc(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_order_product UNIQUE (id_order, id_product),
    INDEX idx_order (id_order),
    INDEX idx_product (id_product)
);

-- Crear tabla de solicitud de movimiento
CREATE TABLE IF NOT EXISTS movement_requests_amc (
    id_request INT PRIMARY KEY AUTO_INCREMENT,
    order_date VARCHAR(100),
    sm_code VARCHAR(100),
    contract VARCHAR(100),
    order_number VARCHAR(100),
    operation_plant VARCHAR(100),
    ubication VARCHAR(100),
    requester VARCHAR(100),
    personal VARCHAR(100),
    estimated_date VARCHAR(100)
);

-- Crear tabla de detalles de solicitud de movimiento
CREATE TABLE IF NOT EXISTS movement_request_details_amc (
    id_request_detail INT PRIMARY KEY AUTO_INCREMENT,
    id_request INT,
    sku VARCHAR(50),
    name VARCHAR(100),
    quantity INT,
    unit VARCHAR(20),
    description VARCHAR(255),
    FOREIGN KEY (id_request) REFERENCES movement_requests_amc(id_request) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_request (id_request)
);

-- Crear tabla de detalles de proveedores y productos
CREATE TABLE IF NOT EXISTS supplier_product_amc (
    id_supplier_product INT PRIMARY KEY AUTO_INCREMENT,
    id_supplier INT,
    id_product INT,
    FOREIGN KEY (id_supplier) REFERENCES suppliers_amc(id_supplier) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products_amc(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_supplier (id_supplier),
    INDEX idx_product_supplier (id_product)
);

-- Crear tabla de movimientos de productos
CREATE TABLE IF NOT EXISTS product_movements_amc (
    id_movement INT PRIMARY KEY AUTO_INCREMENT,
    id_product INT,
    movement_type ENUM('entrada', 'salida') NOT NULL,
    quantity INT NOT NULL,
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_product) REFERENCES products_amc(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_product_movement (id_product),
    INDEX idx_movement_date (movement_date)
);

-- Agregar tabla de herramientas internas
CREATE TABLE IF NOT EXISTS internal_tools_amc (
    id_tool INT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    contract_assigned VARCHAR(100),
    stock INT NOT NULL
);

-- Agregar tabla de inventario de suministros
CREATE TABLE IF NOT EXISTS supply_inventory_amc (
    id_supply INT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    stock INT NOT NULL
);

-- Agregar vista para obtener todos los productos
CREATE VIEW get_all_products AS
SELECT
    products_amc.id_product,
    products_amc.sku,
    products_amc.name,
    products_amc.udm,
    products_amc.stock,
    products_amc.minStock,
    products_amc.maxStock,
    products_amc.reorderPoint,
    product_categories_amc.name AS category_name,
    suppliers_amc.name AS supplier_name
FROM
    products_amc
    LEFT JOIN supplier_product_amc ON products_amc.id_product = supplier_product_amc.id_product
    LEFT JOIN product_categories_amc ON products_amc.id_category = product_categories_amc.id_category
    LEFT JOIN suppliers_amc ON supplier_product_amc.id_supplier = suppliers_amc.id_supplier;

-- Agregar vista para obtener todas las órdenes
CREATE
OR REPLACE VIEW get_all_orders AS
SELECT
    orders_amc.id_order,
    orders_amc.id_customer,
    customers_amc.name AS customer_name,
    orders_amc.order_date,
    orders_amc.sm_code,
    orders_amc.contract,
    orders_amc.order_number,
    orders_amc.operation_plant,
    orders_amc.ubication,
    orders_amc.requester,
    orders_amc.personal,
    orders_amc.estimated_date,
    orders_amc.status,
    GROUP_CONCAT(
        CONCAT(
            products_amc.id_product,
            ' : ',
            products_amc.name,
            ' : ',
            order_details_amc.quantity,
            ' : ',
            order_details_amc.description
        )
        ORDER BY
            order_details_amc.id_order_detail SEPARATOR '; '
    ) AS products_info
FROM
    orders_amc
    JOIN order_details_amc ON orders_amc.id_order = order_details_amc.id_order
    JOIN customers_amc ON orders_amc.id_customer = customers_amc.id_customer
    JOIN products_amc ON order_details_amc.id_product = products_amc.id_product
GROUP BY
    orders_amc.id_order;

CREATE
OR REPLACE VIEW get_all_movement_requests AS
SELECT
    mra.id_request,
    mra.order_date,
    mra.sm_code,
    mra.contract,
    mra.order_number,
    mra.operation_plant,
    mra.ubication,
    mra.requester,
    mra.personal,
    mra.estimated_date,
    GROUP_CONCAT(
        CONCAT(
            mrd.sku,
            ' : ',
            mrd.name,
            ' : ',
            mrd.quantity,
            ' : ',
            mrd.unit,
            ' : ',
            mrd.description
        )
        ORDER BY
            mrd.id_request_detail SEPARATOR '; '
    ) AS movement_details
FROM
    movement_requests_amc mra
    JOIN movement_request_details_amc mrd ON mra.id_request = mrd.id_request
GROUP BY
    mra.id_request;