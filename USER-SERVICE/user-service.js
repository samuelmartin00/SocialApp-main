const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./swagger'); // Update with the correct path

const app = express();
const port = 3001;

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));



// Replace with your actual PostgreSQL connection string
const pool = new Pool({
    connectionString: 'postgresql://admin:admin@localhost:5555/socialweb',
});

// Middleware to log incoming requests
app.use((req, res, next) => {
    console.log(`Received ${req.method} request at ${req.originalUrl}`);
    console.log('Request Body:', req.body);
    next();
});

// Express built-in JSON parsing middleware
app.use(express.json());


/**
 * @swagger
 * /register:
 *   post:
 *     description: Register a new user
 *     produces:
 *       - application/json
 *     parameters:
 *       - name: user
 *         description: User object
 *         in: body
 *         required: true
 *         schema:
 *           $ref: '#/definitions/RegistrationRequest'
 *     responses:
 *       200:
 *         description: Successful registration
 *         schema:
 *           $ref: '#/definitions/RegistrationResponse'
 */
// Handle user registration
app.post('/register', async (req, res) => {
    
    try {
        const { name, username, email, password } = req.body;

        // Hash the password before storing it
        const hashedPassword = await bcrypt.hash(password, 10);

        const result = await pool.query(
            'INSERT INTO users (name, username, email, password) VALUES ($1, $2, $3, $4) RETURNING *',
            [name, username, email, hashedPassword]
        );

        const newUser = result.rows[0];

        // Instead of sending { newUser }, send newUser directly
        res.json(newUser);
    } catch (error) {
        console.error('Error during user registration:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

/**
 * @swagger
 * /login:
 *   post:
 *     description: Login with email or username
 *     produces:
 *       - application/json
 *     parameters:
 *       - name: credentials
 *         description: Login credentials
 *         in: body
 *         required: true
 *         schema:
 *           $ref: '#/definitions/LoginRequest'
 *     responses:
 *       200:
 *         description: Successful login
 *         schema:
 *           $ref: '#/definitions/LoginResponse'
 */
// Handle user login with email or username
app.post('/login', async (req, res) => {
    try {
        const { email_or_username, password,} = req.body; // Update variable names

        const result = await pool.query(
            'SELECT * FROM users WHERE email = $1 OR username = $2',
            [email_or_username, email_or_username]
        );

        const user = result.rows[0];

        if (!user) {
            res.status(401).json({ error: 'Invalid credentials' });
            return;
        }
        const hashedPassword = user.password; 
        //hashed_password = bcrypt.hash(password,10)
        console.log('Hola -->  ' + email_or_username)
        console.log('Hola -->  ' + password)
        console.log('Hola -->  ' + JSON.stringify(hashedPassword))
        
        // console.log('Hola -->  ' + JSON.stringify({hashed_password}))
        // Compare the hashed password

        // Compare the hashed password
console.log('User from database:', user);
console.log('Provided password:', password);
console.log('Stored hashed password:', user.password);

const passwordMatch = await bcrypt.compare(password, user.password);
console.log('Password match:', passwordMatch);

if (!passwordMatch) {
    res.status(401).json({ error: 'Invalid credentials' });
    return;
}


/*
        const passwordMatch = await bcrypt.compare(password, user.password);
        console.log(passwordMatch)
        if (!passwordMatch) {
            res.status(401).json({ error: 'Invalid credentials' });
            return;
        }
*/

        //email_or_username = username;
        //password = hashedPassword;
        // Generate JWT token
        const token = jwt.sign({ userId: user.id, username: user.username}, 'your-secret-key', { expiresIn: '1h' });

        console.log(token);
        // Return the token
        res.status(200).json({ user: { id: user.id, name: user.name, username: user.username, email: user.email }, token: token });
        return 
    } catch (error) {
        console.error('Error during user login:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});


/**
 * @swagger
 * /edit_profile:
 *   put:
 *     description: Edit user profile
 *     produces:
 *       - application/json
 *     parameters:
 *       - name: user
 *         description: User object
 *         in: body
 *         required: true
 *         schema:
 *           $ref: '#/definitions/UserProfile'
 *     responses:
 *       200:
 *         description: Successful profile edit
 *         schema:
 *           $ref: '#/definitions/UserProfile'
 *       500:
 *         description: Internal Server Error
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 */
// Handle profile editing
app.put('/edit_profile', async (req, res) => {
    try {
        const { id, name, username, email } = req.body;

        const result = await pool.query(
            'UPDATE users SET name = $1, username = $2, email = $3 WHERE id = $4 RETURNING *',
            [name, username, email, id]
        );

        const updatedUser = result.rows[0];
        res.json(updatedUser);
    } catch (error) {
        console.error('Error during profile editing:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

/**
 * @swagger
 * /users:
 *   get:
 *     description: Get all users
 *     produces:
 *       - application/json
 *     responses:
 *       200:
 *         description: Successful retrieval of users
 *         schema:
 *           type: array
 *           items:
 *             $ref: '#/definitions/UserProfile'
 *       500:
 *         description: Internal Server Error
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 */
// Retrieve and return all users
app.get('/users', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM users');
        const users = result.rows.map(user => ({
            user_id: user.id,
            name: user.name,
            username: user.username,
            email: user.email,
        }));
        res.json(users);
    } catch (error) {
        console.error('Error during fetching users:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

/**
 * @swagger
 * /users/username/{username}:
 *   get:
 *     description: Get a user by username
 *     produces:
 *       - application/json
 *     parameters:
 *       - name: username
 *         in: path
 *         description: Username of the user
 *         required: true
 *         type: string
 *     responses:
 *       200:
 *         description: Successful retrieval of user by username
 *         schema:
 *           $ref: '#/definitions/UserProfile'
 *       404:
 *         description: User not found
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 *       500:
 *         description: Internal Server Error
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 */
// Retrieve a user by username
app.get('/users/username/:username', async (req, res) => {
    try {
        const { username } = req.params;
        const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
        console.log("HELLO1 " + username)

        console.log("HELLO1.1 " + result.rowCount)
        if (result.rows.length === 0) {
            res.status(404).json({ error: 'User not found' });
            console.log("HELLO2 " +(result.rows[0].username))
            return;
        }
        //console.log("HELLO3 " + result.rows[0].username)

        const user = result.rows[0];
        

        res.status(200).json({
            user_id: user.id,
            name: user.name,
            username: user.username,
            email: user.email,
        });
    } catch (error) {
        console.error('Error during fetching user by username:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});


/**
 * @swagger
 * /users/id/{id}:
 *   get:
 *     description: Get a user by ID
 *     produces:
 *       - application/json
 *     parameters:
 *       - name: id
 *         in: path
 *         description: ID of the user
 *         required: true
 *         type: integer
 *     responses:
 *       200:
 *         description: Successful retrieval of user by ID
 *         schema:
 *           $ref: '#/definitions/UserProfile'
 *       404:
 *         description: User not found
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 *       500:
 *         description: Internal Server Error
 *         schema:
 *           $ref: '#/definitions/ErrorResponse'
 */
// Retrieve a user by ID
app.get('/users/id/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const result = await pool.query('SELECT * FROM users WHERE id = $1', [id]);

        if (result.rows.length === 0) {
            res.status(404).json({ error: 'User not found' });
            return;
        }

        const user = result.rows[0];
        res.json({
            user_id: user.id,
            name: user.name,
            username: user.username,
            email: user.email,
        });
    } catch (error) {
        console.error('Error during fetching user by ID:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});


// Middleware to log outgoing responses
app.use((req, res, next) => {
    console.log(`Sent ${res.statusCode} response`);
    console.log('Response Body:', res.body);
    next();
});



app.listen(port, () => {
    console.log(`User Service listening at http://localhost:${port}`);
});