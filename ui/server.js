const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const CHATBOT_API_URL = process.env.CHATBOT_API_URL || 'http://localhost:8080';

console.log('Starting UI server...');
console.log(`Port: ${PORT}`);
console.log(`Chatbot API URL: ${CHATBOT_API_URL}`);

// Serve static files from 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Parse JSON bodies
app.use(express.json());

// Proxy endpoint to avoid CORS issues
app.post('/api/chat', async (req, res) => {
    try {
        console.log('Proxying chat request to chatbot service...');
        
        const fetch = (await import('node-fetch')).default;
        
        const response = await fetch(`${CHATBOT_API_URL}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(req.body)
        });

        const data = await response.json();
        
        if (!response.ok) {
            console.error('Error from chatbot:', data);
            return res.status(response.status).json(data);
        }
        
        console.log('Successfully received response from chatbot');
        res.json(data);
    } catch (error) {
        console.error('Error proxying request:', error);
        res.status(500).json({ 
            error: 'Failed to communicate with chatbot',
            details: error.message 
        });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        chatbot_url: CHATBOT_API_URL
    });
});

// Serve index.html for root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ UI server running on http://0.0.0.0:${PORT}`);
    console.log(`📡 Proxying to chatbot at: ${CHATBOT_API_URL}`);
});
