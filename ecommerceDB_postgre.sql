SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

CREATE TABLE brand (
    brandID SERIAL PRIMARY KEY,
    brandName VARCHAR(100) NOT NULL
);

CREATE TABLE category (
    categoryID SERIAL PRIMARY KEY,
    categoryName VARCHAR(100) NOT NULL,
    parentCategoryID INT REFERENCES category(categoryID)
);

CREATE TABLE product (
    productID SERIAL PRIMARY KEY,
    productName VARCHAR(150) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL,
    stock INT NOT NULL,
    brandID INT REFERENCES brand(brandID)
);

CREATE TABLE productCategory (
    productID INT REFERENCES product(productID),
    categoryID INT REFERENCES category(categoryID),
    PRIMARY KEY (productID, categoryID)
);

CREATE TABLE country (
    countryID SERIAL PRIMARY KEY,
    countryName VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE city (
    cityID SERIAL PRIMARY KEY,
    cityName VARCHAR(100) NOT NULL,
    countryID INT REFERENCES country(countryID)
);

CREATE TABLE street (
    streetID SERIAL PRIMARY KEY,
    streetName VARCHAR(100) NOT NULL,
	cityID INT REFERENCES city(cityID)
);

CREATE TABLE address (
    addressID SERIAL PRIMARY KEY,
	houseNo varchar(5) NOT NULL,
	apartNo varchar(5),
    postalCode VARCHAR(20),
    streetID INT REFERENCES street(streetID)
);

CREATE TABLE customer (
    customerID SERIAL PRIMARY KEY,
    firstName VARCHAR(50) NOT NULL,
    secondName VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    addressID INT REFERENCES address(addressID)
);

CREATE TABLE paymentMethod (
    methodID SERIAL PRIMARY KEY,
    methodName VARCHAR(50) NOT NULL
);

CREATE TABLE orderStatus (
    statusID SERIAL PRIMARY KEY,
    statusName VARCHAR(50) NOT NULL
);

CREATE TABLE customerOrder (
    orderID SERIAL PRIMARY KEY,
    orderDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    customerID INT REFERENCES customer(customerID),
    statusID INT REFERENCES orderStatus(statusID),
	shippingAddressID INT REFERENCES address(addressID), 
    totalAmount NUMERIC(10,2),
    paymentMethodID INT REFERENCES paymentMethod(methodID)
);

CREATE TABLE orderItem (
    orderItemID SERIAL PRIMARY KEY,
    orderID INT REFERENCES customerOrder(orderID),
    productID INT REFERENCES product(productID),
    quantity INT NOT NULL,
    unitPrice NUMERIC(10,2) NOT NULL,
    discount NUMERIC(5,2) DEFAULT 0
);

CREATE TABLE review (
    reviewID SERIAL PRIMARY KEY,
    customerID INT REFERENCES customer(customerID),
    productID INT REFERENCES product(productID),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    reviewDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
