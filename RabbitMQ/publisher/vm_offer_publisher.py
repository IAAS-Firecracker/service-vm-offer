#!/usr/bin/env python3
import os
import json
import logging
import pika
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class VMOfferPublisher:
    """
    A utility class to handle RabbitMQ connections and publishing messages
    for the service-vm-offer application.
    """
    
    def __init__(self):
        """Initialize the RabbitMQ connection and channel."""
        self.connection = None
        self.channel = None
        self.exchange_name = os.getenv('SERVICE_VM_OFFER_EXCHANGE', 'vm-offer-exchange')
        #ALL QUEUE NAME
        self.queue_name = f"{self.exchange_name}-vm-offer-queue"
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.user = os.getenv('RABBITMQ_USER', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        
    def connect(self):
        """Establish connection to RabbitMQ server and set up the exchange."""
        try:
            # Create connection parameters
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Establish connection
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare a fanout exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='fanout',
                durable=True
            )

            # # Declare a queue with a unique name for this service
            # self.channel.queue_declare(
            #     queue=self.queue_name,
            #     durable=True,
            #     exclusive=False,
            #     auto_delete=False
            # )
            
            # # Bind the queue to the exchange
            # self.channel.queue_bind(
            #     exchange=self.exchange_name,
            #     queue=self.queue_name
            # )
            
            logger.info(f"Successfully connected to RabbitMQ and declared exchange: {self.exchange_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def publish_vm_offer_event(self, action, vm_offer_data):
        """
        Publish a VM offer event to the exchange.
        
        Args:
            action (str): The action performed (create, update, delete)
            vm_offer_data (dict): The VM offer data
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or self.connection.is_closed:
            if not self.connect():
                return False
        
        try:
            # Prepare the message
            message = {
                'action': action,
                'timestamp': str(datetime.now()),
                'data': vm_offer_data
            }
            
            # Convert to JSON
            message_json = json.dumps(message)
            
            # Publish the message
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key='',  # Not needed for fanout exchange
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published {action} event for VM offer: {vm_offer_data.get('id', 'new')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False
    
    def close(self):
        """Close the RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

# Create a singleton instance
vm_offer_publisher = VMOfferPublisher()

# # For testing
# if __name__ == "__main__":
#     from datetime import datetime
    
#     # Test connection
#     rabbitmq_publisher.connect()
    
#     # Test publishing
#     test_data = {
#         'id': 1,
#         'name': 'Test VM Offer',
#         'description': 'Test Description',
#         'cpu_count': 2,
#         'memory_size_mib': 2048,
#         'disk_size_gb': 20,
#         'price_per_hour': 0.25
#     }
    
#     rabbitmq_publisher.publish_vm_offer_event('create', test_data)
    
#     # Close connection
#     rabbitmq_publisher.close()
