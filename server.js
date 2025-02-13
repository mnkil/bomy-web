const express = require('express');
const app = express();

// existing routes...
app.get('/', (req, res) => {
    res.render('main'); // assuming 'main' is your main page template
});

// Add new route for /EQ
app.get('/EQ', (req, res) => {
    res.render('main'); // reuse the 'main' template for /EQ
});

// existing code... 