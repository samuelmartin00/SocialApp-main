/**
 * @swagger
 * definitions:
 *   RegistrationRequest:
 *     type: object
 *     properties:
 *       name:
 *         type: string
 *       username:
 *         type: string
 *       email:
 *         type: string
 *       password:
 *         type: string
 *   RegistrationResponse:
 *     type: object
 *     properties:
 *       user_id:
 *         type: integer
 *       name:
 *         type: string
 *       username:
 *         type: string
 *       email:
 *         type: string
 *   LoginRequest:
 *     type: object
 *     properties:
 *       email_or_username:
 *         type: string
 *       password:
 *         type: string
 *   LoginResponse:
 *     type: object
 *     properties:
 *       username:
 *         type: string
 *       token:
 *         type: string
 *   UserProfile:
 *     type: object
 *     properties:
 *       user_id:
 *         type: integer
 *       name:
 *         type: string
 *       username:
 *         type: string
 *       email:
 *         type: string
 *   ErrorResponse:
 *     type: object
 *     properties:
 *       error:
 *         type: string
 */

// Export the definitions directly
module.exports = {
    RegistrationRequest: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
            },
            username: {
                type: 'string',
            },
            email: {
                type: 'string',
            },
            password: {
                type: 'string',
            },
        },
    },
    RegistrationResponse: {
        type: 'object',
        properties: {
            user_id: {
                type: 'integer',
            },
            name: {
                type: 'string',
            },
            username: {
                type: 'string',
            },
            email: {
                type: 'string',
            },
        },
    },
    LoginRequest: {
        type: 'object',
        properties: {
            email_or_username: {
                type: 'string',
            },
            password: {
                type: 'string',
            },
        },
    },
    LoginResponse: {
        type: 'object',
        properties: {
            username: {
                type: 'string',
            },
            token: {
                type: 'string',
            },
        },
    },
    UserProfile: {
        type: 'object',
        properties: {
            user_id: {
                type: 'integer',
            },
            name: {
                type: 'string',
            },
            username: {
                type: 'string',
            },
            email: {
                type: 'string',
            },
        },
    },
    ErrorResponse: {
        type: 'object',
        properties: {
            error: {
                type: 'string',
            },
        },
    },
};