/*
 * Simple proxy to redirect to the React development server
 */
const http = require('http');
const httpProxy = require('http-proxy');

const proxy = httpProxy.createProxyServer();

const server = http.createServer((req, res) => {
  // Proxy all requests to the React development server
  proxy.web(req, res, { target: 'http://localhost:3000' });
});

console.log('Proxy server running on port 3001, forwarding to React dev server on port 3000');
server.listen(3001);