const swaggerJSDoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');
const swaggerDefinitions = require('./swagger-definitions');

const swaggerDefinition = {
  info: {
    title: 'User Service API',
    version: '1.0.0',
    description: 'API documentation for the User Service',
  },
  host: 'localhost:3001',
  basePath: '/',
  securityDefinitions: {
    BearerAuth: {
      type: 'apiKey',
      name: 'Authorization',
      in: 'header',
    },
  },
};

const options = {
  swaggerDefinition,
  apis: ['./user-service.js'], // Update with the path to your main API file
};

const swaggerSpec = swaggerJSDoc(options);

// Extend swaggerSpec with definitions
swaggerSpec.definitions = swaggerDefinitions;

module.exports = swaggerSpec;