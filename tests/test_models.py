# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
import random
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_a_product(self):
        """It should Read a product"""
        product = ProductFactory()
        app.logger.info(f"test_read_a_product: ProductFactory created: {product}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Fetch the product back and verify all values

        fetched_product = Product.find(product.id)
        self.assertEqual(product.id, fetched_product.id)
        self.assertEqual(product.name, fetched_product.name)
        self.assertEqual(product.description, fetched_product.description)
        self.assertEqual(product.price, fetched_product.price)
        self.assertEqual(product.available, fetched_product.available)
        self.assertEqual(product.category, fetched_product.category)

    def test_update_a_product(self):
        """It should Update a product"""
        product = ProductFactory()
        app.logger.info(f"test_update_a_product: ProductFactory created: {product}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Update description

        new_description = "This is a new description"
        product.description = new_description
        product_original_id = product.id
        product.update()
        self.assertEqual(product_original_id, product.id)
        self.assertEqual(product.description, new_description)

        # Check the database for duplicates and updated value

        products = Product.all()
        self.assertEqual(len(products), 1)
        fetched_product = Product.find(product.id)
        self.assertEqual(fetched_product.id, product.id)
        self.assertEqual(fetched_product.description, new_description)

    def test_update_a_product_without_id(self):
        """It should raise an exception while updating without ID"""
        product = ProductFactory()
        product.create()

        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_create_a_product_with_invalid_availability(self):
        """It should raise an exception when availability is not a boolean"""
        product = ProductFactory()
        product.create()

        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a product"""
        product = ProductFactory()
        app.logger.info(f"test_delete_a_product: ProductFactory created: {product}")
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Check the database to verify that the product exists

        products = Product.all()
        self.assertEqual(len(products), 1)

        # Delete the product

        product.delete()
        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """It should List all products"""

        test_batch_size = 5

        # Check there are no products

        products = Product.all()
        self.assertEqual(len(products), 0)

        # Create n products and store them in the database
        for _ in range(test_batch_size):
            product = ProductFactory()
            product.create()

        # Check there are n products in the database

        products = Product.all()
        self.assertEqual(len(products), test_batch_size)

    def test_find_product_by_name(self):
        """It should Find product by name"""

        test_batch_size = 5

        # Create n products and store them in the database
        products = ProductFactory.create_batch(test_batch_size)
        for product in products:
            product.create()

        # Fetch a random name from the created objects and count the number of its occurences

        random_name = products[random.randrange(0, test_batch_size)].name
        count = len([product for product in products if product.name == random_name])

        # Fetch products with the same name from the database and verify their number
        fetched_products = Product.find_by_name(random_name)
        self.assertEqual(fetched_products.count(), count)
        for fetched_product in fetched_products:
            self.assertEqual(fetched_product.name, random_name)

    def test_find_product_by_availability(self):
        """It should Find product by availability"""

        test_batch_size = 10

        # Create n products and store them in the database
        products = ProductFactory.create_batch(test_batch_size)
        for product in products:
            product.create()

        # Fetch a random product availability from the created objects and
        # count the number of products with the same availability
        random_available = products[random.randrange(0, test_batch_size)].available
        count = len([product for product in products if product.available == random_available])

        # Fetch products with the same availability from the database and verify their number
        fetched_products = Product.find_by_availability(random_available)
        self.assertEqual(fetched_products.count(), count)
        for fetched_product in fetched_products:
            self.assertEqual(fetched_product.available, random_available)

    def test_find_product_by_category(self):
        """It should Find product by category"""

        test_batch_size = 10

        # Create n products and store them in the database
        products = ProductFactory.create_batch(test_batch_size)
        for product in products:
            product.create()

        # Fetch a random product category from the created objects and
        # count the number of products with the same category
        random_category = products[random.randrange(0, test_batch_size)].category
        count = len([product for product in products if product.category == random_category])

        # Fetch products with the same category from the database and verify their number
        fetched_products = Product.find_by_category(random_category)
        self.assertEqual(fetched_products.count(), count)
        for fetched_product in fetched_products:
            self.assertEqual(fetched_product.category, random_category)

    def test_find_product_by_price(self):
        """It should Find product by price"""

        test_batch_size = 10

        # Create n products and store them in the database
        products = ProductFactory.create_batch(test_batch_size)
        for product in products:
            product.create()

        # Fetch a random product price from the created objects, represent it as a string,
        # and count the number of products with the same price
        random_price = products[random.randrange(0, test_batch_size)].price
        count = len([product for product in products if product.price == random_price])
        random_price_string = str(random_price)     # represent it as a string to test conversion

        # Fetch products with the same price from the database and verify their number
        fetched_products = Product.find_by_price(random_price_string)
        self.assertEqual(fetched_products.count(), count)
        for fetched_product in fetched_products:
            self.assertEqual(fetched_product.price, random_price)

    def test_deserialization_empty_args(self):
        """Deserialization should handle empty arguments"""
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.deserialize, None)

    def test_deserialization_incorrect_category(self):
        """Deserialization should handle incorrect category type"""
        product = ProductFactory()
        product_data = product.serialize()
        product_data["category"] = "test_category"
        self.assertRaises(DataValidationError, product.deserialize, product_data)

    def test_deserialization_available_not_bool(self):
        """Deserialization should handle incorrect availability type"""
        product = ProductFactory()
        product_data = product.serialize()
        product_data["available"] = "test"
        self.assertRaises(DataValidationError, product.deserialize, product_data)
