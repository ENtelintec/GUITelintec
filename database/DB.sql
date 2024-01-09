-- Verificar si la base de datos existe y eliminarla si es necesario
DROP DATABASE IF EXISTS inventory_management;

-- Crear la base de datos
CREATE DATABASE inventory_management;

-- Usar la base de datos
USE inventory_management;

-- Crear tabla de categorías de productos
CREATE TABLE IF NOT EXISTS product_categories_amc (
    id_category INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS products_amc (
    id_product INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL,
    id_category INT,
    FOREIGN KEY (id_category) REFERENCES product_categories(id_category) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_category (id_category)
);

-- Crear tabla de clientes
CREATE TABLE IF NOT EXISTS customers_amc (
    id_customer INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    INDEX idx_name (name),
    INDEX idx_email (email)
);

-- Crear tabla de dirección de envío de los clientes
CREATE TABLE IF NOT EXISTS customer_addresses_amc (
    id_address INT PRIMARY KEY AUTO_INCREMENT,
    id_customer INT,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Crear tabla de proveedores
CREATE TABLE IF NOT EXISTS suppliers_amc (
    id_supplier INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20)
);

-- Crear tabla de órdenes
CREATE TABLE IF NOT EXISTS orders_amc (
    id_order INT PRIMARY KEY AUTO_INCREMENT,
    id_customer INT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_status ENUM('pending', 'processing', 'complete') DEFAULT 'pending',
    FOREIGN KEY (id_customer) REFERENCES customers(id_customer) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_customer (id_customer)
);

-- Crear tabla de detalles de órdenes
CREATE TABLE IF NOT EXISTS order_details_amc (
    id_order_detail INT PRIMARY KEY AUTO_INCREMENT,
    id_order INT,
    id_product INT,
    quantity INT NOT NULL,
    FOREIGN KEY (id_order) REFERENCES orders(id_order) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_order_product UNIQUE (id_order, id_product),
    INDEX idx_order (id_order),
    INDEX idx_product (id_product)
);

-- Crear tabla de detalles de proveedores y productos
CREATE TABLE IF NOT EXISTS supplier_product_amc (
    id_supplier_product INT PRIMARY KEY AUTO_INCREMENT,
    id_supplier INT,
    id_product INT,
    FOREIGN KEY (id_supplier) REFERENCES suppliers(id_supplier) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
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
    FOREIGN KEY (id_product) REFERENCES products(id_product) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_product_movement (id_product),
    INDEX idx_movement_date (movement_date)
);